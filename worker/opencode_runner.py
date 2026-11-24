import os
import sys
import asyncio
import shutil
from pathlib import Path


def _find_opencode() -> list[str]:
    if shutil.which("opencode"):
        return ["opencode"]
    if sys.executable:
        return [sys.executable, "-m", "opencode"]
    raise RuntimeError("opencode not found on PATH or as Python module")


def _build_web_pipeline(
    code_dir: str,
    phases_dir: str,
    skill_dir: str,
    vulnhunt_dir: str,
    docker_analysis: bool,
) -> str:
    steps = [
        (
            "Recon",
            "**Phase 1 - Recon** : Écris ##PHASE: Recon## puis active @sastia_analyzer : "
            f"\"Phase 1. VULNHUNT_DIR={vulnhunt_dir} PHASES_DIR={phases_dir} SKILL_DIR={skill_dir}. "
            "Suis phase1_recon.md. Écris phase1_output.md\"",
        ),
        (
            "Hunt",
            "**Phase 2 - Hunt** : Écris ##PHASE: Hunt## puis lis ${PHASES_DIR}/phase2_hunt.md. "
            "Crée les partitions. Dispatche les agents de traçage (3/partition + sink-driven). "
            "Utilise @sastia_analyzer.",
        ),
        (
            "Verify",
            "**Phase 2b - Verify** : Écris ##PHASE: Verify## puis active @sastia_analyzer : "
            "\"Phase 2b. Mêmes vars. Suis phase2b_verify.md. Écris phase2b_output.md\"",
        ),
        (
            "Reproduce",
            "**Phase 3 - Reproduce/Fix/Sweep** : Écris ##PHASE: Reproduce## puis active "
            "@sastia_analyzer : \"Phase 3. Mêmes vars. Suis phase3_reproduce_test.md, "
            "phase3c_fixes.md, phase3d_sweep.md. Écris poc/, exploit_tests/, phase3_output.md, "
            "phase3d_output.md\"",
        ),
    ]

    if docker_analysis:
        steps.append(
            (
                "Docker",
                "**Docker Build** : Écris ##PHASE: Docker## puis active @sastia_docker avec "
                f"CODE_DIR={code_dir} pour builder l'image et lancer le conteneur. "
                "Récupère ## Docker Environment Summary.",
            )
        )
        steps.append(
            (
                "Docker",
                "**Docker Validation** : Active @sastia_analyzer avec : "
                f"\"Validation Docker. VULNHUNT_DIR={vulnhunt_dir} DOCKER_URL=<url> "
                "DOCKER_CONTAINER=<name>. Pour CHAQUE finding, exécute une ATTAQUE RÉELLE "
                "contre le conteneur en marche (curl, socket brut, client du protocole, "
                "binaire du projet). Ne te contente pas de relancer le test unitaire : si le "
                "test est statique ou simulé, la validation ne prouve rien. Verdicts "
                "autorisés : VALIDATED (attaque réelle exécutée sur la cible + sortie brute "
                "capturée) / STATIC-PROOF (preuve statique seulement : grep, modèle de code, "
                "configuration) / FAILED / NOT-TESTED. Écris validation_results.md avec, PAR "
                "FINDING : la commande exacte, la sortie brute observée (copiée telle quelle, "
                "non paraphrasée) et le verdict.\"",
            )
        )

    steps.append(
        (
            "Report",
            "**Rapport** : Écris ##PHASE: Report## puis active @sastia_rapport. "
            "Suis ${PHASES_DIR}/phase4_report.md. Template obligatoire : en-tête "
            "`# VulnHunter Security Audit Report`, Summary `ID | Title | CWE | "
            "Severity | Exploit Test | Status`, sections Resolved Input Inventory / "
            "Not Found / Code Quality / Sweep / Artifacts. Inclus validation_results.md "
            f"si dispo. Écris le JSON dans {vulnhunt_dir}/report.json",
        )
    )

    if docker_analysis:
        steps.append(
            (
                "Report",
                "**NETTOYAGE** : Active @sastia_docker pour supprimer conteneur + image",
            )
        )

    return "\n\n".join(f"{i}. {text}" for i, (_, text) in enumerate(steps, 1))


