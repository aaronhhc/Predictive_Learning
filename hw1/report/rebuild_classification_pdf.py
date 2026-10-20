"""Rebuild classification text while preserving the existing regression PDF exactly.

The existing submission has regression content beginning at y=702 on page 1.
Only the classification rectangle is redacted and replaced from final_homework1.md.
Original header, footer, and all regression content retain their page geometry.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import tempfile

import pymupdf as fitz
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'Homework1_61547048S_黃竑喆.pdf'
FONT_DIR = Path('/System/Library/Fonts/Supplemental')
pdfmetrics.registerFont(TTFont('HomeworkTimes', str(FONT_DIR / 'Times New Roman.ttf')))
pdfmetrics.registerFont(TTFont('HomeworkTimesBold', str(FONT_DIR / 'Times New Roman Bold.ttf')))
pdfmetrics.registerFontFamily('HomeworkTimes', normal='HomeworkTimes', bold='HomeworkTimesBold')


def inline(text):
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    return re.sub(r'`(.+?)`', r'\1', text)


def flowables(source, font_size):
    body = ParagraphStyle('body', fontName='HomeworkTimes', fontSize=font_size,
                          leading=font_size * 1.2857)
    heading = ParagraphStyle('heading', parent=body, fontName='HomeworkTimesBold',
                             fontSize=14.5, leading=18)
    cell = ParagraphStyle('cell', parent=body, fontSize=9, leading=11, alignment=1)
    result = []
    for block in source.strip().split('\n\n'):
        if block.startswith('## '):
            result.append((Paragraph(inline(block[3:]), heading), 7))
        elif block.startswith('|'):
            rows = [line for line in block.splitlines() if not re.fullmatch(r'[|:\- ]+', line)]
            cells = [[Paragraph(inline(s.strip()), cell) for s in line.strip('|').split('|')] for line in rows]
            table = Table(cells, colWidths=[155, 70, 155, 113.0])
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#f0f3f5')),
                ('LINEABOVE',(0,0),(-1,0),0.5,colors.HexColor('#718096')),
                ('LINEBELOW',(0,0),(-1,0),0.5,colors.HexColor('#718096')),
                ('LINEBELOW',(0,-1),(-1,-1),0.5,colors.HexColor('#718096')),
                ('TOPPADDING',(0,0),(-1,-1),3), ('BOTTOMPADDING',(0,0),(-1,-1),3),
                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ]))
            result.append((table, 8))
        else:
            result.append((Paragraph(inline(block.replace('\n',' ')), body), 8))
    return result


def raster_digest(page, clip=None):
    return hashlib.sha256(page.get_pixmap(matrix=fitz.Matrix(1.5,1.5), clip=clip).samples).hexdigest()


def main():
    document = fitz.open(TARGET)
    assert len(document) == 3
    first = document[0]
    regression_rect = fitz.Rect(0, 698, first.rect.width, first.rect.height)
    regression_before = [raster_digest(first, regression_rect)] + [raster_digest(p) for p in list(document)[1:]]
    original_text = [p.get_text() for p in document]
    report = (ROOT / 'report/final_homework1.md').read_text()
    source = '## Problem 2.7' + report.split('## Problem 2.7',1)[1].split('## Problem 2.11',1)[0]
    width = 493
    top, bottom = 150, 696
    for size in (10.5, 10.25, 10.0, 9.75):
        items = flowables(source, size)
        heights = [item.wrap(width, 10000)[1] for item, gap in items]
        total = sum(heights) + sum(gap for item, gap in items[:-1])
        if total <= bottom - top:
            break
    else:
        raise ValueError('Classification content does not fit the reserved region')
    with tempfile.TemporaryDirectory(prefix='hw1-pdf-') as temporary:
        overlay_path = Path(temporary) / 'classification.pdf'
        canvas = Canvas(str(overlay_path), pagesize=(first.rect.width, first.rect.height))
        y = first.rect.height - top
        for (item, gap), height in zip(items, heights):
            y -= height
            item.drawOn(canvas, 51, y)
            y -= gap
        canvas.save()
        first.add_redact_annot(fitz.Rect(45, 145, 550, 697), fill=(1,1,1))
        first.apply_redactions(images=0, graphics=1)
        overlay = fitz.open(overlay_path)
        first.show_pdf_page(first.rect, overlay, 0)
        metadata = document.metadata
        metadata['modDate'] = fitz.get_pdf_now()
        document.set_metadata(metadata)
        rebuilt_path = Path(temporary) / 'submission.pdf'
        document.save(rebuilt_path, garbage=4, deflate=True)
        rebuilt = fitz.open(rebuilt_path)
        regression_after = [raster_digest(rebuilt[0], regression_rect)] + [raster_digest(p) for p in list(rebuilt)[1:]]
        assert regression_before == regression_after, 'Regression rendering changed'
        assert rebuilt[0].get_text().split('Problem 2.11',1)[1].split('1 / 3',1)[0] == original_text[0].split('Problem 2.11',1)[1].split('1 / 3',1)[0]
        assert all(rebuilt[i].get_text() == original_text[i] for i in (1,2))
        for i, page in enumerate(rebuilt):
            page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(f'/private/tmp/hw1-revised-page-{i+1}.png')
        TARGET.write_bytes(rebuilt_path.read_bytes())
    (ROOT / 'results/classification_pdf_verification.json').write_text(json.dumps({
        'pdf':str(TARGET), 'pages':3, 'classification_body_font_size':size,
        'classification_height':total, 'regression_render_sha256_before':regression_before,
        'regression_render_sha256_after':regression_after,
        'regression_text_and_rendering_unchanged':True,
    }, indent=2)+'\n')
    print(f'Updated {TARGET}; font={size}; classification height={total:.2f}; regression pixels unchanged')


if __name__ == '__main__':
    main()
