"""Standalone PDF worker — isolates weasyprint in a subprocess.
Called via: python -m app.services.pdf_worker <input.html> <output.pdf>
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format="[pdf_worker] %(message)s")
logger = logging.getLogger("pdf_worker")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m app.services.pdf_worker <input.html> <output.pdf>", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[1]
    pdf_path = sys.argv[2]

    try:
        from weasyprint import HTML
        logger.info("rendering %s -> %s", html_path, pdf_path)
        doc = HTML(filename=html_path).render()
        logger.info("rendered %d pages", len(doc.pages))
        doc.write_pdf(pdf_path)
        logger.info("done")
    except Exception as e:
        logger.error("failed: %s", e)
        sys.exit(1)
