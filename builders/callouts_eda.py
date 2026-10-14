"""Callout notes for eda-commerce/ (anchors: exact substrings, matched in order)."""
from callouts import c

EDA = {
    'src/events/contracts.ts': [
        ("// Every message shares one envelope (modelled on CloudEvents); `data` varies by type",
         "A common envelope lets every consumer route, log and de-duplicate without "
         "knowing the payload."),
        ("id: Type.String(), // unique per event: the de-duplication key",
         "Consumers remember IDs they have processed (the inbox, Chapter 11)."),
        ("type: Type.Literal(type), // name + version: 'order.placed.v1'",
         "Past-tense name + version. A breaking change gets " + c(".v2") + "; both "
         "versions can coexist on the topic."),
        ("subject: Type.String(), // aggregate ID, also the Kafka message key",
         "The aggregate (order) ID becomes the key: all events of one order land in "
         "one partition, in order."),
        ("correlationId: Type.String(), // ties every message of one business flow together",
         "Follow one customer action across API, Kafka, Temporal and e-mails."),
        ("// A command: addressed to one service, asks it to do something",
         "Commands (imperative: <i>RequestPayment</i>) have one intended receiver; "
         "events (past tense: <i>PaymentSucceeded</i>) have any number."),
        ("export class PoisonMessageError extends Error {}",
         "A separate error class lets the consumer skip retries for messages that can "
         "never succeed."),
        ("if (!Value.Check(schema, json)) {",
         "Validate on the way <b>in</b>: producers can be buggy, other teams evolve "
         "their code, and the payload is untrusted input."),
        ("id: meta.id ?? randomUUID(),",
         "Random by default; a caller can pass a deterministic ID (the saga does)."),
    ],
    'src/kafka/client.ts': [
        ("// Topics are created explicitly (auto-create is off):",
         "Auto-created topics get default settings and invite typos; create them "
         "deliberately (or with infrastructure-as-code)."),
        ("const missing = [...topics, ...topics.map(dlqOf)].filter(",
         "Every topic gets a dead-letter twin, " + c("orders.dlq") + "."),
        ("const producer = kafka.producer({ kafkaJS: { idempotent: true } });",
         "Idempotent producer: retries after a lost acknowledgement don't write "
         "duplicates to the log, and per-partition order is kept."),
        ("key: event.subject, // same key -> same partition -> ordered per order",
         "Ordering is guaranteed <b>per partition</b> only. Choose the key = the thing "
         "whose events must stay in order."),
        ("'event-id': event.id,",
         "Headers: routing and tracing metadata readable without parsing the body "
         "(verified with " + c("kafka-console-consumer") + ")."),
    ],
    'src/kafka/consumer.ts': [
        ("groupId: string; // one group per service: each group gets every message",
         "Consumer group = one logical subscriber. Instances in the same group split the "
         "partitions; different groups each get everything."),
        ("const consumer = kafka.consumer({ kafkaJS: { groupId, fromBeginning: true } });",
         c("fromBeginning") + " only matters the first time a group starts; afterwards "
         "it resumes from its committed offsets."),
        ("// Offsets are committed only after eachMessage resolves: at-least-once delivery",
         "Crash before the commit &rarr; the message is delivered again. Design every "
         "handler for duplicates."),
        ("await dlq.publishRaw(dlqOf(topic), {",
         "The original bytes go to the DLQ untouched, plus diagnostics headers "
         "for whoever investigates or replays it."),
        ("if (err instanceof PoisonMessageError) return toDlq(err, 0); // never retry",
         "Poison messages are parked immediately (" + c("dlq-attempts: 0") + " in the "
         "test)."),
        ("// Bounded in-process retries for transient failures, then park in the DLQ",
         "Retrying in place keeps order but blocks the partition; for long outages use "
         "retry topics or pause the consumer instead."),
        ("await delay(backoffMs * 2 ** (attempt - 1));",
         "Exponential backoff between attempts."),
    ],
    'src/inbox.ts': [
        ("PRIMARY KEY (consumer, event_id))`);",
         "One row per (consumer, event): each service de-duplicates independently."),
        ("'INSERT OR IGNORE INTO processed_events VALUES (?, ?, ?)',",
         "Postgres equivalent: " + c("INSERT ... ON CONFLICT DO NOTHING") + "."),
        ("db.exec('BEGIN IMMEDIATE');",
         "The marker and the handler's own writes commit together."),
        ("return false; // duplicate delivery: already handled",
         "Second delivery of the same event: no effect (proven in the reliability "
         "test)."),
    ],
    'src/order-api/outbox.ts': [
        ("// Transactional outbox: the event is written in the SAME database transaction as",
         "The dual-write problem: writing to the DB <i>and</i> Kafka can't be atomic. "
         "The outbox turns it into one local transaction plus a relay."),
        ("add(topic: string, event: DomainEvent) {",
         "Called inside the business transaction (see the API below)."),
        ("// Publish pending events in order. A crash between publish and mark means the",
         "The relay is at-least-once too: the test simulates exactly this crash and "
         "sees the event twice on the topic."),
        ("// Polling relay; production alternatives: CDC with Debezium reading the WAL",
         "Change data capture avoids polling and preserves commit order across "
         "instances."),
    ],
    'src/order-api/app.ts': [
        ("request.headers['x-correlation-id'] ?? randomUUID(),",
         "Take the caller's correlation ID (or start one): it travels with every "
         "message from here on."),
        ("db.exec('BEGIN');",
         "One local transaction..."),
        ("outbox.add(",
         "...the order row <b>and</b> the OrderPlaced event."),
        ("reply.code(202).header('location', `/orders/${orderId}`);",
         "The rest happens asynchronously: 202 Accepted, poll the status URL."),
        ("// Read side (CQRS): served from the projection built from events",
         "Reads come from a separate read model that is <b>eventually</b> consistent."),
    ],
    'src/payment-service/service.ts': [
        ("// Autonomous service: consumes commands, owns its data, publishes facts",
         "Nobody else reads its tables; others learn about payments only through its "
         "events."),
        ("await inbox.once(event.id, async () => {",
         "Duplicate commands are absorbed: one charge per order (asserted end to end)."),
        ("charge.run(outcome.data.paymentId, orderId, amountCents);",
         "The charge record shares the inbox transaction."),
        ("await publisher.publish(topics.paymentEvents, outcome);",
         "Simplification: the publish is inside the DB transaction. Production code "
         "would use an outbox here too."),
        ("groupId: `${topics.prefix}payment-service`,",
         "Scale out by adding instances with the same group ID (up to the partition "
         "count)."),
    ],
    'src/saga/workflows.ts': [
        ("export const paymentResult = defineSignal<[PaymentOutcome]>('paymentResult');",
         "The payment answer arrives from Kafka as a <b>signal</b> (see the bridge)."),
        ("payment ??= outcome; // first answer wins; redelivered events are ignored",
         "Signals can also be delivered twice (Kafka redelivery): keep the first."),
        ("// Step 1: reserve stock (synchronous call to the inventory service)",
         "Not everything has to go through Kafka: a quick synchronous call is fine "
         "inside an activity."),
        ("err.cause.type === 'OutOfStock'",
         "A business failure: cancel without asking for payment (verified: no "
         "command on the topic)."),
        ("await a.requestPayment(order, correlationId);",
         "Publishes a <b>command</b> to Kafka and returns immediately."),
        ("const answered = await condition(",
         "A durable wait: survives worker restarts. The payment service can be down "
         "for minutes (drill in Chapter 16)."),
        ("await a.releaseStock(order.orderId);",
         "Compensation: undo the reservation when payment fails or times out."),
    ],
    'src/saga/activities.ts': [
        ("id, // deterministic: a retried activity publishes the SAME event ID",
         "Temporal retries activities; deterministic event IDs let downstream inboxes "
         "drop the repeats."),
        ("if (shortage) throw ApplicationFailure.nonRetryable(shortage, 'OutOfStock');",
         "Non-retryable: out of stock won't fix itself in a second."),
        ("inventory.release(orderId); // idempotent: releasing twice is a no-op",
         "Every activity is safe to run more than once."),
        ("topics.paymentCommands,",
         "Commands go to the payment service's own topic."),
    ],
    'src/saga/bridges.ts': [
        ("export const sagaId = (orderId: string) => `order-saga-${orderId}`;",
         "Business ID &rarr; Workflow ID: the link between the Kafka world and Temporal."),
        ("// The Workflow ID is derived from the order, so a redelivered event cannot",
         "Verified: re-publishing OrderPlaced leaves the saga's run ID unchanged and "
         "the order charged once."),
        ("workflowIdReusePolicy: 'REJECT_DUPLICATE',",
         "Even after the saga finished, a late duplicate can't start it again."),
        ("if (!(err instanceof WorkflowExecutionAlreadyStartedError)) throw err;",
         "Already started = success for an idempotent consumer."),
        ("// Kafka -> Temporal (2): payment facts become signals to the waiting saga",
         "Request/reply over Kafka, correlated by order ID."),
        ("// The saga already finished (e.g. timed out): a late answer is not an error",
         "A <b>late</b> success after a timeout means money was taken for a cancelled "
         "order: production systems refund here (Chapter 19)."),
    ],
    'src/notifications/service.ts': [
        ("// Choreography: reacts to order events on its own; nobody calls it, nobody waits.",
         "Adding this service needed no change anywhere else."),
        ("// Event-carried state transfer: the email address travels in the event, so this",
         "Fat events trade a bigger payload for full autonomy: no synchronous lookups."),
        ("await inbox.once(event.id, () =>",
         "Customers must not get the same e-mail twice."),
    ],
    'src/projections/order-status.ts': [
        ("// Read model built by folding events.",
         "CQRS: the write side publishes events; this read side reshapes them for one "
         "query."),
        ("if (!views.has(event.subject)) {",
         "Idempotent: a redelivered OrderPlaced doesn't reset a CONFIRMED order."),
        ("case 'order.confirmed.v1':",
         "Per-key ordering guarantees PLACED is applied before CONFIRMED."),
    ],
    'test/platform.test.ts': [
        ("env = await TestWorkflowEnvironment.createLocal(); // real Temporal dev server",
         "Real Temporal dev server (not time-skipping): the saga waits on Kafka "
         "traffic in real time."),
        ("prefix: uniquePrefix('platform'),",
         "Unique topic, group and task-queue names isolate each test run on the "
         "shared broker."),
        ("const finalView = (orderId: string, on: Platform = platform) =>",
         "Eventual consistency in tests: poll the read model until it settles."),
        ("assert.equal(platform.payments.chargesFor(orderId), 1);",
         "End-to-end proof that the customer was charged exactly once."),
    ],
    'test/reliability.test.ts': [
        ("db.exec('UPDATE outbox SET published_at = NULL');",
         "Simulates the crash between \"published\" and \"marked as published\"."),
        ("await waitFor(() => raw.messages.filter((m) => m.key === orderId).length === 2, {",
         "The duplicate really is on the topic..."),
        ("assert.deepEqual(awarded, [orderId], 'two deliveries, one effect');",
         "...and the inbox turns two deliveries into one effect."),
    ],
}
