from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Preformatted, XPreformatted, Table, TableStyle, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from highlight import highlight
from annotate import annotated
import callouts
import re

from paths import pdf
OUT = pdf('Fastify_Temporal_Companion_Guide.pdf')

ACCENT = colors.HexColor("#1f3a93")
ACCENT_LIGHT = colors.HexColor("#e8edf9")
CODE_BG = colors.HexColor("#f4f6fa")
CODE_BORDER = colors.HexColor("#d5dbe8")
NOTE_BG = colors.HexColor("#fff7e0")
WARN_BG = colors.HexColor("#fdecec")
GREY = colors.HexColor("#555555")

ss = getSampleStyleSheet()
PART = ParagraphStyle("PART", parent=ss["Title"], textColor=colors.white, fontSize=22,
                      leading=28, backColor=ACCENT, borderPadding=(10, 10, 10, 10),
                      spaceBefore=0, spaceAfter=18, alignment=0)
H1 = ParagraphStyle("H1", parent=ss["Heading1"], textColor=ACCENT, fontSize=17,
                    leading=21, spaceBefore=16, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], textColor=ACCENT, fontSize=12.5,
                    spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("Body", parent=ss["BodyText"], fontSize=10, leading=14, spaceAfter=5)
BULLET = ParagraphStyle("Bullet", parent=BODY, leftIndent=14, bulletIndent=4, spaceAfter=2)
CODE = ParagraphStyle("Code", fontName="Courier", fontSize=8.2, leading=10.3,
                      backColor=CODE_BG, borderColor=CODE_BORDER, borderWidth=0.6,
                      borderPadding=6, leftIndent=6, rightIndent=6,
                      spaceBefore=6, spaceAfter=10)
CAPTION = ParagraphStyle("Cap", parent=BODY, fontName="Helvetica-Bold", fontSize=8.5,
                         textColor=GREY, spaceAfter=0, spaceBefore=4)
NOTE = ParagraphStyle("Note", parent=BODY, backColor=NOTE_BG,
                      borderColor=colors.HexColor("#e8c55a"), borderWidth=0.6,
                      borderPadding=6, leftIndent=6, rightIndent=6,
                      spaceBefore=6, spaceAfter=10)
WARN = ParagraphStyle("Warn", parent=NOTE, backColor=WARN_BG,
                      borderColor=colors.HexColor("#e08a8a"))
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=9, leading=11.5, spaceAfter=0)
CELLB = ParagraphStyle("CellB", parent=CELL, fontName="Helvetica-Bold", textColor=colors.white)


class Story(list):
    """Holds headings until the next flowable, then keeps them together."""
    pending = []

    def append(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("H1", "H2"):
            self.pending.append(f)
            return
        if self.pending:
            inner = f._content if isinstance(f, KeepTogether) else [f]
            f = KeepTogether(self.pending + inner)
            self.pending = []
        super().append(f)


story = Story()
M = "<font face='Courier'>%s</font>"


def c(t): return M % t
def part(t):
    super(Story, story).append(PageBreak())
    super(Story, story).append(Paragraph(t, PART))
def h1(t): story.append(Paragraph(t, H1))
def h2(t): story.append(Paragraph(t, H2))
def p(t): story.append(Paragraph(t, BODY))
def note(t): story.append(Paragraph("<b>Tip:</b> " + t, NOTE))
def warn(t): story.append(Paragraph("<b>Watch out:</b> " + t, WARN))
def bullets(items):
    for i in items:
        story.append(Paragraph(i, BULLET, bulletText="\u2022"))
def steps(items):
    for n, i in enumerate(items, 1):
        story.append(Paragraph(i, BULLET, bulletText=f"{n}."))
ANNOTATE = {}          # path -> callout notes; filled only inside the project part
_MARKER = re.compile(r'^// ((?:src|test)/[\w/.-]+\.ts)\s*$')


def _split_files(body):
    """[(path|None, text)] split on '// src/x.ts' marker lines."""
    out, cur_path, cur = [], None, []
    for ln in body.split("\n"):
        m = _MARKER.match(ln)
        if m:
            if cur and any(x.strip() for x in cur):
                out.append((cur_path, "\n".join(cur).strip("\n")))
            cur_path, cur = m.group(1), [ln]
        else:
            cur.append(ln)
    if cur:
        out.append((cur_path, "\n".join(cur).strip("\n")))
    return out


def code(src, caption=None):
    body = src.strip("\n")
    if ANNOTATE and _MARKER.match(body.split("\n")[0]):
        for k, (path, text) in enumerate(_split_files(body)):
            cap = caption if k == 0 else None
            if path in ANNOTATE:
                for f in annotated(text, cap, ANNOTATE[path], path, CODE, BODY, ACCENT,
                                   CAPTION):
                    story.append(f)
            else:
                _plain_code(text, cap)
        return
    _plain_code(body, caption)


def _plain_code(src, caption=None):
    block = []
    if caption:
        block.append(Paragraph(caption, CAPTION))
    body = src.strip("\n")
    if body.count("\n") > 45:                 # long listing: allow page splits
        for f in block:
            story.append(f)
        story.append(XPreformatted(highlight(body), CODE))
        return
    block.append(XPreformatted(highlight(body), CODE))
    story.append(KeepTogether(block))
def table(rows, widths):
    data = [[Paragraph(x, CELLB) for x in rows[0]]] + \
           [[Paragraph(x, CELL) for x in r] for r in rows[1:]]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CODE_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, CODE_BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    if len(rows) <= 12:
        story.append(KeepTogether([t, Spacer(1, 8)]))
    else:
        for hd in story.pending:
            super(Story, story).append(hd)
        story.pending = []
        super(Story, story).append(t)
        super(Story, story).append(Spacer(1, 8))


# ---------- diagram helpers ----------
def box(d, x, y, w, h, label, fill=ACCENT_LIGHT, stroke=ACCENT, bold=True, size=9):
    d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=stroke, strokeWidth=1, rx=4, ry=4))
    lines = label.split("\n")
    for i, ln in enumerate(lines):
        yy = y + h / 2 + (len(lines) / 2 - i - 0.75) * (size + 2)
        d.add(String(x + w / 2, yy, ln, textAnchor="middle", fontSize=size,
                     fontName="Helvetica-Bold" if (bold and i == 0) else "Helvetica"))


