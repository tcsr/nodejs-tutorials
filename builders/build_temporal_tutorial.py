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
OUT = pdf('Temporal_NodeJS_Complete_Tutorial.pdf')

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
        story.append(t)
        story.append(Spacer(1, 8))


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


# =========================================================================
# TITLE + TOC
# =========================================================================
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'examples_content.py'), encoding='utf8').read())

super(Story, story).append(Spacer(1, 60 * mm))
super(Story, story).append(Paragraph("Temporal with Node.js", ParagraphStyle(
    "T", parent=H1, fontSize=32, leading=38, alignment=TA_CENTER)))
super(Story, story).append(Paragraph("The Complete Practical Tutorial", ParagraphStyle(
    "ST", parent=BODY, fontSize=16, leading=20, alignment=TA_CENTER, textColor=GREY,
    spaceAfter=24)))
super(Story, story).append(Paragraph(
    "From installation and project setup, through SDK imports and the runtime model "
    "and 15 tested real-world examples, "
    "to signals, timers, error handling, versioning, testing, production deployment "
    "and a complete end-to-end order-processing service.",
    ParagraphStyle("TD", parent=BODY, alignment=TA_CENTER, fontSize=11, leading=16)))
super(Story, story).append(Spacer(1, 30 * mm))
super(Story, story).append(Paragraph(
    "Verified with @temporalio/* 1.24 &middot; Temporal CLI 1.9 &middot; Node.js 24 &middot; TypeScript 7",
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
h1("1. Why Temporal?")
p("Most backend processes are more than one step: charge a card, reserve stock, send an "
  "email, wait for approval, ship. Coding that reliably by hand means queues, cron jobs, "
  "status columns, retry tables, dead-letter handling and idempotency checks &mdash; and "
  "still hoping nothing crashes between step 2 and step 3.")
p("<b>Temporal</b> is a <b>durable execution</b> platform. You write the process as plain "
  "async TypeScript. Temporal records every step in an <b>event history</b>; if your process "
  "crashes, a new worker picks up the history, replays the code to the exact same point, and "
  "continues. Waiting 30 days is one line of code and costs nothing while waiting.")
table([
    ["Without Temporal", "With Temporal"],
    ["Hand-written retry loops, backoff, DLQs", "Declarative retry policy per activity"],
    ["State stored in DB status columns", "State is just local variables in the workflow"],
    ["Cron + polling to resume long waits", c("await sleep('30 days')")],
    ["Custom compensation / rollback logic spread across services",
     "Saga pattern in one function with try/catch"],
    ["Hard to see where a process is stuck", "Web UI shows full event history of each run"],
], [85 * mm, 85 * mm])
p("Common use cases: order &amp; payment flows, onboarding, subscriptions/billing, data "
  "pipelines &amp; ETL, infrastructure provisioning, human approvals, AI agent orchestration, "
  "and any microservice orchestration that must not lose progress.")

h2("1.1 Real-world examples in this guide")
p("Every topic is shown twice: first the concept, then a <b>real-world example</b> "
  "that runs and is covered by tests. All examples live in "
  + c("temporal-examples/") + " next to this PDF (35 tests, all passing).")
table([
    ["Scenario", "Topics", "Section"],
    ["Charging a card", "Activities, retries, idempotency, typed failures", "6.5"],
    ["Flight search", "Parallel activities, local activities, partial failure", "7.5"],
    ["Shopping cart", "Signals, queries, updates, validators, idle timeout", "11.1"],
    ["14-day free trial", "Durable timers, condition + timeout", "12.3"],
    ["Nightly sales report", "Schedules, time zones, overlap/catch-up", "12.4"],
    ["Loan application", "Error types, timeouts, local activities", "13.5"],
    ["Video transcoding", "Heartbeats, resume, cancellation, cleanup", "14.1"],
    ["Employee onboarding", "Child workflows, parent close policy", "15.4"],
    ["Loyalty account", "Entity workflow, continue-as-new, dedupe", "15.5"],
    ["E-mail campaign", "Bounded fan-out, pagination, progress query", "15.6"],
    ["Trip booking", "Saga compensation", "16.1"],
    ["Expense approval", "Human-in-the-loop, escalation", "16.2"],
    ["Identity verification", "Polling via retry policy", "16.3"],
    ["Document review", "Async activity completion (webhooks)", "16.4"],
    ["Live fraud-check rollout", "Versioning, patching, replay tests", "17.3"],
], [42 * mm, 108 * mm, 20 * mm])

h1("2. Architecture &amp; Runtime Model")
p("A Temporal application has three parts: the <b>Temporal Service</b> (server), your "
  "<b>Workers</b> (Node.js processes running your code) and <b>Clients</b> (code that starts "
  "and talks to workflows). The server <i>never</i> runs your code &mdash; it stores history "
  "and hands out tasks; workers pull tasks, execute them and report back.")
story.append(architecture_diagram())
story.append(Spacer(1, 6))
h2("2.1 Key terms")
table([
    ["Term", "Meaning"],
    ["<b>Workflow Definition</b>", "An exported async function in " + c("workflows.ts") +
     ". Deterministic orchestration logic."],
    ["<b>Workflow Execution</b>", "One running instance, identified by <b>Workflow ID</b> + "
     "<b>Run ID</b>."],
    ["<b>Activity</b>", "A normal async function with side effects (HTTP, DB, files, email). "
     "Retried automatically."],
    ["<b>Worker</b>", "Process that polls a task queue and runs workflow + activity code."],
    ["<b>Task Queue</b>", "Named queue. Clients start workflows on it; workers listen on it."],
    ["<b>Namespace</b>", "Isolation unit (like a database). Dev server default: " +
     c("default") + "."],
    ["<b>Event History</b>", "Append-only log of everything that happened in an execution."],
    ["<b>Workflow Task</b>", "\"Advance the workflow code\" job given to a worker."],
    ["<b>Activity Task</b>", "\"Run this activity with these args\" job given to a worker."],
    ["<b>Command</b>", "What workflow code asks for: schedule activity, start timer, "
     "complete, etc."],
], [42 * mm, 128 * mm])
h2("2.2 What happens at runtime (step by step)")
steps([
    "Client calls " + c("client.workflow.start(orderWorkflow, {...})") + ". The server "
    "writes <i>WorkflowExecutionStarted</i> and puts a <b>workflow task</b> on the task queue.",
    "A worker long-polling that queue receives the task, loads the workflow bundle into a "
    "V8 isolate, and runs the function until it blocks on something (e.g. an activity call).",
    "The worker returns <b>commands</b> (\"schedule activity chargeCard\") to the server, "
    "which records them and places an <b>activity task</b> on the queue.",
    "A worker (same or different) picks up the activity task, runs your real Node function, "
    "and reports the result or error. The server records <i>ActivityTaskCompleted</i>.",
    "The server schedules a new workflow task. The worker feeds the result into the "
    "waiting " + c("await") + " and the workflow continues to its next step.",
    "When the function returns, the worker sends <i>CompleteWorkflowExecution</i>. The "
    "result is stored and returned to anyone awaiting " + c("handle.result()") + ".",
])
h2("2.3 Replay: how crashes are survived")
p("Workers cache running workflows in memory. If a worker dies (or the cache is evicted), "
  "the next worker receives the full event history and <b>replays</b> the workflow code from "
  "the beginning. Every " + c("await") + " on an activity that already completed resolves "
  "instantly with the recorded result, so the code arrives at the same state without "
  "re-running side effects.")
story.append(replay_diagram())
p("This is why workflow code must be <b>deterministic</b>: given the same history, it must "
  "issue the same commands in the same order. Anything non-deterministic (I/O, random, "
  "wall-clock time) belongs in activities. The SDK helps by sandboxing workflow code "
  "(Chapter 5).")

h1("3. Installation")
h2("3.1 Prerequisites")
bullets([
    "<b>Node.js 20 or newer</b> (examples verified on Node 24) &mdash; check with "
    + c("node -v") + ".",
    "npm / pnpm / yarn.",
    "Supported OS: Windows x64, macOS (Intel/Apple Silicon), Linux x64/arm64 with glibc. "
    "The worker uses a native Rust core, so <b>Alpine/musl images are not supported</b>.",
    "Optional: Docker (for a full self-hosted server), Git.",
])
h2("3.1a Tested with")
p("Every command and the complete Part VI project in this guide were run against these "
  "versions (September 2026). The companion projects are "
  + c("temporal-order-service/") + " (Part VI) and " + c("temporal-examples/")
  + " (15 real-world examples, 35 tests), next to this PDF.")
table([
    ["Component", "Version", "Notes"],
    ["Node.js", "24.15", "20+ supported"],
    [c("@temporalio/*") + " (client, worker, workflow, activity, testing)", "1.24.0",
     "keep all SDK packages on the same version"],
    ["Temporal CLI / Server / UI", "1.9.1 / 1.32.0 / 2.54.1", c("temporal server start-dev")],
    ["TypeScript", "7.0.2", "native compiler: use " + c("tsx") + ", not ts-node/ts-jest"],
    [c("tsx"), "4.23", "runs .ts files, watch mode"],
    ["Express", "5.2.1", "async errors handled natively"],
    ["OS", "Windows 11", "also works on macOS / Linux (glibc)"],
], [62 * mm, 40 * mm, 68 * mm])
h2("3.2 Install the Temporal CLI")
p("The CLI contains a complete single-binary dev server, the Web UI and admin commands.")
code("""
# macOS (Homebrew)
brew install temporal

# macOS / Linux (install script)
curl -sSf https://temporal.download/cli.sh | sh
# adds ~/.temporalio/bin - add it to your PATH

# Windows
#  1. Download the Windows amd64 zip from https://temporal.io/download
#  2. Extract temporal.exe to e.g. C:\\tools\\temporal
#  3. Add that folder to PATH (System Properties > Environment Variables)

# Verify
temporal --version
""")
h2("3.3 Start the development server")
code("""
# In-memory (data lost on exit) - fastest for learning
temporal server start-dev

# Persist to a SQLite file, custom UI port, pre-create a namespace
temporal server start-dev --db-filename temporal.db --ui-port 8233 --namespace orders
""")
table([
    ["Endpoint", "Default", "Used by"],
    ["gRPC frontend", c("localhost:7233"), "Workers and Clients"],
    ["Web UI", c("http://localhost:8233"), "You, in the browser"],
    ["Namespace", c("default"), "Pass " + c("namespace") + " in Worker/Client options"],
], [45 * mm, 55 * mm, 70 * mm])
h2("3.4 Other server options")
bullets([
    "<b>Docker Compose</b> (Postgres/MySQL/Elasticsearch-backed, closer to production): "
    "clone " + c("github.com/temporalio/docker-compose") + " and run "
    + c("docker compose up") + ".",
    "<b>Kubernetes</b>: official Helm charts (" + c("temporalio/helm-charts") + ").",
    "<b>Temporal Cloud</b>: managed service; you get a namespace endpoint plus an API key or "
    "mTLS certificates (Chapter 20).",
])
h2("3.4a No CLI? Start the dev server from Node")
p("The testing package can download and run the same dev server binary for you &mdash; "
  "handy on locked-down machines or in CI (verified on Windows):")
code("""
// scripts/dev-server.ts   ->   npx tsx scripts/dev-server.ts
import { TestWorkflowEnvironment } from '@temporalio/testing';

async function main() {
  const env = await TestWorkflowEnvironment.createLocal({
    server: { ip: '127.0.0.1', port: 7233, ui: true, uiPort: 8233 },
  });
  console.log('Temporal dev server on localhost:7233, UI on http://localhost:8233');
  const stop = async () => { await env.teardown(); process.exit(0); };
  process.on('SIGINT', stop);
  process.on('SIGTERM', stop);
  setInterval(() => {}, 1 << 30);   // keep process alive
}
main().catch((err) => { console.error(err); process.exit(1); });
""")
h2("3.5 Useful admin commands")
code("""
temporal operator namespace create --namespace orders
temporal operator namespace list
temporal operator search-attribute create --name CustomerId --type Keyword
temporal operator cluster health
""")

h1("4. Project Setup from Scratch")
h2("4.1 Option A: scaffold a sample")
code("""
npx @temporalio/create@latest ./my-temporal-app --sample hello-world
cd my-temporal-app
npm run start.watch     # terminal 1: worker with auto-reload
npm run workflow        # terminal 2: runs the client
""")
p("Other useful samples: " + c("activities-cancellation-heartbeating") + ", "
  + c("child-workflows") + ", " + c("saga") + ", " + c("schedules") + ", "
  + c("expense") + ", " + c("nextjs-ecommerce-oneclick") + ". List them all at "
  "github.com/temporalio/samples-typescript.")
h2("4.2 Option B: manual setup (recommended to learn)")
code("""
mkdir temporal-orders && cd temporal-orders
npm init -y

# Runtime SDK packages
npm install @temporalio/client @temporalio/worker @temporalio/workflow \\
            @temporalio/activity @temporalio/common

# Dev tooling
npm install -D typescript tsx @types/node @temporalio/testing
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
    "outDir": "./lib"
  },
  "include": ["src/**/*.ts"]
}
""", "tsconfig.json")
code("""
{
  "name": "temporal-orders",
  "private": true,
  "scripts": {
    "build": "tsc",
    "dev-server": "tsx scripts/dev-server.ts",
    "worker": "tsx src/worker.ts",
    "worker:watch": "tsx watch src/worker.ts",
    "client": "tsx src/client.ts",
    "api": "tsx src/api.ts",
    "start:worker": "node lib/worker.js",
    "test": "node --import tsx --test test/*.test.ts"
  }
}
""", "package.json (scripts section)")
warn("TypeScript 7 is a native (Go) compiler with no JavaScript API, so " + c("ts-node")
     + ", " + c("ts-jest") + " and similar tools fail on a fresh install. Use " + c("tsx")
     + " to run TypeScript and Node's built-in test runner (or Vitest) for tests. TS 7 also "
     "removed " + c('"moduleResolution": "node"') + " &mdash; use " + c('"nodenext"') + ".")
h2("4.3 Recommended layout")
code("""
temporal-orders/
  src/
    shared.ts        # task queue name, shared types (imported by all)
    activities.ts    # side effects - runs in normal Node.js
    workflows.ts     # orchestration - bundled & run in V8 sandbox
    worker.ts        # registers workflows + activities, polls task queue
    client.ts        # starts workflows / sends signals (scripts, APIs)
    api.ts           # optional HTTP layer (Express) that uses the client
  test/
    workflows.test.ts
  tsconfig.json
  package.json
""")
h2("4.4 Plain JavaScript and ES modules")
p("TypeScript is optional. In JavaScript, drop the types and keep everything else the same "
  "(workflow files can be " + c(".js") + "). With ES modules (" + c('"type": "module"') + "), "
  + c("require.resolve") + " is unavailable &mdash; resolve the workflows file like this:")
code("""
// worker.mjs
import { fileURLToPath } from 'node:url';
const workflowsPath = fileURLToPath(new URL('./workflows.js', import.meta.url));
""")

h1("5. SDK Packages, Imports &amp; the Workflow Sandbox")
h2("5.1 Which package goes where")
table([
    ["Package", "Import it in", "Main exports"],
    [c("@temporalio/workflow"), "workflows.ts ONLY",
     "proxyActivities, proxyLocalActivities, sleep, condition, defineSignal/Query/Update, "
     "setHandler, executeChild, startChild, continueAsNew, patched, CancellationScope, "
     "workflowInfo, uuid4, log, ApplicationFailure"],
    [c("@temporalio/activity"), "activities.ts",
     "activityInfo, heartbeat, sleep, cancelled, cancellationSignal, log, Context, "
     "ApplicationFailure"],
    [c("@temporalio/worker"), "worker.ts",
     "Worker, NativeConnection, Runtime, DefaultLogger, bundleWorkflowCode"],
    [c("@temporalio/client"), "client.ts, api.ts",
     "Connection, Client, WorkflowHandle, WorkflowNotFoundError, "
     "WorkflowFailedError, ScheduleOverlapPolicy"],
    [c("@temporalio/common"), "anywhere",
     "ApplicationFailure, failure types, RetryPolicy type, data converter types"],
    [c("@temporalio/testing"), "tests",
     "TestWorkflowEnvironment, MockActivityEnvironment"],
], [42 * mm, 30 * mm, 98 * mm])
h2("5.2 The import rules")
code("""
// workflows.ts
import { proxyActivities, sleep } from '@temporalio/workflow';  // OK
import type * as activities from './activities';               // OK - type only
import { TASK_QUEUE, type OrderInput } from './shared';        // OK - pure code
import { formatMoney } from './utils/money';                   // OK if deterministic

import * as activities from './activities';    // BAD: pulls DB/HTTP libs into sandbox
import axios from 'axios';                     // BAD: network I/O
import fs from 'fs';                           // BAD: Node built-in, bundling fails
import { Client } from '@temporalio/client';   // BAD: not allowed in workflows
""")
p("Why " + c("import type") + "? The workflow only needs the <i>signatures</i> of your "
  "activities to create typed proxies; the real implementations are registered on the "
  "Worker. Type-only imports disappear at compile time, so nothing leaks into the bundle.")
h2("5.3 What the sandbox does for you")
p("When a Worker starts, it uses webpack to <b>bundle</b> " + c("workflowsPath") +
  " and all its imports, then runs each workflow in an isolated V8 context where:")
bullets([
    c("Math.random()") + " is seeded deterministically per execution.",
    c("Date.now()") + " / " + c("new Date()") + " return the time of the current workflow "
    "task (constant during a task, replayed identically).",
    c("setTimeout") + " is replaced by a durable timer (prefer " + c("sleep()") + ").",
    "Node built-ins (" + c("fs") + ", " + c("http") + ", " + c("process") +
    ") are unavailable &mdash; bundling fails fast if you import them.",
    "Global state is isolated per execution.",
])
warn("The sandbox cannot protect you from logic changes. Changing the order or number of "
     "activity calls in a deployed workflow can break running executions on replay. "
     "Use versioning (Chapter 17).")

# =========================================================================
part("Part II &mdash; Core Building Blocks")
# =========================================================================
h1("6. Activities")
p("Activities are ordinary async functions. They can do anything: call APIs, query databases, "
  "read files, use any npm package. They should be <b>idempotent</b> because Temporal may run "
  "them more than once (retries, worker crash after completion but before reporting).")
h2("6.1 Basic activities")
code("""
// src/activities.ts
import { log } from '@temporalio/activity';

export async function sendEmail(to: string, subject: string): Promise<void> {
  log.info('Sending email', { to, subject });
  await mailer.send({ to, subject });
}

export async function getExchangeRate(from: string, to: string): Promise<number> {
  const res = await fetch(`https://api.example.com/rate?from=${from}&to=${to}`);
  if (!res.ok) throw new Error(`Rate API ${res.status}`);   // retried automatically
  return (await res.json()).rate;
}
""")
h2("6.2 Dependency injection (DB clients, config)")
p("Create activities from a factory so they share connections and are easy to test:")
code("""
// src/activities.ts
import type { Pool } from 'pg';

export function createActivities(db: Pool) {
  return {
    async saveOrder(orderId: string, total: number): Promise<void> {
      await db.query(
        'INSERT INTO orders(id,total) VALUES($1,$2) ON CONFLICT (id) DO NOTHING',
        [orderId, total],            // ON CONFLICT = idempotent on retries
      );
    },
    async getOrderTotal(orderId: string): Promise<number> {
      const r = await db.query('SELECT total FROM orders WHERE id=$1', [orderId]);
      return Number(r.rows[0].total);
    },
  };
}

// worker.ts:  activities: createActivities(new Pool({ connectionString: ... }))
// workflows.ts:
//   proxyActivities<ReturnType<typeof createActivities>>({ ... })
""")
h2("6.3 Activity context")
code("""
import { activityInfo, heartbeat, sleep, cancellationSignal, log }
  from '@temporalio/activity';

export async function processVideo(url: string): Promise<string> {
  const info = activityInfo();
  log.info('Starting', {
    attempt: info.attempt,
    workflowId: info.workflowExecution?.workflowId,   // undefined outside workflows
  });

  const res = await fetch(url, { signal: cancellationSignal() }); // aborts on cancel
  for (let pct = 0; pct <= 100; pct += 10) {
    heartbeat(pct);            // tells server "still alive" + progress
    await sleep('2 seconds');  // cancellation-aware sleep
  }
  return 'done';
}
""")
table([
    ["activityInfo() field", "Use"],
    [c("attempt"), "Current attempt number (starts at 1)."],
    [c("activityId / activityType"), "Identify the call in logs."],
    [c("workflowExecution"), "{ workflowId, runId } of the calling workflow."],
    [c("heartbeatDetails"), "Last value passed to heartbeat() before a retry &mdash; "
     "resume from checkpoint."],
    [c("taskToken"), "Needed for asynchronous completion (see below)."],
], [55 * mm, 115 * mm])
h2("6.4 Asynchronous activity completion")
p("When the real work is finished by an external system (e.g. a webhook), the activity can "
  "return without completing, and something else completes it later:")
code("""
import { activityInfo, CompleteAsyncError } from '@temporalio/activity';

export async function requestManualReview(docId: string): Promise<string> {
  const token = Buffer.from(activityInfo().taskToken).toString('base64');
  await reviewSystem.createTicket({ docId, callbackToken: token });
  throw new CompleteAsyncError();  // "I'll be completed from outside"
}

// Later, in your webhook handler (client side):
await client.activity.complete(Buffer.from(token, 'base64'), 'APPROVED');
""")

ex_payments("6.5")

h1("7. Workflows")
h2("7.1 Anatomy of a workflow")
code("""
// src/workflows.ts
import { proxyActivities, log, workflowInfo, sleep } from '@temporalio/workflow';
import type * as activities from './activities';

const { sendEmail, getExchangeRate } = proxyActivities<typeof activities>({
  startToCloseTimeout: '30 seconds',
});

export interface InvoiceInput {
  customerEmail: string; amountUsd: number; currency: string;
}

export async function invoiceWorkflow(input: InvoiceInput): Promise<number> {
  const { workflowId } = workflowInfo();
  log.info('Invoice started', { workflowId });           // replay-safe logger

  const rate = await getExchangeRate('USD', input.currency);
  const amount = Math.round(input.amountUsd * rate * 100) / 100;

  await sendEmail(input.customerEmail, `Invoice: ${amount} ${input.currency}`);
  await sleep('7 days');                                  // durable timer
  await sendEmail(input.customerEmail, 'Payment reminder');
  return amount;
}
""")
note("Take a <b>single object argument</b>. You can add optional fields later without "
     "breaking running workflows or callers.")
h2("7.2 Running steps in parallel")
code("""
// Parallel activities - plain Promise.all works and is deterministic
const [user, cart, prefs] = await Promise.all([
  getUser(userId), getCart(userId), getPreferences(userId),
]);

// Race: first to finish wins
const winner = await Promise.race([fastProvider(q), slowProvider(q)]);
""")
h2("7.3 Local activities")
p(c("proxyLocalActivities") + " runs short activities (&lt; a few seconds) inside the same "
  "workflow task, without a round-trip through the task queue. Lower latency and fewer "
  "history events; use for quick lookups or validations.")
code("""
import { proxyLocalActivities } from '@temporalio/workflow';
const { validateAddress } = proxyLocalActivities<typeof activities>({
  startToCloseTimeout: '5 seconds',
});
""")
h2("7.4 Helpers available inside workflows")
table([
    ["API", "Purpose"],
    [c("workflowInfo()"), "workflowId, runId, workflowType, taskQueue, attempt, "
     "continueAsNewSuggested, historyLength, ..."],
    [c("log"), "Replay-aware logger (does not re-log during replay)."],
    [c("uuid4()"), "Deterministic UUID (use instead of crypto.randomUUID)."],
    [c("sleep(duration)"), "Durable timer. Accepts ms or strings like '5 minutes'."],
    [c("condition(fn, timeout?)"), "Wait until fn() is true; returns false on timeout."],
    [c("upsertSearchAttributes()"), "Update indexed fields visible to list queries."],
    [c("patched(id)"), "Versioning branch for code changes."],
], [50 * mm, 120 * mm])

ex_travel("7.5")

h1("8. Workers")
h2("8.1 A production-ready worker")
code("""
// src/worker.ts
import { NativeConnection, Worker, Runtime, DefaultLogger } from '@temporalio/worker';
import * as activities from './activities';
import { TASK_QUEUE } from './shared';

Runtime.install({ logger: new DefaultLogger('INFO') });   // optional, once per process

async function run() {
  const connection = await NativeConnection.connect({
    address: process.env.TEMPORAL_ADDRESS ?? 'localhost:7233',
  });
  try {
    const worker = await Worker.create({
      connection,
      namespace: process.env.TEMPORAL_NAMESPACE ?? 'default',
      taskQueue: TASK_QUEUE,
      workflowsPath: require.resolve('./workflows'),
      activities,
      maxConcurrentActivityTaskExecutions: 100,
      maxConcurrentWorkflowTaskExecutions: 40,
      shutdownGraceTime: '30 seconds',   // let activities finish on SIGTERM
    });
    console.log(`Worker polling task queue "${TASK_QUEUE}"`);
    await worker.run();                  // resolves after graceful shutdown
  } finally {
    await connection.close();
  }
}

run().catch((err) => { console.error(err); process.exit(1); });
""")
h2("8.2 Worker lifecycle")
steps([
    "<b>Create</b>: connects, bundles workflow code (a few seconds; see pre-bundling in "
    "Chapter 20), registers activities.",
    "<b>Run</b>: long-polls the task queue for workflow and activity tasks, executes them, "
    "keeps a cache of running workflows.",
    "<b>Shutdown</b>: on SIGINT/SIGTERM (default) or " + c("worker.shutdown()") + " it stops "
    "polling, waits up to " + c("shutdownGraceTime") + " for in-flight activities, then "
    + c("run()") + " resolves.",
])
h2("8.3 Things to know")
bullets([
    "Workers are <b>stateless</b> from the server's view. Run as many replicas as you need; "
    "tasks are load-balanced automatically.",
    "All workers on one task queue must register the <b>same</b> workflows and activities.",
    "You can split workflows and activities into different workers/queues (e.g. a GPU "
    "worker for a " + c("transcode") + " queue). Set " + c("taskQueue") + " in "
    + c("proxyActivities") + " options to route activities.",
    "If no worker is running, nothing fails &mdash; tasks wait in the queue until one starts.",
])

h1("9. Clients")
h2("9.1 Connecting")
code("""
import { Connection, Client } from '@temporalio/client';

const connection = await Connection.connect({ address: 'localhost:7233' });
const client = new Client({ connection, namespace: 'default' });
// Create ONE client per process and reuse it (e.g. export from a module).
""")
h2("9.2 Starting workflows")
code("""
import { invoiceWorkflow } from './workflows';
import { defineSearchAttributeKey, SearchAttributeType } from '@temporalio/common';

// Register first (CLI):
//   temporal operator search-attribute create --name CustomerId --type Keyword
const CustomerId = defineSearchAttributeKey('CustomerId', SearchAttributeType.KEYWORD);

// start: returns immediately with a handle
const handle = await client.workflow.start(invoiceWorkflow, {
  taskQueue: 'orders',
  workflowId: `invoice-${invoiceId}`,          // business ID = natural dedup
  args: [{ customerEmail: 'a@b.com', amountUsd: 120, currency: 'EUR' }],
  workflowExecutionTimeout: '30 days',          // optional hard cap
  memo: { createdBy: 'billing-api' },           // unindexed metadata
  typedSearchAttributes: [{ key: CustomerId, value: 'c-42' }],   // indexed
});

// execute: start + wait for the result
const amount = await client.workflow.execute(invoiceWorkflow, {
  taskQueue: 'orders', workflowId: `invoice-${invoiceId}`, args: [input],
});
""")
h2("9.3 Working with existing executions")
code("""
const handle = client.workflow.getHandle('invoice-123');   // no network call yet

const result = await handle.result();          // waits for completion
const desc   = await handle.describe();        // status, start time, memo, ...
console.log(desc.status.name);                 // RUNNING | COMPLETED | FAILED | ...

await handle.cancel();                         // graceful: raises CancelledFailure inside
await handle.terminate('bad data');            // immediate hard stop, no cleanup

// List with a visibility query
for await (const wf of client.workflow.list({
  query: `WorkflowType = 'invoiceWorkflow' AND ExecutionStatus = 'Running'`,
})) {
  console.log(wf.workflowId, wf.startTime);
}
""")
h2("9.4 Workflow ID policies")
table([
    ["Option", "Values and effect"],
    [c("workflowIdReusePolicy"), "What happens when a <b>closed</b> run with the same ID "
     "exists: ALLOW_DUPLICATE (default), ALLOW_DUPLICATE_FAILED_ONLY, REJECT_DUPLICATE."],
    [c("workflowIdConflictPolicy"), "What happens when a <b>running</b> run with the same ID "
     "exists: FAIL (default, throws WorkflowExecutionAlreadyStartedError), USE_EXISTING, "
     "TERMINATE_EXISTING."],
], [50 * mm, 120 * mm])

h1("10. First Run: Hello World End to End")
p("Put everything together and watch the runtime flow from Chapter 2 happen for real.")
code("""
// src/shared.ts
export const TASK_QUEUE = 'hello-tq';

// src/activities.ts
export async function greet(name: string): Promise<string> {
  return `Hello, ${name}!`;
}

// src/workflows.ts
import { proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';
const { greet } = proxyActivities<typeof activities>({ startToCloseTimeout: '1 minute' });

export async function greetingWorkflow(name: string): Promise<string> {
  return await greet(name);
}

// src/client.ts
import { Connection, Client } from '@temporalio/client';
import { greetingWorkflow } from './workflows';
import { TASK_QUEUE } from './shared';

async function run() {
  const client = new Client({ connection: await Connection.connect() });
  const handle = await client.workflow.start(greetingWorkflow, {
    taskQueue: TASK_QUEUE, args: ['Temporal'], workflowId: 'hello-' + Date.now(),
  });
  console.log('Started', handle.workflowId);
  console.log(await handle.result());
}
run().catch((e) => { console.error(e); process.exit(1); });
""", "Four small files (worker.ts is the one from Chapter 8)")
code("""
temporal server start-dev      # terminal 1
npm run worker                 # terminal 2
npm run client                 # terminal 3
# -> Started hello-1727512345678
# -> Hello, Temporal!
""", "Run")
h2("10.1 Reading the event history")
p("Open " + c("http://localhost:8233") + ", click the workflow, and look at the history "
  "(or run " + c("temporal workflow show -w hello-...") + "):")
table([
    ["#", "Event", "Meaning"],
    ["1", "WorkflowExecutionStarted", "Client call recorded with args and task queue."],
    ["2-4", "WorkflowTask Scheduled/Started/Completed", "Worker ran code until "
     + c("await greet()") + "; returned a ScheduleActivity command."],
    ["5", "ActivityTaskScheduled", "Activity task placed on the queue."],
    ["6", "ActivityTaskStarted", "Worker picked it up (written with the completion)."],
    ["7", "ActivityTaskCompleted", "Result \"Hello, Temporal!\" stored."],
    ["8-10", "WorkflowTask Scheduled/Started/Completed", "Worker resumed the workflow with "
     "the result; it returned."],
    ["11", "WorkflowExecutionCompleted", "Final result stored."],
], [14 * mm, 62 * mm, 94 * mm])
h2("10.2 Prove durability")
steps([
    "Change the workflow to " + c("await sleep('1 minute')") + " between two activity calls.",
    "Start it, then kill the worker (Ctrl+C) while it sleeps.",
    "Wait past the minute, then restart the worker.",
    "The workflow continues immediately after the sleep; the first activity is <b>not</b> "
    "executed again. That is replay in action.",
])

# =========================================================================
part("Part III &mdash; Workflow Features")
# =========================================================================
h1("11. Signals, Queries &amp; Updates")
table([
    ["Message", "Direction", "Can change state?", "Returns value?", "Needs running worker?"],
    ["<b>Signal</b>", "into workflow", "Yes", "No (fire &amp; forget)", "No (buffered)"],
    ["<b>Query</b>", "read from workflow", "No (read-only)", "Yes", "Yes"],
    ["<b>Update</b>", "into workflow", "Yes", "Yes (waits for handler)", "Yes"],
], [22 * mm, 32 * mm, 32 * mm, 42 * mm, 42 * mm])
ex_cart("11.1")

h1("12. Timers &amp; Schedules")
h2("12.1 Durable timers")
code("""
import { sleep, condition } from '@temporalio/workflow';

await sleep('30 days');                  // survives restarts; zero cost while waiting
await sleep(5000);                       // milliseconds also accepted

// Wait for a signal OR a timeout
const approved = await condition(() => approvedBy !== undefined, '48 hours');
if (!approved) { /* escalate */ }

// Timer vs activity race
const result = await Promise.race([
  slowActivity(),
  sleep('10 minutes').then(() => 'TIMED_OUT' as const),
]);
""")
h2("12.2 Schedules (replacement for cron)")
code("""
import { ScheduleOverlapPolicy } from '@temporalio/client';

await client.schedule.create({
  scheduleId: 'daily-sales-report',
  spec: {
    calendars: [{ hour: 2, minute: 0 }],     // or cronExpressions: ['0 2 * * *']
    // intervals: [{ every: '15 minutes' }],
  },
  action: {
    type: 'startWorkflow',
    workflowType: reportWorkflow,
    taskQueue: 'reports',
    args: [{ region: 'EU' }],
  },
  policies: { overlap: ScheduleOverlapPolicy.SKIP, catchupWindow: '1 hour' },
});

const sched = client.schedule.getHandle('daily-sales-report');
await sched.trigger();                        // run now
await sched.pause('maintenance window');
await sched.unpause();
await sched.delete();
""")
code("""
temporal schedule list
temporal schedule describe --schedule-id daily-sales-report
temporal schedule trigger  --schedule-id daily-sales-report
""", "CLI equivalents")

ex_trial("12.3")
ex_reports("12.4")

h1("13. Error Handling, Retries &amp; Timeouts")
h2("13.1 Activity timeouts")
table([
    ["Timeout", "What it limits", "Guidance"],
    [c("startToCloseTimeout"), "One attempt of the activity.",
     "<b>Always set</b> (or scheduleToClose). Slightly above worst-case run time."],
    [c("scheduleToCloseTimeout"), "Whole activity incl. all retries.",
     "Use to bound total effort, e.g. '10 minutes'."],
    [c("scheduleToStartTimeout"), "Time waiting in the queue.",
     "Rarely needed; for routing to a fallback queue."],
    [c("heartbeatTimeout"), "Max gap between heartbeats.",
     "Set for long activities so crashes are detected fast."],
], [44 * mm, 52 * mm, 74 * mm])
h2("13.2 Retry policy")
code("""
const { chargeCard } = proxyActivities<typeof activities>({
  startToCloseTimeout: '20 seconds',
  retry: {
    initialInterval: '1 second',     // first retry delay
    backoffCoefficient: 2,           // 1s, 2s, 4s, 8s ...
    maximumInterval: '1 minute',     // cap per-retry delay
    maximumAttempts: 10,             // 0 or unset = unlimited
    nonRetryableErrorTypes: ['CardDeclined', 'InvalidAmount'],
  },
});
""")
h2("13.3 Throwing errors from activities")
code("""
import { ApplicationFailure } from '@temporalio/activity';

export async function chargeCard(orderId: string, cents: number): Promise<string> {
  if (cents <= 0) {
    throw ApplicationFailure.nonRetryable('Amount must be positive', 'InvalidAmount');
  }
  const r = await gateway.charge({ idempotencyKey: orderId, cents });
  if (r.status === 'declined') {
    throw ApplicationFailure.create({
      message: 'Card declined', type: 'CardDeclined', nonRetryable: true,
      details: [{ reason: r.reason }],
    });
  }
  if (r.status === 'rate_limited') {
    throw ApplicationFailure.create({         // retryable, custom delay
      message: 'Rate limited', nextRetryDelay: '30 seconds',
    });
  }
  return r.transactionId;          // network errors etc. just throw -> retried
}
""")
h2("13.4 Catching errors in workflows")
code("""
import { ActivityFailure, ApplicationFailure } from '@temporalio/workflow';

try {
  await chargeCard(orderId, cents);
} catch (err) {
  if (err instanceof ActivityFailure && err.cause instanceof ApplicationFailure) {
    if (err.cause.type === 'CardDeclined') {
      await sendEmail(email, 'Your card was declined');
      return 'DECLINED';
    }
  }
  throw err;   // anything else: fail the workflow
}
""")
table([
    ["Failure class", "When you see it"],
    [c("ActivityFailure"), "Wrapper when an activity finally fails; " + c(".cause") +
     " holds the reason."],
    [c("ApplicationFailure"), "Your own business error (from activity or workflow)."],
    [c("TimeoutFailure"), "An activity/child timed out (" + c("timeoutType") + " says which)."],
    [c("CancelledFailure"), "Scope or workflow was cancelled."],
    [c("ChildWorkflowFailure"), "A child workflow failed; " + c(".cause") + " has details."],
    [c("WorkflowFailedError"), "(Client side) thrown by " + c("handle.result()") +
     " when the workflow failed."],
], [45 * mm, 125 * mm])
warn("In a <b>workflow</b>, throwing a plain " + c("Error") + " does NOT fail the execution "
     "&mdash; it fails the workflow <i>task</i>, which is retried forever (so you can deploy a "
     "fix). To deliberately fail the workflow, throw " + c("ApplicationFailure") + ".")

ex_loan("13.5")

h1("14. Cancellation")
p("Cancellation is cooperative. " + c("handle.cancel()") + " raises a "
  + c("CancelledFailure") + " at the workflow's current " + c("await") + "; the workflow "
  "can clean up before exiting.")
code("""
import { CancellationScope, isCancellation, proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';

const { provisionVm, deleteVm, processData } = proxyActivities<typeof activities>({
  startToCloseTimeout: '10 minutes', heartbeatTimeout: '30 seconds',
});

export async function dataJobWorkflow(jobId: string): Promise<void> {
  const vmId = await provisionVm(jobId);
  try {
    await processData(vmId);
  } catch (err) {
    if (isCancellation(err)) console.log('Job cancelled, cleaning up');
    throw err;
  } finally {
    // Cleanup must run even though the workflow is being cancelled
    await CancellationScope.nonCancellable(() => deleteVm(vmId));
  }
}

// Time-box part of a workflow
await CancellationScope.withTimeout('5 minutes', () => processData(vmId));

// Cancel one branch manually
const scope = new CancellationScope();
const p = scope.run(() => processData(vmId));
scope.cancel();
""")
p("<b>Activities</b> only learn about cancellation through heartbeats: call "
  + c("heartbeat()") + " regularly and use " + c("cancellationSignal()") + " or "
  + c("await cancelled()") + " to stop work.")

ex_video("14.1")

h1("15. Child Workflows, Continue-As-New &amp; Fan-out")
h2("15.1 Child workflows")
code("""
import { executeChild, startChild, ParentClosePolicy } from '@temporalio/workflow';

export async function onboardingWorkflow(companyId: string, userIds: string[]) {
  // Wait for all children (each is its own execution with its own history)
  await Promise.all(userIds.map((uid) =>
    executeChild(onboardUserWorkflow, {
      workflowId: `onboard-${companyId}-${uid}`,
      args: [uid],
    })));

  // Start a child that outlives the parent
  await startChild(auditWorkflow, {
    workflowId: `audit-${companyId}`, args: [companyId],
    parentClosePolicy: ParentClosePolicy.ABANDON,
  });
}
""")
p("Use children to partition big work (each child has its own 50K-event history limit), "
  "to reuse workflows, or to give a sub-process its own ID and lifecycle.")
h2("15.2 Continue-As-New")
p("A single execution's history is limited (warnings at ~10K events, hard limit ~50K events "
  "/ 50 MB). Long-running or looping workflows should periodically restart themselves with "
  "fresh history, carrying state forward as arguments:")
code("""
import { continueAsNew, workflowInfo, condition, allHandlersFinished }
  from '@temporalio/workflow';

export async function accountWorkflow(state: AccountState): Promise<void> {
  setupHandlers(state);                            // signals mutate state
  while (!workflowInfo().continueAsNewSuggested) {
    await condition(() => state.pending.length > 0, '1 hour');
    await processPending(state);
  }
  await condition(allHandlersFinished);            // don't drop in-flight signals
  await continueAsNew<typeof accountWorkflow>(state);
}
""")
h2("15.3 Batch fan-out with bounded concurrency")
code("""
export async function batchWorkflow(ids: string[]): Promise<number> {
  const CHUNK = 50;
  let ok = 0;
  for (let i = 0; i < ids.length; i += CHUNK) {
    const results = await Promise.allSettled(
      ids.slice(i, i + CHUNK).map((id) => processItem(id)));
    ok += results.filter((r) => r.status === 'fulfilled').length;
  }
  return ok;
}
// For 10K+ items: fan out to child workflows, or continue-as-new every N chunks.
""")

# =========================================================================
ex_onboarding("15.4")
ex_loyalty("15.5")
ex_campaign("15.6")

part("Part IV &mdash; Common Patterns")
# =========================================================================
h1("16. Patterns Cookbook")
ex_trip("16.1")
ex_expense("16.2")
ex_kyc("16.3")
ex_review("16.4")

h2("16.5 Entity workflow (one workflow per long-lived object)")
p("Model a customer, device or subscription as a workflow with ID "
  + c("subscription-{id}") + ". Signals/updates change it, queries read it, a loop with "
  + c("condition") + " waits for events, and continue-as-new keeps history small "
  "(Chapter 15.2 and the loyalty example in 15.5). Monthly billing becomes:")
code("""
export async function subscriptionWorkflow(s: Sub): Promise<void> {
  setHandler(cancelSub, () => { s.cancelled = true; });
  for (let i = 0; i < 12 && !s.cancelled; i++) {
    await chargeMonthly(s.customerId, s.plan);
    await condition(() => s.cancelled, '30 days');   // sleep, but wake on cancel
  }
  if (!s.cancelled) await continueAsNew<typeof subscriptionWorkflow>(s);
}
""")
h2("16.6 Idempotency checklist")
bullets([
    "Use business IDs as Workflow IDs " + c("order-{id}") + " &mdash; duplicate starts are "
    "rejected by the server.",
    "Pass an idempotency key (workflowId or " + c("workflowId + activityId") + ") to "
    "payment and other external APIs.",
    "Use upserts / " + c("ON CONFLICT DO NOTHING") + " in database activities.",
])

# =========================================================================
part("Part V &mdash; Production Readiness")
# =========================================================================
h1("17. Versioning Workflow Code")
p("Running executions replay using the <i>new</i> code you deploy. If the new code issues "
  "different commands than recorded in history, the worker raises a "
  + c("DeterminismViolationError") + " and the workflow task gets stuck.")
table([
    ["Safe changes", "Unsafe without versioning"],
    ["Activity implementation code", "Adding/removing/reordering activity calls"],
    ["Timeouts and retry policies", "Adding/removing timers (sleep) or child workflows"],
    ["Adding new signal/query/update handlers", "Changing activity type names"],
    ["Logging", "Changing branching that alters which commands run"],
], [85 * mm, 85 * mm])
h2("17.1 Patching")
code("""
import { patched, deprecatePatch } from '@temporalio/workflow';

export async function orderWorkflow(order: Order) {
  await reserveInventory(order);
  if (patched('fraud-check-v1')) {
    await fraudCheck(order);          // new executions (and new replays) run this
  }
  await chargeCard(order);            // old executions skip it on replay
}

// Later, once NO execution started before the patch is still running:
//   1. replace patched(...) with deprecatePatch('fraud-check-v1') and keep the new code
//   2. after those finish too, delete the deprecatePatch call entirely
""")
h2("17.2 Other strategies")
bullets([
    "<b>New workflow type</b>: copy to " + c("orderWorkflowV2") + ", route new starts to it, "
    "let old ones drain.",
    "<b>Worker Versioning</b>: tag workers with a build ID/deployment version so executions "
    "stay pinned to the code they started on.",
    "<b>Replay tests</b> in CI catch non-determinism before deploy (Chapter 18.4).",
])

ex_versioning("17.3")

h1("18. Testing")
h2("18.1 Setup: Node's test runner + tsx")
p("No extra framework needed. Add " + c('"test": "node --import tsx --test test/*.test.ts"')
  + " to package.json. The time-skipping test server is downloaded automatically on the "
  "first run.")
h2("18.2 Unit-test activities")
code("""
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { MockActivityEnvironment } from '@temporalio/testing';
import { chargeCard } from '../src/activities';

test('rejects negative amounts', async () => {
  const env = new MockActivityEnvironment({ attempt: 1 });
  await assert.rejects(env.run(chargeCard, 'o-1', -5), /positive/);
});
""")
h2("18.3 Test workflows with time skipping")
p("This is the real test suite of the Part VI order service (all tests pass; the "
  "2-minute approval timeout completes in about 3 seconds):")
code("""
// Run with: node --import tsx --test test/*.test.ts
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { TestWorkflowEnvironment } from '@temporalio/testing';
import { Worker } from '@temporalio/worker';
import { WorkflowFailedError } from '@temporalio/client';
import { ApplicationFailure } from '@temporalio/common';
import { orderWorkflow, approveOrder, getStatus } from '../src/workflows';
import type { OrderInput } from '../src/shared';

let env: TestWorkflowEnvironment;
const calls: string[] = [];

// Mocked activities: record calls instead of touching real systems
const activities = {
  reserveInventory: async (_id: string, sku: string) => {
    calls.push(`reserve:${sku}`);
    if (sku === 'NONE') {
      throw ApplicationFailure.nonRetryable('Out of stock', 'OutOfStock');
    }
  },
  releaseInventory: async () => { calls.push('release'); },
  chargePayment: async (id: string) => { calls.push('charge'); return `txn-${id}`; },
  refundPayment: async () => { calls.push('refund'); },
  shipOrder: async (id: string) => { calls.push('ship'); return `TRACK-${id}`; },
  sendEmail: async () => { calls.push('email'); },
};

const order = (over: Partial<OrderInput> = {}): OrderInput => ({
  orderId: `o-${Math.random().toString(36).slice(2, 8)}`,
  customerEmail: 'a@b.com', sku: 'BOOK', quantity: 1, amount: 20, ...over,
});

async function withWorker<T>(fn: () => Promise<T>): Promise<T> {
  const worker = await Worker.create({
    connection: env.nativeConnection,
    taskQueue: 'test',
    workflowsPath: require.resolve('../src/workflows'),
    activities,
  });
  return worker.runUntil(fn);
}

before(async () => { env = await TestWorkflowEnvironment.createTimeSkipping(); });
after(async () => { await env?.teardown(); });

test('small order ships without approval', async () => {
  calls.length = 0;
  const input = order();
  const result = await withWorker(() => env.client.workflow.execute(orderWorkflow, {
    workflowId: input.orderId, taskQueue: 'test', args: [input],
  }));
  assert.equal(result, `TRACK-${input.orderId}`);
  assert.deepEqual(calls, ['reserve:BOOK', 'charge', 'ship', 'email']);
});

test('large order auto-cancels after 2 min without approval', async () => {
  calls.length = 0;
  const input = order({ amount: 5000 });
  const started = Date.now();
  const result = await withWorker(() => env.client.workflow.execute(orderWorkflow, {
    workflowId: input.orderId, taskQueue: 'test', args: [input],
  }));
  assert.equal(result, 'CANCELLED');
  assert.ok(Date.now() - started < 30_000, '2-minute timer should be skipped');
  assert.deepEqual(calls, ['email']);
});

test('large order ships after approval signal', async () => {
  calls.length = 0;
  const input = order({ amount: 5000 });
  await withWorker(async () => {
    const handle = await env.client.workflow.start(orderWorkflow, {
      workflowId: input.orderId, taskQueue: 'test', args: [input],
    });
    await env.sleep('30 seconds');                        // advance the test clock
    assert.equal(await handle.query(getStatus), 'AWAITING_APPROVAL');
    await handle.signal(approveOrder, 'manager');
    assert.equal(await handle.result(), `TRACK-${input.orderId}`);
  });
});
""", "test/order.test.ts (excerpt)")
code("""
# tests 4, pass 4, fail 0
#  - small order ships without approval
#  - large order auto-cancels after 2 min without approval
#  - large order ships after approval signal
#  - out-of-stock order fails without compensation
""", "npm test")
h2("18.4 Replay tests (catch non-determinism)")
code("""
import { test } from 'node:test';
import { Connection, Client } from '@temporalio/client';
import { Worker } from '@temporalio/worker';

// Export real histories:  temporal workflow show -w order-123 --output json > h.json
test('new code replays old history', async () => {
  const client = new Client({ connection: await Connection.connect() });
  const history = await client.workflow.getHandle('order-123').fetchHistory();
  await Worker.runReplayHistory(
    { workflowsPath: require.resolve('../src/workflows') }, history);
  // throws DeterminismViolationError if the change is incompatible
});
""")

ex_testing("18.5")

h1("19. Observability &amp; Debugging")
h2("19.1 Web UI")
bullets([
    "Filter executions by type, status, ID or search attributes.",
    "Event history (timeline / compact / JSON), inputs and outputs of every activity.",
    "Pending activities with attempt count and last failure &mdash; first place to look "
    "when something seems stuck.",
    "Send signals, cancel, terminate and reset from the UI.",
])
h2("19.2 Logging")
code("""
// workflows: replay-aware, includes workflowId/runId automatically
import { log } from '@temporalio/workflow';
log.info('Charging', { amount });

// activities: includes activity metadata automatically
import { log } from '@temporalio/activity';
log.warn('Slow gateway', { ms: 3200 });

// worker process: route SDK logs to your logger (winston/pino adapter possible)
Runtime.install({ logger: new DefaultLogger('INFO', (entry) => console.log(entry)) });
""")
h2("19.3 Metrics &amp; tracing")
code("""
import { Runtime } from '@temporalio/worker';
Runtime.install({
  telemetryOptions: {
    metrics: { prometheus: { bindAddress: '0.0.0.0:9464' } },  // scrape /metrics
  },
});
// Tracing: @temporalio/interceptors-opentelemetry adds spans for client, workflow
// and activity calls. Key metrics: schedule-to-start latency, task slots used,
// activity failures, workflow task failures.
""")
h2("19.4 Debugging checklist")
table([
    ["Symptom", "Likely cause / fix"],
    ["Workflow stays Running, nothing happens", "No worker on that task queue/namespace. "
     "Check the UI \"Workers\" tab and the task queue name spelling."],
    ["Activity attempt count keeps rising", "Activity throws each time. Read "
     "\"last failure\" in the UI; add nonRetryable errors or fix the bug."],
    ["WorkflowTaskFailed repeated in history", "Workflow code threw a plain Error, or "
     "non-determinism after a deploy. Fix code and redeploy; it resumes."],
    [c("DeterminismViolationError"), "Code change without " + c("patched()") + ". Roll "
     "back, or patch, or reset the execution."],
    ["Bundling error: Module not found 'fs'/'crypto'", "A Node-only package imported "
     "(directly or transitively) from workflows.ts. Move to activity, use "
     + c("import type") + "."],
    ["ActivityFailure: TimeoutFailure START_TO_CLOSE", "Activity slower than "
     + c("startToCloseTimeout") + ", or worker died mid-activity."],
], [58 * mm, 112 * mm])

h1("20. Deployment")
h2("20.1 Pre-bundle workflow code")
p("Bundling at worker startup takes seconds and needs webpack at runtime. For production, "
  "bundle at build time:")
code("""
// scripts/bundle.ts
import { bundleWorkflowCode } from '@temporalio/worker';
import { writeFile } from 'fs/promises';
import path from 'path';

async function bundle() {
  const { code } = await bundleWorkflowCode({
    workflowsPath: require.resolve('../src/workflows'),
  });
  await writeFile(path.join(__dirname, '../workflow-bundle.js'), code);
}
bundle();

// worker.ts (production)
const worker = await Worker.create({
  ...options,
  workflowBundle: { codePath: require.resolve('../workflow-bundle.js') },
});
""")
h2("20.2 Dockerfile")
code("""
# glibc base image required by the Temporal worker - do NOT use alpine
FROM node:22-bookworm-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build && npx tsx scripts/bundle.ts && npm prune --omit=dev
ENV NODE_ENV=production
CMD ["node", "lib/worker.js"]
""")
h2("20.3 Connecting to Temporal Cloud")
code("""
// API key authentication
const connection = await NativeConnection.connect({    // Connection.connect for clients
  // e.g. <region>.<cloud>.api.temporal.io:7233
  address: process.env.TEMPORAL_ADDRESS!,
  tls: true,
  apiKey: process.env.TEMPORAL_API_KEY!,
});

// mTLS authentication
import fs from 'fs';
const connection = await NativeConnection.connect({
  address: 'my-ns.a1b2c.tmprl.cloud:7233',
  tls: { clientCertPair: {
    crt: fs.readFileSync(process.env.TEMPORAL_CLIENT_CERT_PATH!),
    key: fs.readFileSync(process.env.TEMPORAL_CLIENT_KEY_PATH!),
  } },
});
// namespace: 'my-ns.a1b2c' in Worker.create / new Client(...)
""")
warn("Never commit API keys or certificates. Load them from environment variables or a "
     "secrets manager.")
h2("20.4 Scaling &amp; operations")
bullets([
    "Scale workers horizontally; watch <b>schedule-to-start latency</b> to know when you need "
    "more.",
    "Tune " + c("maxConcurrentActivityTaskExecutions") + " to what your downstream systems "
    "can handle.",
    "Deploy with rolling restarts; " + c("shutdownGraceTime") + " lets activities finish.",
    "Keep payloads small (&lt; 2 MB each; aim for KBs). Store files in S3/DB and pass keys.",
    "Encrypt sensitive payloads with a custom <b>PayloadCodec</b> passed as "
    + c("dataConverter: { payloadCodecs: [...] }") + " to both Client and Worker.",
    "Separate task queues for workloads with different scaling or resource needs.",
])

# =========================================================================
part("Part VI &mdash; End-to-End Project: Order Service")
ANNOTATE.update(callouts.TEMPORAL)
# =========================================================================
h1("21. Building an Order-Processing Service")
p("A complete, runnable service tying together everything: an Express HTTP API uses the "
  "Temporal Client; a Worker runs an order workflow with manual approval for large orders, "
  "customer cancellation, status queries, retries on a flaky payment gateway and saga "
  "compensation.")
table([
    ["Endpoint", "Temporal operation"],
    [c("POST /orders"), c("client.workflow.start(orderWorkflow)")],
    [c("GET /orders/:id"), c("handle.query(getStatus)") + " + " + c("handle.describe()")],
    [c("POST /orders/:id/approve"), c("handle.signal(approveOrder, approver)")],
    [c("POST /orders/:id/cancel"), c("handle.signal(cancelOrder)")],
    [c("GET /orders/:id/result"), c("handle.result()")],
], [55 * mm, 115 * mm])
h2("21.1 Install")
code("""
mkdir order-service && cd order-service && npm init -y
npm install @temporalio/client @temporalio/worker @temporalio/workflow \\
            @temporalio/activity express
npm install -D typescript tsx @types/node @types/express @temporalio/testing
# tsconfig.json: the one from Chapter 4.2 (module/moduleResolution "nodenext")
""")
code("""
// src/shared.ts
export const TASK_QUEUE = 'orders';

export interface OrderInput {
  orderId: string;
  customerEmail: string;
  sku: string;
  quantity: number;
  amount: number;          // in dollars
}

export type OrderStatus =
  | 'RECEIVED' | 'AWAITING_APPROVAL' | 'RESERVED' | 'CHARGED'
  | 'SHIPPED' | 'CANCELLED' | 'FAILED';
""", "21.2 Shared definitions")
code("""
// src/activities.ts
import { activityInfo, ApplicationFailure, log } from '@temporalio/activity';

// Fake inventory for the demo (per worker process)
const stock = new Map<string, number>([['BOOK', 10], ['LAPTOP', 2]]);

export async function reserveInventory(orderId: string, sku: string, qty: number) {
  const available = stock.get(sku) ?? 0;
  if (available < qty) {
    throw ApplicationFailure.nonRetryable(`Out of stock: ${sku}`, 'OutOfStock');
  }
  stock.set(sku, available - qty);
  log.info('Inventory reserved', { orderId, sku, qty, left: available - qty });
}

export async function releaseInventory(orderId: string, sku: string, qty: number) {
  stock.set(sku, (stock.get(sku) ?? 0) + qty);
  log.info('Inventory released', { orderId, sku, qty });
}

export async function chargePayment(orderId: string, amount: number): Promise<string> {
  const { attempt } = activityInfo();
  if (attempt < 3) {                       // simulate a flaky gateway
    log.warn('Payment gateway timeout (simulated)', { orderId, attempt });
    throw new Error('Payment gateway timeout');
  }
  log.info('Payment charged', { orderId, amount, attempt });
  return `txn-${orderId}`;
}

export async function refundPayment(txnId: string) {
  log.info('Payment refunded', { txnId });
}

export async function shipOrder(orderId: string): Promise<string> {
  return `TRACK-${orderId.toUpperCase()}`;
}

export async function sendEmail(to: string, message: string) {
  log.info('EMAIL', { to, message });
}
""", "21.3 Activities")
code("""
// src/workflows.ts
import {
  proxyActivities, defineSignal, defineQuery, setHandler, condition, log,
  ApplicationFailure, CancellationScope,
} from '@temporalio/workflow';
import type * as activities from './activities';
import type { OrderInput, OrderStatus } from './shared';

const {
  reserveInventory, releaseInventory, chargePayment, refundPayment, shipOrder, sendEmail,
} = proxyActivities<typeof activities>({
  startToCloseTimeout: '30 seconds',
  retry: { initialInterval: '1 second', backoffCoefficient: 2, maximumAttempts: 5 },
});

export const approveOrder = defineSignal<[string]>('approveOrder');
export const cancelOrder  = defineSignal('cancelOrder');
export const getStatus    = defineQuery<OrderStatus>('getStatus');

const APPROVAL_LIMIT = 1000;

export async function orderWorkflow(input: OrderInput): Promise<string> {
  let status: OrderStatus = 'RECEIVED';
  let approvedBy: string | undefined;
  let cancelled = false;

  setHandler(approveOrder, (user) => { approvedBy = user; });
  setHandler(cancelOrder, () => { cancelled = true; });
  setHandler(getStatus, () => status);

  // 1. Large orders need a human
  if (input.amount > APPROVAL_LIMIT) {
    status = 'AWAITING_APPROVAL';
    const decided = await condition(() => approvedBy !== undefined || cancelled,
                                    '2 minutes');
    if (!decided || cancelled) {
      status = 'CANCELLED';
      await sendEmail(input.customerEmail, `Order ${input.orderId} was not approved`);
      return 'CANCELLED';
    }
    log.info('Order approved', { approvedBy });
  }

  // 2. Saga: each step registers its undo
  const compensations: Array<() => Promise<void>> = [];
  const checkCancelled = () => {
    if (cancelled) throw ApplicationFailure.nonRetryable('Cancelled by customer');
  };

  try {
    await reserveInventory(input.orderId, input.sku, input.quantity);
    status = 'RESERVED';
    compensations.unshift(() => releaseInventory(input.orderId, input.sku,
                                                 input.quantity));
    checkCancelled();

    const txnId = await chargePayment(input.orderId, input.amount);
    status = 'CHARGED';
    compensations.unshift(() => refundPayment(txnId));
    checkCancelled();

    const tracking = await shipOrder(input.orderId);
    status = 'SHIPPED';
    await sendEmail(input.customerEmail, `Order ${input.orderId} shipped: ${tracking}`);
    return tracking;
  } catch (err) {
    status = cancelled ? 'CANCELLED' : 'FAILED';
    await CancellationScope.nonCancellable(async () => {
      for (const undo of compensations) await undo();
      await sendEmail(input.customerEmail,
                      `Order ${input.orderId} ${status.toLowerCase()}`);
    });
    if (cancelled) return 'CANCELLED';
    throw err;
  }
}
""", "21.4 Workflow")
code("""
// src/worker.ts
import { NativeConnection, Worker } from '@temporalio/worker';
import * as activities from './activities';
import { TASK_QUEUE } from './shared';

async function run() {
  const connection = await NativeConnection.connect({
    address: process.env.TEMPORAL_ADDRESS ?? 'localhost:7233',
  });
  const worker = await Worker.create({
    connection,
    namespace: process.env.TEMPORAL_NAMESPACE ?? 'default',
    taskQueue: TASK_QUEUE,
    workflowsPath: require.resolve('./workflows'),
    activities,
  });
  console.log('Order worker started');
  await worker.run();
}
run().catch((err) => { console.error(err); process.exit(1); });
""", "21.5 Worker")
code("""
// src/api.ts
import express, { Request, Response, NextFunction } from 'express';
import {
  Connection, Client, WorkflowNotFoundError, WorkflowFailedError,
} from '@temporalio/client';
import { orderWorkflow, approveOrder, cancelOrder, getStatus } from './workflows';
import { TASK_QUEUE, OrderInput } from './shared';

// Express 5 forwards rejected promises from async handlers to the error middleware

async function main() {
  const connection = await Connection.connect({
    address: process.env.TEMPORAL_ADDRESS ?? 'localhost:7233',
  });
  const client = new Client({ connection, namespace: 'default' });
  const app = express();
  app.use(express.json());

  app.post('/orders', async (req, res) => {
    const input: OrderInput = { orderId: `ord-${Date.now()}`, ...req.body };
    const handle = await client.workflow.start(orderWorkflow, {
      taskQueue: TASK_QUEUE,
      workflowId: `order-${input.orderId}`,
      args: [input],
    });
    res.status(202).json({ workflowId: handle.workflowId });
  });

  app.get('/orders/:id', async (req, res) => {
    const handle = client.workflow.getHandle(req.params.id);
    const desc = await handle.describe();
    // Queries are answered by a worker; without one they would hang, so cap the wait
    const status = await connection
      .withDeadline(Date.now() + 5_000, () => handle.query(getStatus))
      .catch(() => 'UNKNOWN (no worker available)');
    res.json({ workflowId: req.params.id, status, execution: desc.status.name });
  });

  app.post('/orders/:id/approve', async (req, res) => {
    await client.workflow.getHandle(req.params.id)
      .signal(approveOrder, req.body.approver ?? 'admin');
    res.sendStatus(202);
  });

  app.post('/orders/:id/cancel', async (req, res) => {
    await client.workflow.getHandle(req.params.id).signal(cancelOrder);
    res.sendStatus(202);
  });

  app.get('/orders/:id/result', async (req, res) => {
    const result = await client.workflow.getHandle(req.params.id).result();
    res.json({ result });
  });

  app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
    if (err instanceof WorkflowNotFoundError) {
      return res.status(404).json({ error: 'not found' });
    }
    if (err instanceof WorkflowFailedError) {          // business failure, not a crash
      let cause: Error | undefined = err.cause;         // unwrap ActivityFailure etc.
      while (cause?.cause instanceof Error) cause = cause.cause;
      return res.status(422).json({ status: 'FAILED', reason: cause?.message });
    }
    res.status(500).json({ error: String(err) });
  });

  app.listen(3000, () => console.log('API on http://localhost:3000'));
}
main().catch((err) => { console.error(err); process.exit(1); });
""", "21.6 HTTP API")
h2("21.7 Run the whole system")
code("""
temporal server start-dev           # terminal 1 - Temporal Service + UI :8233
npx tsx src/worker.ts               # terminal 2 - Worker
npx tsx src/api.ts                  # terminal 3 - HTTP API :3000
# no CLI installed? terminal 1 alternative: npx tsx scripts/dev-server.ts (3.4a)
""")
p("On Windows PowerShell use " + c("curl.exe") + " (not the " + c("curl") + " alias) or "
  "any REST client.")
code("""
# A) Small order - completes automatically (payment succeeds on attempt 3)
curl -X POST localhost:3000/orders -H "Content-Type: application/json" \\
  -d '{"customerEmail":"ann@example.com","sku":"BOOK","quantity":1,"amount":25}'
# {"workflowId":"order-ord-1727512345678"}

curl localhost:3000/orders/order-ord-1727512345678
# {"status":"SHIPPED","execution":"COMPLETED", ...}

# B) Large order - waits for approval
curl -X POST localhost:3000/orders -H "Content-Type: application/json" \\
  -d '{"customerEmail":"bob@example.com","sku":"LAPTOP","quantity":1,"amount":2400}'
curl localhost:3000/orders/order-ord-...            # "AWAITING_APPROVAL"
curl -X POST localhost:3000/orders/order-ord-.../approve \\
  -H "Content-Type: application/json" -d '{"approver":"manager-jo"}'
curl localhost:3000/orders/order-ord-.../result     # {"result":"TRACK-ORD-..."}

# C) Out of stock - non-retryable failure, workflow FAILED, nothing to compensate
curl -X POST localhost:3000/orders -H "Content-Type: application/json" \\
  -d '{"customerEmail":"cy@example.com","sku":"LAPTOP","quantity":5,"amount":500}'

# D) Approval timeout - large order with no approval for 2 minutes -> CANCELLED
""")
h2("21.8 What to observe")
bullets([
    "<b>Worker logs</b>: two simulated payment timeouts, then success on attempt 3 &mdash; "
    "retries with exponential backoff, no code for it.",
    "<b>Web UI</b>: the chargePayment activity shows attempts; pending approval orders show "
    "a timer and signal events.",
    "<b>Durability</b>: create a large order, stop the worker, approve via the API, restart "
    "the worker &mdash; the signal was buffered and the order completes.",
    "<b>Compensation</b>: send " + c("/cancel") + " while an order is in progress to see "
    "refundPayment then releaseInventory run (reverse order).",
    "<b>Failures are business results</b>: " + c("GET /orders/:id/result") + " for the "
    "out-of-stock order returns <b>422</b> with " + c('"reason":"Out of stock: LAPTOP"')
    + " (root cause unwrapped from the ActivityFailure).",
    "<b>Queries need a worker</b>: with the worker stopped, " + c("GET /orders/:id")
    + " answers after 5 s with " + c('"status":"UNKNOWN (no worker available)"')
    + " instead of hanging (" + c("connection.withDeadline") + ").",
])
h2("21.9 Next steps for this project")
bullets([
    "Replace the in-memory stock with a real database via the activity factory (6.2).",
    "Add tests with " + c("TestWorkflowEnvironment") + " for the approval timeout (18.3).",
    "Pre-bundle and containerize the worker (20.1-20.2); point it at Temporal Cloud (20.3).",
    "Add a " + c("CustomerId") + " search attribute and list a customer's orders.",
])

# =========================================================================
ANNOTATE.clear()
part("Appendices")
# =========================================================================
h1("A. CLI Reference")
code("""
# Server
temporal server start-dev [--db-filename f.db] [--ui-port 8233] [--namespace ns]

# Workflows  (-w = --workflow-id)
temporal workflow start     --type orderWorkflow --task-queue orders -w order-1 \\
                            --input '{"orderId":"1","sku":"BOOK","quantity":1}'
temporal workflow execute   ...same flags...          # start and wait for result
temporal workflow list      --query "ExecutionStatus='Running'"
temporal workflow describe  -w order-1
temporal workflow show      -w order-1 [--output json]  # event history
temporal workflow result    -w order-1
temporal workflow signal    -w order-1 --name approveOrder --input '"alice"'
temporal workflow query     -w order-1 --type getStatus
temporal workflow update execute -w cart-1 --name applyCoupon --input '"SAVE10"'
temporal workflow cancel    -w order-1
temporal workflow terminate -w order-1 --reason "bad input"
temporal workflow reset     -w order-1 --type LastWorkflowTask
temporal workflow stack     -w order-1           # where is the code blocked?

# Task queues, schedules, namespaces
temporal task-queue describe --task-queue orders   # see connected workers
temporal schedule list | describe | trigger | delete --schedule-id X
temporal operator namespace create --namespace orders
""")
h1("B. Troubleshooting Quick Reference")
table([
    ["Error / symptom", "Fix"],
    [c("Connection refused 127.0.0.1:7233"), "Server not running, or wrong "
     + c("address") + ". Start " + c("temporal server start-dev") + "."],
    [c("Namespace default is not found"), "Create it, or pass the right " + c("namespace")
     + " to both Worker and Client."],
    [c("WorkflowExecutionAlreadyStartedError"), "Workflow ID already running. Use a new ID, "
     "or " + c("workflowIdConflictPolicy: 'USE_EXISTING'") + "."],
    [c("Activity function X is not registered"), "Worker's " + c("activities") + " object "
     "lacks that function, or you are running an old worker."],
    [c("Workflow type X not found"), "Workflow not exported from " + c("workflowsPath")
     + ", or a different worker is polling the same queue."],
    ["Workflow bundling fails with Node module errors", "Non-deterministic import in the "
     "workflow file tree; use " + c("import type") + " / move code to activities."],
    ["Worker fails to start on Alpine", "Use a Debian/Ubuntu (glibc) based image."],
    ["Query hangs / times out", "Queries are answered by a worker. Start one, or bound "
     "the call with " + c("connection.withDeadline(Date.now() + 5000, ...)") + "."],
    [c("Failed to load native binding") + " (webpack / swc) on Windows",
     "Seen with " + c("@swc/core") + " 1.16.13 (native cache permission check). Pin "
     + c('"overrides": { "@swc/core": "1.16.2" }') + " in package.json."],
    ["Workflow task fails with " + c("TypeError") + ", workflow keeps running",
     "Plain errors in workflow code fail the <i>task</i>, which is retried. Fix and "
     "redeploy; e.g. " + c("RetryState") + " must be imported from "
     + c("@temporalio/common") + "."],
    ["Deadline passed but no " + c("TimeoutFailure"),
     "Expired between retries: check " + c("ActivityFailure.retryState === 'TIMEOUT'")
     + " (see 16.3)."],
    [c("ts-node") + " / " + c("ts-jest") + " crash with TypeScript 7",
     "TS 7 has no JS API. Use " + c("tsx") + " and " + c("node --test") + " or Vitest."],
    [c("TMPRL1100 / nondeterminism"), "See Chapter 17 &mdash; patch or reset."],
], [68 * mm, 102 * mm])
h1("C. Glossary")
table([
    ["Term", "Definition"],
    ["Activity", "Function that performs side effects; retried by Temporal."],
    ["Command", "Instruction from workflow code to the server (schedule activity, start timer)."],
    ["Continue-As-New", "Completing a run and atomically starting a new one with fresh history."],
    ["Determinism", "Same history &rArr; same commands. Required for replay."],
    ["Event History", "Durable, ordered record of an execution's events."],
    ["Local Activity", "Short activity executed within a workflow task on the same worker."],
    ["Namespace", "Isolation boundary for workflows, queues and settings."],
    ["Replay", "Re-executing workflow code against history to rebuild state."],
    ["Run ID", "Unique ID of one run of a workflow ID (changes on continue-as-new/retry)."],
    ["Saga", "Pattern of undoing completed steps when a later step fails."],
    ["Schedule", "Server-side cron-like trigger that starts workflows."],
    ["Search Attribute", "Indexed field on an execution usable in list queries."],
    ["Signal / Query / Update", "Messages to write / read / read-write a running workflow."],
    ["Task Queue", "Queue by which the server dispatches tasks to workers."],
    ["Worker", "Process hosting workflow and activity code, polling task queues."],
], [40 * mm, 130 * mm])
h2("Further resources")
bullets([
    "Docs: docs.temporal.io/develop/typescript",
    "API reference: typescript.temporal.io",
    "Samples: github.com/temporalio/samples-typescript",
    "Free courses: learn.temporal.io (Temporal 101 / 102 / Versioning, TypeScript track)",
    "Community: community.temporal.io and the Temporal Slack",
])


# =========================================================================
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
    cv.drawString(20 * mm, A4[1] - 12 * mm, "Temporal with Node.js - Complete Tutorial")
    cv.drawRightString(A4[0] - 20 * mm, 10 * mm, f"Page {doc.page}")
    cv.restoreState()


doc = Doc(OUT, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
          topMargin=20 * mm, bottomMargin=18 * mm,
          title="Temporal with Node.js - Complete Tutorial", author="Claude")
doc.multiBuild(list(story), onFirstPage=on_page, onLaterPages=on_page)
print("wrote", OUT)
