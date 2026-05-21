import logging
import markdown
import os
import re
import subprocess
import sys

logger = logging.getLogger("sastia.report")


def generate_pdf(markdown_text: str, output_path: str) -> str:
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', markdown_text)

    html_path = output_path.replace(".pdf", ".html")
    html_content = ("<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n</head>\n"
                    "<body style=\"font-family:DejaVu Sans,sans-serif;font-size:11pt;line-height:1.6\">\n"
                    + markdown.markdown(cleaned, extensions=["tables", "fenced_code"])
                    + "\n</body>\n</html>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("generating PDF (%dB HTML)", len(html_content))

    worker_script = os.path.join(os.path.dirname(__file__), "pdf_worker.py")
    result = subprocess.run(
        [sys.executable, worker_script, html_path, output_path],
        capture_output=True, text=True, timeout=120,
    )
    for line in result.stdout.strip().splitlines():
        logger.info("[worker] %s", line)
    for line in result.stderr.strip().splitlines():
        logger.error("[worker] %s", line)

    if result.returncode != 0:
        raise RuntimeError(f"PDF worker failed (exit {result.returncode})")

    pdf_size = os.path.getsize(output_path)
    logger.info("PDF generated: %dB", pdf_size)

    return output_path
