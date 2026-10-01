"""Annotated code listings: split a file into chunks, badge key lines, notes after each chunk."""
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (Paragraph, XPreformatted, Table, TableStyle, KeepTogether,
                                Spacer)
from highlight import highlight

BADGE = ('&nbsp;&nbsp;<font name="Helvetica-Bold" size="7" color="#ffffff" '
         'backColor="{bg}">&nbsp;{n}&nbsp;</font>')


def _chunks(lines, min_len=14, max_len=34):
    """Split at blank lines into chunks of roughly min_len..max_len lines."""
    chunks, cur = [], []
    for i, ln in enumerate(lines):
        if not ln.strip() and len(cur) >= min_len:
            chunks.append(cur)
            cur = []
            continue
        cur.append(i)
        if len(cur) >= max_len and i + 1 < len(lines) and not lines[i + 1].strip():
            chunks.append(cur)
            cur = []
    if cur:
        if chunks and len(cur) < 5:          # avoid tiny trailing chunk
            chunks[-1].extend(cur)
        else:
            chunks.append(cur)
    return chunks


def _locate(lines, notes, path):
    """Map each note anchor to a line index (anchors must appear in order)."""
    found, start = [], 0
    for anchor, text in notes:
        for i in range(start, len(lines)):
            if anchor in lines[i]:
                found.append((i, text))
                start = i + 1
                break
        else:
            raise ValueError(f'{path}: callout anchor not found (in order): {anchor!r}')
    return found


def annotated(body, caption, notes, path, code_style, body_style, accent, caption_style):
    lines = body.split('\n')
    marks = _locate(lines, notes, path)
    num_of_line = {i: n for n, (i, _) in enumerate(marks, 1)}
    text_of_num = {n: t for n, (_, t) in enumerate(marks, 1)}
    bg = accent.hexval().replace('0x', '#')

    note_style = ParagraphStyle('Note', parent=body_style, fontSize=9, leading=12,
                                spaceAfter=0)
    num_style = ParagraphStyle('Num', parent=note_style, fontName='Helvetica-Bold',
                               textColor=colors.white, alignment=1)

    flow = []
    for ci, idxs in enumerate(_chunks(lines)):
        # drop blank lines at chunk edges
        while idxs and not lines[idxs[0]].strip():
            idxs = idxs[1:]
        while idxs and not lines[idxs[-1]].strip():
            idxs = idxs[:-1]
        if not idxs:
            continue
        seg = [lines[i] for i in range(idxs[0], idxs[-1] + 1)]
        # highlight whole segment (lexer context), then append badges per line
        hl = highlight('\n'.join(seg)).split('\n')
        for k, li in enumerate(range(idxs[0], idxs[-1] + 1)):
            if li in num_of_line:
                hl[k] += BADGE.format(bg=bg, n=num_of_line[li])
        pre = XPreformatted('\n'.join(hl), code_style)
        nums = [num_of_line[i] for i in range(idxs[0], idxs[-1] + 1) if i in num_of_line]
        part = []
        if ci == 0 and caption:
            part.append(Paragraph(caption, caption_style))
        part.append(pre)
        if nums:
            rows = [[Paragraph(str(n), num_style), Paragraph(text_of_num[n], note_style)]
                    for n in nums]
            t = Table(rows, colWidths=[7.5 * mm, 156.5 * mm], hAlign='RIGHT')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), accent),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 2.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
                ('LEFTPADDING', (1, 0), (1, -1), 6),
                ('LEFTPADDING', (0, 0), (0, -1), 1),
                ('RIGHTPADDING', (0, 0), (0, -1), 1),
                ('LINEBELOW', (1, 0), (1, -2), 0.3, colors.HexColor('#d5dbe8')),
                ('LINEBELOW', (0, 0), (0, -2), 1.2, colors.white),
            ]))
            part += [t, Spacer(1, 10)]
        if len(seg) <= 40:
            flow.append(KeepTogether(part))
        else:
            flow.extend(part)
    return flow
