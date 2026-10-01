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
OUT = pdf('Fastify_NodeJS_Complete_Tutorial.pdf')

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


# =========================================================================
# TITLE + TOC
# =========================================================================
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fastify_examples_content.py'), encoding='utf8').read())

super(Story, story).append(Spacer(1, 60 * mm))
super(Story, story).append(Paragraph("Fastify with Node.js", ParagraphStyle(
    "T", parent=H1, fontSize=32, leading=38, alignment=TA_CENTER)))
super(Story, story).append(Paragraph("The Complete Practical Tutorial", ParagraphStyle(
    "ST", parent=BODY, fontSize=16, leading=20, alignment=TA_CENTER, textColor=GREY,
    spaceAfter=24)))
super(Story, story).append(Paragraph(
    "Installation, routing, the request lifecycle, validation &amp; serialization, plugins "
    "&amp; encapsulation, decorators, hooks, error handling, logging, the plugin ecosystem, "
    "TypeScript, testing, performance, deployment, 14 tested real-world examples and a "
    "complete production-style REST API.",
    ParagraphStyle("TD", parent=BODY, alignment=TA_CENTER, fontSize=11, leading=16)))
super(Story, story).append(Spacer(1, 30 * mm))
super(Story, story).append(Paragraph(
    "Verified with Fastify 5.12 &middot; Node.js 24 &middot; TypeScript 7",
    ParagraphStyle("TV", parent=BODY, alignment=TA_CENTER, textColor=GREY)))
super(Story, story).append(PageBreak())

toc = TableOfContents()
toc.levelStyles = [
    ParagraphStyle("TOC0", fontName="Helvetica-Bold", fontSize=11, leading=15,
                   textColor=ACCENT, spaceBefore=8),
    ParagraphStyle("TOC1", fontName="Helvetica", fontSize=9.5, leading=12.5, leftIndent=14),
]
super(Story, story).append(Paragraph("Contents", ParagraphStyle("TOCH", parent=H1)))
super(Story, story).append(toc)

# =========================================================================
part("Part I &mdash; Getting Started")
# =========================================================================
h1("1. Why Fastify?")
p("<b>Fastify</b> is a fast, low-overhead web framework for Node.js. It is built around "
  "three ideas that set it apart from Express:")
bullets([
    "<b>Schema-first</b>: routes declare JSON Schemas for input and output. Input is "
    "validated with Ajv; output is serialized with compiled " + c("fast-json-stringify") +
    " functions &mdash; both faster and safer than hand-written checks and "
    + c("JSON.stringify") + ".",
    "<b>Plugins with encapsulation</b>: everything (routes, hooks, decorators, DB "
    "connections) is a plugin. Each plugin gets its own isolated context, so features "
    "can't accidentally leak into each other.",
    "<b>A defined request lifecycle</b> with typed hooks at every stage, instead of an "
    "untyped middleware chain.",
])
table([
    ["Topic", "Express", "Fastify"],
    ["Async handlers", "Errors in async code need wrappers (v4)",
     "Native: return a value or throw"],
    ["Validation", "Bring your own (Joi, zod, express-validator)", "Built-in JSON Schema (Ajv)"],
    ["Serialization", c("JSON.stringify"), "Compiled per-route serializer (2-3x faster)"],
    ["Logging", "Bring your own", "Pino built-in, request-scoped " + c("request.log")],
    ["Structure", "Global middleware stack", "Encapsulated plugin tree"],
    ["TypeScript", "Community types", "First-class types, type providers"],
    ["Testing", "supertest", "Built-in " + c("app.inject()") + " (no network)"],
], [30 * mm, 65 * mm, 75 * mm])

h2("1.1 Real-world examples in this guide")
p("Every major topic is shown twice: first the concept, then a <b>real-world example</b> "
  "that runs and is covered by tests. All examples live in " + c("fastify-examples/")
  + " next to this PDF (54 tests, all passing).")
table([
    ["Scenario", "Topics", "Section"],
    ["E-commerce catalog", "Regex params, wildcards, versioning, prefixes, redirects", "5.5"],
    ["CSV exports, cacheable data", "Streams, headers, ETag/304, HEAD", "6.4"],
    ["Live order tracking", "Server-Sent Events, hijack, cleanup", "6.5"],
    ["User sign-up", "TypeBox validation, field errors, response whitelist, OpenAPI",
     "7.6"],
    ["Multi-tenant SaaS", "fp() vs encapsulation, request decorators", "9.1"],
    ["Production observability", "Hooks, request IDs, audit, redaction, maintenance",
     "10.4"],
    ["Bank transfers", "Domain errors, RFC 9457 problem details", "11.5"],
    ["Payment webhooks", "Raw-body parser, HMAC signatures, replay + dedupe", "12.1"],
    ["Inventory reservations", "Database plugin, transactions, SQL safety", "15.3"],
    ["Login and roles", "JWT, refresh rotation, RBAC, API keys", "16.4"],
    ["Hardening a public API", "Helmet, CORS, brute-force limits, body limits", "17.1"],
    ["Profile picture uploads", "Streaming multipart, magic bytes, limits", "19.4"],
    ["Support chat", "WebSockets, auth on upgrade, rooms", "19.5"],
    ["Zero-downtime deploys", "Graceful shutdown, readiness, keep-alive", "24.4"],
], [44 * mm, 106 * mm, 20 * mm])

h1("2. Core Architecture")
h2("2.1 The request lifecycle")
p("Every request flows through the same fixed stages. You attach behaviour with "
  "<b>hooks</b> rather than ordering middleware. Knowing this diagram is the key to "
  "understanding Fastify.")
story.append(lifecycle_diagram())
story.append(Spacer(1, 6))
steps([
    "<b>Routing</b> &mdash; find-my-way (radix tree) matches method + URL. No match "
    "&rarr; 404 handler.",
    "<b>onRequest</b> &mdash; body not parsed yet. Ideal for auth, rate checks, request IDs.",
    "<b>preParsing</b> &mdash; can transform the raw body stream (e.g. decompress).",
    "<b>Parsing</b> &mdash; content-type parser turns the body into " + c("request.body") + ".",
    "<b>preValidation</b> &rarr; <b>Validation</b> &mdash; body, querystring, params, "
    "headers checked against schemas. Failure &rarr; 400.",
    "<b>preHandler</b> &mdash; last stop before your code (authorization, loading entities).",
    "<b>Handler</b> &mdash; your route function returns data or calls " + c("reply.send()")
    + ".",
    "<b>preSerialization</b> &rarr; <b>Serialization</b> &mdash; object turned into JSON "
    "using the response schema for that status code.",
    "<b>onSend</b> &mdash; last chance to change the payload/headers.",
    "<b>onResponse</b> &mdash; after the response is sent. Metrics, cleanup.",
])
h2("2.2 Plugins and encapsulation")
p("A Fastify app is a <b>tree of plugins</b>. Each " + c("register()") + " call creates a "
  "child context that inherits from its parent but whose own hooks, decorators and routes "
  "are invisible to siblings and parents. Wrapping a plugin with "
  + c("fastify-plugin") + " (fp) opts out of encapsulation, so what it adds is shared "
  "with the parent &mdash; used for shared utilities like DB connections.")
story.append(encapsulation_diagram())
story.append(Spacer(1, 6))
p("Plugins are loaded <b>asynchronously and in order</b> by a boot loader (avvio). "
  "The server starts listening only after every plugin is ready.")

h1("3. Installation")
h2("3.1 Prerequisites")
bullets([
    "<b>Node.js 20 or newer</b> (Fastify v5 requirement). Check with " + c("node -v") + ".",
    "npm, pnpm or yarn.",
    "Optional: " + c("curl") + " or a REST client, Docker for deployment.",
])
h2("3.1a Tested with")
p("The complete Part V project, its tests and every behaviour described in this guide "
  "were run against these versions (September 2026). The runnable projects are "
  + c("fastify-tasks-api/") + " (Part V) and " + c("fastify-examples/")
  + " (14 real-world examples, 54 tests), next to this PDF.")
table([
    ["Component", "Version", "Notes"],
    ["Node.js", "24.15", "Fastify 5 needs 20+"],
    [c("fastify"), "5.12.5", ""],
    [c("@fastify/type-provider-typebox"), "6.1.0", "re-exports " + c("Type")
     + " from the " + c("typebox") + " 1.x package"],
    [c("@fastify/jwt") + " / " + c("@fastify/swagger") + " / " + c("@fastify/swagger-ui"),
     "10.2 / 9.9 / 6.1", ""],
    [c("@fastify/cors") + " / " + c("@fastify/helmet") + " / " + c("@fastify/rate-limit"),
     "11.3 / 13.1 / 11.2", ""],
    [c("@fastify/env") + " / " + c("@fastify/sensible"), "7.0 / 6.0", ""],
    [c("fastify-cli"), "8.0.2", ""],
    ["TypeScript / tsx", "7.0.2 / 4.23", "TS 7 = native compiler; run with tsx"],
], [62 * mm, 38 * mm, 70 * mm])
h2("3.2 Option A: scaffold with fastify-cli")
code("""
npx fastify-cli generate my-api --lang=ts     # omit --lang for JavaScript
cd my-api
npm install
npm run dev                                   # http://localhost:3000
""")
p("The generated project uses " + c("@fastify/autoload") + " with " + c("plugins/")
  + " and " + c("routes/") + " folders and a ready-to-run test setup.")
