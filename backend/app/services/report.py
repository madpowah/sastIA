import logging
import markdown
import os
import re
import sys

logger = logging.getLogger("sastia.report")


def generate_pdf(markdown_text: str, output_path: str) -> str:
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', markdown_text)

    html_path = output_path.replace(".pdf", ".html")
    html_content = ("<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n</head>\n"
                    "<body>\n" + markdown.markdown(cleaned, extensions=["tables", "fenced_code"]) + "\n</body>\n</html>")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("generating PDF (%sB HTML)", len(html_content))

    try:
        from weasyprint import HTML
        doc = HTML(string=html_content).render()
        n_pages = len(doc.pages)
        logger.info("weasyprint rendered %d pages", n_pages)
        doc.write_pdf(output_path)
        logger.info("PDF written to %s", output_path)
        if n_pages < 2:
            logger.warning("only %d pages for %dB HTML - content may be truncated", n_pages, len(html_content))
    except Exception as e:
        logger.error("weasyprint failed: %s", e)
        raise

    return output_path
