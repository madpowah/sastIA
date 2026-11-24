"""Detect the kind of target a SAST IA audit is running against.

The worker uses this before launching the manager agent so that it can pick
the right VulnHunter skill:

* ``web``    -> ``vulnhunt`` (HTTP apps, APIs, web services, managed runtimes)
* ``native`` -> ``vulnhunt-native`` (libraries, daemons, drivers, firmware,
                protocol parsers, anything with memory/lifetime primitives)

The detector is intentionally heuristic and deterministic. It only inspects
file names, extensions and a bounded sample of file contents; it never executes
the target. An explicit hint (``analysis_type`` = ``web``/``native``) always
wins over the heuristic.
"""

from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

WEB = "web"
NATIVE = "native"
AUTO = "auto"

# ── Scan limits ───────────────────────────────────────────────────────────────
MAX_FILES = 40_000
MAX_CONTENT_FILES = 4_000
MAX_FILE_BYTES = 1_000_000

IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode",
    "node_modules", "vendor", "third_party", "third-party", "external",
    "deps", "dist", "build", "out", "target", "bin", "obj",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".tox", ".venv", "venv",
    "coverage", ".next", ".nuxt", "venv-native", "virtualenv",
    "vulnhunt_results", "vulnhunt_native_results",
}

NATIVE_SOURCE_EXTS = {
    ".c", ".h", ".cc", ".cpp", ".cxx", ".c++", ".hpp", ".hh", ".hxx",
    ".rs", ".asm", ".s", ".S", ".ld", ".lds", ".dts", ".dtsi", ".ino",
}

CONFIG_NAMES = {
    "package.json", "requirements.txt", "pyproject.toml", "pipfile",
    "gemfile", "gemfile.lock", "composer.json", "pom.xml", "build.gradle",
    "build.gradle.kts", "settings.gradle", "cargo.toml", "cmakelists.txt",
    "makefile", "meson.build", "configure.ac", "go.mod", "angular.json",
    "next.config.js", "next.config.mjs", "nuxt.config.js", "nuxt.config.ts",
    "vite.config.js", "vite.config.ts", "manage.py", "wsgi.py", "asgi.py",
    "urls.py", "settings.py", "artisan", "index.php",
}

# ── Native signals ────────────────────────────────────────────────────────────
KERNEL_PATTERNS = [
    r"#include\s*<linux/",
    r"\bmodule_init\s*\(",
    r"\bmodule_exit\s*\(",
    r"\bMODULE_LICENSE\b",
    r"\bEXPORT_SYMBOL",
    r"\bcopy_from_user\b",
    r"\bcopy_to_user\b",
    r"\bioctl\s*\(",
    r"\bDriverEntry\b",
    r"\bIRP_MJ_",
    r"\bNTSTATUS\b",
    r"\bWDF_[A-Z]",
    r"\bcontainer_of\b",
    r"\bspin_lock",
    r"\b__user\b",
    r"\bdevm_kzalloc\b",
    r"\bplatform_driver\b",
    r"\bKASAN\b",
]

MEMORY_PATTERNS = [
    r"\bmalloc\s*\(",
    r"\bcalloc\s*\(",
    r"\brealloc\s*\(",
    r"\bfree\s*\(",
    r"\bmemcpy\s*\(",
    r"\bmemmove\s*\(",
    r"\bmemset\s*\(",
    r"\bstrcpy\s*\(",
    r"\bstrcat\s*\(",
    r"\bsprintf\s*\(",
    r"\bsnprintf\s*\(",
    r"\balloca\s*\(",
    r"\bmmap\s*\(",
    r"\bmunmap\s*\(",
    r"\bVirtualAlloc\b",
    r"\bHeapAlloc\b",
    r"\bunsafe\s*\{",
    r"\btransmute\b",
    r"\bfrom_raw_parts\b",
    r"\bBox::from_raw\b",
]

NATIVE_BUILD_PATTERNS = [
    r"\bobj-m\b",
    r"\badd_library\s*\(",
    r"\badd_executable\s*\(",
    r"\bcmake_minimum_required\s*\(",
    r"\bproject\s*\(",
    r"\bmeson\.build",
    r"crate-type\s*=\s*\[[^\]]*(cdylib|staticlib)",
    r"#!\[no_std\]",
    r"\bLD\s*=",
    r"\bCC\s*=",
    r"-fsanitize=",
]

NATIVE_BINARY_EXTS = {".ko", ".sys", ".dll", ".so", ".a", ".o"}