def _build_native_pipeline(
    code_dir: str,
    phases_dir: str,
    skill_dir: str,
    vulnhunt_dir: str,
    docker_analysis: bool,
) -> str:
    common = f"VULNHUNT_DIR={vulnhunt_dir} PHASES_DIR={phases_dir} SKILL_DIR={skill_dir}"
    dynamic = (
        "TARGET_MODE=dynamic, DOCKER_CONTAINER=<name>, DOCKER_URL=<url>"
        if docker_analysis
        else "TARGET_MODE=static"
    )

    steps = [
        (
            "Shaping",
            "**Phase 0 - Target Shaping** : Écris ##PHASE: Shaping## puis active "
            f"@sastia_analyzer : \"Phase 0. {common}. Suis phase0_target_shaping.md. "
            "Écris target_shaping.md\"",
        ),
        (
            "Recon",
            "**Phase 1 - Recon** : Écris ##PHASE: Recon## puis active @sastia_analyzer : "
            f"\"Phase 1. {common}. Suis phase1_recon.md. Écris phase1_output.md, "
            "state_identity_inventory.md, invariant_register.md, negative_space.md, "
            "risk_ranking.md\"",
        ),
        (
            "Hunt",
            "**Phase 2 - Hunt** : Écris ##PHASE: Hunt## puis lis ${PHASES_DIR}/phase2_hunt.md. "
            "Crée les partitions natives. Dispatche 1 agent par lens (INJ/AUTH/MEM/PROTO/IDENT) "
            "et par partition, plus un agent sink-driven. Minimum (5 × partitions) + 1, "
            "en vagues de 6 maximum. Utilise @sastia_analyzer.",
        ),
        (
            "Verify",
            "**Phase 2b - Verify** : Écris ##PHASE: Verify## puis active @sastia_analyzer : "
            "\"Phase 2b. Mêmes vars. Suis phase2b_verify.md. Lis results/, "
            "state_identity_inventory.md, invariant_register.md, negative_space.md. "
            "Écris phase2b_output.md et latent_defects.md\"",
        ),
        (
            "Compose",
            "**Phase 2c - Composition** : Écris ##PHASE: Compose## puis active @sastia_analyzer : "
            "\"Phase 2c. Mêmes vars. Suis phase2c_composition.md. Écris phase2c_output.md\"",
        ),
    ]

    if docker_analysis:
        steps.append(
            (
                "Docker",
                "**Docker Build** : Écris ##PHASE: Docker## puis active @sastia_docker avec "
                f"CODE_DIR={code_dir} pour builder l'image et lancer le conteneur. "
                "Récupère ## Docker Environment Summary.",
            )
        )

    steps.append(
        (
            "Reproduce",
            "**Phase 3 - Reproduce/Test/Validate** : Écris ##PHASE: Reproduce## puis active "
            f"@sastia_analyzer : \"Phase 3. {common}. {dynamic}. Suis "
            "phase3_reproduce_test.md. Lis phase2b_output.md et phase2c_output.md. "
            "Écris poc/, exploit_tests/, evidence/, phase3_output.md. "
            "Si TARGET_MODE=dynamic, exécute la validation (ASan/UBSan/KASan, harness, "
            "paquets) dans le conteneur et écris validation_results.md avec, PAR FINDING : "
            "la commande exacte, la sortie brute (rapport sanitizer, crash, code retour) et "
            "le verdict — VALIDATED (attaque réellement exécutée) / STATIC-PROOF (grep, "
            "modèle de code, configuration) / FAILED / NOT-TESTED. Un test tautologique ou "
            "simulé ne valide rien. Sinon marque les findings non prouvés Potential.\"",
        )
    )
    steps.append(
        (
            "Sweep",
            "**Phase 3d - Sweep** : Écris ##PHASE: Sweep## puis active @sastia_analyzer : "
            "\"Phase 3d. Mêmes vars. Suis phase3d_sweep.md. Écris phase3d_output.md\"",
        )
    )
    steps.append(
        (
            "Report",
            "**Rapport** : Écris ##PHASE: Report## puis active @sastia_rapport. "
            "Suis ${PHASES_DIR}/phase4_report.md pour le contenu natif, mais produis "
            "le **même template** que le pipeline web : en-tête `# VulnHunter Security "
            "Audit Report`, Summary `ID | Title | CWE | Severity | Exploit Test | "
            "Status` (ne pas insérer Lens dans cette table), sections Resolved Input "
            "Inventory / Not Found / Code Quality / Sweep / Artifacts, puis ajoute "
            "Confirmed compositions / Latent defects / Coverage artifacts. Inclus "
            f"validation_results.md si dispo. Écris le JSON dans {vulnhunt_dir}/report.json",
        )
    )

    if docker_analysis:
        steps.append(
            (
                "Report",
                "**NETTOYAGE** : Active @sastia_docker pour supprimer conteneur + image",
            )
        )

    return "\n\n".join(f"{i}. {text}" for i, (_, text) in enumerate(steps, 1))


