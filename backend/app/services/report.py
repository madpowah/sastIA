import logging
import markdown
import os
import re
import subprocess
import sys

logger = logging.getLogger("sastia.report")


def log(msg: str):
    print(f"[report] {msg}", file=sys.stderr, flush=True)
    logger.info(msg)


def generate_pdf(markdown_text: str, output_path: str) -> str:
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', markdown_text)

    html_path = output_path.replace(".pdf", ".html")
    html_content = ("<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\"></head>"
                    "<body>\n"
                    + markdown.markdown(cleaned, extensions=["tables", "fenced_code"])
                    + "\n</body></html>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    log(f"HTML size: {len(html_content)}B -> {html_path}")

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
