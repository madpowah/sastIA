import markdown
import os
import re
import subprocess
import sys


def generate_pdf(markdown_text: str, output_path: str) -> str:
    cleaned = re.sub(r'[\f]', '\n', markdown_text)
    html_body = markdown.markdown(cleaned, extensions=["tables", "fenced_code"])

    html_path = output_path.replace(".pdf", ".html")

    HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page { size: A4; margin: 2cm; }
    body { font-family: 'DejaVu Sans', 'Liberation Sans', Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #333; }
    h1 { color: #c00; border-bottom: 2px solid #c00; padding-bottom: 6px; }
    h2 { color: #555; margin-top: 20px; }
    h3 { color: #666; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0; }
    th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
    th { background: #f0f0f0; }
    pre { background: #f5f5f5; padding: 10px 14px; font-size: 9pt; white-space: pre-wrap; word-break: break-word; }
    code { background: #f5f5f5; padding: 1px 4px; font-size: 9pt; }
    pre code { background: none; padding: 0; }
    blockquote { border-left: 3px solid #36c; margin: 12px 0; padding: 6px 12px; background: #f8faff; }
</style>
</head>
<body>
__BODY__
</body>
</html>"""

    styled_html = HTML_TEMPLATE.replace("__BODY__", html_body)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(styled_html)

    # Try weasyprint CLI first (more robust), fallback to Python API
    try:
        result = subprocess.run(
            [sys.executable, "-m", "weasyprint", html_path, output_path],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"weasyprint CLI failed: {result.stderr.strip()}")
        if result.stderr:
            print(f"[report] weasyprint stderr: {result.stderr.strip()}")
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        print(f"[report] CLI approach failed ({e}), trying Python API...")
        from weasyprint import HTML
        HTML(filename=html_path).write_pdf(output_path)

    pdf_size = os.path.getsize(output_path)
    html_size = os.path.getsize(html_path)
    print(f"[report] PDF={pdf_size}B HTML={html_size}B ratio={pdf_size/html_size:.2%}")

    if pdf_size < 1024:
        print(f"[report] WARNING: PDF very small ({pdf_size}B) vs HTML ({html_size}B)")

    return output_path
