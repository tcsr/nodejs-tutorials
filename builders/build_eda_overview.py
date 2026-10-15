"""Builds 'Event-Driven Systems in Practice' from eda_overview.md.

A prose-first architecture overview (EDA, Kafka, Temporal, DynamoDB, Datadog).
The markdown subset understood here:
  % title / %% subtitle / %%% date      # h1 / ## h2
  ```lang [file=name] ... ```           > note        - bullet
  | table | rows |  (first row = header) [fig:name]
Inline: `code`, **bold**, *italic*.
"""
import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Polygon
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, NextPageTemplate, PageBreak, Paragraph,
    Spacer, XPreformatted, Table, TableStyle, ListFlowable, ListItem, KeepTogether,
    CondPageBreak,
)
from reportlab.platypus.tableofcontents import TableOfContents

from paths import pdf

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, 'eda_overview.md')
OUTPUT = pdf('Event_Driven_Systems_in_Practice.pdf')

FONTS = r'C:\Windows\Fonts'
for name, file in [('Georgia', 'georgia.ttf'), ('Georgia-Bold', 'georgiab.ttf'),
                   ('Georgia-Italic', 'georgiai.ttf'), ('Georgia-BoldItalic', 'georgiaz.ttf'),
                   ('Consolas', 'consola.ttf'), ('Segoe', 'segoeui.ttf'),
                   ('Segoe-Bold', 'segoeuib.ttf')]:
    pdfmetrics.registerFont(TTFont(name, os.path.join(FONTS, file)))
pdfmetrics.registerFontFamily('Georgia', normal='Georgia', bold='Georgia-Bold',
                              italic='Georgia-Italic', boldItalic='Georgia-BoldItalic')

INK = colors.HexColor('#222222')
GREY = colors.HexColor('#6b6b6b')
RULE = colors.HexColor('#c8c8c8')
CODE_BG = colors.HexColor('#f5f4f0')
ACCENT = colors.HexColor('#2f5d7c')

PAGE_W, PAGE_H = A4
MARGIN = 2.3 * cm
TEXT_W = PAGE_W - 2 * MARGIN

body = ParagraphStyle('body', fontName='Georgia', fontSize=10.3, leading=15.2,
                      textColor=INK, spaceAfter=7)
h1 = ParagraphStyle('h1', fontName='Georgia-Bold', fontSize=17, leading=22,
                    textColor=INK, spaceBefore=16, spaceAfter=10)
h2 = ParagraphStyle('h2', fontName='Georgia-Bold', fontSize=12, leading=16,
                    textColor=INK, spaceBefore=10, spaceAfter=5)
note = ParagraphStyle('note', parent=body, fontName='Georgia-Italic', textColor=GREY,
                      leftIndent=0, spaceAfter=0)
cell = ParagraphStyle('cell', parent=body, fontSize=8.8, leading=12, spaceAfter=0)
cell_head = ParagraphStyle('cellh', parent=cell, fontName='Georgia-Bold')
code_style = ParagraphStyle('code', fontName='Consolas', fontSize=8, leading=10.6,
                            textColor=INK)
caption = ParagraphStyle('caption', parent=body, fontName='Georgia-Italic', fontSize=9,
                         leading=12, textColor=GREY, alignment=TA_CENTER, spaceBefore=4,
                         spaceAfter=12)
toc_l0 = ParagraphStyle('toc0', parent=body, fontSize=10.5, leading=19, spaceAfter=0)


# ---------------------------------------------------------------- inline markup
def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def inline(text):
    parts = text.split('`')
    out = []
    for i, part in enumerate(parts):
        if i % 2:
            out.append(f'<font name="Consolas" size="9">{esc(part)}</font>')
        else:
            p = esc(part)
            p = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', p)
            p = re.sub(r'\*(.+?)\*', r'<i>\1</i>', p)
            out.append(p)
    return ''.join(out)


# ---------------------------------------------------------------- figures
SANS, SANS_B = 'Segoe', 'Segoe-Bold'
BOX_FILL = colors.HexColor('#f3f3f1')
BOX_LINE = colors.HexColor('#8a8a8a')