h2("3.3 Option B: manual setup (recommended to learn)")
code("""
mkdir fastify-demo && cd fastify-demo
npm init -y
npm install fastify fastify-plugin
npm install -D typescript tsx @types/node pino-pretty
npx tsc --init
""")
code("""
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "sourceMap": true,
    "rootDir": "./src",
    "outDir": "./dist"
  },
  "include": ["src/**/*.ts"]
}
""", "tsconfig.json")
code("""
"scripts": {
  "dev":   "tsx watch src/server.ts",
  "build": "tsc",
  "start": "node dist/server.js",
  "test":  "node --import tsx --test test/*.test.ts"
}
""", "package.json scripts")
warn("TypeScript 7 removed " + c('"moduleResolution": "node"') + " (use "
     + c('"nodenext"') + ") and has no JavaScript API, so " + c("ts-node") + "/"
     + c("ts-jest") + " no longer work. Use " + c("tsx") + " and " + c("node --test") + ".")
note(c("tsx") + " runs TypeScript directly with fast reloads. In production, compile with "
     + c("tsc") + " and run plain JavaScript.")
h2("3.4 JavaScript (CommonJS and ESM)")
code("""
// CommonJS - server.js
const fastify = require('fastify')({ logger: true });

// ES modules - server.mjs (or "type": "module" in package.json)
import Fastify from 'fastify';
const fastify = Fastify({ logger: true });
""")

h1("4. Your First Server")
code("""
// src/server.ts
import Fastify from 'fastify';

const app = Fastify({ logger: true });

app.get('/', async (request, reply) => {
  return { hello: 'world' };            // object -> JSON, status 200
});

const start = async () => {
  try {
    await app.listen({ port: 3000, host: '0.0.0.0' });
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
};
start();
""")
code("""
npm run dev
curl http://localhost:3000/
# {"hello":"world"}
# server log (JSON, pino):
# {"level":30,"reqId":"req-1","req":{"method":"GET","url":"/"},
#  "msg":"incoming request"}
""", "Run it")
h2("4.1 Important server options")
table([
    ["Option", "Default", "Purpose"],
    [c("logger"), "false", "true, or a pino config object (level, redact, transport)."],
    [c("bodyLimit"), "1 MiB", "Max request body size in bytes."],
    [c("trustProxy"), "false", "Trust X-Forwarded-* headers behind a load balancer."],
    [c("connectionTimeout"), "0", "Socket timeout in ms."],
    [c("requestTimeout"), "0", "Max time to receive the full request (set in prod)."],
    [c("genReqId"), "counter", "Custom request-ID generator (e.g. UUIDs)."],
    [c("requestIdHeader"), "false", "Reuse an incoming ID header, e.g. 'x-request-id'."],
    [c("ajv"), "&mdash;", "Customize the Ajv validator (see Chapter 7)."],
    [c("http2") + " / " + c("https"), "&mdash;", "Enable HTTP/2 or TLS directly."],
], [42 * mm, 22 * mm, 106 * mm])
h2("4.2 listen() details")
bullets([
    "Always pass an object: " + c("{ port, host }") + " (v5 removed positional args).",
    "Use " + c("host: '0.0.0.0'") + " in Docker/Kubernetes; the default " + c("localhost") +
    " is not reachable from outside the container.",
    c("port: 0") + " picks a random free port (handy in tests).",
    c("await app.ready()") + " loads all plugins without listening (used by tests).",
])

# =========================================================================
part("Part II &mdash; Core Concepts")
# =========================================================================
h1("5. Routing")
h2("5.1 Shorthand and full declarations")
code("""
app.get('/users', listUsers);
app.post('/users', createUser);
app.put('/users/:id', replaceUser);
app.patch('/users/:id', updateUser);
app.delete('/users/:id', deleteUser);
app.head('/ping', ping);
app.all('/any', anyMethod);                  // every method

// Full declaration - everything in one object
app.route({
  method: ['GET', 'HEAD'],
  url: '/articles/:slug',
  schema: { params: { type: 'object', properties: { slug: { type: 'string' } } } },
  preHandler: [loadArticle],                 // route-level hook
  handler: async (request) => request.article,
});
""")
h2("5.2 URL parameters, wildcards and query strings")
code("""
// Named params
app.get('/users/:userId/posts/:postId', async (req) => req.params);
// GET /users/7/posts/42 -> { "userId": "7", "postId": "42" }

// Regex-constrained param (only digits)
app.get('/orders/:id(^\\\\d+)', async (req) => ({ id: req.params.id }));

// Multiple params in one segment
app.get('/range/:from-:to', async (req) => req.params);    // /range/10-20

// Wildcard
app.get('/files/*', async (req) => ({ path: req.params['*'] }));

// Query string: GET /search?q=node&page=2
app.get('/search', async (req) => req.query);             // { q: 'node', page: '2' }
""")
note("Without a schema, params and query values are strings. With a schema, Fastify "
     "<b>coerces</b> them to the declared types (" + c("page") + " becomes the number 2).")
h2("5.3 Async handlers vs reply.send()")
code("""
// Preferred: async + return
app.get('/a', async () => ({ ok: true }));

// Set status/headers, then return
app.post('/b', async (request, reply) => {
  reply.code(201).header('Location', '/b/1');
  return { id: 1 };
});

// Callback style (no async) - must call reply.send exactly once
app.get('/c', (request, reply) => { reply.send({ ok: true }); });
""")
warn("In an " + c("async") + " handler, either <b>return</b> the value or call "
     + c("reply.send()") + " and <b>return reply</b>. Calling send() and also returning "
     "a different value logs a \"Reply already sent\" warning.")
h2("5.4 Route prefixes and constraints")
code("""
// Prefix all routes of a plugin
app.register(async (api) => {
  api.get('/status', async () => ({ ok: true }));           // GET /api/v1/status
}, { prefix: '/api/v1' });

// Version constraint (Accept-Version header, semver)
app.get('/items', { constraints: { version: '2.0.0' } }, async () => 'v2 items');
// curl -H "Accept-Version: 2.x" localhost:3000/items

// Host constraint
app.get('/', { constraints: { host: 'admin.example.com' } }, adminHome);
""")

fx_catalog("5.5")

h1("6. Request &amp; Reply")
h2("6.1 The request object")
table([
    ["Property", "Description"],
    [c("request.params") + ", " + c("query") + ", " + c("body") + ", " + c("headers"),
     "Parsed (and validated/coerced) input."],
    [c("request.id"), "Request ID (also in every log line)."],
    [c("request.log"), "Child logger bound to this request."],
    [c("request.ip") + " / " + c("ips") + " / " + c("hostname") + " / " + c("protocol"),
     "Client info (respects trustProxy)."],
    [c("request.method") + " / " + c("url"), "HTTP method and raw URL."],
    [c("request.routeOptions"), "Matched route info: url pattern, method, config, schema."],
    [c("request.raw"), "Underlying Node " + c("IncomingMessage") + "."],
    [c("request.server"), "The Fastify instance for this context."],
], [70 * mm, 100 * mm])
h2("6.2 The reply object")
code("""
app.get('/demo', async (request, reply) => {
  reply
    .code(200)                              // status
    .header('Cache-Control', 'no-store')    // single header
    .headers({ 'X-A': '1', 'X-B': '2' })    // several
    .type('application/json');              // content-type
  return { ok: true };
});

app.get('/old', async (req, reply) => reply.redirect('/new', 301));

app.get('/text', async (req, reply) => {
  reply.type('text/plain');
  return 'plain text';
});

// Streams and buffers are sent as-is
import { createReadStream } from 'node:fs';
app.get('/log', async (req, reply) => {
  reply.type('text/plain');
  return createReadStream('./app.log');
});

// reply.elapsedTime -> ms since request start; reply.sent -> already sent?
""")
h2("6.3 Taking over the response (hijack) - Server-Sent Events")
code("""
app.get('/events', (request, reply) => {
  reply.hijack();                           // Fastify will not touch the response
  reply.raw.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    Connection: 'keep-alive',
  });
  const timer = setInterval(() => {
    reply.raw.write(`data: ${JSON.stringify({ now: Date.now() })}\\n\\n`);
  }, 1000);
  request.raw.on('close', () => clearInterval(timer));
});
""")

fx_downloads("6.4")
fx_tracking("6.5")

h1("7. Validation &amp; Serialization")
p("Every route may have a " + c("schema") + " with " + c("body") + ", " + c("querystring")
  + ", " + c("params") + ", " + c("headers") + " and " + c("response") + " keys. Input "
  "schemas are compiled with <b>Ajv</b>; response schemas with <b>fast-json-stringify</b>. "
  "Both are compiled once at startup.")
h2("7.1 Validating input")
code("""
const createUserSchema = {
  body: {
    type: 'object',
    required: ['email', 'name'],
    additionalProperties: false,
    properties: {
      email: { type: 'string', format: 'email' },
      name:  { type: 'string', minLength: 2, maxLength: 80 },
      age:   { type: 'integer', minimum: 13 },
      role:  { type: 'string', enum: ['user', 'admin'], default: 'user' },
    },
  },
  querystring: {
    type: 'object',
    properties: { notify: { type: 'boolean', default: false } },
  },
  headers: {
    type: 'object',
    properties: { 'x-tenant-id': { type: 'string' } },
    required: ['x-tenant-id'],
  },
} as const;

app.post('/users', { schema: createUserSchema }, async (request, reply) => {
  reply.code(201);
  return { id: 1, ...request.body };   // body.role defaulted to 'user'
});
""")
code("""
curl -X POST localhost:3000/users -H "Content-Type: application/json" \\
     -H "x-tenant-id: t1" -d '{"email":"bad","name":"A"}'
# 400 {"statusCode":400,"code":"FST_ERR_VALIDATION","error":"Bad Request",
#      "message":"body/email must match format \\"email\\""}
""", "Invalid request -> automatic 400")
warn("Fastify v5 requires <b>full JSON Schemas</b> for querystring, params and headers "
     "(an object with " + c("type: 'object'") + " and " + c("properties") + "). The old "
     "shorthand " + c("{ q: { type: 'string' } }") + " is no longer accepted.")
