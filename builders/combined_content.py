# Content for the Fastify + Temporal companion guide. Executed inside build_combined_tutorial.py.
import callouts_combined

from paths import project
PROJ = project('fastify-temporal-orders')


def pfile(path, caption=None):
    """Embed a project file verbatim (read at build time, never copied by hand)."""
    src = open(os.path.join(PROJ, path), encoding='utf8').read().rstrip('\n')
    code('// ' + path + '\n' + src, caption)


def combined_arch():
    d = Drawing(480, 150)
    lbl = dict(textAnchor="middle", fontSize=7.5, fontName="Helvetica", fillColor=GREY)
    box(d, 0, 70, 72, 50, "HTTP client\nweb, mobile\n(HTTPS JSON)", size=7.6)
    box(d, 92, 60, 102, 70, "Fastify API\nvalidation\nidempotency\nerror mapping",
        fill=NOTE_BG, size=7.6)
    box(d, 252, 65, 90, 60, "Temporal\nService\nhistory, queue", size=7.6)
    box(d, 392, 60, 88, 70, "Worker\norderWorkflow\n+ activities", fill=NOTE_BG, size=7.6)
    box(d, 392, 0, 88, 32, "Payments, stock,\nemail", size=7.4)
    arrow(d, 72, 95, 92, 95, "")
    arrow(d, 194, 108, 252, 108, "")
    d.add(String(223, 113, "start / signal", **lbl))
    arrow(d, 252, 82, 194, 82, "")
    d.add(String(223, 72, "query / result", **lbl))
    arrow(d, 392, 95, 342, 95, "")
    d.add(String(367, 100, "long-poll", **lbl))
    arrow(d, 425, 60, 425, 32, "")
    d.add(String(455, 43, "activities", **lbl))
    return d


# =========================================================================
# TITLE + TOC
# =========================================================================
super(Story, story).append(Spacer(1, 55 * mm))
super(Story, story).append(Paragraph("Fastify + Temporal", ParagraphStyle(
    "T", parent=H1, fontSize=32, leading=38, alignment=TA_CENTER)))
super(Story, story).append(Paragraph("Durable HTTP APIs with Node.js", ParagraphStyle(
    "ST", parent=BODY, fontSize=16, leading=20, alignment=TA_CENTER, textColor=GREY,
    spaceAfter=24)))
super(Story, story).append(Paragraph(
    "A companion to the Fastify and Temporal tutorials: put a fast, validated Fastify API "
    "in front of durable Temporal workflows &mdash; idempotent requests, asynchronous "
    "request-reply, long-polling, signals over HTTP, error mapping, health checks, "
    "end-to-end tests and failure drills.",
    ParagraphStyle("TD", parent=BODY, alignment=TA_CENTER, fontSize=11, leading=16)))
