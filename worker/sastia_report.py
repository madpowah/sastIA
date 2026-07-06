"""
Generate detailed vulnerability entries from raw Semgrep/Gitleaks results.
Used by the worker to ensure callback data is always complete.
"""

import json
import re
from pathlib import Path
from typing import Optional


def _semgrep_severity(check_id: str, extra: dict) -> tuple[str, float]:
    """Determine severity from Semgrep rule context."""
    if "missing-or-broken-authorization" in check_id:
        return "High", 7.5
    if "regular-expression-dos" in check_id or "redos" in check_id.lower():
        return "Medium", 5.0
    if any(kw in check_id.lower() for kw in ["sql-injection", "rce", "command-injection", "xss"]):
        return "Critical", 9.0
    sev_map = {"ERROR": ("Critical", 9.0), "WARNING": ("High", 7.0), "INFO": ("Medium", 5.0)}
    raw = extra.get("severity", "INFO")
    return sev_map.get(raw, ("Low", 2.5))


def _gitleaks_severity(rule_id: str, file_path: str, entropy: float) -> tuple[str, float]:
    """Map Gitleaks rules to severity levels."""
    if ".AssemblyReference.cache" in file_path or ".csproj.AssemblyReference" in file_path:
        return "Info", 0.0
    if "private-key" in rule_id or "private_key" in rule_id:
        return "Critical", 9.0
    if "password" in rule_id.lower() or "secret" in rule_id.lower():
        return "Critical", 8.5
    if entropy > 5.0:
        return "High", 7.5
    return "Medium", 5.5


def parse_semgrep_results(semgrep_path: Path) -> list[dict]:
    """Convert Semgrep JSON results to vulnerability entries."""
    if not semgrep_path.exists():
        return []
    data = json.loads(semgrep_path.read_text())
    vulns = []
    for n, r in enumerate(data.get("results", []), 1):
        extra = r.get("extra", {})
        metadata = extra.get("metadata", {})
        cwe_list = metadata.get("cwe", [])
        check_id = r.get("check_id", "")
        severity, cvss = _semgrep_severity(check_id, extra)
        code = extra.get("lines", "")
        if code:
            code = re.sub(r'^```\w*\s*\n?', '', code)
            code = re.sub(r'\n?```\s*$', '', code)
        vulns.append({
            "id": f"V-{n:02d}",
            "title": (extra.get("message", "").split(".")[0][:100]
                      or f"Semgrep finding"),
            "severity": severity,
            "cvss": cvss,
            "cwe": cwe_list[0] if cwe_list else "",
            "file_path": r.get("path", "").replace("/workspace/", ""),
            "line": r.get("start", {}).get("line", 0),
            "type": (metadata.get("vulnerability_class") or [check_id.split(".")[-1]])[0],
            "description": extra.get("message", ""),
            "impact": f"Likelihood: {metadata.get('likelihood', 'MEDIUM')} | Impact: {metadata.get('impact', 'MEDIUM')}",
            "recommendation": "Review and fix the identified security issue. Refer to OWASP/CWE references.",
            "validation_status": "Non validé",
            "proof": "",
            "code_snippet": code,
        })
    return vulns


def parse_gitleaks_results(gitleaks_path: Path) -> list[dict]:
    """Convert Gitleaks JSON results to vulnerability entries."""
    if not gitleaks_path.exists():
        return []
    data = json.loads(gitleaks_path.read_text())
    vulns = []
    for n, r in enumerate(data, 1):
        file_path = r.get("File", "").replace("/workspace/", "")
        rule_id = r.get("RuleID", "")
        entropy = r.get("Entropy", 0)
        severity, cvss = _gitleaks_severity(rule_id, file_path, entropy)
        vulns.append({
            "id": f"S-{n:02d}",
            "title": r.get("Description", "Secret leak")[:100],
            "severity": severity,
            "cvss": cvss,
            "cwe": "CWE-798: Use of Hardcoded Credentials",
            "file_path": file_path,
            "line": r.get("StartLine", 0),
            "type": "secret_leak",
            "description": r.get("Description", ""),
            "impact": f"Exposed {rule_id} (entropy: {entropy:.1f})",
            "recommendation": "Rotate the exposed credential immediately. Use a secrets manager.",
            "validation_status": "Non validé (pas d'accès au service distant)",
            "proof": "",
            "code_snippet": r.get("Match", ""),
        })
    return vulns


def merge_reports(
    audit_dir: Path,
    agent_report_path: Optional[Path] = None,
) -> dict:
    """
    Merge raw scan results with the agent's JSON report.
    Returns a payload dict suitable for the sastIA callback endpoint.
    """
    semgrep_vulns = parse_semgrep_results(audit_dir / "semgrep-results.json")
    gitleaks_vulns = parse_gitleaks_results(audit_dir / "gitleaks-report.json")
    raw_vulns = semgrep_vulns + gitleaks_vulns

    # Try to read the agent's report JSON for the executive summary
    summary = ""
    if agent_report_path and agent_report_path.exists():
        try:
            agent_data = json.loads(agent_report_path.read_text())
            summary = agent_data.get("summary", "")
            # If agent provided its own vulns, use them (they may have better descriptions)
            agent_vulns = agent_data.get("vulnerabilities", [])
            if isinstance(agent_vulns, list) and len(agent_vulns) > 0:
                # Merge: use agent vulns but ensure all raw findings are also included
                raw_ids = {(v.get("file_path", ""), v.get("line", 0)) for v in raw_vulns}
                for av in agent_vulns:
                    key = (av.get("file_path", ""), av.get("line", 0))
                    if key in raw_ids:
                        raw_ids.discard(key)
                    elif av.get("file_path") or av.get("line"):
                        # Agent vuln with file/line we don't have in raw → keep it
                        pass
                # Add raw vulns that the agent missed
                kept_raw_ids = {(v.get("file_path", ""), v.get("line", 0)) for v in agent_vulns}
                for rv in raw_vulns:
                    key = (rv.get("file_path", ""), rv.get("line", 0))
                    if key not in kept_raw_ids:
                        agent_vulns.append(rv)
                vulns = agent_vulns
            else:
                vulns = raw_vulns
        except (json.JSONDecodeError, KeyError):
            vulns = raw_vulns
    else:
        vulns = raw_vulns

    # Compute metrics
    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for v in vulns:
        s = v.get("severity", "").lower()
        if s in sev_counts:
            sev_counts[s] += 1
        else:
            sev_counts["info"] += 1

    total = sum(sev_counts.values())

    # Build callback payload (matching CallbackBody in backend)
    payload = {
        "vulnerabilities": vulns,
        "summary": summary,
        "metrics": sev_counts,
        "report_markdown": None,  # Let the backend generate it
    }
    return payload