h2("7.2 Default Ajv behaviour")
table([
    ["Ajv option", "Fastify default", "Effect"],
    [c("coerceTypes"), "'array'", "\"42\" &rarr; 42 for integer fields; single value &rarr; "
     "array when schema says array."],
    [c("useDefaults"), "true", "Missing properties get their " + c("default") + "."],
    [c("removeAdditional"), "true", "Extra props removed when "
     + c("additionalProperties: false") + " is set."],
    [c("allErrors"), "false", "Stop at the first error (safer against DoS)."],
], [35 * mm, 30 * mm, 105 * mm])
code("""
// Customize (e.g. add formats plugin, change behaviour)
const app = Fastify({
  ajv: {
    customOptions: { removeAdditional: 'all', allErrors: false },
    plugins: [require('ajv-formats')],     // Fastify already includes common formats
  },
});
""")
h2("7.3 Response schemas: speed and safety")
code("""
app.get('/users/:id', {
  schema: {
    params: { type: 'object', properties: { id: { type: 'integer' } } },
    response: {
      200: {
        type: 'object',
        properties: { id: { type: 'integer' }, email: { type: 'string' },
                      name: { type: 'string' } },
      },
      404: { $ref: 'errorResponse#' },
    },
  },
}, async (request) => {
  const user = await db.users.find(request.params.id);
  // user contains passwordHash - but it is NOT in the schema, so it is NOT sent
  return user;
});
""")
note("A response schema is also a security feature: fields not listed (password hashes, "
     "internal flags) are silently dropped from the output.")
h2("7.4 Shared schemas with $ref")
code("""
app.addSchema({
  $id: 'errorResponse',
  type: 'object',
  properties: {
    statusCode: { type: 'integer' }, error: { type: 'string' },
    message: { type: 'string' },
  },
});
app.addSchema({
  $id: 'user',
  type: 'object',
  properties: { id: { type: 'integer' }, name: { type: 'string' } },
});

app.get('/users', {
  schema: { response: { 200: { type: 'array', items: { $ref: 'user#' } } } },
}, listUsers);
""")
h2("7.5 Type providers: one schema, full TypeScript types")
code("""
npm install @fastify/type-provider-typebox
""")
code("""
import Fastify from 'fastify';
import { TypeBoxTypeProvider, Type } from '@fastify/type-provider-typebox';

const app = Fastify().withTypeProvider<TypeBoxTypeProvider>();

const Product = Type.Object({
  id: Type.Integer(),
  name: Type.String({ minLength: 1 }),
  price: Type.Number({ minimum: 0 }),
  tags: Type.Array(Type.String(), { default: [] }),
});

app.post('/products', {
  schema: {
    body: Type.Omit(Product, ['id']),
    response: { 201: Product },
  },
}, async (request, reply) => {
  // request.body is typed: { name: string; price: number; tags: string[] }
  const product = { id: 1, ...request.body };
  reply.code(201);
  return product;                       // checked against Product at compile time
});
""")
p("Alternatives: " + c("@fastify/type-provider-json-schema-to-ts") + " (plain JSON Schema "
  "objects with " + c("as const") + ") or community Zod providers "
  "(" + c("fastify-type-provider-zod") + ").")

fx_signup("7.6")

h1("8. Plugins &amp; Encapsulation")
h2("8.1 Writing and registering a plugin")
code("""
// src/routes/users.ts
import type { FastifyPluginAsync } from 'fastify';

interface UsersOptions { maxPageSize: number }

const usersRoutes: FastifyPluginAsync<UsersOptions> = async (app, opts) => {
  app.get('/', async () => ({ pageSize: opts.maxPageSize, users: [] }));
  app.get('/:id', async (req) => ({ id: (req.params as { id: string }).id }));
};
export default usersRoutes;

// src/app.ts
app.register(usersRoutes, { prefix: '/users', maxPageSize: 50 });
""")
h2("8.2 Encapsulation in action")
code("""
app.register(async function adminContext(admin) {
  admin.addHook('onRequest', requireAdmin);     // only for routes in this context
  admin.decorate('auditLog', writeAudit);       // only visible here (and children)
  admin.get('/admin/stats', async () => stats());
});

app.register(async function publicContext(pub) {
  pub.get('/public/info', async () => info());  // requireAdmin does NOT run here
  // pub.auditLog -> undefined
});
""")
h2("8.3 Sharing with fastify-plugin")
code("""
// src/plugins/db.ts
import fp from 'fastify-plugin';
import { Pool } from 'pg';

declare module 'fastify' {
  interface FastifyInstance { db: Pool }
}

export default fp(async (app, opts: { connectionString: string }) => {
  const pool = new Pool({ connectionString: opts.connectionString });
  await pool.query('SELECT 1');                // fail fast at boot
  app.decorate('db', pool);
  app.addHook('onClose', async () => { await pool.end(); });
}, { name: 'db' });

// app.ts
await app.register(dbPlugin, { connectionString: process.env.DATABASE_URL! });
// app.db is now available everywhere (root and all children)
""")
table([
    ["Plugin type", "Use for", "Wrap with fp?"],
    ["Utility / connection", "DB pools, config, auth decorators, shared hooks", "Yes"],
    ["Feature / routes", "Route groups with their own hooks and prefix", "No"],
], [40 * mm, 100 * mm, 30 * mm])
h2("8.4 Loading order and readiness")
code("""
app.register(pluginA);
app.register(pluginB);            // starts after A has fully loaded
app.after(() => {
  // A and B are loaded here
});
await app.ready();                // everything loaded (listen() calls this for you)

// fp metadata can enforce dependencies and Fastify version
export default fp(plugin, {
  name: 'auth', fastify: '5.x', dependencies: ['db', '@fastify/jwt'],
});
""")

h1("9. Decorators")
p("Decorators add properties or methods to the instance, request or reply. They are the "
  "Fastify way to share things (instead of attaching to " + c("req") + " ad hoc), and they "
  "keep object shapes stable for V8 performance.")
code("""
// Instance
app.decorate('config', { featureX: true });
app.decorate('sum', (a: number, b: number) => a + b);

// Request - initialize with null (or a getter), then set in a hook
app.decorateRequest('user', null);
app.addHook('preHandler', async (request) => {
  request.user = await loadUser(request.headers.authorization);
});

// Request with per-request object: use a getter (objects are not allowed directly)
app.decorateRequest('ctx', { getter() { return { startedAt: Date.now() }; } });

// Reply
app.decorateReply('ok', function (data: unknown) {
  return this.code(200).send({ success: true, data });
});

app.hasDecorator('config');       // true
""")
code("""
declare module 'fastify' {
  interface FastifyInstance {
    config: { featureX: boolean };
    sum(a: number, b: number): number;
  }
  interface FastifyRequest { user: { id: string; role: string } | null }
  interface FastifyReply { ok(data: unknown): FastifyReply }
}
""", "TypeScript: declaration merging for decorators")
warn("Decorating the request/reply with a <b>shared object or array</b> means every "
     "request shares the same reference. Fastify v5 throws for this; initialize with "
     + c("null") + " or use a getter.")

fx_tenant("9.1")

h1("10. Hooks")
h2("10.1 Request/reply hooks")
table([
    ["Hook", "Signature (async)", "Typical use"],
    [c("onRequest"), c("(req, reply)"), "Authentication, request timing."],
    [c("preParsing"), c("(req, reply, payload)"), "Transform raw body stream."],
    [c("preValidation"), c("(req, reply)"), "Normalize input before schema check."],
    [c("preHandler"), c("(req, reply)"), "Authorization, load resources."],
    [c("preSerialization"), c("(req, reply, payload)"), "Wrap/transform the returned object."],
    [c("onSend"), c("(req, reply, payload)"), "Change serialized payload/headers."],
    [c("onResponse"), c("(req, reply)"), "Metrics, logging (response already sent)."],
    [c("onError"), c("(req, reply, error)"), "Observe errors (cannot change response)."],
    [c("onTimeout"), c("(req, reply)"), "Socket timed out."],
    [c("onRequestAbort"), c("(req)"), "Client closed the connection early."],
], [34 * mm, 50 * mm, 86 * mm])
code("""
// Global timing header
app.addHook('onRequest', async (request) => {
  request.log.debug({ url: request.url }, 'start');
});
app.addHook('onSend', async (request, reply, payload) => {
  reply.header('X-Response-Time', `${reply.elapsedTime.toFixed(1)}ms`);
  return payload;                          // must return (possibly modified) payload
});

// Envelope every JSON response
app.addHook('preSerialization', async (request, reply, payload) => {
  return { data: payload, requestId: request.id };
});

// Short-circuit: respond early from a hook
app.addHook('onRequest', async (request, reply) => {
  if (maintenanceMode) {
    return reply.code(503).send({ message: 'Maintenance' });   // stops the chain
  }
});
""")
h2("10.2 Route-level hooks")
code("""
app.get('/admin', {
  onRequest: [app.authenticate],             // array or single function
  preHandler: async (request) => {
    if (request.user?.role !== 'admin') throw app.httpErrors.forbidden();
  },
}, async () => ({ secret: 42 }));
""")
h2("10.3 Application hooks")
table([
    ["Hook", "Runs when"],
    [c("onRoute"), "A route is registered (inspect/modify route options)."],
    [c("onRegister"), "A new encapsulated context is created."],
    [c("onReady"), "All plugins loaded, before listening. Warm caches."],
    [c("onListen"), "Server is listening."],
    [c("preClose") + " / " + c("onClose"), "During " + c("app.close()") +
     " &mdash; close DB pools, flush queues."],
], [45 * mm, 125 * mm])
code("""
app.addHook('onRoute', (route) => {
  app.log.info(`${route.method} ${route.url}`);   // print route table at boot
});
app.addHook('onReady', async () => { await warmCache(); });
app.addHook('onClose', async (instance) => { await instance.db.end(); });
""")
note("Hooks follow encapsulation: a hook added inside a plugin runs only for routes in "
     "that plugin and its children. Use " + c("app.printRoutes()") + " and "
     + c("app.printPlugins()") + " to debug the tree.")

