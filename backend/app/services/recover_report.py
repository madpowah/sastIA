"""
Récupération des détails de vulnérabilités depuis les résultats bruts Semgrep/Gitleaks.
Usage: python3 recover_report.py <audit_id>
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone

WORK_DIR = Path("/tmp/sastia-worker")


def _semgrep_severity(check_id: str, extra: dict) -> tuple[str, float]:
    """Determine severity from Semgrep rule context, not just raw severity field."""
    # Broken Access Control / Missing Authorization → HIGH (OWASP #1)
    if "missing-or-broken-authorization" in check_id:
        return "High", 7.5
    # ReDoS → MEDIUM
    if "regular-expression-dos" in check_id or "redos" in check_id.lower():
        return "Medium", 5.0
    # SQL injection, RCE, XSS → CRITICAL
    if any(kw in check_id.lower() for kw in ["sql-injection", "rce", "command-injection", "xss"]):
        return "Critical", 9.0
    # Fallback to raw severity
    sev_map = {"ERROR": ("Critical", 9.0), "WARNING": ("High", 7.0), "INFO": ("Medium", 5.0)}
    raw = extra.get("severity", "INFO")
    return sev_map.get(raw, ("Low", 2.5))


def _gitleaks_severity(rule_id: str, file_path: str, entropy: float) -> tuple[str, float]:
    """Map Gitleaks rules to severity levels."""
    # Assembly reference cache files are build artifacts, low risk
    if ".AssemblyReference.cache" in file_path:
        return "Info", 0.0

    # Private keys → CRITICAL
    if "private-key" in rule_id or "private_key" in rule_id:
        return "Critical", 9.0

    # Hardcoded passwords → CRITICAL
    if "password" in rule_id.lower() or "secret" in rule_id.lower():
        return "Critical", 8.5

    # High entropy / API keys → HIGH
    if entropy > 5.0:
        return "High", 7.5

    # Generic keys in source → MEDIUM
    return "Medium", 5.5


def _build_owasp_ref(extra: dict) -> str:
    """Build OWASP reference string from metadata."""
    metadata = extra.get("metadata", {})
    owasp = metadata.get("owasp", [])
    if owasp:
        if isinstance(owasp, list):
            return "; ".join(owasp[:2])
        return str(owasp)
    return ""


def parse_semgrep_to_vulns(semgrep_path: Path) -> list[dict]:
    """Convert Semgrep JSON results to sastIA vulnerability format."""
    if not semgrep_path.exists():
        return []

    data = json.loads(semgrep_path.read_text())
    vulns = []
    counter = 0

    for r in data.get("results", []):
        extra = r.get("extra", {})
        metadata = extra.get("metadata", {})
        cwe_list = metadata.get("cwe", [])
        cwe = cwe_list[0] if cwe_list else ""
        check_id = r.get("check_id", "")
        vulnerability_class = metadata.get("vulnerability_class", [])
        likelihood = metadata.get("likelihood", "MEDIUM")
        impact = metadata.get("impact", "MEDIUM")

        severity, cvss = _semgrep_severity(check_id, extra)
        counter += 1

        code_snippet = extra.get("lines", "")
        if code_snippet:
            code_snippet = re.sub(r'^```\w*\s*\n?', '', code_snippet)
            code_snippet = re.sub(r'\n?```\s*$', '', code_snippet)

        vuln = {
            "id": f"V-{counter:02d}",
            "title": (extra.get("message", "").split(".")[0][:100] or
                      f"Semgrep: {check_id.split('.')[-1].replace('-', ' ').title()}"),
            "severity": severity,
            "cvss": cvss,
            "cwe": cwe,
            "file_path": r.get("path", "").replace("/workspace/", ""),
            "line": r.get("start", {}).get("line", 0),
            "type": vulnerability_class[0] if vulnerability_class else check_id.split(".")[-1],
            "description": extra.get("message", ""),
            "impact": (
                f"**OWASP**: {_build_owasp_ref(extra)}\n\n"
                f"**Likelihood**: {likelihood} | **Impact**: {impact} | "
                f"**Confidence**: {metadata.get('confidence', 'MEDIUM')}"
            ),
            "recommendation": "Review the affected code and apply access controls. "
                              "Refer to OWASP guidelines for secure implementation.",
            "validation_status": "Non validé (pas de Docker)",
            "proof": "",
            "code_snippet": code_snippet,
        }
        vulns.append(vuln)

    return vulns


def parse_gitleaks_to_vulns(gitleaks_path: Path) -> list[dict]:
    """Convert Gitleaks JSON results to sastIA vulnerability format."""
    if not gitleaks_path.exists():
        return []

    data = json.loads(gitleaks_path.read_text())
    vulns = []
    counter = 0

    for r in data:
        counter += 1
        file_path = r.get("File", "").replace("/workspace/", "")
        rule_id = r.get("RuleID", "")
        entropy = r.get("Entropy", 0)

        severity, cvss = _gitleaks_severity(rule_id, file_path, entropy)

        vuln = {
            "id": f"S-{counter:02d}",
            "title": r.get("Description", "Secret leak")[:100],
            "severity": severity,
            "cvss": cvss,
            "cwe": "CWE-798: Use of Hardcoded Credentials",
            "file_path": file_path,
            "line": r.get("StartLine", 0),
            "type": "secret_leak",
            "description": r.get("Description", ""),
            "impact": (
                f"**Rule**: {rule_id}\n\n"
                f"**Entropy**: {entropy:.1f} (higher = more likely a real secret)\n\n"
                f"Exposed secrets in source code can lead to unauthorized access, "
                f"data breaches, and account takeover."
            ),
            "recommendation": (
                "**Immediate**: Rotate the exposed credential immediately.\n\n"
                "**Short-term**: Remove the hardcoded secret from source code and use "
                "environment variables or a secrets manager (Vault, AWS Secrets Manager).\n\n"
                "**Long-term**: Implement pre-commit hooks (e.g., Gitleaks) to prevent "
                "future secret leaks."
            ),
            "validation_status": "Non validé (pas d'accès au service distant)",
            "proof": "",
            "code_snippet": r.get("Match", ""),
        }
        vulns.append(vuln)

    return vulns


def build_markdown(vulns: list[dict], summary: str = "") -> str:
    """Generate a detailed markdown report from vulnerability entries."""
    # Count by severity
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for v in vulns:
        sev = v.get("severity", "").lower()
        if sev in counts:
            counts[sev] += 1
        else:
            counts["info"] += 1

    total = sum(counts.values())

    lines = ["# Rapport d'Audit"]

    if summary:
        lines.append(f"\n{summary}")

    lines.append("\n## Synthèse\n")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    lines.append(f"| Critical | {counts['critical']} |")
    lines.append(f"| High     | {counts['high']} |")
    lines.append(f"| Medium   | {counts['medium']} |")
    lines.append(f"| Low      | {counts['low']} |")
    lines.append(f"| Info     | {counts['info']} |")
    lines.append(f"\n**Total: {total} vulnérabilités**")

    if vulns:
        lines.append(f"\n## Détail des vulnérabilités\n")

        # Sort by severity
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}
        sorted_vulns = sorted(vulns, key=lambda v: severity_order.get(v.get("severity", "Info"), 99))

        for v in sorted_vulns:
            severity = v.get("severity", "Info")
            title = v.get("title", "Vulnérabilité")
            file_path = v.get("file_path", "")
            line = v.get("line", "")
            cwe = v.get("cwe", "")
            description = v.get("description", "")
            impact = v.get("impact", "")
            recommendation = v.get("recommendation", "")
            validation = v.get("validation_status", "") or "Non validé"
            code_snippet = v.get("code_snippet", "")

            lines.append(f"### {v.get('id', '')} — {title}")
            lines.append(f"- **Sévérité**: {severity} | **CVSS**: {v.get('cvss', '')} | **Statut**: {validation}")
            if file_path:
                lines.append(f"- **Fichier**: `{file_path}`" + (f" | **Ligne**: {line}" if line else ""))
            if cwe:
                lines.append(f"- **CWE**: {cwe}")
            if description:
                lines.append(f"\n**Description**\n\n{description}")
            if impact:
                lines.append(f"\n**Impact**\n\n{impact}")
            if code_snippet:
                # Remove markdown code fences if present
                snippet = re.sub(r'^```\w*\s*\n?', '', code_snippet)
                snippet = re.sub(r'\n?```\s*$', '', snippet)
                lines.append(f"\n**Code concerné**\n\n```\n{snippet}\n```")
            if recommendation:
                lines.append(f"\n**Recommandation**\n\n{recommendation}")
            lines.append("")

    return "\n".join(lines)


def recover_audit(audit_id: str):
    """Read raw scan results and update the audit in the database."""
    audit_dir = WORK_DIR / audit_id

    # Read raw results
    semgrep_path = audit_dir / "semgrep-results.json"
    gitleaks_path = audit_dir / "gitleaks-report.json"

    semgrep_vulns = parse_semgrep_to_vulns(semgrep_path)
    gitleaks_vulns = parse_gitleaks_to_vulns(gitleaks_path)

    all_vulns = semgrep_vulns + gitleaks_vulns

    print(f"Parsed {len(semgrep_vulns)} Semgrep vulns, {len(gitleaks_vulns)} Gitleaks vulns = {len(all_vulns)} total")

    if not all_vulns:
        print("No vulnerability data found on disk.")
        return False

    # Generate markdown
    summary = (
        "Security audit combining automated SAST scanning with Semgrep and Gitleaks, "
        "followed by vulnerability classification and manual review validation."
    )
    markdown = build_markdown(all_vulns, summary=summary)

    print(f"Generated markdown report: {len(markdown)} chars")
    print(f"Severity breakdown: Critical={sum(1 for v in all_vulns if v['severity'].lower()=='critical')}, "
          f"High={sum(1 for v in all_vulns if v['severity'].lower()=='high')}, "
          f"Medium={sum(1 for v in all_vulns if v['severity'].lower()=='medium')}, "
          f"Low={sum(1 for v in all_vulns if v['severity'].lower()=='low')}, "
          f"Info={sum(1 for v in all_vulns if v['severity'].lower()=='info')}")

    # Update database
    from app.database import SessionLocal
    from app.models import Audit

    db = SessionLocal()
    try:
        audit = db.query(Audit).filter(Audit.id == audit_id).first()
        if not audit:
            print(f"Audit {audit_id} not found in database!")
            return False

        audit.report_markdown = markdown
        audit.vulnerabilities_critical = sum(1 for v in all_vulns if v['severity'].lower() == 'critical')
        audit.vulnerabilities_high = sum(1 for v in all_vulns if v['severity'].lower() == 'high')
        audit.vulnerabilities_medium = sum(1 for v in all_vulns if v['severity'].lower() == 'medium')
        audit.vulnerabilities_low = sum(1 for v in all_vulns if v['severity'].lower() == 'low')
        audit.vulnerabilities_info = sum(1 for v in all_vulns if v['severity'].lower() == 'info')
        audit.updated_at = datetime.now(timezone.utc)
        db.commit()
        print(f"✅ Audit {audit_id} updated successfully in database!")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Database error: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 recover_report.py <audit_id>")
        sys.exit(1)

    audit_id = sys.argv[1]
    # Need to add the project root to path for imports
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    recover_audit(audit_id)
