"""Standalone PDF worker — sanitizes HTML then renders via weasyprint.
"""
import os
import re
import subprocess
import sys


_DANGEROUS_TAGS = (
    "title", "script", "style", "html", "head", "body",
    "meta", "link", "base", "form", "input", "select",
    "textarea", "iframe", "frame", "frameset", "object",
    "embed", "applet", "svg", "math",
)


CSS = """
    @page { size: A4; margin: 2cm; }
    body { font-family: 'DejaVu Sans', 'Liberation Sans', Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #1f2937; }
    h1 { color: #dc2626; border-bottom: 2px solid #dc2626; padding-bottom: 6px; margin-top: 24px; }
    h1:first-of-type { margin-top: 0; }
    h2 { color: #374151; margin-top: 20px; }
    h3 { color: #4b5563; margin-top: 18px; }
    h4 { color: #6b7280; }
    table { width: 100%; border-collapse: collapse; margin: 12px 0; }
    th, td { border: 1px solid #d1d5db; padding: 6px 10px; text-align: left; }
    th { background: #f3f4f6; font-weight: bold; }
    pre { background: #f1f5f9; padding: 10px 14px; border-radius: 4px; font-size: 9pt; line-height: 1.4; white-space: pre-wrap; word-break: break-word; }
    code { background: #f1f5f9; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
    pre code { background: none; padding: 0; }
    blockquote { border-left: 4px solid #3b82f6; margin: 14px 0; padding: 8px 16px; background: #f8fafc; }
    img { max-width: 100%; height: auto; }
"""


def _sanitize_body(body: str) -> str:
    def _escape_tag(m):
        full = m.group(0)
        if full.startswith("</"):
            return "&lt;/" + m.group(1) + "&gt;"
        attrs = m.group(2) or ""
        if attrs and not attrs.endswith("/"):
            attrs += " "
        return "&lt;" + m.group(1) + attrs + "&gt;"

    pattern = r'</?(' + '|'.join(_DANGEROUS_TAGS) + r')([^>]*/?)?>'
    before = len(re.findall(r'<(title|script|style|html|head|body|meta)[>\s]', body, re.IGNORECASE))
    result = re.sub(pattern, _escape_tag, body, flags=re.IGNORECASE | re.DOTALL)
    after = len(re.findall(r'<(title|script|style|html|head|body|meta)[>\s]', result, re.IGNORECASE))
    if before - after > 0:
        print(f"[pdf_worker] sanitized {before - after} dangerous HTML tags in body")
    return result


def _render_html(body: str, pdf_path: str) -> bool:
    full = (
        "<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n"
        "<style>" + CSS + "</style>\n</head>\n<body>\n"
        + body + "\n</body>\n</html>"
    )
    result = subprocess.run(
        [sys.executable, "-m", "weasyprint", "-", pdf_path],
        input=full,
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"[pdf_worker] render FAILED: {result.stderr.strip()[:300]}", file=sys.stderr)
        return False
    return True


def main():
    if len(sys.argv) != 3:
        print("Usage: python -m app.services.pdf_worker <input.html> <output.pdf>", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[1]
    pdf_path = sys.argv[2]

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    print(f"[pdf_worker] HTML: {len(html_content)}B")

    # Extract body content only (skip <html>, <head>, <body> tags from template)
    m = re.search(r'<body[^>]*>(.*)</body>', html_content, re.DOTALL)
    body = m.group(1) if m else html_content
    body = _sanitize_body(body)

    if not _render_html(body, pdf_path):
        print("[pdf_worker] rendering failed", file=sys.stderr)
        sys.exit(1)

    pdf_size = os.path.getsize(pdf_path)
    print(f"[pdf_worker] PDF: {pdf_size}B")


if __name__ == "__main__":
    main()