super(Story, story).append(Spacer(1, 30 * mm))
super(Story, story).append(Paragraph(
    "Verified with Fastify 5.12 &middot; @temporalio/* 1.24 &middot; Node.js 24 "
    "&middot; TypeScript 7",
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
part("Part I &mdash; Architecture")
# =========================================================================
h1("1. Why Combine Fastify and Temporal?")
p("Each tool is excellent at one side of the problem. <b>Fastify</b> is the edge: it "
  "validates input, authenticates callers, documents the API and answers in "
  "milliseconds. <b>Temporal</b> is the engine: it runs multi-step business processes "
  "that must finish &mdash; with retries, timers, human approvals and compensation "
  "&mdash; even across crashes and deploys.")
p("An HTTP request should not run a 3-day approval process, and a workflow should not "
  "parse JSON bodies. Put each concern where it belongs:")
table([
    ["Concern", "Lives in", "Why"],
    ["Input validation, auth, rate limits", "Fastify", "Reject bad requests before any "
     "durable work starts"],
    ["API docs (OpenAPI)", "Fastify", "Generated from the same schemas"],
    ["Idempotency", "Both", "Fastify turns the Idempotency-Key into a Workflow ID; "
     "Temporal enforces uniqueness"],
    ["Multi-step process, state", "Temporal workflow", "Durable, replayable, survives "
     "crashes"],
    ["Calls to external systems, retries", "Temporal activities", "Declarative retry "
     "policies, heartbeats, timeouts"],
    ["Waiting (approvals, timers)", "Temporal workflow", "Days-long waits cost nothing"],
    ["Progress / status for clients", "Workflow query, exposed by Fastify", "Single "
     "source of truth"],
    ["Mapping outcomes to HTTP codes", "Fastify error handler", "404 / 422 / 503 in one "
     "place"],
], [52 * mm, 43 * mm, 75 * mm])

h1("2. Architecture")
story.append(combined_arch())
story.append(Spacer(1, 8))
p("The API never executes business steps itself. It only talks to the Temporal Service "
  "through the client (start, signal, query, result). Workers &mdash; a separate "
  "process &mdash; pull tasks and do the work. You can scale, deploy and restart API and "
  "workers independently.")
h2("2.1 Life of an order")
table([
    ["#", "HTTP", "What happens"],
    ["1", c("POST /orders") + " + Idempotency-Key",
     "Schema validation, then " + c("workflow.start()") + " with Workflow ID "
     + c("order-{key}") + ". Returns <b>202</b> + Location immediately."],
    ["2", "&mdash;", "A worker picks up the task and runs the workflow: reserve stock, "
     "charge (with retries), ship, email. Orders over 1000 wait for approval."],
    ["3", c("GET /orders/{id}"), "Describe + workflow query &rarr; business status "
     "(e.g. AWAITING_APPROVAL) and execution status (RUNNING)."],
    ["4", c("POST /orders/{id}/approve"), "Sends a signal. Stored durably even if no worker "
     "is running."],
    ["5", c("GET /orders/{id}/result?waitSeconds=10"), "Long-poll: 200 with the result if it "
     "completes in time, otherwise 202 with the current status."],
    ["6", "&mdash;", "Failure &rarr; 422 with the business reason; unknown ID &rarr; 404; "
     "Temporal down &rarr; 503 + Retry-After."],
], [8 * mm, 58 * mm, 104 * mm])

h1("3. Designing HTTP for Long-Running Work")
h2("3.1 Asynchronous request-reply")
p("A durable process can take seconds or weeks, so the API must not hold the "
  "connection open. The standard pattern: accept the work with <b>202 Accepted</b>, "
  "return a <b>Location</b> to poll, and let clients optionally long-poll for a bounded "
  "time (" + c("waitSeconds") + ", max 30).")
h2("3.2 Mapping Temporal outcomes to HTTP")
table([
    ["Situation", "Temporal signal", "HTTP response"],
    ["Order accepted", c("workflow.start()") + " ok", "202 + Location"],
    ["Same Idempotency-Key again", "USE_EXISTING / REJECT_DUPLICATE",
     "202, same Workflow ID, no new run"],
    ["Status requested", "describe + query", "200 {status, execution}"],
    ["Status while no worker runs", "query exceeds 5 s deadline",
     "200 with status UNKNOWN"],
    ["Result not ready", "RUNNING or long-poll deadline", "202 with current status"],
    ["Completed", c("result()"), "200 {result}"],
    ["Business failure", c("WorkflowFailedError"), "422 + root-cause message"],
    ["Unknown order", c("WorkflowNotFoundError"), "404"],
    ["Temporal unreachable / too slow", "gRPC UNAVAILABLE / DEADLINE_EXCEEDED",
     "503 + Retry-After: 5"],
    ["Invalid input", "&mdash; (never reaches Temporal)", "400"],
], [48 * mm, 60 * mm, 62 * mm])
h2("3.3 Idempotency for free")
p("Clients (and proxies) retry POSTs. Using the " + c("Idempotency-Key") + " header as "
  "the Workflow ID makes Temporal the arbiter: while the order runs, a retry attaches to "
  "the existing run (" + c("USE_EXISTING") + "); after it finished, the server rejects a "
  "second run (" + c("REJECT_DUPLICATE") + ") and the API answers with the same order. "
  "No idempotency table, no race conditions.")

h1("4. Tested With")
p("The complete project in Parts II&ndash;III was type-checked, tested (7 end-to-end "
  "tests) and run live against a Temporal dev server, including the failure drills in "
  "Chapter 11. It lives in " + c("fastify-temporal-orders/") + " next to this PDF.")
table([
    ["Component", "Version", "Notes"],
    ["Node.js", "24.15", "20+ required by Fastify 5"],
    [c("fastify"), "5.12.5", "with sensible, swagger 9.9, swagger-ui 6.1"],
    [c("@fastify/type-provider-typebox"), "6.1.0", "TypeBox 1.x"],
    [c("@temporalio/*"), "1.24.0", "client, worker, workflow, activity, testing"],
    ["Temporal CLI / Server", "1.9.1 / 1.32.0", "dev server"],
    ["TypeScript / tsx", "7.0.2 / 4.23", "run with tsx; tests with " + c("node --test")],
], [62 * mm, 35 * mm, 73 * mm])

# =========================================================================
part("Part II &mdash; Build It")
ANNOTATE.update(callouts_combined.COMBINED)
# =========================================================================
h1("5. Project Setup")
code("""
mkdir fastify-temporal-orders && cd fastify-temporal-orders && npm init -y
npm install fastify fastify-plugin @fastify/sensible @fastify/swagger \\
            @fastify/swagger-ui @fastify/type-provider-typebox close-with-grace \\
            @temporalio/client @temporalio/worker @temporalio/workflow \\
            @temporalio/activity @temporalio/common
npm install -D typescript tsx @types/node pino-pretty @temporalio/testing
""")
code("""
"scripts": {
  "dev-server": "tsx scripts/dev-server.ts",
  "worker": "tsx src/worker.ts",
  "api": "tsx watch src/server.ts",
  "build": "tsc",
  "test": "node --import tsx --test test/*.test.ts"
}
""", "package.json scripts")
code("""
fastify-temporal-orders/
  src/
    shared.ts  activities.ts  workflows.ts  worker.ts   # from the Temporal guide
    plugins/temporal.ts      # Temporal client as a Fastify decorator
    schemas/order.ts         # TypeBox schemas (validation, types, docs)
    routes/orders.ts         # HTTP <-> workflow operations
    routes/health.ts         # readiness incl. Temporal reachability
    app.ts                   # buildApp(): plugins, error mapping, routes
    server.ts                # listen + graceful shutdown
  scripts/dev-server.ts      # Temporal dev server without installing the CLI
  test/orders.test.ts        # HTTP -> workflow end-to-end tests
""", "Layout (tsconfig.json: module / moduleResolution \"nodenext\", as in both guides)")

h1("6. The Workflow Side (Reused)")
p("The workflow, activities and worker are the <b>unchanged</b> files from Part VI of "
  "the Temporal tutorial (explained there line by line). What the API relies on:")
bullets([
    "Task queue " + c("orders") + "; workflow " + c("orderWorkflow(input)") + ".",
    "Signals " + c("approveOrder(approver)") + " and " + c("cancelOrder()") + "; query "
    + c("getStatus") + ".",
    "Orders above 1000 wait up to 2 minutes for approval, then cancel themselves.",
    "Out-of-stock throws a non-retryable " + c("OutOfStock") + " failure; the payment "
    "activity fails twice before succeeding (simulated).",
])
pfile('src/shared.ts')

h1("7. The Temporal Client Plugin")
p("One Temporal client per process, created at boot and shared through a decorator. "
  "The plugin accepts a ready-made client so tests can inject the time-skipping server.")
pfile('src/plugins/temporal.ts')

h1("8. Schemas")
pfile('src/schemas/order.ts')

h1("9. Routes: HTTP to Workflow Operations")
pfile('src/routes/orders.ts')

h1("10. App Builder and Error Mapping")
pfile('src/app.ts')
h2("10.1 Health check and server")
pfile('src/routes/health.ts')
pfile('src/server.ts')

# =========================================================================
part("Part III &mdash; Test and Run")
# =========================================================================
h1("11. End-to-End Tests")
p("The tests drive the real Fastify app with " + c("inject()") + ", which calls the real "
  "Temporal client, which runs the real workflow on a real worker &mdash; only the "
  "activities are mocked. Timers are skipped, so the suite runs in seconds.")
pfile('test/orders.test.ts')
code("""
npm test
# ok  rejects an invalid order with 400
# ok  small order: 202 + Location, then result
# ok  Idempotency-Key returns the same order, even after it finished
# ok  large order waits for approval given over HTTP
# ok  failed order maps to 422 with the business reason
# ok  unknown order maps to 404
# ok  health reports Temporal reachable
# tests 7, pass 7, fail 0
""", "Output")
ANNOTATE.clear()

h1("12. Run It")
code("""
npm run dev-server     # terminal 1 (or: temporal server start-dev), UI :8233
npm run worker         # terminal 2
npm run api            # terminal 3, http://localhost:3000, docs at /docs
""")
p("Real responses from the verification run (Windows: use " + c("curl.exe") + "):")
code("""
# 1. Create with an idempotency key -> 202 + Location
curl -i -X POST localhost:3000/orders -H "Content-Type: application/json" \\
     -H "Idempotency-Key: demo-order-0001" \\
     -d '{"customerEmail":"ann@example.com","sku":"BOOK","quantity":1,"amount":25}'
# HTTP/1.1 202 Accepted
# location: /orders/order-demo-order-0001
# {"workflowId":"order-demo-order-0001","statusUrl":"/orders/order-demo-order-0001"}

# 2. Non-blocking result check while it runs -> 202
curl localhost:3000/orders/order-demo-order-0001/result
# {"workflowId":"order-demo-order-0001","status":"RECEIVED","execution":"RUNNING"}

# 3. Long-poll up to 10 s (payment retries twice, then succeeds) -> 200
curl "localhost:3000/orders/order-demo-order-0001/result?waitSeconds=10"
# {"workflowId":"order-demo-order-0001","result":"TRACK-DEMO-ORDER-0001"}

# 4. Same key again -> same order, no second run
curl -X POST localhost:3000/orders -H "Idempotency-Key: demo-order-0001" ...
# {"workflowId":"order-demo-order-0001","statusUrl":"/orders/order-demo-order-0001"}
""")
code("""
# 5. Large order: long-poll 3 s times out -> 202 with status (took 3 s)
curl "localhost:3000/orders/order-demo-large-0002/result?waitSeconds=3"
# {"workflowId":"order-demo-large-0002","status":"AWAITING_APPROVAL",
#  "execution":"RUNNING"}

# 6. Approve, then wait -> 200
curl -X POST localhost:3000/orders/order-demo-large-0001/approve \\
     -H "Content-Type: application/json" -d '{"approver":"manager-jo"}'
# {"workflowId":"order-demo-large-0001","statusUrl":"/orders/order-demo-large-0001"}
curl "localhost:3000/orders/order-demo-large-0001/result?waitSeconds=20"
# {"workflowId":"order-demo-large-0001","result":"TRACK-DEMO-LARGE-0001"}

# 7. Out of stock -> 422 with the business reason
# {"statusCode":422,"error":"Unprocessable Entity","message":"Out of stock: LAPTOP"}

# 8. Validation and unknown IDs
# 400 {"message":"body/customerEmail must match format \\"email\\"", ...}
# 404 {"message":"Order not found", ...}
# 400 {"message":"params/id must match pattern \\"^order-\\"", ...}
""")

h1("13. Failure Drills")
p("Durability is the point of the combination, so it was tested by breaking things "
  "while the API kept running:")
warn("Two bugs were found only by running these drills: the long-poll timeout surfaced as "
     "500 because the deadline error is wrapped in a " + c("ServiceError") + " (fixed with "
     + c("isGrpcDeadlineError") + "), and order creation hung for 20 s when Temporal was "
     "down (fixed with " + c("withDeadline") + " + 503).")
table([
    ["Drill", "Observed behaviour"],
    ["Kill the worker, then " + c("GET /orders/{id}"),
     "200 after 5 s with " + c('status: "UNKNOWN (no worker available)"') + " &mdash; no "
     "hanging request"],
    ["Worker still down: " + c("POST /approve"),
     "202; the signal is stored by Temporal"],
    ["Restart the worker, long-poll the result",
     "200 " + c("TRACK-DEMO-LARGE-0003") + ": the buffered approval was applied"],
    ["Stop the Temporal Service: " + c("GET /health"),
     "503 " + c('{"status":"degraded"}') + " within 3 s"],
    ["Temporal down: " + c("POST /orders"),
     "Before the fix: <b>500 after 20 s</b> (client retries). After: <b>503 + "
     "Retry-After: 5 in about 5 s</b>"],
    ["Restart Temporal, same API process: " + c("GET /health"),
     "200 &mdash; the client reconnected on its own"],
    ["Cancel an order waiting for approval", "202, then result " + c("CANCELLED")],
], [62 * mm, 108 * mm])


# =========================================================================
part("Part IV &mdash; Production Notes")
# =========================================================================
h1("14. Deployment Topology")
bullets([
    "<b>One image, two commands</b>: " + c("node dist/server.js") + " (API) and "
    + c("node dist/worker.js") + " (worker). Deploy them as separate services.",
    "<b>Scale independently</b>: API replicas by request rate; workers by Temporal "
    "<i>schedule-to-start latency</i> (tasks waiting for a worker).",
    "Use a <b>glibc</b> base image (e.g. " + c("node:22-bookworm-slim") + ") &mdash; the "
    "worker's native core does not run on Alpine.",
    "Pre-bundle workflow code for the worker (Temporal guide, Chapter 20.1).",
    "Same " + c("TEMPORAL_ADDRESS") + " / " + c("TEMPORAL_NAMESPACE") + " (and Cloud "
    "credentials) for API and worker.",
])
note("Running the worker inside the API process is possible for small apps and local "
     "development, but it couples crashes, CPU usage and scaling of both. Keep them "
     "separate in production.")
h1("15. Timeouts, Auth and Observability")
bullets([
    "<b>Align timeouts</b>: Fastify " + c("requestTimeout") + " and your load balancer's idle "
    "timeout must exceed the maximum long-poll (30 s) plus the 5 s query bound.",
    "<b>Authentication</b>: add " + c("@fastify/jwt") + " exactly as in the Fastify tutorial "
    "(Chapter 16) and take the approver from " + c("request.user") + " instead of the "
    "request body, so the audit trail in the workflow history is trustworthy.",
    "<b>Authorization</b>: store the owner in the workflow input and check it before "
    "signalling or exposing status (404 for foreign orders, as in the Tasks API).",
    "<b>Correlation</b>: log the Workflow ID with every request (the POST handler already "
    "does for idempotent replays); the Temporal UI then shows the full history for that "
    "ID.",
    "<b>Metrics</b>: watch API p95 latency, 503 rate and Temporal schedule-to-start "
    "latency together.",
])
h1("16. Checklist")
table([
    ["Item", "Where"],
    ["Validate at the edge; reject before starting workflows", "TypeBox schemas"],
    ["Idempotency-Key &rarr; Workflow ID with USE_EXISTING + REJECT_DUPLICATE",
     c("POST /orders")],
    ["202 + Location; bounded long-poll", c("GET /orders/{id}/result")],
    ["Bound every Temporal call made on a request path", c("connection.withDeadline")],
    ["404 / 422 / 503 mapping in one error handler", c("app.ts")],
    ["Health endpoint checks Temporal reachability", c("GET /health")],
    ["Graceful shutdown: HTTP first, then Temporal connection", c("close-with-grace")],
    ["API and worker deployed and scaled separately", "Deployment"],
    ["End-to-end tests with time skipping", c("test/orders.test.ts")],
], [110 * mm, 60 * mm])

# =========================================================================
part("Appendices")
# =========================================================================
h1("A. Endpoint Reference")
table([
    ["Method &amp; path", "Body / query", "Responses"],
    [c("POST /orders"), "CreateOrder; header " + c("Idempotency-Key") + " (optional)",
     "202 Accepted, 400, 503"],
    [c("GET /orders/{id}"), "&mdash;", "200 OrderView, 404, 503"],
    [c("POST /orders/{id}/approve"), c('{"approver": string}'), "202 Accepted, 404, 503"],
    [c("POST /orders/{id}/cancel"), "&mdash;", "202 Accepted, 404, 503"],
    [c("GET /orders/{id}/result"), c("waitSeconds") + " 0&ndash;30 (default 0)",
     "200 ResultReply, 202 OrderView, 404, 422, 503"],
    [c("GET /health"), "&mdash;", "200 reachable, 503 degraded"],
    [c("GET /docs"), "&mdash;", "Swagger UI (JSON at /docs/json)"],
], [52 * mm, 60 * mm, 58 * mm])
h1("B. Troubleshooting")
table([
    ["Symptom", "Cause / fix"],
    ["Long-poll returns 500 instead of 202", "Deadline error is wrapped in "
     + c("ServiceError") + ". Use " + c("isGrpcDeadlineError(err)") + ", not "
     + c("err.code") + "."],
    ["POST hangs ~20 s when Temporal is down", "Client retries internally. Wrap "
     + c("start()") + " in " + c("withDeadline") + " and map to 503."],
    ["GET status hangs", "Query with no worker running. Bound it with "
     + c("withDeadline") + " and return UNKNOWN."],
    ["Idempotent POST starts a second run after completion", "Default reuse policy allows "
     "duplicates. Set " + c("workflowIdReusePolicy: 'REJECT_DUPLICATE'") + "."],
    [c("WorkflowExecutionAlreadyStartedError") + " as 500", "Catch it in the POST handler "
     "and return the existing order."],
    ["Tests hang on teardown", "Call " + c("worker.shutdown()") + " and await the "
     + c("run()") + " promise before " + c("env.teardown()") + "."],
    ["Approval timeout fires instantly in tests", "Time skipping: waiting on "
     + c("result()") + " fast-forwards timers. Signal before waiting."],
], [62 * mm, 108 * mm])
h2("Further reading")
bullets([
    "Fastify with Node.js &mdash; The Complete Practical Tutorial (companion PDF)",
    "Temporal with Node.js &mdash; The Complete Practical Tutorial (companion PDF)",
    "docs.temporal.io/develop/typescript &middot; fastify.dev/docs/latest",
])