fx_observability("10.4")

h1("11. Error Handling")
h2("11.1 Throwing errors")
code("""
app.get('/items/:id', async (request) => {
  const item = await repo.find(request.params.id);
  if (!item) {
    const err = new Error('Item not found') as Error & { statusCode: number };
    err.statusCode = 404;
    throw err;                              // -> 404 JSON response
  }
  return item;
});
""")
h2("11.2 @fastify/sensible - HTTP error helpers")
code("""
npm install @fastify/sensible
""")
code("""
import sensible from '@fastify/sensible';
await app.register(sensible);

app.get('/items/:id', async (request, reply) => {
  const item = await repo.find(request.params.id);
  if (!item) throw app.httpErrors.notFound('Item not found');   // or reply.notFound()
  return item;
});
// also: badRequest, unauthorized, forbidden, conflict, tooManyRequests, ...
// plus app.assert(cond, 400, 'msg'), request.forwarded(), reply.vary(), app.to(promise)
""")
h2("11.3 Custom error classes with @fastify/error")
code("""
import createError from '@fastify/error';

export const InsufficientFunds = createError(
  'APP_INSUFFICIENT_FUNDS', 'Account %s has insufficient funds', 422);

throw new InsufficientFunds(accountId);
// 422 {"statusCode":422,"code":"APP_INSUFFICIENT_FUNDS","error":"Unprocessable Entity",
//      "message":"Account acc-1 has insufficient funds"}
""")
h2("11.4 Central error handler and 404 handler")
code("""
import { STATUS_CODES } from 'node:http';

app.setErrorHandler((error, request, reply) => {
  if (error.validation) {                            // schema validation failure
    return reply.code(400).send({
      statusCode: 400, error: 'Bad Request', message: error.message,
      details: error.validation,
    });
  }
  const status = error.statusCode ?? 500;
  if (status >= 500) request.log.error({ err: error }, 'unhandled error');
  reply.code(status).send({
    statusCode: status,
    error: STATUS_CODES[status] ?? 'Error',        // 'Not Found', 'Unauthorized', ...
    message: status >= 500 ? 'Something went wrong' : error.message, // hide internals
  });
});

app.setNotFoundHandler((request, reply) => {
  reply.code(404).send({ statusCode: 404, error: 'Not Found',
                         message: `Route ${request.method} ${request.url} not found` });
});
""")
p("Error and not-found handlers are also encapsulated: a plugin can set its own "
  "(e.g. an HTML error page for " + c("/web") + " and JSON for " + c("/api") + ").")

fx_problems("11.5")

h1("12. Content-Type Parsers")
p("Fastify parses " + c("application/json") + " and " + c("text/plain") + " out of the "
  "box. Anything else returns <b>415 Unsupported Media Type</b> until you add a parser.")
code("""
// URL-encoded forms
import formbody from '@fastify/formbody';
await app.register(formbody);

// Custom parser: YAML
import yaml from 'yaml';
app.addContentTypeParser('application/yaml', { parseAs: 'string' },
  (request, body, done) => {
    try { done(null, yaml.parse(body as string)); }
    catch (err) { done(err as Error, undefined); }
  });

// Raw buffer for webhook signature checks (e.g. Stripe)
app.register(async (hooks) => {
  hooks.addContentTypeParser('application/json', { parseAs: 'buffer' },
    (req, body, done) => done(null, body));
  hooks.post('/webhooks/stripe', async (req) => verifySignature(req.body as Buffer));
});
""")

fx_webhooks("12.1")

h1("13. Logging with Pino")
code("""
const app = Fastify({
  logger: {
    level: process.env.LOG_LEVEL ?? 'info',
    redact: ['req.headers.authorization', 'req.headers.cookie'],
    transport: process.env.NODE_ENV === 'production'
      ? undefined                                    // raw JSON in prod
      : { target: 'pino-pretty', options: { translateTime: 'HH:MM:ss' } },
  },
  genReqId: () => crypto.randomUUID(),
  requestIdHeader: 'x-request-id',                   // reuse incoming ID if present
  disableRequestLogging: false,
});

app.get('/orders/:id', async (request) => {
  request.log.info({ orderId: request.params }, 'fetching order');  // includes reqId
  return {};
});
""")
bullets([
    "Levels: " + c("fatal, error, warn, info, debug, trace") + ".",
    "Use " + c("request.log") + " inside handlers so every line carries the request ID.",
    "To pass your own pino instance use " + c("loggerInstance: pino(...)") +
    " (v5 change).",
    "Pino logs are JSON &mdash; ship them to ELK, Loki, Datadog, CloudWatch as-is.",
])
note("See the observability example in 10.4 for redaction, request-ID propagation and "
     "capturing logs in tests.")

# =========================================================================
part("Part III &mdash; The Plugin Ecosystem")
# =========================================================================
h1("14. Configuration with @fastify/env")
code("""
npm install @fastify/env
""")
code("""
import fp from 'fastify-plugin';
import fastifyEnv from '@fastify/env';

const schema = {
  type: 'object',
  required: ['DATABASE_URL', 'JWT_SECRET'],
  properties: {
    PORT: { type: 'number', default: 3000 },
    HOST: { type: 'string', default: '0.0.0.0' },
    DATABASE_URL: { type: 'string' },
    JWT_SECRET: { type: 'string', minLength: 32 },
  },
};

declare module 'fastify' {
  interface FastifyInstance {
    config: { PORT: number; HOST: string; DATABASE_URL: string; JWT_SECRET: string };
  }
}

export default fp(async (app) => {
  await app.register(fastifyEnv, { schema, dotenv: true });   // reads .env too
}, { name: 'env' });
// Boot fails with a clear error if a required variable is missing or invalid.
""")

h1("15. Databases")
h2("15.1 PostgreSQL with @fastify/postgres")
code("""
import postgres from '@fastify/postgres';
await app.register(postgres, { connectionString: app.config.DATABASE_URL });

app.get('/users/:id', async (request) => {
  const { rows } = await app.pg.query(
    'SELECT id, email, name FROM users WHERE id = $1', [request.params.id]);
  if (!rows[0]) throw app.httpErrors.notFound();
  return rows[0];
});

// Transactions
app.post('/transfer', async (request) => {
  return app.pg.transact(async (client) => {
    await client.query('UPDATE accounts SET bal = bal - $1 WHERE id = $2', [amt, from]);
    await client.query('UPDATE accounts SET bal = bal + $1 WHERE id = $2', [amt, to]);
    return { ok: true };
  });
});
""")
h2("15.2 Any ORM (Prisma, Drizzle, Knex, Mongoose) via a plugin")
code("""
import fp from 'fastify-plugin';
import { PrismaClient } from '@prisma/client';

declare module 'fastify' { interface FastifyInstance { prisma: PrismaClient } }

export default fp(async (app) => {
  const prisma = new PrismaClient();
  await prisma.$connect();
  app.decorate('prisma', prisma);
  app.addHook('onClose', async () => { await prisma.$disconnect(); });
}, { name: 'prisma' });

// usage: const user = await app.prisma.user.findUnique({ where: { id } });
""")
p("Other official plugins: " + c("@fastify/mongodb") + ", " + c("@fastify/mysql") + ", "
  + c("@fastify/redis") + ", " + c("@fastify/elasticsearch") + ".")

fx_inventory("15.3")

h1("16. Authentication")
h2("16.1 JWT with @fastify/jwt")
code("""
npm install @fastify/jwt
""")
code("""
import jwt from '@fastify/jwt';
import type { FastifyRequest } from 'fastify';

declare module '@fastify/jwt' {
  interface FastifyJWT {
    payload: { sub: string; role: 'user' | 'admin' };   // what you sign
    user: { sub: string; role: 'user' | 'admin' };      // request.user after verify
  }
}
declare module 'fastify' {
  interface FastifyInstance { authenticate(req: FastifyRequest): Promise<void> }
}

await app.register(jwt, { secret: app.config.JWT_SECRET, sign: { expiresIn: '15m' } });

app.decorate('authenticate', async (request: FastifyRequest) => {
  try { await request.jwtVerify(); }
  catch { throw app.httpErrors.unauthorized('Invalid or expired token'); }
});

app.post('/login', async (request) => {
  const user = await checkCredentials(request.body);
  return { token: app.jwt.sign({ sub: user.id, role: user.role }) };
});

app.get('/me', { onRequest: [app.authenticate] }, async (request) => request.user);
""")
h2("16.2 Combining strategies with @fastify/auth")
code("""
import fastifyAuth from '@fastify/auth';
await app.register(fastifyAuth);

app.get('/reports', {
  preHandler: app.auth([app.verifyJwt, app.verifyApiKey]),   // either passes
  // app.auth([a, b], { relation: 'and' })                   // both must pass
}, getReports);
""")
h2("16.3 Cookies and sessions")
code("""
import cookie from '@fastify/cookie';
import session from '@fastify/session';

await app.register(cookie);
await app.register(session, {
  secret: app.config.SESSION_SECRET,         // >= 32 chars
  cookie: { secure: true, httpOnly: true, sameSite: 'lax', maxAge: 86_400_000 },
});

app.post('/login', async (request) => {
  request.session.userId = user.id;          // stored server-side
  return { ok: true };
});
// Default store is in-memory: use a Redis/DB store in production.
""")

