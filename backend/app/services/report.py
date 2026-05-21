import markdown
import os
import re
import subprocess
import sys


def generate_pdf(markdown_text: str, output_path: str) -> str:
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', markdown_text)
    html_body = markdown.markdown(cleaned, extensions=["tables", "fenced_code"])

    html_path = output_path.replace(".pdf", ".html")
    html_content = ("<!DOCTYPE html>\n<html>\n<meta charset=\"utf-8\">\n"
                    "<body style=\"font-family:DejaVu Sans,sans-serif;font-size:11pt;line-height:1.6\">\n"
                    + html_body + "\n</body>\n</html>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "weasyprint", html_path, output_path],
            capture_output=True, text=True, timeout=120,
        )
        print(f"[report] weasyprint exit={result.returncode} stderr={result.stderr!r}")
    except Exception as e:
        print(f"[report] weasyprint exception: {e}")
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(output_path)

    pdf_size = os.path.getsize(output_path)
    html_size = os.path.getsize(html_path)
    print(f"[report] PDF={pdf_size}B HTML={html_size}B")

    return output_path
