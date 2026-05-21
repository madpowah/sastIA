"""Standalone PDF worker — validates HTML and calls weasyprint in a subprocess.
"""
import sys
import os


def main():
    if len(sys.argv) != 3:
        print("Usage: python -m app.services.pdf_worker <input.html> <output.pdf>", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[1]
    pdf_path = sys.argv[2]

    html_size = os.path.getsize(html_path)
    print(f"[pdf_worker] HTML size: {html_size}B")

    with open(html_path, "r", encoding="utf-8") as f:
        raw = f.read()

    # Quick sanity: unique chars
    unique = set(raw)
    print(f"[pdf_worker] HTML unique chars: {len(unique)}")

    # Try to parse with lxml (what weasyprint uses internally)
    try:
        from lxml import etree
        parser = etree.HTMLParser(recover=True)
        tree = etree.parse(html_path, parser)
        root = tree.getroot()
        if root is None:
            print("[pdf_worker] ERROR: lxml produced no root", file=sys.stderr)
            sys.exit(1)
        body = root.find(".//body")
        if body is not None:
            text_len = len("".join(body.itertext()))
            print(f"[pdf_worker] lxml body text length: {text_len} chars")
        errors = [m for m in parser.error_log if m.level >= 2]
        if errors:
            print(f"[pdf_worker] lxml errors: {len(errors)}")
            for e in errors[:5]:
                print(f"  - line {e.line}: {e.message}")
    except Exception as e:
        print(f"[pdf_worker] lxml parse failed: {e}", file=sys.stderr)

    # Render with weasyprint
    try:
        from weasyprint import HTML
        print("[pdf_worker] rendering...")
        doc = HTML(filename=html_path, encoding="utf-8").render()
        n_pages = len(doc.pages)
        print(f"[pdf_worker] pages: {n_pages}")
        doc.write_pdf(pdf_path)
        pdf_size = os.path.getsize(pdf_path)
        print(f"[pdf_worker] PDF size: {pdf_size}B")
        print(f"[pdf_worker] done")
    except Exception as e:
        print(f"[pdf_worker] FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