def arrow(d, x1, y1, x2, y2, label="", dy=4, color=GREY):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1.1))
    import math
    a = math.atan2(y2 - y1, x2 - x1)
    s = 6
    d.add(Polygon([x2, y2,
                   x2 - s * math.cos(a - 0.4), y2 - s * math.sin(a - 0.4),
                   x2 - s * math.cos(a + 0.4), y2 - s * math.sin(a + 0.4)],
                  fillColor=color, strokeColor=color))
    if label:
        d.add(String((x1 + x2) / 2, (y1 + y2) / 2 + dy, label, textAnchor="middle",
                     fontSize=7.5, fontName="Helvetica", fillColor=GREY))


def architecture_diagram():
    d = Drawing(480, 190)
    box(d, 0, 70, 110, 60, "Client app\n(API, script, CLI)")
    d.add(Rect(160, 10, 160, 170, fillColor=colors.white, strokeColor=ACCENT,
               strokeWidth=1.2, rx=6, ry=6))
    d.add(String(240, 165, "Temporal Service", textAnchor="middle", fontSize=10,
                 fontName="Helvetica-Bold", fillColor=ACCENT))
    box(d, 175, 105, 130, 45, "Event History\n(durable DB)", size=8.5)
    box(d, 175, 30, 130, 50, "Task Queue\n\"orders\"", size=8.5)
    d.add(Rect(370, 10, 110, 170, fillColor=colors.white, strokeColor=ACCENT,
               strokeWidth=1.2, rx=6, ry=6))
    d.add(String(425, 165, "Worker (Node.js)", textAnchor="middle", fontSize=10,
                 fontName="Helvetica-Bold", fillColor=ACCENT))
    box(d, 380, 100, 90, 50, "Workflow code\n(V8 sandbox)", size=8)
    box(d, 380, 25, 90, 50, "Activity code\n(plain Node)", size=8)
    arrow(d, 110, 110, 160, 125, "start/signal", dy=6)
    arrow(d, 160, 85, 110, 90, "result/query", dy=-10)
    arrow(d, 370, 55, 320, 55, "long-poll", dy=5)
    arrow(d, 320, 140, 370, 140, "tasks", dy=5)
    arrow(d, 370, 115, 320, 115, "commands", dy=-10)
    return d


def replay_diagram():
    d = Drawing(480, 120)
    xs = [0, 100, 200, 300, 400]
    labels = ["Worker gets\nworkflow task", "Fetch history\nevents 1..N",
              "Re-run code;\nSDK returns\nrecorded results", "Reach new\ncode path",
              "Send new\ncommands"]
    for x, lb in zip(xs, labels):
        box(d, x, 35, 80, 55, lb, size=7.8)
    for x in xs[:-1]:
        arrow(d, x + 80, 62, x + 100, 62)
    d.add(String(240, 10, "Replay: completed activities are NOT re-executed; "
                 "their results come from history.", textAnchor="middle",
                 fontSize=8, fontName="Helvetica", fillColor=GREY))
    return d