# ── Web signals ───────────────────────────────────────────────────────────────
WEB_FRAMEWORK_PATTERNS = [
    r"@app\.(?:route|get|post|put|patch|delete)\s*\(",
    r"\bAPIRouter\s*\(",
    r"\bFlask\s*\(",
    r"\bFastAPI\s*\(",
    r"\bStarlette\s*\(",
    r"\bexpress\s*\(",
    r"\b(?:router|app)\.(?:get|post|put|patch|delete|use)\s*\(",
    r"\bserver\.listen\s*\(",
    r"\bapp\.listen\s*\(",
    r"@(?:Get|Post|Put|Patch|Delete|Request)Mapping",
    r"\bHttpServlet\b",
    r"\bRestController\b",
    r"\bRoute::(?:get|post|put|patch|delete)\s*\(",
    r"<\?php",
    r"<form\b",
    r"\bfetch\s*\(",
    r"\baxios\.",
    r"from\s+['\"]react['\"]",
    r"from\s+['\"]vue['\"]",
    r"\bngOnInit\b",
    r"\bdangerouslySetInnerHTML\b",
]

WEB_DEPENDENCY_PATTERN = re.compile(
    r"(?:^|[\s\"'/:@])(?:express|koa|fastify|hapi|@nestjs/core|next|nuxt|"
    r"react-dom|react|vue|@angular/core|svelte|astro|django|flask|fastapi|"
    r"starlette|tornado|pyramid|rails|sinatra|laravel/framework|"
    r"symfony/framework-bundle|spring-boot-starter-web|spring-webmvc|"
    r"Microsoft\.AspNetCore|actix-web|axum|rocket|warp)(?:[\s\"'/:=,)]|$)",
    re.IGNORECASE,
)

WEB_STRUCTURE_NAMES = {
    "manage.py": 5,
    "urls.py": 4,
    "wsgi.py": 5,
    "asgi.py": 5,
    "settings.py": 2,
    "artisan": 5,
    "index.php": 2,
    "next.config.js": 5,
    "next.config.mjs": 5,
    "nuxt.config.js": 5,
    "nuxt.config.ts": 5,
    "angular.json": 5,
    "vite.config.js": 2,
    "vite.config.ts": 2,
    "composer.json": 2,
    "gemfile": 2,
    "package.json": 1,
    "requirements.txt": 1,
    "pyproject.toml": 1,
    "pom.xml": 1,
    "build.gradle": 1,
    "go.mod": 1,
}

WEB_DIR_NAMES = {
    "routes": 3, "controllers": 3, "views": 2, "templates": 2,
    "static": 1, "public": 1, "pages": 2, "components": 1, "app": 1,
    "api": 1, "middleware": 2, "handlers": 1,
}

MANAGED_EXTS = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".rb", ".php",
    ".java", ".kt", ".kts", ".cs", ".go", ".swift", ".scala", ".vue",
    ".svelte", ".html", ".htm", ".erb", ".twig", ".ejs", ".hbs", ".pug",
}


@dataclass
class TargetDetection:
    target_type: str
    confidence: str
    reasons: list[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    @property
    def skill_name(self) -> str:
        return "vulnhunt-native" if self.target_type == NATIVE else "vulnhunt"

    @property
    def results_dir_name(self) -> str:
        return "vulnhunt_native_results" if self.target_type == NATIVE else "vulnhunt_results"

    def to_dict(self) -> dict:
        return {
            "target_type": self.target_type,
            "confidence": self.confidence,
            "skill": self.skill_name,
            "results_dir": self.results_dir_name,
            "reasons": self.reasons,
            "stats": self.stats,
        }


def _normalize_hint(hint: str | None) -> str | None:
    if not hint:
        return None
    value = hint.strip().lower()
    if value in (WEB, "vulnhunt", "webapp", "web-app", "application"):
        return WEB
    if value in (NATIVE, "vulnhunt-native", "vulnhunt_native", "non-web", "binary"):
        return NATIVE
    return None  # "code", "auto" and unknown values trigger detection


def _iter_files(root: Path):
    seen = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames
            if d.lower() not in IGNORED_DIRS and not d.startswith(".git")
        )
        for name in filenames:
            if name.startswith(".") and name not in (".env", ".env.example"):
                continue
            path = Path(dirpath) / name
            try:
                if not path.is_file() or path.is_symlink():
                    continue
            except OSError:
                continue
            yield path
            seen += 1
            if seen >= MAX_FILES:
                return


def _read_sample(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, ValueError):
        return None


