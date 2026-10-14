# Content for "Event-Driven Architecture with Node.js". Executed inside build_eda_guide.py.
import callouts_eda
from paths import project

EDA_DIR = project('eda-commerce')


def eda_file(path, caption=None):
    """Embed an eda-commerce file verbatim (annotated when notes exist)."""
    src = open(os.path.join(EDA_DIR, path), encoding='utf8').read().rstrip('\n')
    body = '// ' + path + '\n' + src
    notes = callouts_eda.EDA.get(path)
    if notes:
        for f in annotated(body, caption, notes, path, CODE, BODY, ACCENT, CAPTION):
            story.append(f)
    else:
        _plain_code(body, caption)


def lbl(d, x, y, text, anchor='middle', size=7.5):
    d.add(String(x, y, text, textAnchor=anchor, fontSize=size, fontName='Helvetica',
                 fillColor=GREY))


def flow_diagram():
    d = Drawing(480, 235)
    # producers / orchestrator (left)
    box(d, 0, 185, 118, 40, "Order API\n+ outbox", fill=NOTE_BG, size=7.6)
    box(d, 0, 95, 118, 60, "Order saga\n(Temporal workflow)\nstarted / signalled\nby the bridges",
        fill=NOTE_BG, size=7.2)
    box(d, 0, 10, 118, 34, "Payment bridge\n(Kafka -> signal)", size=7.4)
    # topics (middle)
    d.add(Rect(160, 0, 150, 235, fillColor=colors.white, strokeColor=ACCENT,
               strokeWidth=1.1, rx=6, ry=6))
    d.add(String(235, 222, "Kafka", textAnchor='middle', fontSize=9.5,
                 fontName='Helvetica-Bold', fillColor=ACCENT))
    box(d, 172, 170, 126, 38, "orders\n(events, key = orderId)", size=7.4)
    box(d, 172, 100, 126, 38, "payments.commands", size=7.4)
    box(d, 172, 30, 126, 38, "payments.events", size=7.4)
    # consumers (right)
    box(d, 352, 205, 128, 22, "Saga starter", size=7.4)
    box(d, 352, 178, 128, 22, "Order-status projection", size=7.4)
    box(d, 352, 151, 128, 22, "Notifications", size=7.4)
    box(d, 352, 98, 128, 42, "Payment service\n(inbox)", fill=NOTE_BG, size=7.6)
    # arrows
    arrow(d, 118, 205, 172, 192)                       # API -> orders
    arrow(d, 118, 140, 172, 180)                       # saga -> orders (confirmed/cancelled)
    lbl(d, 145, 152, "confirm/cancel", size=6.8)
    arrow(d, 118, 118, 172, 118)                       # saga -> commands
    lbl(d, 145, 123, "command", size=6.8)
    for y in (216, 189, 162):
        arrow(d, 298, 189, 352, y)                     # orders -> consumers
    arrow(d, 298, 119, 352, 119)                       # commands -> payment
    arrow(d, 400, 98, 298, 52)                         # payment -> events
    lbl(d, 368, 70, "result event", size=6.8)
    arrow(d, 172, 47, 118, 30)                         # events -> bridge
    arrow(d, 59, 44, 59, 95)                           # bridge -> saga (signal)
    lbl(d, 80, 66, "signal", size=6.8)
    return d


def partitions_diagram():
    d = Drawing(480, 150)
    d.add(String(0, 138, "Topic orders (3 partitions)", fontSize=8.5,
                 fontName='Helvetica-Bold', fillColor=ACCENT))
    keys = [["A1", "C1", "A2", "A3", "C2", "A4"], ["B1", "B2", "D1", "B3", "D2", ""],
            ["E1", "E2", "E3", "F1", "", ""]]
    for p, row in enumerate(keys):
        y = 105 - p * 32
        lbl(d, 0, y + 9, f"P{p}", anchor='start', size=8)
        for i, k in enumerate(row):
            fill = ACCENT_LIGHT if k else colors.white
            d.add(Rect(22 + i * 34, y, 32, 24, fillColor=fill, strokeColor=ACCENT,
                       strokeWidth=0.8))
            if k:
                d.add(String(38 + i * 34, y + 8, k, textAnchor='middle', fontSize=7.5,
                             fontName='Helvetica'))
        lbl(d, 22 + 6 * 34 + 4, y + 9, "-> offsets 0, 1, 2, ...", anchor='start', size=7)
    # groups
    box(d, 330, 92, 150, 40, "Group order-status-view\n1 instance: P0 P1 P2", size=7.2)
    box(d, 330, 38, 150, 40, "Group payment-service\n2 instances: P0+P1 | P2",
        fill=NOTE_BG, size=7.2)
    lbl(d, 240, 0, "Same key (A, B, ...) -> same partition -> ordered. "
        "Each group reads everything; members of a group split partitions.", size=7)
    return d