async def run_manager_agent(
    code_dir: str,
    audit_id: str,
    callback_url: str,
    repo_url: str | None = None,
    model_id: str | None = None,
    report_language: str = "en",
    docker_analysis: bool = False,
    callback_secret: str | None = None,
    timeout: int = 18000,
    target_type: str = "web",
    target_detection: dict | None = None,
    results_dir: str | None = None,
) -> str:
    audit_dir = os.path.dirname(code_dir)
    worker_log = os.path.join(audit_dir, "opencode.log")
    partial_file = os.path.join(audit_dir, "agent-partial.md")
    prompt_file = os.path.join(audit_dir, "prompt.txt")

    source_desc = repo_url or f"uploaded file (extracted to {code_dir})"

    report_language_instruction = {
        "fr": "Le rapport final DOIT être rédigé en français.",
        "en": "The final report MUST be written in English.",
    }.get(report_language, "The final report MUST be written in English.")

    target_type = "native" if target_type == "native" else "web"
    skill_name = "vulnhunt-native" if target_type == "native" else "vulnhunt"
    results_name = "vulnhunt_native_results" if target_type == "native" else "vulnhunt_results"
    vulnhunt_dir = results_dir or os.path.join(code_dir, results_name)

    skill_dir = os.path.expanduser(f"~/.config/opencode/skills/{skill_name}")
    phases_dir = os.path.join(skill_dir, "phases")

    detection = target_detection or {}
    evidence = "; ".join(detection.get("reasons") or []) or "n/a"
    confidence = detection.get("confidence", "n/a")
    target_label = (
        "non-web / native (librairie, service, daemon, driver, firmware, parser)"
        if target_type == "native"
        else "web (application, API, site, service HTTP)"
    )

    if target_type == "native":
        pipeline = _build_native_pipeline(
            code_dir, phases_dir, skill_dir, vulnhunt_dir, docker_analysis
        )
        pipeline_note = (
            "Méthodologie native : lenses INJ/AUTH/MEM/PROTO/IDENT + composition (Phase 2c). "
            "Les invariants, l'état, les pools et les défauts latents font partie de la preuve. "
        )
    else:
        pipeline = _build_web_pipeline(
            code_dir, phases_dir, skill_dir, vulnhunt_dir, docker_analysis
        )
        pipeline_note = (
            "Méthodologie web : inventaire des entrées, traçage input → sink, "
            "vérification adversariale, sweep. "
        )

    prompt = f"""Tu es SastIA_manager, l'orchestrateur d'audit de sécurité de SAST IA.

Le code source à analyser se trouve ici : {code_dir}
Il provient de : {source_desc}
L'ID de l'audit est : {audit_id}
{report_language_instruction}

## Classification de la cible (déjà effectuée par le worker)

- TARGET_TYPE={target_type}
- TARGET_LABEL={target_label}
- TARGET_CLASS_CONFIDENCE={confidence}
- TARGET_CLASS_EVIDENCE={evidence}
- SKILL_NAME={skill_name}

Le worker a pré-classé la cible. Utilise **uniquement** la méthodologie
`{skill_name}` via `${{SKILL_DIR}}/SKILL.md`. Si les premiers fichiers inspectés
contredisent manifestement cette classification, signale-le dans le rapport
(section "Not found / excluded") mais ne mélange pas les deux méthodologies.

## Variables
- CODE_DIR={code_dir}
- VULNHUNT_DIR={vulnhunt_dir}
- PHASES_DIR={phases_dir}
- SKILL_DIR={skill_dir}
- CALLBACK_URL={callback_url} (le worker envoie le callback automatiquement)
- DOCKER_ENABLED={'true' if docker_analysis else 'false'}
- TARGET_MODE={'dynamic' if docker_analysis else 'static'}

Compatible tous modèles. L'ANALYSE est statique, mais les tests d'exploit DOIVENT être exécutés :
**Bash is AVAILABLE for exploit-test execution** (`--no-read-only --enable-bash`). Écris des tests
exécutables, lance-les contre la cible, et colle la sortie brute observée.
Si DOCKER_ENABLED, la validation dynamique s'exécute dans le conteneur Docker. {pipeline_note}

## Pipeline

Suis `${{SKILL_DIR}}/SKILL.md`. Phases dans `${{PHASES_DIR}}/`.

{pipeline}

IMPORTANT : Ne fais pas d'analyse toi-même. Dispatche TOUT."""

    DEFAULT_MODEL = "opencode/deepseek-v4-flash-free"

    model = model_id or os.environ.get("OPENCODE_MODEL", DEFAULT_MODEL)
    if model and "/" not in model:
        model = f"opencode-go/{model}"
    opencode_cmd = _find_opencode()
    Path(prompt_file).write_text(prompt, encoding="utf-8")
    # NOTE: OpenCode 2 removed the `run --dir` flag. The working directory is
    # set with the subprocess `cwd=` below, which is what `--dir` did.
    cmd = [
        *opencode_cmd, "run",
        "--model", model,
        prompt,
    ]

    print(f"[opencode] Launching agent with model {model}...")
    print(f"[opencode] Workspace dir: {audit_dir}")
    print(f"[opencode] Code dir: {code_dir}")
    print(f"[opencode] Callback: {callback_url}")
    print(f"[opencode] Log file: {worker_log}")
    print(f"[opencode] Command: {' '.join(cmd[:4])} ...")

    collected_lines: list[str] = []
    save_interval = 30
    last_save = asyncio.get_event_loop().time()

    async def _stream(stream_name: str, stream: asyncio.StreamReader | None, log_f):
        nonlocal last_save
        if stream is None:
            return
        while True:
            line = await stream.readline()
            if not line:
                break
            text = line.decode(errors="replace")
            log_f.write(f"[{stream_name}] {text}")
            log_f.flush()
            collected_lines.append(text)

            now = asyncio.get_event_loop().time()
            if now - last_save > save_interval:
                last_save = now
                partial = "".join(collected_lines[-200:])
                try:
                    Path(partial_file).write_text(partial, encoding="utf-8")
                except OSError:
                    pass

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=audit_dir,
        )

        with open(worker_log, "w", encoding="utf-8") as lf:
            lf.write(f"# opencode log — audit {audit_id}\n")
            import time as ttime
            lf.write(f"# started at {ttime.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            lf.flush()

            stdout_task = asyncio.create_task(_stream("stdout", proc.stdout, lf))
            stderr_task = asyncio.create_task(_stream("stderr", proc.stderr, lf))

            try:
                await asyncio.wait_for(
                    asyncio.gather(stdout_task, stderr_task, proc.wait()),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                lf.write(f"\n\n[TIMEOUT] Agent timed out after {timeout}s ({timeout//3600}h)\n")
                lf.flush()
                proc.kill()
                _ = await asyncio.wait_for(proc.wait(), timeout=10.0)
                partial = "".join(collected_lines)
                if partial.strip():
                    Path(partial_file).write_text(partial, encoding="utf-8")
                raise RuntimeError(
                    f"SastIA_manager agent timed out after {timeout}s. "
                    f"Log: {worker_log} (lines collected: {len(collected_lines)})"
                )

        return_code = await proc.wait()
        result = "".join(collected_lines)

        if result.strip():
            Path(partial_file).write_text(result, encoding="utf-8")

        if return_code != 0:
            print(f"[opencode] Agent exited with code {return_code}")
            if not result.strip():
                raise RuntimeError(f"Agent exited with code {return_code} and no output")

        print(f"[opencode] SastIA_manager agent completed (exit code {return_code}, {len(collected_lines)} lines)")
        return result

    except FileNotFoundError:
        raise RuntimeError("opencode not found. Install: pip install opencode")