def _weighted_extension_score(counts: Counter) -> float:
    return (
        counts.get(".c", 0) * 1.0
        + counts.get(".cc", 0) * 1.0
        + counts.get(".cpp", 0) * 1.0
        + counts.get(".cxx", 0) * 1.0
        + counts.get(".c++", 0) * 1.0
        + counts.get(".rs", 0) * 1.0
        + counts.get(".h", 0) * 0.3
        + counts.get(".hpp", 0) * 0.3
        + counts.get(".hh", 0) * 0.3
        + counts.get(".asm", 0) * 1.5
        + counts.get(".s", 0) * 1.5
        + counts.get(".S", 0) * 1.5
        + counts.get(".ld", 0) * 1.0
        + counts.get(".dts", 0) * 1.5
        + counts.get(".dtsi", 0) * 1.5
        + counts.get(".ino", 0) * 1.5
    )


def _web_extension_score(counts: Counter) -> float:
    return (
        counts.get(".php", 0) * 0.8
        + counts.get(".jsx", 0) * 1.0
        + counts.get(".tsx", 0) * 1.0
        + counts.get(".vue", 0) * 1.5
        + counts.get(".svelte", 0) * 1.5
        + counts.get(".html", 0) * 0.4
        + counts.get(".htm", 0) * 0.4
        + counts.get(".css", 0) * 0.1
        + counts.get(".scss", 0) * 0.1
        + counts.get(".erb", 0) * 0.8
        + counts.get(".twig", 0) * 0.8
        + counts.get(".ejs", 0) * 0.8
        + counts.get(".hbs", 0) * 0.8
        + counts.get(".pug", 0) * 0.8
    )


