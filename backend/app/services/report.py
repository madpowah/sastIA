import markdown
import os


def generate_pdf(markdown_text: str, output_path: str) -> str:
    try:
        from weasyprint import HTML
    except ImportError:
        raise

    html_body = markdown.markdown(markdown_text, extensions=["tables", "fenced_code"])

    html_path = output_path.replace(".pdf", ".html")

    styled_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {
        size: A4;
        margin: 1.5cm 2cm;
    }
    body {
        font-family: 'DejaVu Sans', Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #1f2937;
    }
    h1 { color: #dc2626; border-bottom: 2px solid #dc2626; padding-bottom: 8px; page-break-before: always; }
    h1:first-of-type { page-break-before: avoid; }
    h2 { color: #374151; margin-top: 24px; }
    h3 { color: #4b5563; }
    h4 { color: #6b7280; }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        page-break-inside: avoid;
    }
    th, td {
        border: 1px solid #d1d5db;
        padding: 8px 12px;
        text-align: left;
        word-break: break-word;
    }
    th { background-color: #f3f4f6; font-weight: bold; }
    blockquote {
        border-left: 4px solid #3b82f6;
        margin: 16px 0;
        padding: 8px 16px;
        background: #f8fafc;
        page-break-inside: avoid;
    }
    pre {
        background: #f1f5f9;
        padding: 12px 16px;
        border-radius: 4px;
        font-size: 9pt;
        line-height: 1.4;
        white-space: pre-wrap;
        word-break: break-word;
        page-break-inside: avoid;
    }
    pre code {
        background: none;
        padding: 0;
        font-size: inherit;
        border-radius: 0;
    }
    code {
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10pt;
        word-break: break-word;
    }
    img { max-width: 100%; height: auto; }
    ul, ol { page-break-inside: avoid; }
    p { orphans: 3; widows: 3; }
</style>
</head>
<body>
%s
</body>
</html>""" % html_body

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(styled_html)

    try:
        HTML(string=styled_html).write_pdf(output_path)
    except Exception:
        raise

    return output_path
