"""Standalone PDF worker — splits large HTML into chunks, renders each
with weasyprint, then merges them. Works around bugs where weasyprint
silently stops rendering after ~2 pages.
"""
import os
import re
import subprocess
import sys
import tempfile


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


def _chunk_html(full_html: str) -> list[str]:
    """Split HTML at <h2> boundaries so each chunk stays small."""
    match = re.match(r'(.*?</body>\s*</html>\s*$)', full_html, re.DOTALL)
    header_end = full_html.find("<h2")
    if header_end == -1:
        return [full_html]

    prefix = full_html[:header_end]
    rest = full_html[header_end:]

    sections = re.split(r'(?=<h2)', rest)
    chunks = []
    for sec in sections:
        chunks.append(
            "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\">\n"
            "<style>\n"
            "body{font-family:DejaVu Sans,sans-serif;font-size:11pt;line-height:1.6;color:#333;}\n"
            "table{border-collapse:collapse;width:100%;margin:10px 0;}\n"
            "th,td{border:1px solid #999;padding:5px 8px;text-align:left;}\n"
            "th{background:#eee;}\n"
            "pre{background:#f5f5f5;padding:8px 12px;font-size:9pt;white-space:pre-wrap;}\n"
            "code{background:#f5f5f5;padding:1px 4px;font-size:9pt;}\n"
            "</style></head><body>\n"
            + prefix + sec
            + "\n</body></html>"
        )
    print(f"[pdf_worker] split into {len(chunks)} chunks")
    return chunks


def _merge_pdfs(pdf_paths: list[str], output_path: str) -> bool:
    """Merge multiple PDFs into one using PyPDF2."""
    try:
        from PyPDF2 import PdfMerger
    except ImportError:
        try:
            from pypdf import PdfMerger
        except ImportError:
            print("[pdf_worker] PyPDF2/pypdf not available, leaving separate PDFs")
            return False

    merger = PdfMerger()
    for p in pdf_paths:
        if os.path.getsize(p) > 100:
            merger.append(p)
        else:
            print(f"[pdf_worker] skipping tiny chunk: {p} ({os.path.getsize(p)}B)")
    merger.write(output_path)
    merger.close()
    print(f"[pdf_worker] merged {len(pdf_paths)} PDFs -> {output_path}")
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

    # Try normal render first
    output_dir = os.path.dirname(pdf_path) or "."
    single_pdf = os.path.join(output_dir, ".single.pdf")
    if _render_html(html_content, single_pdf):
        if os.path.getsize(single_pdf) > 50000:
            print("[pdf_worker] single render produced >50KB, likely complete")
            os.replace(single_pdf, pdf_path)
            return

        from PyPDF2 import PdfReader
        n_pages = len(PdfReader(single_pdf).pages)
        print(f"[pdf_worker] single render: {n_pages} pages, {os.path.getsize(single_pdf)}B")
        if n_pages > 3:
            print("[pdf_worker] already has >3 pages, using it")
            os.replace(single_pdf, pdf_path)
            return
        print("[pdf_worker] too few pages, trying chunked approach")

    # Chunked render
    chunks = _chunk_html(html_content)
    chunk_pdfs = []
    tmpdir = tempfile.mkdtemp(prefix="pdf_")

    for i, chunk_html in enumerate(chunks):
        out = os.path.join(tmpdir, f"chunk_{i:03d}.pdf")
        if _render_html(chunk_html, out) and os.path.getsize(out) > 100:
            chunk_pdfs.append(out)
            print(f"[pdf_worker] chunk {i}: {os.path.getsize(out)}B")
        else:
            print(f"[pdf_worker] chunk {i}: FAILED, skipping")

    if not chunk_pdfs:
        print("[pdf_worker] all chunks failed, trying single fallback")
        os.replace(single_pdf, pdf_path)
        return

    _merge_pdfs(chunk_pdfs, pdf_path)
    print(f"[pdf_worker] final PDF: {os.path.getsize(pdf_path)}B")

    for p in chunk_pdfs + [single_pdf]:
        try:
            os.remove(p)
        except OSError:
            pass


if __name__ == "__main__":
    main()