def detect_target(code_dir: str | Path, hint: str | None = None) -> TargetDetection:
    """Classify ``code_dir`` as ``web`` or ``native``.

    ``hint`` is the audit's ``analysis_type`` (or an env override). Values
    ``web`` and ``native`` force the result; anything else triggers detection.
    """
    forced = _normalize_hint(hint)
    if forced:
        return TargetDetection(
            target_type=forced,
            confidence="high",
            reasons=[f"explicit hint: {hint}"],
            stats={"forced": True},
        )

    root = Path(code_dir)
    if not root.exists():
        return TargetDetection(WEB, "low", [f"missing directory: {root}"], {})

    ext_counts: Counter = Counter()
    dir_names: Counter = Counter()
    native_source_files = 0
    managed_source_files = 0
    native_binaries = 0
    kernel_hits = 0
    memory_hits = 0
    web_marker_hits = 0
    web_dependency_hits = 0
    native_build_hits = 0
    web_structure_score = 0.0
    scanned = 0
    sampled = 0
    build_files: list[str] = []

    for path in _iter_files(root):
        scanned += 1
        suffix = path.suffix.lower()
        name = path.name.lower()
        ext_counts[suffix] += 1
        if suffix in NATIVE_SOURCE_EXTS:
            native_source_files += 1
        if suffix in MANAGED_EXTS:
            managed_source_files += 1
        if suffix in NATIVE_BINARY_EXTS:
            native_binaries += 1

        web_structure_score += WEB_STRUCTURE_NAMES.get(name, 0)

        for parent in path.relative_to(root).parts[:-1]:
            if parent.lower() in WEB_DIR_NAMES:
                dir_names[parent.lower()] += 1
                web_structure_score += 0.5

        is_build_file = name in {
            "cmakelists.txt", "makefile", "meson.build", "configure.ac",
            "cargo.toml", "package.json", "requirements.txt", "pyproject.toml",
            "gemfile", "composer.json", "pom.xml", "build.gradle", "go.mod",
        }
        is_native_file = suffix in NATIVE_SOURCE_EXTS or is_build_file
        is_web_file = suffix in MANAGED_EXTS or (is_build_file and suffix != ".toml")

        should_sample = (
            sampled < MAX_CONTENT_FILES
            and (is_native_file or is_web_file or name in CONFIG_NAMES)
        )
        if not should_sample:
            continue
        content = _read_sample(path)
        if content is None:
            continue
        sampled += 1

        if suffix in NATIVE_SOURCE_EXTS or name in {"cmakelists.txt", "makefile", "cargo.toml", "meson.build", "configure.ac"}:
            for pattern in KERNEL_PATTERNS:
                kernel_hits += len(re.findall(pattern, content, re.IGNORECASE))
            for pattern in MEMORY_PATTERNS:
                memory_hits += len(re.findall(pattern, content))
            for pattern in NATIVE_BUILD_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    native_build_hits += 1

        if suffix in MANAGED_EXTS or name in CONFIG_NAMES:
            for pattern in WEB_FRAMEWORK_PATTERNS:
                web_marker_hits += len(re.findall(pattern, content, re.IGNORECASE))
            web_dependency_hits += len(WEB_DEPENDENCY_PATTERN.findall(content))

        if is_build_file and name not in build_files:
            build_files.append(name)

    native_ext_score = min(_weighted_extension_score(ext_counts), 12.0)
    web_ext_score = min(_web_extension_score(ext_counts), 12.0)
    web_dir_score = min(
        sum(min(count, 4) * WEB_DIR_NAMES.get(name, 1) for name, count in dir_names.items())
        * 0.25,
        6.0,
    )
    web_structure_score = min(web_structure_score, 10.0)

    native_score = (
        native_ext_score
        + min(kernel_hits * 3.0, 18.0)
        + min(memory_hits * 0.25, 10.0)
        + min(native_build_hits * 2.0, 8.0)
        + min(native_binaries * 1.0, 4.0)
    )
    web_score = (
        web_ext_score
        + web_structure_score
        + web_dir_score
        + min(web_marker_hits * 1.0, 12.0)
        + min(web_dependency_hits * 4.0, 12.0)
    )

    stats = {
        "files_scanned": scanned,
        "files_sampled": sampled,
        "native_source_files": native_source_files,
        "managed_source_files": managed_source_files,
        "native_binaries": native_binaries,
        "kernel_hits": kernel_hits,
        "memory_hits": memory_hits,
        "web_marker_hits": web_marker_hits,
        "web_dependency_hits": web_dependency_hits,
        "native_build_hits": native_build_hits,
        "native_score": round(native_score, 2),
        "web_score": round(web_score, 2),
        "extensions": dict(ext_counts.most_common(12)),
        "build_files": build_files[:12],
    }

    reasons: list[str] = []

    # Hard signal: kernel/driver code is always native, even with a web admin UI.
    if kernel_hits >= 3:
        reasons.append(
            f"{kernel_hits} kernel/driver signals (module_init, copy_from_user, ioctl, ...)"
        )
        if native_source_files >= 1:
            reasons.append(f"{native_source_files} C/C++/Rust/asm source files")
        return TargetDetection(NATIVE, "high", reasons, stats)

    if native_source_files == 0 and managed_source_files > 0:
        reasons.append(
            f"no native source; {managed_source_files} managed/web source files"
        )
        if web_marker_hits:
            reasons.append(f"{web_marker_hits} web framework/HTTP markers")
        if web_dependency_hits:
            reasons.append(f"{web_dependency_hits} web framework dependency references")
        confidence = "high" if web_score >= 4 else "medium"
        return TargetDetection(WEB, confidence, reasons, stats)

    if native_score >= 7 and native_score > web_score * 1.2:
        reasons.append(
            f"native score {native_score:.1f} > web score {web_score:.1f}"
        )
        if native_source_files:
            reasons.append(f"{native_source_files} native source files")
        if memory_hits:
            reasons.append(f"{memory_hits} memory/lifetime API calls (malloc/free/memcpy/unsafe, ...)")
        if kernel_hits:
            reasons.append(f"{kernel_hits} kernel/driver signals")
        return TargetDetection(NATIVE, "high", reasons, stats)

    if native_source_files >= 10 and web_score < 4:
        reasons.append(
            f"{native_source_files} native source files vs weak web signals (score {web_score:.1f})"
        )
        if memory_hits:
            reasons.append(f"{memory_hits} memory/lifetime API calls")
        return TargetDetection(NATIVE, "medium", reasons, stats)

    if web_score >= 5 and web_score >= native_score:
        reasons.append(
            f"web score {web_score:.1f} >= native score {native_score:.1f}"
        )
        if web_marker_hits:
            reasons.append(f"{web_marker_hits} web framework/HTTP markers")
        if web_dependency_hits:
            reasons.append(f"{web_dependency_hits} web framework dependency references")
        if managed_source_files:
            reasons.append(f"{managed_source_files} managed/web source files")
        return TargetDetection(WEB, "high", reasons, stats)

    if web_score >= 2 and native_score < 5:
        reasons.append(
            f"web indicators present (score {web_score:.1f}) with weak native signals ({native_score:.1f})"
        )
        return TargetDetection(WEB, "medium", reasons, stats)

    if native_score > web_score:
        reasons.append(
            f"native score {native_score:.1f} > web score {web_score:.1f}"
        )
        return TargetDetection(NATIVE, "medium", reasons, stats)

    # Nothing conclusive: the web pipeline is the safe default (it was the
    # historical behaviour of SAST IA and handles any managed codebase).
    reasons.append(
        f"inconclusive (native {native_score:.1f} / web {web_score:.1f}); defaulting to web"
    )
    return TargetDetection(WEB, "low", reasons, stats)


def detect_from_env(code_dir: str | Path, hint: str | None = None) -> TargetDetection:
    """Like :func:`detect_target` but honours ``SASTIA_TARGET_TYPE``."""
    env_hint = os.getenv("SASTIA_TARGET_TYPE")
    return detect_target(code_dir, hint=env_hint or hint)
