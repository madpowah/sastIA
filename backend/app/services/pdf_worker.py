"""Standalone PDF worker — multiple fallback strategies for PDF generation.
"""
import os
import subprocess
import sys
import tempfile


def try_weasyprint_stdin(html_content: str, pdf_path: str) -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "weasyprint", "-", pdf_path],
            input=html_content,
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            print(f"[pdf_worker] weasyprint stdin OK -> {pdf_path}")
            if result.stderr.strip():
                print(f"[pdf_worker] stderr: {result.stderr.strip()[:200]}")
            return True
        print(f"[pdf_worker] weasyprint stdin FAILED (code {result.returncode})")
        print(f"[pdf_worker] stderr: {result.stderr.strip()[:500]}")
    except Exception as e:
        print(f"[pdf_worker] weasyprint stdin exception: {e}")
    return False


def try_weasyprint_file(html_path: str, pdf_path: str) -> bool:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "weasyprint", html_path, pdf_path],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            print(f"[pdf_worker] weasyprint file OK -> {pdf_path}")
            if result.stderr.strip():
                print(f"[pdf_worker] stderr: {result.stderr.strip()[:200]}")
            return True
        print(f"[pdf_worker] weasyprint file FAILED (code {result.returncode})")
        print(f"[pdf_worker] stderr: {result.stderr.strip()[:500]}")
    except Exception as e:
        print(f"[pdf_worker] weasyprint file exception: {e}")
    return False


def try_pandoc(markdown_text: str, pdf_path: str) -> bool:
    try:
        subprocess.run(["pandoc", "--version"], capture_output=True, timeout=5)
    except Exception:
        return False
    try:
        result = subprocess.run(
            ["pandoc", "-f", "markdown", "-o", pdf_path, "--pdf-engine=weasyprint"],
            input=markdown_text,
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            print(f"[pdf_worker] pandoc + weasyprint OK")
            return True
        print(f"[pdf_worker] pandoc failed: {result.stderr.strip()[:500]}")
    except Exception as e:
        print(f"[pdf_worker] pandoc exception: {e}")
    return False


def try_fallback_text(markdown_text: str, pdf_path: str, html_path: str) -> bool:
    """Write a minimal HTML and copy as .txt if all else fails."""
    txt = html_path.replace(".html", ".txt")
    with open(txt, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    print(f"[pdf_worker] fallback: markdown saved to {txt}")
    return False


def main():
    if len(sys.argv) != 3:
        print("Usage: python -m app.services.pdf_worker <input.html> <output.pdf>", file=sys.stderr)
        sys.exit(1)

    html_path = sys.argv[1]
    pdf_path = sys.argv[2]

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    print(f"[pdf_worker] HTML: {len(html_content)}B")
    print(f"[pdf_worker] strategies: stdin -> file -> pandoc -> text")

    if try_weasyprint_stdin(html_content, pdf_path):
        return
    if try_weasyprint_file(html_path, pdf_path):
        return
    if try_pandoc(html_content, pdf_path):
        return

    try_fallback_text(html_content, pdf_path, html_path)
    sys.exit(1)


if __name__ == "__main__":
    main()