def box(d, x, y, w, h, label, sub=None, fill=BOX_FILL, bold=True):
    d.add(Rect(x, y, w, h, rx=3, ry=3, fillColor=fill, strokeColor=BOX_LINE,
               strokeWidth=0.7))
    cy = y + h / 2 + (3 if sub else -3)
    d.add(String(x + w / 2, cy, label, fontName=SANS_B if bold else SANS, fontSize=8.5,
                 fillColor=INK, textAnchor='middle'))
    if sub:
        d.add(String(x + w / 2, cy - 11, sub, fontName=SANS, fontSize=7,
                     fillColor=GREY, textAnchor='middle'))


def arrow(d, x1, y1, x2, y2, label=None, dx=0, dy=4, color=INK, dashed=False,
          anchor='middle'):
    line = Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=0.8)
    if dashed:
        line.strokeDashArray = [3, 2]
    d.add(line)
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    s = 5
    d.add(Polygon([x2, y2,
                   x2 - s * math.cos(a - 0.4), y2 - s * math.sin(a - 0.4),
                   x2 - s * math.cos(a + 0.4), y2 - s * math.sin(a + 0.4)],
                  fillColor=color, strokeColor=color, strokeWidth=0.5))
    if label:
        d.add(String((x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label, fontName=SANS,
                     fontSize=7, fillColor=GREY, textAnchor=anchor))


def text(d, x, y, s, size=7.5, color=GREY, anchor='middle', font=SANS):
    d.add(String(x, y, s, fontName=font, fontSize=size, fillColor=color,
                 textAnchor=anchor))


def fig_choreography():
    d = Drawing(TEXT_W, 175)
    # left: choreography
    text(d, 105, 162, 'Choreography', 9, INK, font=SANS_B)
    box(d, 60, 112, 90, 30, 'Order service')
    box(d, 0, 40, 80, 30, 'Inventory')
    box(d, 130, 40, 80, 30, 'Payment')
    arrow(d, 85, 112, 45, 71, 'OrderPlaced', dx=-26)
    arrow(d, 80, 55, 129, 55)
    text(d, 105, 28, 'StockReserved', 7)
    arrow(d, 170, 71, 130, 112, 'PaymentSucceeded', dx=34)
    text(d, 105, 8, 'each service reacts to the previous event')
    d.add(Line(TEXT_W / 2, 10, TEXT_W / 2, 165, strokeColor=RULE, strokeWidth=0.6))
    # right: orchestration
    ox = TEXT_W / 2 + 10
    text(d, ox + 110, 162, 'Orchestration', 9, INK, font=SANS_B)
    box(d, ox + 60, 108, 100, 34, 'Order saga', 'owns the sequence', fill=colors.HexColor('#e8eef2'))
    box(d, ox + 0, 30, 90, 30, 'Inventory')
    box(d, ox + 130, 30, 90, 30, 'Payment')
    arrow(d, ox + 85, 108, ox + 50, 61, 'ReserveStock', dx=-32)
    arrow(d, ox + 60, 61, ox + 95, 108, None, color=GREY, dashed=True)
    arrow(d, ox + 135, 108, ox + 170, 61, 'RequestPayment', dx=36)
    arrow(d, ox + 160, 61, ox + 125, 108, None, color=GREY, dashed=True)
    text(d, ox + 110, 8, 'commands out, replies (dashed) back')
    return d, 'The same order flow, choreographed (left) and orchestrated (right).'


def fig_bridges():
    d = Drawing(TEXT_W, 190)
    kafka_fill = colors.HexColor('#f1ede4')
    temporal_fill = colors.HexColor('#e8eef2')
    text(d, 4, 176, 'Kafka', 8.5, INK, 'start', SANS_B)
    text(d, TEXT_W - 4, 176, 'Temporal', 8.5, INK, 'end', SANS_B)
    box(d, 0, 125, 105, 34, 'orders', 'topic', fill=kafka_fill)
    box(d, 160, 125, 110, 34, 'Saga starter', 'Kafka consumer')
    box(d, TEXT_W - 125, 95, 125, 64, 'orderSaga', 'order-saga-o-123', fill=temporal_fill)
    arrow(d, 105, 142, 159, 142, 'OrderPlaced')
    arrow(d, 270, 142, TEXT_W - 126, 142, 'start (ID from order)')
    box(d, 0, 64, 105, 34, 'payment.commands', 'topic', fill=kafka_fill)
    box(d, 160, 54, 110, 32, 'Payment service', 'another team')
    box(d, 0, 6, 105, 34, 'payment.events', 'topic', fill=kafka_fill)
    box(d, 160, 6, 110, 34, 'Payment bridge', 'Kafka consumer')
    arrow(d, TEXT_W - 125, 101, 106, 93, 'RequestPayment (activity)', dx=60, dy=5)
    arrow(d, 106, 72, 159, 72)
    arrow(d, 175, 54, 106, 34)
    text(d, 109, 22, 'PaymentSucceeded', 6.5, GREY, 'start')
    arrow(d, 106, 15, 159, 15)
    arrow(d, 271, 23, TEXT_W - 62, 94, 'signal: paymentResult', dx=70, dy=-22,
          color=ACCENT)
    return d, ('Two small bridges connect Kafka and Temporal: one starts sagas, '
               'the other turns payment events into signals.')


def fig_architecture():
    d = Drawing(TEXT_W, 300)
    aws = colors.HexColor('#faf9f6')
    d.add(Rect(0, 52, TEXT_W, 245, rx=4, ry=4, fillColor=aws, strokeColor=RULE,
               strokeWidth=0.7, strokeDashArray=[4, 3]))
    text(d, 8, 285, 'AWS account', 8, GREY, 'start', SANS_B)
    kafka_fill = colors.HexColor('#f1ede4')
    temporal_fill = colors.HexColor('#e8eef2')
    db_fill = colors.HexColor('#eef2ea')
    box(d, 8, 225, 78, 34, 'Client')
    box(d, 112, 225, 100, 34, 'Order API', 'Fastify on ECS')
    box(d, 245, 225, 100, 34, 'DynamoDB', 'orders + outbox', fill=db_fill)
    box(d, 368, 225, 82, 34, 'Outbox relay', 'Lambda on Streams')
    arrow(d, 86, 242, 111, 242)
    arrow(d, 212, 242, 244, 242, 'tx')
    arrow(d, 345, 242, 367, 242)
    box(d, 112, 150, TEXT_W - 120, 38, 'Amazon MSK (Kafka)',
        'orders  ·  payment.commands  ·  payment.events  ·  *.dlq', fill=kafka_fill)
    arrow(d, 409, 225, 409, 189)
    box(d, 8, 75, 90, 38, 'Temporal', 'Cloud or EKS', fill=temporal_fill)
    box(d, 112, 75, 100, 38, 'Saga workers', '+ bridges')
    box(d, 226, 75, 100, 38, 'Payment service', 'own DynamoDB')
    box(d, 340, 75, 110, 38, 'Projection, e-mail', 'choreographed')
    arrow(d, 98, 94, 111, 94)
    arrow(d, 111, 98, 99, 98)
    arrow(d, 162, 149, 162, 114)
    arrow(d, 176, 114, 176, 149)
    arrow(d, 270, 149, 270, 114)
    arrow(d, 284, 114, 284, 149)
    arrow(d, 395, 149, 395, 114)
    arrow(d, 162, 224, 162, 189, dashed=True, color=GREY)
    text(d, 168, 203, 'GET status (read model)', 6.5, GREY, 'start')
    box(d, 0, 6, TEXT_W, 32, 'Datadog',
        'APM traces  ·  Data Streams Monitoring  ·  Temporal metrics  ·  '
        'DynamoDB / MSK via AWS integration  ·  logs', fill=colors.HexColor('#efe9f3'))
    for x in (60, 160, 290, 400):
        arrow(d, x, 52, x, 39, color=GREY, dashed=True)
    return d, ('Reference deployment on AWS. Dashed arrows into Datadog are agents and '
               'integrations, not application traffic.')


def fig_sequence():
    lanes = ['Client', 'Order API', 'DynamoDB', 'Relay', 'Kafka', 'Saga', 'Payment']
    d = Drawing(TEXT_W, 300)
    step = TEXT_W / len(lanes)
    xs = [step * i + step / 2 for i in range(len(lanes))]
    for x, name in zip(xs, lanes):
        box(d, x - 30, 272, 60, 22, name)
        d.add(Line(x, 272, x, 8, strokeColor=RULE, strokeWidth=0.7,
                   strokeDashArray=[2, 2]))
    rows = [
        (0, 1, 'POST /orders', '0 ms'),
        (1, 2, 'order + outbox (tx)', '20 ms'),
        (1, 0, '202 Accepted', '30 ms'),
        (2, 3, 'stream record', '~0.5 s'),
        (3, 4, 'OrderPlaced', ''),
        (4, 5, 'start saga', ''),
        (5, 4, 'RequestPayment', ''),
        (4, 6, 'command', ''),
        (6, 4, 'PaymentSucceeded', '~1.5 s'),
        (4, 5, 'signal', ''),
        (5, 2, 'confirm order', '~2 s'),
    ]
    y = 252
    for a, b, label, t in rows:
        color = GREY if b < a and label in ('202 Accepted',) else INK
        arrow(d, xs[a], y, xs[b] + (-2 if b > a else 2), y, label, dy=3, color=color)
        if t:
            text(d, 2, y - 2, t, 6.5, GREY, 'start')
        y -= 22
    return d, ('One order on a good day. The client has its answer after 30 ms; '
               'the rest happens asynchronously in about two seconds.')


FIGURES = {
    'choreography': fig_choreography,
    'bridges': fig_bridges,
    'architecture': fig_architecture,
    'sequence': fig_sequence,
}


# ---------------------------------------------------------------- blocks
def code_block(src, lang):
    pre = XPreformatted(esc(src.rstrip('\n')), code_style)
    t = Table([[pre]], colWidths=[TEXT_W])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('LINEBEFORE', (0, 0), (0, -1), 1.5, RULE),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    t.spaceBefore, t.spaceAfter = 3, 10
    return t


def note_block(lines):
    p = Paragraph(inline(' '.join(lines)), note)
    t = Table([[p]], colWidths=[TEXT_W - 1.2 * cm])
    t.setStyle(TableStyle([
        ('LINEBEFORE', (0, 0), (0, -1), 1.2, ACCENT),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    t.hAlign = 'LEFT'
    t.spaceBefore, t.spaceAfter = 4, 10
    return t


def bullet_block(items):
    lf = ListFlowable(
        [ListItem(Paragraph(inline(i), ParagraphStyle('li', parent=body, spaceAfter=3)),
                  leftIndent=14, value='\u2013') for i in items],
        bulletType='bullet', start='\u2013', leftIndent=14, bulletFontName='Georgia',
        bulletFontSize=10)
    return [lf, Spacer(1, 5)]


def table_block(rows):
    cells = [[c.strip() for c in r.strip().strip('|').split('|')] for r in rows]
    n = len(cells[0])
    lengths = [max(len(r[i]) for r in cells) for i in range(n)]
    total = sum(lengths)
    widths = [TEXT_W * max(0.18, l / total) for l in lengths]
    widths = [w * TEXT_W / sum(widths) for w in widths]
    data = [[Paragraph(inline(c), cell_head if r == 0 else cell) for c in row]
            for r, row in enumerate(cells)]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.9, INK),
        ('LINEBELOW', (0, 0), (-1, 0), 0.6, INK),
        ('LINEBELOW', (0, 1), (-1, -2), 0.3, RULE),
        ('LINEBELOW', (0, -1), (-1, -1), 0.9, INK),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    t.spaceBefore, t.spaceAfter = 4, 12
    return t


class Heading(Paragraph):
    def __init__(self, text, style, level, key):
        super().__init__(text, style)
        self.toc_level, self.key = level, key


def parse(md):
    meta, story = {}, []
    lines = md.split('\n')
    i, section, sub, fig_no = 0, 0, 0, 0
    para = []

    def flush():
        if para:
            story.append(Paragraph(inline(' '.join(para)), body))
            para.clear()

    while i < len(lines):
        line = lines[i]
        if line.startswith('%%% '):
            meta['date'] = line[4:]
        elif line.startswith('%% '):
            meta['subtitle'] = line[3:]
        elif line.startswith('% '):
            meta['title'] = line[2:]
        elif line.startswith('# '):
            flush()
            title = line[2:]
            numbered = title not in ('About this document', 'Further reading')
            if numbered:
                section += 1
                sub = 0
                label = f'{section}.&nbsp;&nbsp;{esc(title)}'
            else:
                label = esc(title)
            story.append(CondPageBreak(7 * cm))
            story.append(Heading(label, h1, 0, f's{len(story)}'))
        elif line.startswith('## '):
            flush()
            sub += 1
            story.append(CondPageBreak(4 * cm))
            story.append(Heading(f'{section}.{sub}&nbsp;&nbsp;{inline(line[3:])}', h2,
                                 1, f's{len(story)}'))
        elif line.startswith('```'):
            flush()
            lang = line[3:].split()[0] if line[3:].strip() else ''
            j = i + 1
            buf = []
            while not lines[j].startswith('```'):
                buf.append(lines[j])
                j += 1
            story.append(code_block('\n'.join(buf), lang))
            i = j
        elif line.startswith('[fig:'):
            flush()
            fig_no += 1
            drawing, cap = FIGURES[line[5:-1]]()
            story.append(KeepTogether([Spacer(1, 4), drawing,
                                       Paragraph(f'Figure {fig_no}. {esc(cap)}', caption)]))
        elif line.startswith('> '):
            flush()
            buf = []
            while i < len(lines) and lines[i].startswith('>'):
                buf.append(lines[i][1:].strip())
                i += 1
            story.append(note_block(buf))
            continue
        elif line.startswith('- '):
            flush()
            items = []
            while i < len(lines) and (lines[i].startswith('- ') or
                                      lines[i].startswith('  ')):
                if lines[i].startswith('- '):
                    items.append(lines[i][2:].strip())
                else:
                    items[-1] += ' ' + lines[i].strip()
                i += 1
            story.extend(bullet_block(items))
            continue
        elif line.startswith('| '):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith('| '):
                rows.append(lines[i])
                i += 1
            story.append(table_block(rows))
            continue
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
        i += 1
    flush()
    return meta, story


# ---------------------------------------------------------------- document
class Doc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if not isinstance(flowable, Heading):
            return
        text_ = flowable.getPlainText()
        self.canv.bookmarkPage(flowable.key)
        self.canv.addOutlineEntry(text_, flowable.key, level=flowable.toc_level)
        if flowable.toc_level == 0:
            self.notify('TOCEntry', (0, text_, self.page, flowable.key))


def build():
    meta, story = parse(open(SOURCE, encoding='utf-8').read())
    doc = Doc(OUTPUT, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
              topMargin=2.4 * cm, bottomMargin=2.2 * cm, title=meta['title'],
              subject=meta['subtitle'])
    frame = Frame(MARGIN, 2.2 * cm, TEXT_W, PAGE_H - 4.6 * cm, id='f',
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    def title_page(c, _doc):
        c.saveState()
        c.setFillColor(ACCENT)
        c.rect(MARGIN, PAGE_H - 9.2 * cm, 2.2 * cm, 0.12 * cm, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont('Georgia-Bold', 30)
        y = PAGE_H - 11 * cm
        for word_line in ['Event-Driven Systems', 'in Practice']:
            c.drawString(MARGIN, y, word_line)
            y -= 38
        c.setFont('Georgia-Italic', 13)
        c.setFillColor(GREY)
        c.drawString(MARGIN, y - 10, meta['subtitle'])
        c.setFont('Georgia', 10)
        c.drawString(MARGIN, 3 * cm, meta['date'])
        c.restoreState()

    def page(c, d):
        c.saveState()
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        c.line(MARGIN, PAGE_H - 1.6 * cm, PAGE_W - MARGIN, PAGE_H - 1.6 * cm)
        c.setFont('Georgia-Italic', 8.5)
        c.setFillColor(GREY)
        c.drawString(MARGIN, PAGE_H - 1.4 * cm, meta['title'])
        c.setFont('Georgia', 9)
        c.drawCentredString(PAGE_W / 2, 1.3 * cm, str(d.page))
        c.restoreState()

    doc.addPageTemplates([PageTemplate('title', [frame], onPage=title_page),
                          PageTemplate('body', [frame], onPage=page)])
    toc = TableOfContents()
    toc.levelStyles = [toc_l0]
    toc.dotsMinLevel = 0
    front = [NextPageTemplate('body'), PageBreak(),
             Paragraph('Contents', h1), Spacer(1, 6), toc, PageBreak()]
    doc.multiBuild(front + story)
    print(OUTPUT)


if __name__ == '__main__':
    build()