# Content for the Fastify tutorial. Executed inside build_fastify.py after helpers.

def lifecycle_diagram():
    d = Drawing(480, 215)
    row1 = ["Incoming\nrequest", "Routing", "onRequest", "preParsing", "Body\nparsing",
            "preValidation"]
    row2 = ["Schema\nvalidation", "preHandler", "Handler", "preSerialization",
            "Serialize", "onSend"]
    w, h, gap = 68, 38, 14
    for i, lb in enumerate(row1):
        x = i * (w + gap)
        hook = lb.startswith("on") or lb.startswith("pre")
        box(d, x, 160, w, h, lb, fill=NOTE_BG if hook else ACCENT_LIGHT, size=7.8)
        if i:
            arrow(d, x - gap, 179, x, 179)
    arrow(d, 5 * (w + gap) + w / 2, 160, 5 * (w + gap) + w / 2, 128)
    for i, lb in enumerate(reversed(row2)):
        x = i * (w + gap)
        hook = lb.startswith("on") or lb.startswith("pre")
        box(d, x, 90, w, h, lb, fill=NOTE_BG if hook else ACCENT_LIGHT, size=7.8)
    for i in range(5, 0, -1):
        x = i * (w + gap)
        arrow(d, x, 109, x - gap, 109)
    arrow(d, w / 2, 90, w / 2, 62)
    box(d, 0, 25, w, h, "Response\nsent", size=7.8)
    arrow(d, w, 44, w + gap, 44)
    box(d, w + gap, 25, w, h, "onResponse", fill=NOTE_BG, size=7.8)
    box(d, 3 * (w + gap), 25, 2 * w + gap, h,
        "Error anywhere:\nonError -> setErrorHandler", fill=WARN_BG,
        stroke=colors.HexColor("#c05050"), size=7.8)
    d.add(String(480, 5, "Yellow = hooks you can attach. Blue = Fastify internals.",
                 textAnchor="end", fontSize=7.5, fontName="Helvetica", fillColor=GREY))
    return d


def encapsulation_diagram():
    d = Drawing(480, 170)
    box(d, 175, 125, 130, 38, "Root instance\nlogger, @fastify/sensible", size=8)
    box(d, 10, 60, 140, 42, "fp(dbPlugin)\napp.decorate('db')", fill=NOTE_BG, size=8)
    box(d, 170, 60, 140, 42, "adminRoutes\naddHook(onRequest: auth)", size=8)
    box(d, 330, 60, 140, 42, "publicRoutes\n(no auth hook)", size=8)
    box(d, 170, 5, 140, 38, "adminRoutes/users\ninherits auth hook", size=8)
    arrow(d, 210, 125, 80, 102)
    arrow(d, 240, 125, 240, 102)
    arrow(d, 270, 125, 400, 102)
    arrow(d, 240, 60, 240, 43)
    d.add(String(80, 108, "fp: 'db' lifted to root", textAnchor="middle", fontSize=7.5,
                 fontName="Helvetica", fillColor=GREY))
    d.add(String(400, 45, "cannot see admin's hook", textAnchor="middle", fontSize=7.5,
                 fontName="Helvetica", fillColor=GREY))
    return d



exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'combined_content.py'), encoding='utf8').read())

class Doc(SimpleDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("PART", "H1"):
            level = 0 if f.style.name == "PART" else 1
            text = f.getPlainText()
            key = "k%d" % id(f)
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=level == 0)
            self.notify("TOCEntry", (level, text, self.page, key))


def on_page(cv, doc):
    if doc.page == 1:
        return
    cv.saveState()
    cv.setStrokeColor(ACCENT)
    cv.setLineWidth(0.6)
    cv.line(20 * mm, A4[1] - 14 * mm, A4[0] - 20 * mm, A4[1] - 14 * mm)
    cv.setFont("Helvetica", 8)
    cv.setFillColor(GREY)
    cv.drawString(20 * mm, A4[1] - 12 * mm, "Fastify + Temporal - Companion Guide")
    cv.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Page {doc.page}")
    cv.restoreState()


doc = Doc(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
          topMargin=20 * mm, bottomMargin=18 * mm,
          title="Fastify + Temporal - Companion Guide", author="Claude")
doc.multiBuild(list(story), onFirstPage=on_page, onLaterPages=on_page)
print("wrote", OUT)
