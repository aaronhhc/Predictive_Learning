"""Build the submission PDF from final_homework1.md.

Markdown is converted to HTML, math is typeset with KaTeX (loaded from a CDN),
and the page is printed to PDF with headless Google Chrome (macOS path below).

    uv run --no-project --with markdown python report/build_pdf.py
"""
from pathlib import Path
import html
import re
import subprocess
import tempfile

import markdown

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "report/final_homework1.md"
TARGET = ROOT / "Homework1_61547048S_黃竑喆.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
KATEX = "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9"

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: 'Times New Roman', Times, serif; font-size: 11pt; line-height: 1.38; color: #111; }
h1 { font-size: 24pt; margin: 0 0 10pt; }
h2 { font-size: 15pt; margin: 18pt 0 6pt; break-after: avoid; }
h3 { font-size: 12.5pt; margin: 14pt 0 4pt; break-after: avoid; }
p { margin: 0 0 8pt; }
a { color: #1a4f9c; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 9.5pt; break-inside: avoid; }
th, td { padding: 3pt 8pt; border-bottom: 0.5pt solid #cbd2d9; }
thead th { border-top: 0.5pt solid #718096; border-bottom: 0.5pt solid #718096; background: #f0f3f5; }
.katex-display { margin: 8pt 0; break-inside: avoid; }
"""


def render(text):
    math = []

    def stash(match):
        math.append(match.group(0))
        return f"@@MATH{len(math) - 1}@@"

    text = re.sub(r"\$\$.+?\$\$", stash, text, flags=re.S)
    body = markdown.markdown(text, extensions=["tables"])
    body = re.sub(r"@@MATH(\d+)@@", lambda m: html.escape(math[int(m.group(1))]), body)
    # right-align numeric columns declared with ---: in the Markdown source
    return body


def main():
    source = SOURCE.read_text()
    body = render(source)
    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Homework 1 — 黃竑喆 — 61547048S</title>
<link rel="stylesheet" href="{KATEX}/katex.min.css"><style>{CSS}</style>
<script defer src="{KATEX}/katex.min.js"></script>
<script defer src="{KATEX}/contrib/auto-render.min.js"></script>
<script>document.addEventListener('DOMContentLoaded',()=>renderMathInElement(document.body,
{{delimiters:[{{left:'$$',right:'$$',display:true}}]}}));</script>
</head><body>{body}</body></html>"""
    with tempfile.TemporaryDirectory(prefix="hw1-pdf-") as tmp:
        page_path = Path(tmp) / "report.html"
        page_path.write_text(page)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--virtual-time-budget=20000", f"--print-to-pdf={TARGET}",
                        page_path.as_uri()], check=True, capture_output=True)
    print(f"Wrote {TARGET}")


if __name__ == "__main__":
    main()