fx_auth("16.4")

h1("17. Security Plugins")
code("""
npm install @fastify/helmet @fastify/cors @fastify/rate-limit
""")
code("""
import helmet from '@fastify/helmet';
import cors from '@fastify/cors';
import rateLimit from '@fastify/rate-limit';

await app.register(helmet);                              // secure HTTP headers
await app.register(cors, {
  origin: ['https://app.example.com'],                   // never '*' with credentials
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
});
await app.register(rateLimit, {
  max: 100,                                              // per IP per window
  timeWindow: '1 minute',
  // redis: new Redis(),                                 // share limits across instances
});

// Stricter limit for one route
app.post('/login', { config: { rateLimit: { max: 5, timeWindow: '1 minute' } } }, login);
""")
h2("Security checklist")
bullets([
    "Validate every input with schemas; use " + c("additionalProperties: false") + ".",
    "Always define response schemas to avoid leaking fields.",
    "Keep " + c("bodyLimit") + " small; raise it only on upload routes.",
    "Set " + c("trustProxy") + " correctly so " + c("request.ip") + " and rate limits "
    "use the real client IP.",
    "Hide 5xx error details from clients (Chapter 11.4); redact secrets in logs.",
    "Keep secrets in environment variables, validated by " + c("@fastify/env") + ".",
])

fx_security("17.1")

h1("18. OpenAPI / Swagger Docs")
code("""
npm install @fastify/swagger @fastify/swagger-ui
""")
code("""
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';

// Register BEFORE your routes so they are picked up
await app.register(swagger, {
  openapi: {
    info: { title: 'Tasks API', version: '1.0.0' },
    components: {
      securitySchemes: { bearerAuth: { type: 'http', scheme: 'bearer' } },
    },
  },
});
await app.register(swaggerUi, { routePrefix: '/docs' });

app.get('/tasks', {
  schema: {
    tags: ['tasks'],
    summary: 'List tasks',
    security: [{ bearerAuth: [] }],
    response: { 200: { type: 'array', items: { $ref: 'task#' } } },
  },
}, listTasks);
// Browse http://localhost:3000/docs  - JSON at /docs/json
""")
p("Your validation schemas <i>are</i> your API documentation &mdash; they can never drift "
  "apart.")

h1("19. Static Files, Uploads &amp; WebSockets")
h2("19.1 Static files")
code("""
import fastifyStatic from '@fastify/static';
import path from 'node:path';

await app.register(fastifyStatic, {
  root: path.join(__dirname, '..', 'public'),
  prefix: '/public/',                         // /public/logo.png
});
app.get('/', async (req, reply) => reply.sendFile('index.html'));
""")
h2("19.2 File uploads with @fastify/multipart")
code("""
import multipart from '@fastify/multipart';
import { createWriteStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';

await app.register(multipart, { limits: { fileSize: 10 * 1024 * 1024, files: 1 } });

app.post('/avatar', async (request, reply) => {
  const data = await request.file();          // streaming - no full buffering
  if (!data) throw app.httpErrors.badRequest('file required');
  if (!['image/png', 'image/jpeg'].includes(data.mimetype)) {
    throw app.httpErrors.unsupportedMediaType();
  }
  await pipeline(data.file, createWriteStream(`./uploads/${crypto.randomUUID()}`));
  if (data.file.truncated) throw app.httpErrors.payloadTooLarge();
  reply.code(201);
  return { filename: data.filename };
});
// curl -F "file=@me.png" localhost:3000/avatar
""")
h2("19.3 WebSockets")
code("""
import websocket from '@fastify/websocket';
await app.register(websocket);

const clients = new Set<import('ws').WebSocket>();

app.get('/chat', { websocket: true }, (socket, request) => {
  clients.add(socket);
  socket.on('message', (msg) => {
    for (const c of clients) c.send(`${request.id}: ${msg}`);   // broadcast
  });
  socket.on('close', () => clients.delete(socket));
});
// Normal hooks (onRequest auth, etc.) run on the upgrade request.
""")

# =========================================================================
fx_uploads("19.4")
fx_chat("19.5")

part("Part IV &mdash; TypeScript, Testing &amp; Production")
# =========================================================================
h1("20. TypeScript in Depth")
h2("20.1 Route generics (no type provider)")
code("""
interface GetUser {
  Params: { id: string };
  Querystring: { expand?: 'posts' | 'comments' };
  Headers: { 'x-tenant-id': string };
  Reply: { 200: { id: string; name: string }; 404: { message: string } };
}

app.get<GetUser>('/users/:id', async (request, reply) => {
  request.params.id;                 // string
  request.query.expand;              // 'posts' | 'comments' | undefined
  if (!found) return reply.code(404).send({ message: 'nope' });
  return { id: request.params.id, name: 'Ann' };
});
""")
p("Generics give types but <b>no runtime validation</b> &mdash; you still need a schema. "
  "Type providers (Chapter 7.5) give both from a single definition, so prefer them.")
h2("20.2 Typed plugins")
code("""
import type { FastifyPluginAsync } from 'fastify';
import type { FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox';

// Plain plugin with typed options
const plugin: FastifyPluginAsync<{ prefixMsg: string }> = async (app, opts) => { };

// Plugin whose routes get TypeBox inference automatically
const routes: FastifyPluginAsyncTypebox = async (app) => {
  app.get('/x', { schema: { querystring: Type.Object({ n: Type.Integer() }) } },
    async (req) => req.query.n * 2);      // req.query.n is number
};
""")
h2("20.3 Useful types")
table([
    ["Type", "Use"],
    [c("FastifyInstance"), "The app / plugin instance (augment for decorators)."],
    [c("FastifyRequest") + ", " + c("FastifyReply"), "Handler/hook parameters (augment for "
     "request/reply decorators)."],
    [c("FastifyPluginAsync&lt;Opts&gt;"), "Async plugin with typed options."],
    [c("FastifyServerOptions"), "Options passed to " + c("Fastify()") + " (for "
     + c("buildApp(opts)") + ")."],
    [c("RouteShorthandOptions"), "Options object of " + c("app.get(url, opts, handler)") + "."],
    [c("FastifyError"), "Error type in error handlers (has statusCode, code, validation)."],
], [60 * mm, 110 * mm])

h1("21. Testing")
h2("21.1 Separate app construction from listening")
code("""
// src/app.ts - builds the app, never listens
export async function buildApp(opts: FastifyServerOptions = {}) {
  const app = Fastify(opts);
  await app.register(/* plugins, routes */);
  return app;
}

// src/server.ts - production entry point
const app = await buildApp({ logger: true });
await app.listen({ port: 3000, host: '0.0.0.0' });
""")
h2("21.2 inject(): HTTP tests without a network")
code("""
// test/users.test.ts  - run with: node --import tsx --test test/*.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildApp } from '../src/app';

test('GET /users/:id returns the user', async (t) => {
  const app = await buildApp();
  t.after(() => app.close());

  const res = await app.inject({ method: 'GET', url: '/users/1' });

  assert.equal(res.statusCode, 200);
  assert.deepEqual(res.json(), { id: 1, name: 'Ann' });
  assert.match(res.headers['content-type'] as string, /application\\/json/);
});

test('POST /users validates body', async (t) => {
  const app = await buildApp();
  t.after(() => app.close());

  const res = await app.inject({
    method: 'POST', url: '/users',
    headers: { 'x-tenant-id': 't1' },
    payload: { email: 'not-an-email', name: 'A' },
  });
  assert.equal(res.statusCode, 400);
});
""")
h2("21.3 Testing plugins and mocking dependencies")
code("""
test('uses a fake repository', async (t) => {
  const app = Fastify();
  app.decorate('repo', { find: async () => ({ id: 1, name: 'Fake' }) });  // mock
  await app.register(usersRoutes, { prefix: '/users' });
  t.after(() => app.close());

  const res = await app.inject('/users/1');
  assert.equal(res.json().name, 'Fake');
});

// Chainable API
const res = await app.inject().get('/users').headers({ authorization: 'Bearer x' }).end();
""")
note("Tests run in milliseconds because " + c("inject()") + " calls the router directly "
     "(via light-my-request) &mdash; no ports, no sockets. Jest, Vitest and tap work the "
     "same way.")

fx_testing("21.4")

h1("22. Project Structure &amp; Autoload")
code("""
src/
  app.ts              # buildApp(): registers plugins then routes
  server.ts           # listen + graceful shutdown
  plugins/            # fp-wrapped, shared (env, db, auth, sensible, swagger)
    env.ts
    db.ts
    auth.ts
  routes/             # encapsulated feature plugins; folder name = URL prefix
    health/index.ts   # -> /health
    users/index.ts    # -> /users
    users/_id/posts.ts
  schemas/            # TypeBox / JSON schemas
  services/           # business logic, independent of Fastify
test/
""")
code("""
import AutoLoad from '@fastify/autoload';
import path from 'node:path';

export async function buildApp(opts = {}) {
  const app = Fastify(opts);
  await app.register(AutoLoad, { dir: path.join(__dirname, 'plugins') });
  await app.register(AutoLoad, {
    dir: path.join(__dirname, 'routes'),
    options: { prefix: '/api' },       // /api/users, /api/health ...
  });
  return app;
}
""", "@fastify/autoload registers every file in a folder")
p("Autoload keeps " + c("app.ts") + " tiny as the app grows. Explicit " + c("register()")
  + " calls (as in the Part V project) are easier to follow for small apps.")