# =========================================================================
# TITLE + TOC
# =========================================================================
super(Story, story).append(Spacer(1, 50 * mm))
super(Story, story).append(Paragraph("Event-Driven Architecture", ParagraphStyle(
    "T", parent=H1, fontSize=30, leading=36, alignment=TA_CENTER)))
super(Story, story).append(Paragraph("with Node.js, TypeScript, Kafka and Temporal",
    ParagraphStyle("ST", parent=BODY, fontSize=15, leading=20, alignment=TA_CENTER,
                   textColor=GREY, spaceAfter=24)))
super(Story, story).append(Paragraph(
    "Concepts, patterns and a complete, tested order platform: typed event contracts, "
    "idempotent producers, consumer groups, the transactional outbox, idempotent "
    "consumers, dead-letter topics, choreography and orchestration, a Temporal saga "
    "driven by Kafka, CQRS read models, failure drills and production practices.",
    ParagraphStyle("TD", parent=BODY, alignment=TA_CENTER, fontSize=11, leading=16)))
super(Story, story).append(Spacer(1, 30 * mm))
super(Story, story).append(Paragraph(
    "Verified with Kafka 4.1 (KRaft) &middot; @confluentinc/kafka-javascript 1.11 "
    "&middot; @temporalio/* 1.24 &middot; Node.js 24 &middot; TypeScript 7",
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
part("Part I &mdash; Concepts")
# =========================================================================
h1("1. What Event-Driven Architecture Is")
p("In a <b>request-driven</b> system, services call each other: the order service calls "
  "payments, then inventory, then e-mail, and waits for each answer. In an "
  "<b>event-driven</b> system, services announce facts &mdash; <i>an order was placed</i>, "
  "<i>a payment succeeded</i> &mdash; and other services react on their own schedule. "
  "The producer neither knows nor waits for its consumers.")
table([
    ["", "Request-driven (sync calls)", "Event-driven (messages)"],
    ["Coupling", "Caller knows every callee and its API", "Producer knows only the "
     "event; consumers come and go"],
    ["Availability", "One slow/down service blocks the chain",
     "Messages wait in Kafka until the consumer is back"],
    ["Scaling", "Every service sized for peak traffic",
     "Consumers scale independently; the log absorbs bursts"],
    ["New features", "Change the caller to call one more service",
     "Add a consumer; nothing else changes"],
    ["Audit / replay", "Must be built separately", "The log <i>is</i> a history; "
     "new consumers can replay it"],
    ["Consistency", "Immediate (inside one call chain)", "<b>Eventual</b>: views lag "
     "slightly behind"],
    ["Debugging", "One stack trace", "A flow spans many services: needs correlation IDs "
     "and tracing"],
], [28 * mm, 66 * mm, 76 * mm])
h2("1.1 What you pay for it")
bullets([
    "<b>Duplicates</b>: brokers and relays deliver at least once. Every consumer with side "
    "effects must be idempotent.",
    "<b>Ordering</b> is per partition, not global.",
    "<b>Eventual consistency</b>: the read model may show PLACED for a moment after payment "
    "succeeded. UIs and APIs must be designed for it (202 + status URL).",
    "<b>Schema evolution</b>: events are a public API that outlives the code that wrote "
    "them.",
    "<b>Long business processes</b> (wait for payment, compensate on failure) are hard to "
    "see when they are spread across many consumers. This is where Temporal comes in.",
])
p("Don't use EDA for simple CRUD apps or for flows that genuinely need an immediate, "
  "consistent answer (\"is this username taken?\"). Use it where decoupling, buffering, "
  "fan-out and auditability pay for the extra moving parts.")

h1("2. Messages: Events, Commands and Queries")
table([
    ["Kind", "Example", "Name", "Receivers", "Expectation"],
    ["Event", "order.placed.v1", "Past tense: a fact", "0..n, unknown to the producer",
     "None: the producer moves on"],
    ["Command", "payment.requested.v1", "Imperative: a request",
     "Exactly one service", "Somebody will act and report back"],
    ["Query", "GET /orders/{id}", "Question", "One service", "An immediate answer "
     "(usually HTTP, not Kafka)"],
], [21 * mm, 36 * mm, 34 * mm, 41 * mm, 38 * mm])
h2("2.1 How much data goes into an event?")
table([
    ["Style", "What the event contains", "Trade-off"],
    ["Event notification", "Just IDs: \"order 42 changed\"", "Small, but consumers call "
     "back for details (coupling, load)"],
    ["Event-carried state transfer", "Everything consumers need (email, items, "
     "total...)", "Bigger events, fully autonomous consumers. <b>Used in this guide.</b>"],
    ["Event sourcing", "Every state change; the log is the source of truth",
     "Full history and replay, but a different programming model"],
], [44 * mm, 60 * mm, 66 * mm])
h2("2.2 Naming and versioning")
bullets([
    c("domain.entity.happened.vN") + ": " + c("order.placed.v1") + ", "
    + c("payment.failed.v1") + ".",
    "Additive changes (new optional fields) keep the version; renaming or removing a field "
    "or changing its meaning is a new version that coexists on the same topic.",
    "Validate every incoming message against its schema; reject what you don't understand "
    "to a dead-letter topic instead of crashing.",
])

h1("3. Kafka Fundamentals")
story.append(partitions_diagram())
story.append(Spacer(1, 6))
table([
    ["Concept", "What it means for your design"],
    ["Topic", "A named, append-only log. Here: " + c("orders") + ", "
     + c("payments.commands") + ", " + c("payments.events") + " (+ a "
     + c(".dlq") + " each)."],
    ["Partition", "Unit of parallelism and ordering. Order is guaranteed only within one "
     "partition."],
    ["Key", "Chooses the partition (hash). Same key, same partition, same order. Key by "
     "the entity whose events must stay ordered (orderId)."],
    ["Offset", "Position in a partition. Consumers commit offsets; after a restart they "
     "resume from the last commit."],
    ["Consumer group", "One logical subscriber. Every group gets every message; instances "
     "in a group split the partitions (max useful instances = partitions)."],
    ["Retention / compaction", "Messages stay for a time/size limit, or, compacted, the "
     "latest value per key is kept forever."],
    ["Replication / ISR", "Each partition is copied to replicas; " + c("acks=all")
     + " waits for the in-sync replicas. (Single broker in development.)"],
    ["KRaft", "Kafka's built-in consensus (no ZooKeeper since Kafka 4.0)."],
], [36 * mm, 134 * mm])
h2("3.1 Delivery guarantees")
table([
    ["Guarantee", "How it happens", "Consequence"],
    ["At most once", "Commit the offset, then process", "A crash loses the message"],
    ["At least once", "Process, then commit (this guide)", "A crash re-delivers: "
     "handlers must be idempotent"],
    ["Exactly once", "Kafka transactions for read-process-write <i>within Kafka</i>",
     "Doesn't cover side effects outside Kafka (DB, e-mail, HTTP)"],
], [32 * mm, 70 * mm, 68 * mm])
note("The practical recipe: <b>at-least-once delivery + idempotent consumers</b> "
     "(an inbox, deterministic IDs, upserts). The tests in Part III prove it end to end.")

h1("4. Choreography vs Orchestration")
table([
    ["", "Choreography", "Orchestration"],
    ["Who decides the next step", "Each service, by reacting to events",
     "One coordinator (here: a Temporal workflow)"],
    ["Coupling", "Lowest: services only know events", "Coordinator knows the steps"],
    ["Visibility of the process", "Spread across services and topics",
     "One function; one history per order in the Temporal UI"],
    ["Timeouts, compensation, retries", "Hand-built in every service",
     "Built in: timers, retry policies, sagas"],
    ["Best for", "Fan-out side effects (e-mail, analytics, search, read models)",
     "Multi-step business transactions with deadlines and compensation"],
], [40 * mm, 64 * mm, 66 * mm])
p("This guide uses <b>both</b>: the order saga is orchestrated by Temporal (reserve "
  "stock &rarr; request payment &rarr; wait &rarr; confirm or compensate), while the "
  "read model and notifications simply react to events. Kafka connects everything; "
  "Temporal never replaces it &mdash; it owns the <i>process state</i>, Kafka owns the "
  "<i>event stream</i>.")

h1("5. The Example Platform")
story.append(flow_diagram())
story.append(Spacer(1, 6))
h2("5.1 Life of an order")
table([
    ["#", "Step", "Mechanism"],
    ["1", "POST /orders: order row + OrderPlaced in one DB transaction; 202 Accepted",
     "Transactional outbox"],
    ["2", "Relay publishes OrderPlaced to " + c("orders") + " (key = orderId)",
     "Idempotent producer"],
    ["3", "Saga starter starts workflow " + c("order-saga-{orderId}"),
     "Kafka &rarr; Temporal, Workflow ID de-dup"],
    ["4", "Saga reserves stock, publishes PaymentRequested to "
     + c("payments.commands"), "Activity, deterministic event ID"],
    ["5", "Payment service charges, publishes PaymentSucceeded/Failed",
     "Inbox (idempotent consumer)"],
    ["6", "Payment bridge signals the saga", "Kafka &rarr; Temporal signal"],
    ["7", "Saga publishes OrderConfirmed (or releases stock + OrderCancelled)",
     "Saga compensation"],
    ["8", "Projection updates the read model; notifications e-mail the customer",
     "Choreography, CQRS"],
], [8 * mm, 112 * mm, 50 * mm])
h2("5.2 Patterns and where they live")
table([
    ["Problem", "Pattern", "Code"],
    ["Save + publish atomically", "Transactional outbox", c("order-api/outbox.ts")],
    ["Duplicate deliveries", "Inbox / idempotent consumer, deterministic IDs",
     c("inbox.ts") + ", " + c("saga/activities.ts")],
    ["Messages that always fail", "Dead-letter topic", c("kafka/consumer.ts")],
    ["Untrusted payloads", "Typed, validated contracts", c("events/contracts.ts")],
    ["Long-running process", "Saga orchestrated by Temporal", c("saga/workflows.ts")],
    ["Kafka &harr; workflow", "Starter + signal bridge", c("saga/bridges.ts")],
    ["Queries over events", "CQRS projection", c("projections/order-status.ts")],
    ["Tracing a flow", "Correlation ID in envelope + headers", "everywhere"],
], [44 * mm, 66 * mm, 60 * mm])
h2("5.3 Tested with")
p("Everything in Parts II and III was type-checked, run and tested (17 tests) against a "
  "real Kafka broker and a real Temporal dev server. The project is "
  + c("eda-commerce/") + " (github.com/tcsr/eda-commerce).")
table([
    ["Component", "Version", "Notes"],
    ["Kafka", "4.1.0", "Docker image " + c("apache/kafka") + ", single node, KRaft"],
    ["Kafka client", "@confluentinc/kafka-javascript 1.11", "librdkafka 2.16; "
     "KafkaJS-compatible API"],
    ["Temporal", "@temporalio/* 1.24", "Dev server via " + c("@temporalio/testing")],
    ["Fastify / TypeBox", "5.12 / 1.3", "Order API, event schemas"],
    ["Node.js / TypeScript", "24.15 / 7.0", c("node:sqlite") + " for service databases"],
], [36 * mm, 56 * mm, 78 * mm])
note("Why the Confluent client? KafkaJS, long the default for Node.js, has not been "
     "maintained since 2023. Confluent's client wraps librdkafka (the C library behind "
     "most Kafka clients) and offers a KafkaJS-compatible API, so KafkaJS code ports with "
     "few changes.")

# =========================================================================
part("Part II &mdash; Building It")
# =========================================================================
h1("6. Setup")
code("""
mkdir eda-commerce && cd eda-commerce && npm init -y
npm install @confluentinc/kafka-javascript fastify @fastify/type-provider-typebox \\
            typebox @temporalio/client @temporalio/worker @temporalio/workflow \\
            @temporalio/activity @temporalio/common
npm install -D typescript tsx @types/node @temporalio/testing
""")
p("Kafka runs in Docker in KRaft mode: one container acts as both controller and "
  "broker. Auto topic creation is off on purpose.")
_plain_code('// docker-compose.yml\n' +
            open(os.path.join(EDA_DIR, 'docker-compose.yml'), encoding='utf8')
            .read().rstrip('\n').replace('# Single-node', '# Single-node'), None)
code("""
docker compose up -d --wait     # waits for the healthcheck
npm run smoke                   # create topic, produce 4 messages, consume them back
# sent partitions: [ 1 ]
# received: [ 'order-0@p1:{"i":2}:c2', 'order-0@p1:{"i":4}:c4', ... ]
""", "Verify the broker")
code("""
src/
  config.ts                 topic names (prefixable for tests), broker list
  events/contracts.ts       typed, versioned event envelope + validation
  kafka/client.ts           topics, idempotent producer
  kafka/consumer.ts         consumer runner: at-least-once, retries, DLQ
  inbox.ts                  idempotent-consumer helper
  order-api/                Fastify API + transactional outbox
  payment-service/          command handler with inbox
  saga/                     Temporal workflow, activities, Kafka bridges
  projections/              CQRS read model
  notifications/            choreographed side effect
  inventory.ts              stock reservations (called by the saga)
  platform.ts               wires everything (one process for demo and tests)
test/                       contracts, Kafka basics, reliability, end-to-end
""", "Project layout")

h1("7. Event Contracts")
p("Events are an API between teams. They are defined once, typed with TypeBox (so "
  "TypeScript knows every field), and validated when consumed.")
eda_file('src/events/contracts.ts')

h1("8. Producing Events")
eda_file('src/kafka/client.ts')

h1("9. Consuming Events")
p("One runner used by every service: parse and validate, call the handler, retry "
  "transient failures a few times, send everything else to the dead-letter topic, then "
  "let the offset be committed.")
eda_file('src/kafka/consumer.ts')

h1("10. The Transactional Outbox")
p("The order service must store the order <i>and</i> tell the world about it. Writing to "
  "the database and to Kafka separately can fail half-way: an order nobody hears about, "
  "or an event about an order that was rolled back. The outbox makes it one local "
  "transaction.")
eda_file('src/order-api/outbox.ts')
eda_file('src/order-api/app.ts')

h1("11. Idempotent Consumers")
eda_file('src/inbox.ts')
p("The payment service combines the inbox with its own data: a command it has already "
  "processed is ignored, so a duplicate can never charge twice.")
eda_file('src/payment-service/service.ts')

h1("12. Orchestration: a Temporal Saga Driven by Kafka")
p("The order process has deadlines, a wait for another service and compensation. As "
  "choreography it would be spread over several consumers with hand-made timers and "
  "state tables. As a Temporal workflow it is one readable function whose state "
  "survives crashes.")
eda_file('src/saga/workflows.ts')
eda_file('src/saga/activities.ts')
h2("12.1 Bridging Kafka and Temporal")
p("Two small consumers connect the event stream to workflows: one <b>starts</b> a saga "
  "per order, one turns payment results into <b>signals</b>.")
eda_file('src/saga/bridges.ts')

h1("13. Choreography and CQRS")
p("Not everything needs a coordinator. The read model and notifications react to "
  "order events independently, each in its own consumer group.")
eda_file('src/projections/order-status.ts')
eda_file('src/notifications/service.ts')
h2("13.1 Wiring it together")
p(c("platform.ts") + " starts every component in one process for the demo and the "
  "tests. In production each is its own deployment; only the configuration (topics, "
  "group IDs, task queue) connects them.")
eda_file('src/platform.ts')

# =========================================================================
part("Part III &mdash; Testing and Running")
# =========================================================================
h1("14. Testing Strategy")
table([
    ["Level", "File", "Needs", "Proves"],
    ["Contract", c("contracts.test.ts"), "nothing", "Validation, poison detection, "
     "deterministic IDs"],
    ["Broker", c("kafka-basics.test.ts"), "Kafka", "Per-key ordering, fan-out across "
     "groups, partition sharing, headers"],
    ["Patterns", c("reliability.test.ts"), "Kafka", "Outbox, relay crash duplicate, "
     "inbox, retries, DLQ, poison"],
    ["End to end", c("platform.test.ts"), "Kafka + Temporal", "Saga paths, "
     "compensation, duplicates, outages, timeouts"],
], [24 * mm, 42 * mm, 30 * mm, 74 * mm])
p("Each test file uses a unique prefix for topics, consumer groups and the Temporal task "
  "queue, so runs never interfere on the shared broker.")
eda_file('test/reliability.test.ts')
eda_file('test/platform.test.ts')
code("""
npm test
# ok  a valid event round-trips through JSON
# ok  garbage, unknown types and invalid payloads are poison messages
# ok  deterministic IDs make retried publications recognisable
# ok  same key, same partition: events of one order stay in order
# ok  every consumer GROUP gets every event (pub/sub fan-out)
# ok  consumers in the SAME group share the partitions (scale-out)
# ok  headers carry metadata without touching the payload
# ok  outbox: the order and its event are saved together, then relayed
# ok  a relay crash re-publishes; an inbox makes the consumer idempotent
# ok  transient failures are retried in place, then succeed
# ok  a permanently failing message goes to the DLQ with diagnostics
# ok  happy path: reserved, paid, confirmed, customer notified
# ok  payment declined: the saga releases the stock and cancels
# ok  out of stock: cancelled before any payment is requested
# ok  a duplicate OrderPlaced event does not start a second saga
# ok  payment service down: the command waits, the saga waits durably
# ok  no answer before the deadline: the saga times out, compensates
# tests 17, pass 17, fail 0   (about 40 s)
""", "Result")

h1("15. Running the Platform")
code("""
npm run kafka:up        # terminal 1: Kafka in Docker
npm run dev-server      # terminal 2: Temporal dev server, UI http://localhost:8233
npm start               # terminal 3: every service, API on http://localhost:3000
""")
code("""
curl -i -X POST localhost:3000/orders -H "Content-Type: application/json" \\
     -H "x-correlation-id: demo-corr-001" \\
     -d '{"customerId":"c-42","email":"ann@example.com",
          "items":[{"sku":"MUG","qty":2,"priceCents":1200}]}'
# HTTP/1.1 202 Accepted
# location: /orders/919aed8c-6571-4013-842d-a0dd0a371238
# {"orderId":"919aed8c-...","correlationId":"demo-corr-001"}

curl localhost:3000/orders/919aed8c-6571-4013-842d-a0dd0a371238
# {"status":"CONFIRMED","totalCents":2400,"correlationId":"demo-corr-001",
#  "paymentId":"pay_782bbae1", ...}

# An order above the credit limit
# {"status":"CANCELLED","totalCents":89900,"reason":"Insufficient funds", ...}

# Platform log
# [mail] order-confirmed -> ann@example.com (correlation demo-corr-001)
# [mail] order-cancelled -> bob@example.com (correlation 8791dd67-...)
""", "Real responses from the verification run")
h2("15.1 Looking inside Kafka")
code("""
docker exec eda-kafka /opt/kafka/bin/kafka-console-consumer.sh \\
  --bootstrap-server localhost:9092 --topic orders --from-beginning \\
  --property print.key=true --property print.headers=true --property print.partition=true
# Partition:0  event-id:080f9dc8-...,event-type:order.placed.v1,
#              correlation-id:demo-corr-001   919aed8c-...   {"id":"080f9dc8-...", ...}
# Partition:0  event-id:919aed8c-...:confirmed,event-type:order.confirmed.v1,
#              correlation-id:demo-corr-001   919aed8c-...   {"id":"919aed8c-...:confirmed", ...}

# payments.commands: "type":"payment.requested.v1" "amountCents":2400
# payments.events:   "type":"payment.succeeded.v1" "paymentId":"pay_782bbae1"

docker exec eda-kafka /opt/kafka/bin/kafka-consumer-groups.sh \\
  --bootstrap-server localhost:9092 --describe --all-groups
# notifications        orders             lag=0
# order-saga-payments  payments.events    lag=0
# order-saga-starter   orders             lag=0
# order-status-view    orders             lag=0
# payment-service      payments.commands  lag=0
""")
p("Both events of the order share key and partition 0 (ordered); the saga's event ID is "
  "deterministic (" + c("{orderId}:confirmed") + "); the correlation ID set by the HTTP "
  "caller appears on every message. Five consumer groups read independently, all "
  "caught up (lag 0).")
warn("On Windows Git Bash, prefix " + c("docker exec") + " commands with "
     + c("MSYS_NO_PATHCONV=1") + ": otherwise " + c("/opt/kafka/...") + " is rewritten "
     "to a Windows path and the command silently prints nothing (happened during "
     "verification).")

h1("16. Failure Drills")
p("Each drill is an automated test against the real broker and Temporal server:")
table([
    ["Drill", "What happened (verified)"],
    ["Relay crashes after publishing, before marking", "OrderPlaced is on the topic "
     "<b>twice</b>; the inbox-protected consumer applied it <b>once</b>"],
    ["The same OrderPlaced is delivered again later", "Saga run ID unchanged; customer "
     "charged once"],
    ["Handler fails twice, then works", "3 attempts with backoff; processed; no DLQ entry"],
    ["Handler always fails", "After 3 attempts: DLQ message with original key/bytes and "
     + c("dlq-error") + ", " + c("dlq-attempts: 3") + ", topic, group"],
    ["Invalid JSON on the topic", "Straight to the DLQ (" + c("dlq-attempts: 0") + "), "
     "the partition keeps moving"],
    ["Payment declined", "Stock released (8 &rarr; 8), CANCELLED \"Insufficient funds\", "
     "cancellation e-mail"],
    ["Out of stock", "CANCELLED before any payment command was published"],
    ["Payment service down", "Saga stays AWAITING_PAYMENT; command waits in Kafka; "
     "service restarts &rarr; CONFIRMED"],
    ["No answer within the deadline (3 s)", "Saga times out, releases stock, CANCELLED "
     "\"Payment timed out\""],
], [60 * mm, 110 * mm])

# =========================================================================
part("Part IV &mdash; Production")
# =========================================================================
h1("17. Partitions, Ordering and Scaling")
bullets([
    "<b>Partition count</b> caps parallelism per consumer group. Start with a number "
    "that covers expected peak consumers (e.g. 12 or 24); increasing later reshuffles "
    "keys across partitions, so per-key ordering breaks for a while.",
    "<b>Key choice</b>: the entity whose events must stay ordered (order, account). Avoid "
    "hot keys (one tenant producing most traffic).",
    "<b>Rebalances</b> pause consumption while partitions move between instances. Use "
    "cooperative/incremental rebalancing and keep handlers short.",
    "<b>Consumer lag</b> (" + c("kafka-consumer-groups.sh --describe") + ", or metrics "
    "exporters) is the key health signal: alert on growing lag, not on a fixed number.",
    "<b>Blocking retries</b> (this guide) keep order but stall a partition. For long "
    "outages, pause the consumer, or move failed messages to delayed retry topics "
    "(" + c("orders.retry.1m") + ", " + c("orders.retry.10m") + ") and accept reordering "
    "for those.",
])
h1("18. Schema Evolution")
table([
    ["Change", "Safe?", "How"],
    ["Add an optional field", "Yes", "Same version; old consumers ignore it"],
    ["Add a required field", "No", "Add it as optional first, or publish "
     + c(".v2")],
    ["Rename / remove / change meaning", "No", "New version; publish both during the "
     "migration; retire v1 when no consumer needs it"],
    ["New event type", "Yes", "Unknown types go to the DLQ in strict consumers: decide "
     "whether to ignore instead"],
], [52 * mm, 16 * mm, 102 * mm])
p("At scale, use a <b>schema registry</b> (Confluent Schema Registry, Apicurio) with JSON "
  "Schema, Avro or Protobuf: producers register schemas, the registry enforces "
  "compatibility rules, and consumers fetch the schema by ID from the message.")
h1("19. Consistency Traps")
bullets([
    "<b>Late answers</b>: if the payment succeeds <i>after</i> the saga timed out, money "
    "was taken for a cancelled order. Handle it: the bridge publishes a refund command "
    "when it signals a finished saga, or the payment service checks a deadline carried "
    "in the command.",
    "<b>Outbox on every producer</b>: the payment service here publishes inside its "
    "database transaction for brevity; a crash between charge and publish would leave "
    "the saga waiting until its timeout. Production code uses an outbox there too.",
    "<b>Exactly-once</b> in Kafka (transactions, " + c("isolation.level=read_committed")
    + ") covers Kafka-to-Kafka processing only. Side effects in databases and other "
    "systems still need idempotency.",
    "<b>Read-your-writes</b>: right after POST the read model may not have the order. "
    "Return 202 + Location, or read from the write side for the creating user.",
])
h1("20. Observability")
bullets([
    "<b>Correlation IDs</b> in the envelope and headers (this guide); log them in every "
    "service.",
    "<b>Distributed tracing</b>: propagate W3C " + c("traceparent") + " in Kafka headers "
    "(OpenTelemetry has Kafka instrumentation); Temporal has an OpenTelemetry interceptor.",
    "<b>Metrics</b>: consumer lag per group, DLQ message rate, handler latency and errors, "
    "outbox backlog (unpublished rows), saga durations and failure reasons.",
    "<b>Temporal UI</b>: every order's saga history (search by Workflow ID "
    + c("order-saga-{orderId}") + ").",
    "<b>DLQ tooling</b>: a small CLI or admin page to inspect, fix and replay DLQ messages "
    "back to the original topic.",
])
h1("21. Security and Operations")
bullets([
    "TLS for client connections, SASL (SCRAM or OAUTHBEARER) for authentication, ACLs "
    "per service (who may produce/consume which topic).",
    "No secrets or unnecessary personal data in events: they are copied to every "
    "consumer and kept for the retention period. Prefer IDs over raw personal data where "
    "you can.",
    "Replication factor 3 and " + c("min.insync.replicas=2") + " in production; "
    + c("acks=all") + " producers (the idempotent producer implies it).",
    "Retention: days for operational topics; compaction for \"latest state per key\" "
    "topics; DLQs long enough to investigate.",
    "Each service and each consumer group is its own deployment; scale consumers up to "
    "the partition count.",
])
h1("22. Checklist")
table([
    ["Item", "In this guide"],
    ["Typed, versioned event contracts, validated on consume", "Chapter 7"],
    ["Keys chosen for ordering; topics created explicitly", "Chapter 8"],
    ["At-least-once consumers with bounded retries + DLQ", "Chapter 9"],
    ["Outbox for every service that changes data and publishes", "Chapter 10"],
    ["Idempotent consumers (inbox, deterministic IDs, upserts)", "Chapters 11-12"],
    ["Long-running processes in a workflow engine", "Chapter 12"],
    ["Read models for queries; 202 + status URL for writes", "Chapters 10, 13"],
    ["Correlation IDs end to end", "Chapters 7, 15"],
    ["Failure drills automated in CI", "Chapter 16"],
], [118 * mm, 52 * mm])

# =========================================================================
part("Appendices")
# =========================================================================
h1("A. Kafka CLI Cheat Sheet")
code("""
K=/opt/kafka/bin   # inside the container: docker exec -it eda-kafka bash
$K/kafka-topics.sh --bootstrap-server localhost:9092 --list
$K/kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic orders
$K/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic orders \\
                   --partitions 12 --replication-factor 3
$K/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic orders \\
                   --from-beginning --property print.key=true --property print.headers=true
$K/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic orders \\
                   --property parse.key=true --property key.separator=:
$K/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --all-groups
$K/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group payment-service \\
                   --topic payments.commands --reset-offsets --to-earliest --execute
""")
h1("B. Troubleshooting")
table([
    ["Symptom", "Cause / fix"],
    ["Consumer receives nothing at first", "Group joining / rebalancing takes a few "
     "seconds; " + c("fromBeginning") + " applies only to new groups"],
    ["Old messages are not re-read", "The group has committed offsets. Use a new group "
     "or " + c("--reset-offsets")],
    ["Topic not found", "Auto-create is off: create topics (" + c("ensureTopics") + ")"],
    ["One partition stops moving", "A handler keeps failing (blocking retry). Check the "
     "logs and the DLQ"],
    ["Duplicates downstream", "Expected with at-least-once: add an inbox / "
     "deterministic IDs"],
    ["Temporal bundling: \"Failed to load native binding\"", "Pin "
     + c('"overrides": { "@swc/core": "1.16.2" }') + " (see the Temporal tutorial)"],
    [c("docker exec ... /opt/kafka/...") + " prints nothing on Windows",
     "Set " + c("MSYS_NO_PATHCONV=1") + " in Git Bash"],
], [62 * mm, 108 * mm])
h1("C. Glossary")
table([
    ["Term", "Definition"],
    ["Event", "An immutable fact that something happened, named in the past tense"],
    ["Command", "A request to one service to do something"],
    ["Topic / partition / offset", "Named log / ordered shard of it / position in a shard"],
    ["Consumer group", "Set of consumer instances sharing a subscription"],
    ["Consumer lag", "How far a group is behind the end of the log"],
    ["DLQ", "Dead-letter topic for messages that could not be processed"],
    ["Outbox", "Table written with business data; relayed to the broker"],
    ["Inbox", "Table of processed message IDs used to drop duplicates"],
    ["Saga", "Multi-step process with compensating actions instead of a distributed "
     "transaction"],
    ["Choreography / orchestration", "Services react to events / a coordinator directs "
     "the steps"],
    ["CQRS", "Separate models for writes (commands) and reads (projections)"],
    ["Idempotence", "Doing something twice has the same effect as doing it once"],
], [46 * mm, 124 * mm])
h2("Further reading")
bullets([
    "Companion guides: Fastify with Node.js, Temporal with Node.js, Fastify + Temporal",
    "kafka.apache.org/documentation &middot; github.com/confluentinc/confluent-kafka-javascript",
    "docs.temporal.io/develop/typescript &middot; cloudevents.io",
])
