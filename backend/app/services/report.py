import markdown
import os


def generate_pdf(markdown_text: str, output_path: str) -> str:
    try:
        from weasyprint import HTML
        html_content = markdown.markdown(markdown_text, extensions=["tables", "fenced_code"])
        styled_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: A4;
        margin: 2cm;
    }}
    body {{
        font-family: 'DejaVu Sans', Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #1f2937;
    }}
    h1 {{ color: #dc2626; border-bottom: 2px solid #dc2626; padding-bottom: 8px; }}
    h2 {{ color: #374151; margin-top: 24px; }}
    h3 {{ color: #4b5563; }}
    h4 {{ color: #6b7280; }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
    }}
    th, td {{
        border: 1px solid #d1d5db;
        padding: 8px 12px;
        text-align: left;
    }}
    th {{ background-color: #f3f4f6; font-weight: bold; }}
    blockquote {{
        border-left: 4px solid #3b82f6;
        margin: 16px 0;
        padding: 8px 16px;
        background: #f8fafc;
    }}
    code {{
        background: #f1f5f9;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10pt;
    }}
</style>
</head>
<body>
{html_content}
</body>
</html>"""
        HTML(string=styled_html).write_pdf(output_path)
    except ImportError:
        from weasyprint import HTML  # noqa: F811
        raise
    except Exception:
        with open(output_path.replace(".pdf", ".html"), "w") as f:
            f.write(styled_html)
        raise

    return output_path
