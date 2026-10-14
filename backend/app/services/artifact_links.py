"""Promote and rewrite artifact references in a report so they are clickable.

The report template requires every finding to link its PoC and its exploit
test, but the report agent intermittently writes those paths as code spans
(``poc/VULN-001_x.md``) instead of markdown links. Such a report ends up with
**no clickable artifact at all**: the artifact popup in the UI has nothing to
open, and the link-rewriting pass has nothing to rewrite.

`linkify_report_artifacts()` promotes those code spans to markdown links and
then rewrites every relative artifact link to the backend artifact endpoint,
which is what the frontend intercepts to open the file in its modal viewer.

It runs on the callback path for new reports and can be replayed on any stored
report (see the recovery procedure in the sastia-pipeline skill).
"""

from __future__ import annotations

import re
from collections.abc import Container

# Directory-prefixed artifacts: poc/x.md, exploit_tests/y.py, evidence/z.txt,
# results/w.md, partitions/v.md
_DIR = r"(?:poc|exploit_tests|evidence|results|partitions)"
# Bare root-level artifacts: README.md, report.md, report.json, phase1_output.md,
# phase2b_output.md, validation_results.md, ...
_ROOT = r"(?:README|report|validation_results|docker_environment|phase\d[a-z]?_output)"
_EXT = r"(?:md|json|txt|py|sh|c|log)"

# `poc/VULN-001_x.md` — the whitespace exclusion keeps multi-path spans
# (e.g. `a.txt … b.txt`) from being mistaken for a single artifact.
_SPAN_RE = re.compile(
    r"`(" + _DIR + r"/[^`\s]*?\." + _EXT + r"|" + _ROOT + r"\." + _EXT + r")`"
)

# Existing markdown links, with an optional in-page anchor to preserve.
_LINK_RE = re.compile(
    r"\]\(("
    + _DIR + r"/[^)#\s]*(?:#[^)\s]*)?"
    + r"|" + _ROOT + r"\." + _EXT + r"(?:#[^)\s]*)?"
    + r")"
)


def linkify_report_artifacts(
    markdown: str, audit_id: str, available: Container[str]
) -> str:
    """Return `markdown` with artifact references made clickable.

    `available` is the set of uploaded artifact paths (relative to the audit's
    artifact directory); code spans pointing at anything else are left
    untouched so the report never gains a dead link.
    """
    if not markdown:
        return markdown

    def _promote(match: re.Match[str]) -> str:
        path = match.group(1)
        if path in available:
            return f"[{path}]({path})"
        return match.group(0)

    markdown = _SPAN_RE.sub(_promote, markdown)

    base_url = f"/api/audits/{audit_id}/artifacts/"

    def _rewrite(match: re.Match[str]) -> str:
        target = match.group(1)
        # Leave links to files we do not have untouched rather than pointing
        # the UI at an artifact endpoint that would answer 404.
        if target.split("#", 1)[0] not in available:
            return match.group(0)
        return "](" + base_url + target

    return _LINK_RE.sub(_rewrite, markdown)
