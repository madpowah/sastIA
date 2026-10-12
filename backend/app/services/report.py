import logging
import markdown
import os
import re
import subprocess
import sys
import json
import zipfile
import io

logger = logging.getLogger("sastia.report")


def log(msg: str):
    print(f"[report] {msg}", file=sys.stderr, flush=True)
    logger.info(msg)


def _simplify_for_pdf(markdown_text: str) -> str:
    """Simplify VulnHunter markdown for PDF rendering (A4-friendly)."""
    lines = markdown_text.split("\n")
    out = []
    vuln_sections = []
    current_vuln = []
    in_vuln = False
    header_done = False
    in_summary_table = False

    for line in lines:
        # Track vuln sections
        if line.startswith("### [VULN-"):
            if current_vuln:
                vuln_sections.append("\n".join(current_vuln))
            current_vuln = [line]
            in_vuln = True
            continue
        if in_vuln:
            if line.startswith("---"):
                in_vuln = False
                if current_vuln:
                    vuln_sections.append("\n".join(current_vuln))
                    current_vuln = []
                continue
            if line.startswith("| **"):
                # Skip detail table rows in PDF, we'll format them nicely
                continue
            # Skip the raw table field rows
            if line.startswith("|") and "**" in line:
                continue
            current_vuln.append(line)
            continue

        # Header
        if line.startswith("# ") or line.startswith("**Run ID**"):
            out.append(line)
            header_done = True
            continue
        if not header_done:
            out.append(line)
            continue

        # Skip the detailed findings H2 and separator
        if line.strip() in ("---", "## Detailed Findings", "## Vulnerability Details"):
            continue

        # Handle summary table - simplify it
        if "| ID | Title | CWE | Severity |" in line:
            in_summary_table = True
            out.append("\n## Summary\n")
            out.append("| ID | Title | Severity | Docker |")
            out.append("|----|-------|----------|--------|")
            continue
        if in_summary_table:
            if line.strip().startswith("|") and "VULN-" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 6:
                    vid = parts[1]
                    title = parts[2][:60]
                    sev = parts[4]
                    dock = parts[5][:12]
                    out.append(f"| {vid} | {title} | {sev} | {dock} |")
                continue
            else:
                in_summary_table = False

        # Skip resolved input inventory, sweep table, etc in PDF
        if any(skip in line for skip in [
            "Resolved Input Inventory", "Sweep Verification", "Artifacts",
            "Not Found / Excluded", "Trust Boundaries", "Shared Infrastructure",
            "Subgraph Partition", "Call Graph", "Input Inventory",
        ]):
            # Skip the section header and its contents until next header
            continue

        out.append(line)

    # Close last vuln section
    if current_vuln:
        vuln_sections.append("\n".join(current_vuln))

    # Add reformatted findings
    if vuln_sections:
        out.append("\n## Findings\n")
        for vs in vuln_sections:
            vlines = vs.split("\n")
            title = vlines[0] if vlines else ""
            body = [l for l in vlines[1:] if l.strip() and not l.startswith("|") and "**PoC**" not in l and "**Exploit Test**" not in l]
            out.append(title)
            for b in body:
                out.append(b)
            out.append("")

    return "\n".join(out)


def _wrap_wide_tables(html: str) -> str:
    """Wrap markdown tables with >= 6 columns in a landscape page div.

    WeasyPrint supports named pages: `page: landscape` on an element moves it
    (and only it) onto A4 landscape pages, so wide tables like the input
    inventory (7 cols) or the sweep/root-cause table (8 cols) are no longer
    clipped on the right edge of a portrait page.
    """
    import re as _re

    def _wrap(m: _re.Match) -> str:
        table = m.group(0)
        # Count columns from the first <tr> row
        tr = _re.search(r"<tr[^>]*>(.*?)</tr>", table, _re.S | _re.I)
        if not tr:
            return table
        cols = len(_re.findall(r"<t[hd][^>]*>", tr.group(1), _re.I))
        if cols >= 6:
            return '<div class="landscape">' + table + "</div>"
        return table

    return _re.sub(r"<table>.*?</table>", _wrap, html, flags=_re.S | _re.I)


def generate_pdf(markdown_text: str, output_path: str) -> str:
    # Simplify the markdown for PDF
    simplified = _simplify_for_pdf(markdown_text)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', simplified)

    html_path = output_path.replace(".pdf", ".html")
    html_content = ("<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"></head>"
                    "<body>\n"
                    + _wrap_wide_tables(markdown.markdown(cleaned, extensions=["tables", "fenced_code"]))
                    + "\n</body></html>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    log(f"PDF HTML size: {len(html_content)}B -> {html_path}")

    worker_script = os.path.join(os.path.dirname(__file__), "pdf_worker.py")
    result = subprocess.run(
        [sys.executable, worker_script, html_path, output_path],
        capture_output=True, text=True, timeout=120,
    )
    for line in result.stdout.strip().splitlines():
        log(f"[worker] {line}")
    for line in result.stderr.strip().splitlines():
        log(f"[worker:err] {line}")

    if result.returncode != 0:
        raise RuntimeError(f"PDF worker failed (exit {result.returncode})")

    pdf_size = os.path.getsize(output_path)
    log(f"PDF generated: {pdf_size}B")
    return output_path


def create_report_zip(audit_id: str, artifacts_dir: str, readme_md: str | None) -> bytes:
    """Create a ZIP of the full report: README.md + poc/* + exploit_tests/*."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add README
        if readme_md:
            zf.writestr("README.md", readme_md)

        # Add artifacts
        if os.path.exists(artifacts_dir):
            for root, dirs, files in os.walk(artifacts_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    arcname = os.path.relpath(fpath, artifacts_dir)
                    zf.write(fpath, arcname)

    return buf.getvalue()