h1("23. Performance")
bullets([
    "<b>Define response schemas</b> &mdash; the biggest single win (fast-json-stringify).",
    "Keep handlers " + c("async") + " and never block the event loop (no sync crypto/fs, "
    "no giant JSON parsing in handlers).",
    "Log at " + c("info") + " or higher in production; avoid pino-pretty in production.",
    "Reuse connections (DB pools, HTTP agents with keep-alive, " + c("undici") + ").",
    "Cache with " + c("@fastify/caching") + " / Redis; compress with "
    + c("@fastify/compress") + " (or at the proxy).",
    "Scale by running several processes/containers behind a load balancer.",
    "Protect under load with " + c("@fastify/under-pressure") + " (returns 503 when the event "
    "loop is saturated).",
])
code("""
npx autocannon -c 100 -d 10 http://localhost:3000/     # benchmark
npx clinic doctor -- node dist/server.js               # diagnose bottlenecks
""")
code("""
import underPressure from '@fastify/under-pressure';
await app.register(underPressure, {
  maxEventLoopDelay: 1000,
  maxHeapUsedBytes: 1_000_000_000,
  exposeStatusRoute: '/health/live',
});
""")

h1("24. Deployment")
h2("24.1 Graceful shutdown")
code("""
npm install close-with-grace
""")
code("""
import closeWithGrace from 'close-with-grace';

const app = await buildApp({ logger: true });

closeWithGrace({ delay: 10_000 }, async ({ signal, err }) => {
  if (err) app.log.error({ err }, 'closing because of error');
  else app.log.info({ signal }, 'shutting down');
  await app.close();       // stops accepting, finishes in-flight, runs onClose hooks
});

await app.listen({ port: app.config.PORT, host: '0.0.0.0' });
""")
h2("24.2 Dockerfile")
code("""
FROM node:22-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build && npm prune --omit=dev

FROM node:22-slim
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY package.json ./
USER node
EXPOSE 3000
CMD ["node", "dist/server.js"]
""")
h2("24.3 Production checklist")
table([
    ["Item", "How"],
    ["Listen on all interfaces", c("host: '0.0.0.0'")],
    ["Behind a proxy / LB", c("trustProxy: true") + " (or the proxy's IP list)"],
    ["Health checks", c("/health") + " route + under-pressure for liveness/readiness"],
    ["Timeouts", c("requestTimeout") + ", " + c("connectionTimeout") + ", keep-alive "
     "shorter than the LB's"],
    ["Logs", "JSON to stdout, redact secrets, ship to your log platform"],
    ["Config", c("@fastify/env") + " with a strict schema; secrets from the environment"],
    ["Shutdown", "close-with-grace; " + c("onClose") + " hooks close resources"],
    ["Security", "helmet, cors, rate-limit, response schemas, small bodyLimit"],
], [50 * mm, 120 * mm])

# =========================================================================
fx_shutdown("24.4")

part("Part V &mdash; End-to-End Project: Tasks API")
ANNOTATE.update(callouts.FASTIFY)
# =========================================================================
h1("25. Building a Production-Style REST API")
p("A complete, runnable service combining the concepts: TypeBox schemas with full type "
  "inference, environment validation, JWT authentication, per-user authorization, "
  "security plugins, Swagger docs, a central error handler, graceful shutdown and tests. "
  "Storage is an in-memory repository plugin that you can later swap for a database "
  "plugin without touching routes.")
