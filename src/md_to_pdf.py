"""Convert Member_5_Presentation_Speech_Guide.md to a beautifully styled PDF."""

import subprocess
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "review1"
MD_PATH = REPORT_DIR / "Member_5_Presentation_Speech_Guide.md"
HTML_PATH = REPORT_DIR / "Member_5_Presentation_Speech_Guide.html"
PDF_PATH = REPORT_DIR / "Member_5_Presentation_Speech_Guide.pdf"

CSS = """
@page {
    size: A4;
    margin: 1.8cm 1.5cm 1.8cm 1.5cm;
    @bottom-right {
        content: counter(page);
        font-size: 9pt;
        color: #64748B;
    }
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1E293B;
    line-height: 1.6;
    font-size: 10.5pt;
    margin: 0;
    padding: 0;
}

h1 {
    color: #0F172A;
    font-size: 20pt;
    font-weight: 800;
    margin-top: 0;
    margin-bottom: 4px;
    border-bottom: 2px solid #2563EB;
    padding-bottom: 8px;
}

h2 {
    color: #1E3A8A;
    font-size: 14pt;
    font-weight: 700;
    margin-top: 24px;
    margin-bottom: 8px;
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 4px;
}

h3 {
    color: #1E40AF;
    font-size: 12pt;
    font-weight: 700;
    margin-top: 20px;
    margin-bottom: 6px;
}

h4 {
    color: #334155;
    font-size: 11pt;
    font-weight: 700;
    margin-top: 14px;
    margin-bottom: 4px;
}

p {
    margin-top: 4px;
    margin-bottom: 8px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    margin-bottom: 16px;
    font-size: 9.5pt;
}

th {
    background-color: #1E293B;
    color: #FFFFFF;
    font-weight: 600;
    text-align: left;
    padding: 8px 10px;
    border: 1px solid #0F172A;
}

td {
    padding: 7px 10px;
    border: 1px solid #CBD5E1;
    vertical-align: top;
}

tr:nth-child(even) td {
    background-color: #F8FAFC;
}

blockquote {
    background-color: #F0F9FF;
    border-left: 4px solid #0284C7;
    margin: 10px 0;
    padding: 10px 14px;
    font-style: normal;
    color: #0F172A;
    border-radius: 0 4px 4px 0;
}

blockquote p {
    margin: 4px 0;
}

code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    font-size: 9pt;
    background-color: #F1F5F9;
    padding: 2px 5px;
    border-radius: 3px;
    color: #0F172A;
    border: 1px solid #E2E8F0;
}

pre {
    background-color: #0F172A;
    color: #F8FAFC;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 8.5pt;
    line-height: 1.45;
    margin: 10px 0;
}

pre code {
    background-color: transparent;
    color: #F8FAFC;
    padding: 0;
    border: none;
}

ul, ol {
    margin-top: 4px;
    margin-bottom: 8px;
    padding-left: 20px;
}

li {
    margin-bottom: 4px;
}

strong {
    color: #0F172A;
}

hr {
    border: 0;
    height: 1px;
    background: #E2E8F0;
    margin: 20px 0;
}

.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 8pt;
    font-weight: bold;
    text-transform: uppercase;
}

.badge-pass {
    background-color: #DCFCE7;
    color: #166534;
}
"""

def generate_pdf():
    print(f"Reading markdown from: {MD_PATH}")
    md_content = MD_PATH.read_text(encoding="utf-8")

    # Convert markdown to HTML
    body_html = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "nl2br"]
    )

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Member 5 Presentation Speech Guide & Viva Cheatsheet</title>
    <style>
{CSS}
    </style>
</head>
<body>
{body_html}
</body>
</html>
"""

    HTML_PATH.write_text(full_html, encoding="utf-8")
    print(f"✓ Wrote styled HTML to: {HTML_PATH}")

    # Convert to PDF via headless LibreOffice
    cmd = [
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        str(HTML_PATH),
        "--outdir",
        str(REPORT_DIR)
    ]
    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if HTML_PATH.exists():
        HTML_PATH.unlink()
    if res.returncode != 0:
        print(f"Error converting to PDF: {res.stderr}")
        return False

    print(f"✓ Generated PDF at: {PDF_PATH}")
    if PDF_PATH.exists():
        size_kb = PDF_PATH.stat().st_size / 1024
        print(f"✓ PDF file size: {size_kb:.1f} KB")
    return True

if __name__ == "__main__":
    generate_pdf()
