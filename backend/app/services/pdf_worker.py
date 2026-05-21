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


def _sanitize_html_body(html: str) -> str:
    """Escape raw HTML tags that would break document structure in lxml."""

    def _escape_tag(m):
        full = m.group(0)
        if full.startswith("</"):
            return "&lt;/" + m.group(1) + "&gt;"
        attrs = m.group(2) or ""
        if attrs and not attrs.endswith("/"):
            attrs += " "
        return "&lt;" + m.group(1) + attrs + "&gt;"

    pattern = r'</?(' + '|'.join(_DANGEROUS_TAGS) + r')([^>]*/?)?>'
    return re.sub(pattern, _escape_tag, html, flags=re.IGNORECASE | re.DOTALL)


def _render_html(html: str, pdf_path: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "weasyprint", "-", pdf_path],
        input=html,
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

    before = len(re.findall(r'<(title|script|style|html|head|body|meta)[>\s]', html_content, re.IGNORECASE))
    html_content = _sanitize_html_body(html_content)
    after = len(re.findall(r'<(title|script|style|html|head|body|meta)[>\s]', html_content, re.IGNORECASE))
    if before - after > 0:
        print(f"[pdf_worker] sanitized {before - after} dangerous HTML tags")

    if not _render_html(html_content, pdf_path):
        print("[pdf_worker] rendering failed", file=sys.stderr)
        sys.exit(1)

    pdf_size = os.path.getsize(pdf_path)
    print(f"[pdf_worker] PDF: {pdf_size}B")

    if pdf_size < 20000:
        print(f"[pdf_worker] WARNING: PDF seems small ({pdf_size}B)")


if __name__ == "__main__":
    main()