table([
    ["Method &amp; URL", "Auth", "Description"],
    [c("GET /health"), "&mdash;", "Liveness check"],
    [c("POST /auth/login"), "&mdash;", "Returns a JWT (rate limited: 5/min)"],
    [c("GET /tasks?done=&amp;limit=&amp;offset="), "JWT", "List own tasks with filters"],
    [c("POST /tasks"), "JWT", "Create a task"],
    [c("GET /tasks/:id"), "JWT", "Get one task (404 if not owner)"],
    [c("PATCH /tasks/:id"), "JWT", "Update title/done"],
    [c("DELETE /tasks/:id"), "JWT", "Delete (204)"],
    [c("GET /docs"), "&mdash;", "Swagger UI"],
], [62 * mm, 18 * mm, 90 * mm])
h2("25.1 Install")
code("""
mkdir tasks-api && cd tasks-api && npm init -y
npm install fastify fastify-plugin @fastify/sensible @fastify/env @fastify/jwt \\
            @fastify/helmet @fastify/cors @fastify/rate-limit @fastify/swagger \\
            @fastify/swagger-ui @fastify/type-provider-typebox close-with-grace
npm install -D typescript tsx @types/node pino-pretty
""")
code("""
PORT=3000
HOST=0.0.0.0
LOG_LEVEL=info
JWT_SECRET=replace-with-a-long-random-string-at-least-32-chars
""", ".env  (add to .gitignore)")
code("""
tasks-api/
  src/
    app.ts  server.ts
    schemas/task.ts
    plugins/env.ts  security.ts  swagger.ts  store.ts  auth.ts
    routes/health.ts  auth.ts  tasks.ts
  test/tasks.test.ts
  .env  package.json  tsconfig.json
""", "Layout (tsconfig.json and scripts as in Chapter 3.3)")
code("""
// src/schemas/task.ts
import { Type, Static } from '@fastify/type-provider-typebox';

export const Task = Type.Object({
  id: Type.String(),
  title: Type.String(),
  done: Type.Boolean(),
  ownerId: Type.String(),
  createdAt: Type.String({ format: 'date-time' }),
});
export type Task = Static<typeof Task>;

const Title = Type.String({ minLength: 1, maxLength: 200 });

export const CreateTask = Type.Object({ title: Title }, { additionalProperties: false });
export const UpdateTask = Type.Object(
  { title: Type.Optional(Title), done: Type.Optional(Type.Boolean()) },
  { additionalProperties: false, minProperties: 1 },
);
export const TaskParams = Type.Object({ id: Type.String() });
export const ListQuery = Type.Object({
  done: Type.Optional(Type.Boolean()),
  limit: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),
  offset: Type.Integer({ minimum: 0, default: 0 }),
});
export type ListQuery = Static<typeof ListQuery>;

export const ErrorReply = Type.Object({
  statusCode: Type.Integer(), error: Type.String(), message: Type.String(),
});
""", "25.2 Schemas (single source of truth for validation, types and docs)")
code("""
// src/plugins/env.ts
import fp from 'fastify-plugin';
import fastifyEnv from '@fastify/env';

const schema = {
  type: 'object',
  required: ['JWT_SECRET'],
  properties: {
    PORT: { type: 'number', default: 3000 },
    HOST: { type: 'string', default: '0.0.0.0' },
    JWT_SECRET: { type: 'string', minLength: 32 },
  },
};

declare module 'fastify' {
  interface FastifyInstance {
    config: { PORT: number; HOST: string; JWT_SECRET: string };
  }
}

export default fp(async (app) => {
  await app.register(fastifyEnv, { schema, dotenv: true });
}, { name: 'env' });
""", "25.3 Plugins - environment")
code("""
// src/plugins/security.ts
import fp from 'fastify-plugin';
import helmet from '@fastify/helmet';
import cors from '@fastify/cors';
import rateLimit from '@fastify/rate-limit';

export default fp(async (app) => {
  await app.register(helmet, { contentSecurityPolicy: false });  // CSP off for /docs
  await app.register(cors, { origin: true });                    // tighten in prod
  await app.register(rateLimit, { max: 100, timeWindow: '1 minute' });
}, { name: 'security' });

// src/plugins/swagger.ts
import fp from 'fastify-plugin';
import swagger from '@fastify/swagger';
import swaggerUi from '@fastify/swagger-ui';

export default fp(async (app) => {
  await app.register(swagger, {
    openapi: {
      info: { title: 'Tasks API', version: '1.0.0' },
      components: { securitySchemes: { bearerAuth: { type: 'http', scheme: 'bearer' } } },
    },
  });
  await app.register(swaggerUi, { routePrefix: '/docs' });
}, { name: 'swagger' });
""", "25.4 Plugins - security and docs")
code("""
// src/plugins/store.ts
import fp from 'fastify-plugin';
import { randomUUID, scryptSync, timingSafeEqual } from 'node:crypto';
import type { Task, ListQuery } from '../schemas/task';

interface User { id: string; username: string; salt: string; hash: Buffer }
const hashPw = (pw: string, salt: string) => scryptSync(pw, salt, 32);

export class Store {
  private tasks = new Map<string, Task>();
  private users = new Map<string, User>();

  constructor() {                              // demo users - use a real DB!
    for (const username of ['alice', 'bob']) {
      const salt = randomUUID();
      this.users.set(username,
        { id: randomUUID(), username, salt, hash: hashPw('password123', salt) });
    }
  }

  verifyUser(username: string, password: string): User | undefined {
    const u = this.users.get(username);
    if (!u) return undefined;
    return timingSafeEqual(u.hash, hashPw(password, u.salt)) ? u : undefined;
  }

  listTasks(ownerId: string, q: ListQuery): Task[] {
    return [...this.tasks.values()]
      .filter((t) => t.ownerId === ownerId && (q.done === undefined || t.done === q.done))
      .slice(q.offset, q.offset + q.limit);
  }

  getTask(id: string) { return this.tasks.get(id); }

  createTask(ownerId: string, title: string): Task {
    const task: Task = { id: randomUUID(), title, done: false, ownerId,
                         createdAt: new Date().toISOString() };
    this.tasks.set(task.id, task);
    return task;
  }

  updateTask(id: string, patch: Partial<Pick<Task, 'title' | 'done'>>): Task {
    const task = { ...this.tasks.get(id)!, ...patch };
    this.tasks.set(id, task);
    return task;
  }

  deleteTask(id: string) { this.tasks.delete(id); }
}

declare module 'fastify' { interface FastifyInstance { store: Store } }

export default fp(async (app) => {
  app.decorate('store', new Store());
}, { name: 'store' });
""", "25.5 Plugins - repository (swap for Postgres/Prisma later)")
code("""
// src/plugins/auth.ts
import fp from 'fastify-plugin';
import jwt from '@fastify/jwt';
import type { FastifyRequest } from 'fastify';

declare module '@fastify/jwt' {
  interface FastifyJWT {
    payload: { sub: string; username: string };
    user: { sub: string; username: string };
  }
}
declare module 'fastify' {
  interface FastifyInstance { authenticate(request: FastifyRequest): Promise<void> }
}

export default fp(async (app) => {
  await app.register(jwt, { secret: app.config.JWT_SECRET, sign: { expiresIn: '1h' } });

  app.decorate('authenticate', async (request: FastifyRequest) => {
    try {
      await request.jwtVerify();
    } catch {
      throw app.httpErrors.unauthorized('Invalid or missing token');
    }
  });
}, { name: 'auth', dependencies: ['env'] });
""", "25.6 Plugins - authentication")
code("""
// src/routes/health.ts
import type { FastifyPluginAsync } from 'fastify';

const health: FastifyPluginAsync = async (app) => {
  app.get('/health', {
    schema: { tags: ['system'],
              response: { 200: { type: 'object',
                                 properties: { status: { type: 'string' },
                                               uptime: { type: 'number' } } } } },
  }, async () => ({ status: 'ok', uptime: process.uptime() }));
};
export default health;

// src/routes/auth.ts
import { Type, FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox';
import { ErrorReply } from '../schemas/task';

const authRoutes: FastifyPluginAsyncTypebox = async (app) => {
  app.post('/login', {
    config: { rateLimit: { max: 5, timeWindow: '1 minute' } },   // brute-force guard
    schema: {
      tags: ['auth'],
      body: Type.Object({ username: Type.String(), password: Type.String() }),
      response: { 200: Type.Object({ token: Type.String() }), 401: ErrorReply },
    },
  }, async (request) => {
    const { username, password } = request.body;          // fully typed
    const user = app.store.verifyUser(username, password);
    if (!user) throw app.httpErrors.unauthorized('Invalid credentials');
    return { token: app.jwt.sign({ sub: user.id, username: user.username }) };
  });
};
export default authRoutes;
""", "25.7 Routes - health and login")
code("""
// src/routes/tasks.ts
import { Type, FastifyPluginAsyncTypebox } from '@fastify/type-provider-typebox';
import type { FastifyRequest } from 'fastify';
import { Task, CreateTask, UpdateTask, TaskParams, ListQuery, ErrorReply }
  from '../schemas/task';

const tasksRoutes: FastifyPluginAsyncTypebox = async (app) => {
  // Every route in this plugin requires a valid JWT (encapsulated hook)
  app.addHook('onRequest', app.authenticate);

  const common = { tags: ['tasks'], security: [{ bearerAuth: [] }] };

  const getOwned = (request: FastifyRequest, id: string) => {
    const task = app.store.getTask(id);
    if (!task || task.ownerId !== request.user.sub) {
      throw app.httpErrors.notFound('Task not found');   // don't reveal existence
    }
    return task;
  };

  app.get('/', {
    schema: { ...common, querystring: ListQuery, response: { 200: Type.Array(Task) } },
  }, async (request) => app.store.listTasks(request.user.sub, request.query));

  app.post('/', {
    schema: { ...common, body: CreateTask, response: { 201: Task } },
  }, async (request, reply) => {
    reply.code(201);
    return app.store.createTask(request.user.sub, request.body.title);
  });

  app.get('/:id', {
    schema: { ...common, params: TaskParams, response: { 200: Task, 404: ErrorReply } },
  }, async (request) => getOwned(request, request.params.id));

  app.patch('/:id', {
    schema: { ...common, params: TaskParams, body: UpdateTask,
              response: { 200: Task, 404: ErrorReply } },
  }, async (request) => {
    getOwned(request, request.params.id);
    return app.store.updateTask(request.params.id, request.body);
  });

  app.delete('/:id', {
    schema: { ...common, params: TaskParams, response: { 204: Type.Null(),
                                                         404: ErrorReply } },
  }, async (request, reply) => {
    getOwned(request, request.params.id);
    app.store.deleteTask(request.params.id);
    return reply.code(204).send(null);
  });
};
export default tasksRoutes;
""", "25.8 Routes - tasks CRUD")
code("""
// src/app.ts
import Fastify, { FastifyServerOptions, FastifyError } from 'fastify';
import { STATUS_CODES } from 'node:http';
import sensible from '@fastify/sensible';
import type { TypeBoxTypeProvider } from '@fastify/type-provider-typebox';
import env from './plugins/env';
import security from './plugins/security';
import swagger from './plugins/swagger';
import store from './plugins/store';
import auth from './plugins/auth';
import health from './routes/health';
import authRoutes from './routes/auth';
import tasksRoutes from './routes/tasks';

export async function buildApp(opts: FastifyServerOptions = {}) {
  const app = Fastify(opts).withTypeProvider<TypeBoxTypeProvider>();

  // 1. Shared plugins (order matters: env first)
  await app.register(env);
  await app.register(sensible);
  await app.register(security);
  await app.register(swagger);            // before routes
  await app.register(store);
  await app.register(auth);

  // 2. Central error handling
  app.setErrorHandler((error: FastifyError, request, reply) => {
    const status = error.statusCode ?? 500;
    if (status >= 500) request.log.error({ err: error }, 'unhandled error');
    reply.code(status).send({
      statusCode: status,
      error: STATUS_CODES[status] ?? 'Error',
      message: status >= 500 ? 'Something went wrong' : error.message,
    });
  });

  // 3. Feature routes (encapsulated)
  await app.register(health);
  await app.register(authRoutes, { prefix: '/auth' });
  await app.register(tasksRoutes, { prefix: '/tasks' });

  return app;
}
""", "25.9 App builder")
code("""
// src/server.ts
import closeWithGrace from 'close-with-grace';
import { buildApp } from './app';

async function main() {
  const app = await buildApp({
    logger: {
      level: process.env.LOG_LEVEL ?? 'info',
      redact: ['req.headers.authorization'],
      transport: process.env.NODE_ENV === 'production'
        ? undefined : { target: 'pino-pretty' },
    },
    trustProxy: true,
    requestTimeout: 30_000,
  });

  closeWithGrace({ delay: 10_000 }, async ({ signal, err }) => {
    if (err) app.log.error({ err }, 'shutting down after error');
    else app.log.info({ signal }, 'shutting down');
    await app.close();
  });

  await app.listen({ port: app.config.PORT, host: app.config.HOST });
}

main().catch((err) => { console.error(err); process.exit(1); });
""", "25.10 Server entry point")
code("""
// test/tasks.test.ts
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { buildApp } from '../src/app';

process.env.JWT_SECRET = 'test-secret-test-secret-test-secret-123';
let app: Awaited<ReturnType<typeof buildApp>>;
let token: string;

before(async () => {
  app = await buildApp();
  const res = await app.inject({ method: 'POST', url: '/auth/login',
    payload: { username: 'alice', password: 'password123' } });
  token = res.json().token;
});
after(() => app.close());

const auth = () => ({ authorization: `Bearer ${token}` });

test('rejects requests without a token', async () => {
  const res = await app.inject({ method: 'GET', url: '/tasks' });
  assert.equal(res.statusCode, 401);
});

test('creates, lists, updates and deletes a task', async () => {
  const created = await app.inject({ method: 'POST', url: '/tasks', headers: auth(),
                                     payload: { title: 'Write tests' } });
  assert.equal(created.statusCode, 201);
  const { id } = created.json();

  const list = await app.inject({ url: '/tasks?done=false', headers: auth() });
  assert.equal(list.json().length, 1);

  const patched = await app.inject({ method: 'PATCH', url: `/tasks/${id}`,
                                     headers: auth(), payload: { done: true } });
  assert.equal(patched.json().done, true);

  const del = await app.inject({ method: 'DELETE', url: `/tasks/${id}`,
                                 headers: auth() });
  assert.equal(del.statusCode, 204);
});

test('validates input', async () => {
  const res = await app.inject({ method: 'POST', url: '/tasks', headers: auth(),
                                 payload: { title: '' } });
  assert.equal(res.statusCode, 400);
});
""", "25.11 Tests")
h2("25.12 Run it")
code("""
npm run dev          # tsx watch src/server.ts
npm test             # node --import tsx --test test/*.test.ts
""")
p("On Windows PowerShell use " + c("curl.exe") + " instead of the " + c("curl") + " alias.")
code("""
# 1. Log in
curl -X POST localhost:3000/auth/login -H "Content-Type: application/json" \\
     -d '{"username":"alice","password":"password123"}'
# {"token":"eyJhbGciOi..."}
TOKEN=eyJhbGciOi...

# 2. Create
curl -X POST localhost:3000/tasks -H "Authorization: Bearer $TOKEN" \\
     -H "Content-Type: application/json" -d '{"title":"Learn Fastify"}'
# 201 {"id":"3f2c...","title":"Learn Fastify","done":false,
#      "ownerId":"...","createdAt":"..."}

# 3. List with coerced query params
curl "localhost:3000/tasks?done=false&limit=10" -H "Authorization: Bearer $TOKEN"

# 4. Update / delete
curl -X PATCH localhost:3000/tasks/3f2c... -H "Authorization: Bearer $TOKEN" \\
     -H "Content-Type: application/json" -d '{"done":true}'
curl -X DELETE localhost:3000/tasks/3f2c... -H "Authorization: Bearer $TOKEN"   # 204

# 5. Errors
curl localhost:3000/tasks                       # 401 Invalid or missing token
curl -X POST localhost:3000/tasks -H "Authorization: Bearer $TOKEN" \\
     -H "Content-Type: application/json" -d '{"title":"","x":1}'   # 400 validation

# 6. Docs
open http://localhost:3000/docs
""")
h2("25.13 What to notice")
bullets([
    "<b>No manual validation code</b>: TypeBox schemas validate, coerce ("
    + c("done=false") + " &rarr; boolean), set defaults (" + c("limit=20") + ") and type "
    + c("request.body") + "/" + c("request.query") + ".",
    "<b>Encapsulated auth</b>: the " + c("onRequest") + " hook in " + c("tasks.ts")
    + " protects only task routes; " + c("/health") + " and " + c("/auth") + " stay public.",
    "<b>Response schemas</b> generate Swagger docs and guarantee output shape.",
    "<b>Swappable storage</b>: replace " + c("plugins/store.ts") + " with a Postgres/Prisma "
    "plugin exposing the same methods; routes and tests stay unchanged.",
    "<b>Fast tests</b>: " + c("inject()") + " exercises the full lifecycle (hooks, "
    "validation, serialization) without opening a port.",
    "<b>Unknown fields are stripped, not rejected</b>: " + c('{"title":"ok","x":1}')
    + " creates a task (Ajv " + c("removeAdditional") + "). Set Ajv "
    + c("removeAdditional: false") + " if you prefer a 400.",
    "<b>Rate limit is real</b>: the 6th login attempt within a minute returns "
    + c("429 Too Many Requests") + "; every response carries " + c("x-ratelimit-*")
    + " headers.",
])
h2("25.14 Next steps")
bullets([
    "Persist data with " + c("@fastify/postgres") + " or Prisma (Chapter 15).",
    "Add refresh tokens and roles (" + c("preHandler") + " authorization).",
    "Add " + c("@fastify/under-pressure") + " and containerize (Chapters 23-24).",
    "Split into " + c("@fastify/autoload") + " folders as it grows (Chapter 22).",
])

# =========================================================================
ANNOTATE.clear()
part("Appendices")
# =========================================================================
h1("A. Express to Fastify Cheat Sheet")
table([
    ["Express", "Fastify"],
    [c("const app = express()"), c("const app = Fastify({ logger: true })")],
    [c("app.use(express.json())"), "Built in (JSON parser)"],
    [c("app.use(middleware)"), c("app.addHook('onRequest', fn)") + " or a plugin"],
    [c("express.Router()"), c("app.register(plugin, { prefix })")],
    [c("req.params / req.query / req.body"), c("request.params / query / body")],
    [c("res.status(201).json(x)"), c("reply.code(201); return x")],
    [c("res.set('X', 'y')"), c("reply.header('X', 'y')")],
    [c("res.redirect(url)"), c("reply.redirect(url)")],
    [c("res.sendFile()"), c("@fastify/static") + " + " + c("reply.sendFile()")],
    [c("next(err)"), c("throw err")],
    [c("app.use((err, req, res, next) =&gt; ...)"), c("app.setErrorHandler(fn)")],
    [c("req.user = ...") + " in middleware", c("decorateRequest('user', null)") +
     " + hook"],
    [c("cors()") + ", " + c("helmet()"), c("@fastify/cors") + ", " + c("@fastify/helmet")],
    [c("supertest(app)"), c("app.inject()")],
    ["Existing Express middleware", c("@fastify/express") + " or " + c("@fastify/middie")
     + " (migration bridge)"],
], [80 * mm, 90 * mm])
h1("B. Official Plugins Reference")
table([
    ["Plugin", "Purpose"],
    [c("@fastify/autoload"), "Load plugins/routes from folders"],
    [c("@fastify/sensible"), "HTTP errors, assert, useful utilities"],
    [c("@fastify/env"), "Validated environment configuration"],
    [c("@fastify/cors") + ", " + c("@fastify/helmet"), "CORS and security headers"],
    [c("@fastify/rate-limit"), "Rate limiting (memory or Redis)"],
    [c("@fastify/jwt") + ", " + c("@fastify/auth"), "JWT and auth strategy composition"],
    [c("@fastify/cookie") + ", " + c("@fastify/session"), "Cookies and sessions"],
    [c("@fastify/oauth2"), "OAuth2 login (Google, GitHub, ...)"],
    [c("@fastify/swagger") + ", " + c("@fastify/swagger-ui"), "OpenAPI docs"],
    [c("@fastify/static") + ", " + c("@fastify/view"), "Static files, template rendering"],
    [c("@fastify/multipart") + ", " + c("@fastify/formbody"), "Uploads and form bodies"],
    [c("@fastify/websocket"), "WebSocket routes"],
    [c("@fastify/compress") + ", " + c("@fastify/caching"), "Compression and caching headers"],
    [c("@fastify/postgres") + ", " + c("@fastify/mongodb") + ", " + c("@fastify/redis"),
     "Database connectors"],
    [c("@fastify/under-pressure"), "Load shedding and health status"],
    [c("@fastify/http-proxy"), "Reverse proxy / API gateway"],
    [c("@fastify/schedule"), "Run scheduled jobs (toad-scheduler)"],
], [75 * mm, 95 * mm])
h1("C. Troubleshooting")
table([
    ["Symptom", "Cause / fix"],
    ["Server unreachable in Docker", "Listening on localhost. Use " + c("host: '0.0.0.0'")
     + "."],
    [c("FST_ERR_CTP_INVALID_MEDIA_TYPE") + " / 415", "No parser for that content-type. "
     "Register " + c("@fastify/formbody") + ", " + c("@fastify/multipart") + " or add one."],
    [c("FST_ERR_CTP_BODY_TOO_LARGE") + " / 413", "Increase " + c("bodyLimit")
     + " (globally or per route)."],
    ["Decorator undefined in another plugin", "Plugin not wrapped with "
     + c("fastify-plugin") + ", or registered after the consumer."],
    ["Hook doesn't run for some routes", "Encapsulation: hook added in a sibling context. "
     "Move it to a parent or an fp plugin."],
    ["\"Reply was already sent\"", "Both " + c("reply.send()") + " and a return value in an "
     "async handler. Use one."],
    ["Fields missing from response", "Not listed in the response schema (by design)."],
    ["Querystring schema rejected at startup", "v5 needs full JSON Schema ("
     + c("type: 'object', properties") + ")."],
    [c("FST_ERR_DEC_ALREADY_PRESENT"), "Same decorator registered twice (plugin registered "
     "twice?). Check with " + c("app.hasDecorator()") + "."],
    [c("TS5108 moduleResolution=node10 removed"), "TypeScript 7: set module and "
     "moduleResolution to " + c("nodenext") + "."],
    [c("ts-node") + " / " + c("ts-jest") + " fail with TS 7", "No JS compiler API in TS 7. "
     "Use " + c("tsx") + " and " + c("node --import tsx --test") + "."],
    [c("reply.send()") + " type error with 204 schema", "A " + c("Type.Null()")
     + " response expects " + c("reply.code(204).send(null)") + "."],
    ["Rate limit keyed on the body blocks everyone on an IP",
     "The default " + c("onRequest") + " hook runs before body parsing; set "
     + c("hook: 'preHandler'") + " in the route's rateLimit config (17.1)."],
    [c("app.close()") + " takes ~72 s", "Keep-alive sockets that go idle after close "
     "started wait for " + c("keepAliveTimeout") + ". Send " + c("Connection: close")
     + " while shutting down (24.4)."],
    ["SSE subscribers linger after the tab closes", "Disconnects surface on the next "
     "write; keep the ping interval short (6.5)."],
    ["OpenAPI marks a defaulted field as required", "Wrap it: "
     + c("Type.Optional(Type.Boolean({ default: false }))") + " (7.6)."],
    [c("FST_ERR_PLUGIN_TIMEOUT"), "A plugin never resolved/called done. Await everything; "
     "don't mix callback and async styles."],
], [60 * mm, 110 * mm])
h2("Further resources")
bullets([
    "Docs: fastify.dev/docs/latest",
    "Ecosystem list: fastify.dev/ecosystem",
    "Examples &amp; demo: github.com/fastify/demo",
    "Migration guide v4 &rarr; v5: fastify.dev/docs/latest/Guides/Migration-Guide-V5",
    "Community: Fastify Discord and GitHub discussions",
])


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
    cv.drawString(20 * mm, A4[1] - 12 * mm, "Fastify with Node.js - Complete Tutorial")
    cv.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Page {doc.page}")
    cv.restoreState()


doc = Doc(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
          topMargin=20 * mm, bottomMargin=18 * mm,
          title="Fastify with Node.js - Complete Tutorial", author="Claude")
doc.multiBuild(list(story), onFirstPage=on_page, onLaterPages=on_page)
print("wrote", OUT)
