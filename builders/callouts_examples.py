"""Callout notes for temporal-examples/ (anchors: exact substrings, matched in order)."""
from callouts import c

EXAMPLES = {
    # ---------------------------------------------------------------- payments
    'src/payments/workflows.ts': [
        ("const { chargeCard } = proxyActivities<PaymentActivities>({",
         "Each proxy carries its own policy: the charge is retried, receipts use defaults."),
        ("initialInterval: '1 second', // 1s, 2s, 4s, 8s, 16s between attempts",
         "Exponential backoff gives a struggling gateway room to recover instead of "
         "hammering it."),
        ("maximumAttempts: 6,",
         "Bounded: after 6 attempts the failure reaches the workflow, which fails visibly "
         "in the UI."),
        ("err.cause.type === 'CardDeclined'",
         "Branch on the <b>type</b> the activity assigned, not on message text."),
        ("return { status: 'DECLINED', reason: err.cause.message };",
         "A decline is an expected <b>business result</b>: the workflow completes "
         "normally with DECLINED."),
        ("throw err; // InvalidAmount, or retries exhausted: workflow FAILED",
         "Anything unexpected propagates and fails the execution &mdash; visible, "
         "alertable, resettable."),
    ],
    'src/payments/activities.ts': [
        ("paymentId: string; // our ID, also used as the gateway idempotency key",
         "Activities can run more than once; the provider de-duplicates on this key so a "
         "retry never charges twice."),
        ("export function createPaymentActivities(",
         "Factory with injected dependencies: real SDK clients in production, fakes in "
         "tests. The worker registers the returned object."),
        ("throw ApplicationFailure.nonRetryable(",
         "Bad input can never succeed: fail immediately, no retries."),
        ("if (err instanceof GatewayError && err.status === 402) {",
         "Translate provider errors into Temporal semantics: 402 (declined) is final..."),
        ("throw err; // 5xx, timeouts: retried",
         "...while anything else is assumed transient and handed to the retry policy."),
        ("export type PaymentActivities = ReturnType<typeof createPaymentActivities>;",
         "The workflow imports only this <b>type</b>, never the implementation."),
    ],
    'test/payments.test.ts': [
        ("class FakeGateway {",
         "A fake provider that misbehaves on demand: 503s, then success; declines for "
         "chosen customers."),
        ("env = await TestWorkflowEnvironment.createTimeSkipping();",
         "Real Temporal semantics in-process; retry back-off delays are skipped."),
        ("assert.equal(gateway.calls, 3);",
         "Proof of the retry policy: two 503s, success on the third call."),
        ("assert.equal(gateway.calls, 1); // non-retryable: no retries",
         "Proof that non-retryable errors are not retried."),
    ],
    # ----------------------------------------------------------- travel search
    'src/travel-search/workflows.ts': [
        ("const { validateQuery } = proxyLocalActivities<SearchActivities>({",
         "<b>Local activity</b>: runs inside the workflow task on the same worker &mdash; "
         "ideal for quick, pure checks."),
        ("retry: { maximumAttempts: 2 }, // a slow provider must not stall the search",
         "Search results go stale quickly: fail fast rather than retry for minutes."),
        ("const settled = await Promise.allSettled(",
         "Fan-out: one activity per provider, all in flight at once. "
         + c("Promise.allSettled") + " is deterministic inside workflows."),
        ("else failedProviders.push(input.providers[i]);",
         "Partial failure is normal for aggregators: keep the offers that arrived."),
        ("throw ApplicationFailure.nonRetryable(",
         "Only when every provider failed is the search itself a failure."),
    ],
    # ----------------------------------------------------------- shopping cart
    'src/shopping-cart/workflows.ts': [
        ("export const addItem = defineSignal<[CartItem]>('addItem');",
         "<b>Signal</b>: the storefront fires it and moves on; delivered even if no "
         "worker is running."),
        ("export const getCart = defineQuery<CartView>('getCart');",
         "<b>Query</b>: read-only snapshot for the cart page; never changes history."),
        ("export const applyCoupon = defineUpdate<number, [string]>('applyCoupon');",
         "<b>Update</b>: a change that returns a value to the caller (the discount)."),
        ("let version = 0; // bumps on every change: used for idle detection",
         "Any change resets the idle clock below."),
        ("validator: (code) => {",
         "Validators run <b>before</b> the update is recorded: an unknown coupon is "
         "rejected without touching history."),
        ("orderId = await createOrder(userId, [...items.values()], totalCents());",
         "Update handlers may be async and call activities; the reply is sent when "
         "the order exists."),
        ("const active = await condition(",
         "Wait for a change <i>or</i> the idle timeout, whichever comes first."),
        ("await sendCartReminder(userId, items.size);",
         "After 24 idle hours: one reminder e-mail. After another 24: EXPIRED."),
        ("await condition(allHandlersFinished); // let the checkout update reply first",
         "Never return while an update handler is still running."),
    ],
    'test/shopping-cart.test.ts': [
        ("await handle.signal(addItem, { sku: 'BOOK', qty: 1, priceCents: 1500 });",
         c("handle.signal()") + " returns as soon as the server has stored the signal."),
        ("assert.equal((await handle.query(getCart)).totalCents, 3000);",
         "Two books (merged), the pens removed: the query sees the current state."),
        ("handle.executeUpdate(applyCoupon, { args: ['FREE100'] }),",
         "Validator rejection surfaces as " + c("WorkflowUpdateFailedError") + "."),
        ("const orderId = await handle.executeUpdate(checkout); // reply = new order ID",
         "The caller gets the new order ID synchronously &mdash; no polling."),
        ("const result = await handle.result(); // 48 h skipped",
         "Two 24-hour idle timers elapse in milliseconds under time skipping."),
    ],
    # -------------------------------------------------------------- free trial
    'src/free-trial/workflows.ts': [
        ("export const upgraded = defineSignal<[string]>('upgraded'); // from the billing page",
         "The billing page signals the workflow when the customer pays."),
        ("// One workflow per sign-up: runs for 14 days, costs nothing while it waits",
         "No cron, no \"trials ending today\" SQL scan: each trial is its own durable "
         "timeline."),
        ("if (await condition(() => plan !== undefined, (trialDays - 3) * DAY))",
         c("condition") + " with a timeout = durable timer with an early exit. Survives "
         "deploys and restarts for the full 11 days."),
        ("await sendEmail(email, 'trial-ends-in-3-days');",
         "Day 11: the reminder."),
        ("await downgradeToFree(userId);",
         "Day 14 without payment: downgrade, then tell the customer."),
    ],
    'test/free-trial.test.ts': [
        ("assert.ok(Date.now() - started < 10_000, '14 days of timers are skipped');",
         "14 days of timers complete in seconds."),
        ("await env.sleep('5 days'); // advance the test clock",
         c("env.sleep") + " moves virtual time forward deterministically."),
        ("await handle.signal(upgraded, 'pro');",
         "The upgrade wakes the waiting " + c("condition") + " immediately."),
    ],
    # ----------------------------------------------------------------- reports
    'src/reports/workflows.ts': [
        ("const day = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().slice(0, 10);",
         "Safe in a workflow: the sandbox makes " + c("Date.now()") + " replay-stable."),
        ("await Promise.all(recipients.map((to) => emailReport(to, summary)));",
         "One activity per recipient: a bounced address doesn't block the others."),
    ],
    'src/reports/schedule.ts': [
        ("calendars: [{ hour: 2, minute: 30 }], // 02:30 every day...",
         "Calendar spec (cron expressions also work)."),
        ("timezone: 'Asia/Kolkata', // ...in the business's time zone",
         "Time zones and daylight-saving changes are handled by the server."),
        ("overlap: ScheduleOverlapPolicy.SKIP, // yesterday's run still going? skip",
         "Overlap policy: SKIP, BUFFER_ONE, ALLOW_ALL, CANCEL_OTHER, TERMINATE_OTHER..."),
        ("catchupWindow: '6 hours', // server was down at 02:30? run late",
         "Missed runs within the window are executed once the server is back."),
    ],
    'test/reports.test.ts': [
        ("env = await TestWorkflowEnvironment.createLocal();",
         "Schedules need a full server: this test runs on the real dev server."),
        ("assert.equal(next.toISOString().slice(11, 16), '21:00');",
         "02:30 IST is 21:00 UTC &mdash; verified from the schedule's next action time."),
        ("await schedule.trigger(); // run it right now",
         "Run on demand (e.g. a manager wants today's numbers now)."),
        ("await schedule.pause('Quarter-end freeze');",
         "Pause with a note; visible in the UI and CLI."),
    ],
    # ------------------------------------------------------------------- loans
    'src/loan-application/workflows.ts': [
        ("const { validateApplication } = proxyLocalActivities<LoanActivities>({",
         "Cheap validation as a local activity."),
        ("startToCloseTimeout: '2 seconds', // the bureau's SLA",
         "The timeout encodes the partner's SLA; two attempts, then give up."),
        ("await validateApplication(app); // invalid input: workflow FAILS (bad request)",
         "A non-retryable " + c("InvalidApplication") + " fails the execution: the "
         "request itself was wrong."),
        ("if (err instanceof ActivityFailure && err.cause instanceof TimeoutFailure) {",
         "Infrastructure trouble is <b>not</b> the applicant's fault: route to a human "
         "instead of failing."),
        ("if (score < 600) {",
         "Business rules produce decisions (data), never exceptions."),
        ("async function decide(app: LoanApplication, decision: Decision): Promise<Decision> {",
         "Plain helper functions are fine in workflows &mdash; they're just code."),
    ],
    # ---------------------------------------------------------------- video
    'src/video-transcoding/activities.ts': [
        ("const resumeFrom: number = activityInfo().heartbeatDetails ?? 0;",
         "After a crash the retry receives the <b>last heartbeat details</b>: resume "
         "from that chunk instead of chunk 0."),
        ("encoder.encodeChunk(workDir, chunk, job.resolution),",
         "Real work (ffmpeg, an encoding API...)."),
        ("cancelled(),",
         "Rejects as soon as cancellation arrives (delivered via the heartbeat "
         "response), aborting the current chunk."),
        ("heartbeat(chunk + 1); // \"alive\" + checkpoint for retries",
         "Liveness signal <b>and</b> checkpoint. Heartbeats are throttled by the SDK, "
         "so calling it often is cheap."),
    ],
    'src/video-transcoding/workflows.ts': [
        ("startToCloseTimeout: '4 hours', // a feature film can take hours...",
         "Generous total time for legitimately long work..."),
        ("heartbeatTimeout: '2 seconds', // ...but a dead worker is detected in seconds",
         "...but no heartbeat for 2 s means the worker died: retry on another worker."),
        ("} finally {",
         "Cleanup lives in " + c("finally") + ": success, failure or cancellation."),
        ("await CancellationScope.nonCancellable(() => releaseWorkspace(workDir));",
         "Inside a cancelled workflow, new activities would be cancelled too; "
         + c("nonCancellable") + " lets the cleanup run."),
    ],
    # ------------------------------------------------------------- onboarding
    'src/onboarding/workflows.ts': [
        ("const base = workflowInfo().workflowId; // e.g. onboard-emp-42",
         "Derive child IDs from the parent ID: unique, readable, and idempotent."),
        ("const [accounts, laptopOrder] = await Promise.all([",
         "IT and Facilities run as child workflows <b>in parallel</b>."),
        ("if (!(err instanceof ChildWorkflowFailure)) throw err;",
         "A child's failure arrives as " + c("ChildWorkflowFailure") + " with the "
         "original error as " + c(".cause") + "."),
        ("payroll = 'PENDING_HR';",
         "Contain the failure: onboarding continues, HR finishes payroll by hand."),
        ("parentClosePolicy: ParentClosePolicy.ABANDON,",
         "This child keeps running after the parent completes (default would terminate "
         "it)."),
        ("export async function provisionAccountsWorkflow(emp: Employee): Promise<string[]> {",
         "Each child has its own history, retries and UI page &mdash; IT can inspect "
         "its part independently."),
        ("await sleep('30 days');",
         "A 30-day durable timer in a child that nobody waits for."),
    ],
    # ---------------------------------------------------------------- loyalty
    'src/loyalty/workflows.ts': [
        ("recentOrders: string[]; // de-duplication window for redelivered events",
         "Event sources (Kafka, webhooks) redeliver: remember recent IDs to stay "
         "idempotent."),
        ("// \"Entity workflow\": one long-lived workflow per customer account (Workflow ID",
         "The workflow <b>is</b> the account: state, rules and side effects in one "
         "place, one ID per customer."),
        ("if (state.recentOrders.includes(orderId)) return; // duplicate delivery: ignore",
         "Duplicate event: ignored (the test sends one on purpose)."),
        ("validator: (points) => {",
         "Redeeming more than the balance is rejected before it is recorded."),
        ("await sendTierChangeEmail(state.customerId, previous, tier);",
         "Side effect on a state transition (BRONZE &rarr; SILVER)."),
        ("if (events >= maxEvents || workflowInfo().continueAsNewSuggested) {",
         "Histories are capped (~50K events). Restart periodically, or when the server "
         "suggests it."),
        ("await continueAsNew<typeof loyaltyAccountWorkflow>(state); // fresh history",
         "Same Workflow ID, new run, empty history, state carried as input."),
    ],
    'test/loyalty.test.ts': [
        ("maxEventsPerRun: 5,",
         "Tiny threshold so the test crosses it."),
        ("await handle.signal(earnPoints, { orderId: 'ord_3', amountCents: 1000 });",
         "The duplicate: the balance must not change."),
        ("// Continue-as-new is asynchronous (after the tier e-mail): wait for the new run",
         "Observed: a burst of signals can be delivered in <b>one</b> workflow task, so "
         "the first run processed all 12 before continuing as new."),
        ("assert.equal(account.eventsThisRun, 0, 'the new run starts with a fresh history');",
         "Points and tier survived; the per-run counter started over."),
    ],
    # --------------------------------------------------------------- campaign
    'src/email-campaign/workflows.ts': [
        ("offset?: number; // cursor, carried across continue-as-new",
         "Progress lives in the input so a continued-as-new run picks up exactly here."),
        ("export const progress = defineQuery<CampaignProgress>('progress');",
         "A live progress bar for the marketing dashboard."),
        ("const page = await loadRecipients(listId, offset, pageSize);",
         "Load recipients page by page: payloads stay small (each is limited to 2 MB)."),
        ("const results = await Promise.allSettled(",
         "One batch in flight at a time protects the e-mail provider's rate limits."),
        ("else failed.push(batch[j].email); // bad address: record and move on",
         "Invalid addresses are non-retryable: recorded, not retried, not fatal."),
        ("if (workflowInfo().continueAsNewSuggested) {",
         "1 million recipients would exceed one history; continue-as-new with the "
         "cursor."),
    ],
    # ------------------------------------------------------------------ trips
    'src/trip-booking/workflows.ts': [
        ("const undo = proxyActivities<TripActivities>({",
         "Compensations get their own, more persistent retry policy."),
        ("retry: { initialInterval: '1 second', maximumInterval: '1 minute' }, // unlimited",
         "No " + c("maximumAttempts") + ": a cancellation must eventually succeed "
         "(the test makes it fail twice)."),
        ("compensations.unshift(() => undo.cancelFlight(flight));",
         "Register the undo only <b>after</b> the step succeeded; " + c("unshift")
         + " builds reverse order."),
        ("await CancellationScope.nonCancellable(async () => {",
         "Compensation must run even if someone cancels the booking workflow."),
        ("for (const compensate of compensations) await compensate(); // reverse order",
         "Hotel is released before the flight: last booked, first undone."),
        ("'TripRolledBack',",
         "The workflow still fails &mdash; but cleanly, with nothing left booked."),
    ],
    # ---------------------------------------------------------------- expense
    'src/expense-approval/workflows.ts': [
        ("export const decide = defineSignal<[Decision]>('decide'); // from the approval UI",
         "The approve/reject buttons in the finance tool send this signal."),
        ("decision ??= d;",
         "First decision wins; a late second click is ignored."),
        ("if (expense.amount <= AUTO_APPROVE_LIMIT) {",
         "Policy before people: small amounts never wait for a human."),
        ("if (!(await condition(() => decision !== undefined, '2 days'))) {",
         "The manager has 2 days..."),
        ("state = 'ESCALATED_TO_DIRECTOR';",
         "...then the director gets it. The query lets the UI show who is holding it up."),
        ("return { status: 'AUTO_REJECTED' };",
         "Nobody decided in 5 days: close it rather than wait forever."),
    ],
    # -------------------------------------------------------------------- kyc
    'src/kyc-verification/activities.ts': [
        ("async waitForVerdict(caseId: string): Promise<'VERIFIED' | 'REJECTED'> {",
         "One status check per attempt; the activity itself never loops or sleeps."),
        ("throw ApplicationFailure.retryable(",
         "\"Not ready yet\" = a retryable error. The retry policy becomes the polling "
         "loop."),
    ],
    'src/kyc-verification/workflows.ts': [
        ("const { waitForVerdict } = proxyActivities<KycActivities>({",
         "Proxies may be created inside the workflow, here with options from the input."),
        ("scheduleToCloseTimeout: input.giveUpAfter ?? '2 days', // all polls together",
         "Total budget across all polls."),
        ("backoffCoefficient: 1, // fixed interval: a steady poll",
         "Coefficient 1 = poll every " + c("pollEvery") + " (no exponential growth)."),
        ("(err.retryState === RetryState.TIMEOUT || err.cause instanceof TimeoutFailure)",
         "Found by the test: a deadline that expires <b>between</b> polls returns the "
         "last error with " + c("retryState TIMEOUT") + ", not a "
         + c("TimeoutFailure") + "."),
    ],
    # ---------------------------------------------------------- document review
    'src/document-review/activities.ts': [
        ("const token = Buffer.from(activityInfo().taskToken).toString('base64url');",
         "The task token identifies this exact activity attempt; base64url makes it "
         "URL-safe for a webhook."),
        ("await queue.createTask(documentId, token);",
         "Hand the token to the external system along with the work."),
        ("throw new CompleteAsyncError();",
         "\"I'll be completed later\": the activity stays open without occupying a "
         "worker slot."),
    ],
    'src/document-review/webhook.ts': [
        ("await client.activity.complete(Buffer.from(token, 'base64url'), result);",
         "Completes the waiting activity with a result; the workflow continues."),
        ("await client.activity.fail(Buffer.from(token, 'base64url'), new Error(reason));",
         "Or fails it; the workflow sees an " + c("ActivityFailure") + "."),
    ],
    # ------------------------------------------------------------- versioning
    'src/versioning/workflows-unsafe.ts': [
        ("await a.runFraudCheck(orderId); // breaks every order that started on v1",
         "On replay of a v1 history the worker expects " + c("chargeCard")
         + " here but the code schedules a fraud check: "
         + c("DeterminismViolationError") + "."),
    ],
    'src/versioning/workflows-v2.ts': [
        ("if (patched('fraud-check')) {",
         c("patched()") + " writes a marker into the history the first time it returns "
         "true; replays read that marker."),
        ("// that already passed this point without the patch",
         "Verified by the deploy test: an order waiting <i>before</i> this line when v2 "
         "was deployed still gets the fraud check."),
    ],
    'src/versioning/workflows-v3.ts': [
        ("deprecatePatch('fraud-check'); // still accepts v2 histories (with the marker)",
         "Step 2 of the cleanup: accept histories with the marker, always run the new "
         "code."),
    ],
    'test/versioning.test.ts': [
        ("await Worker.runReplayHistory({ workflowsPath: code('v2') }, v1History); // safe",
         "Replay a real v1 history against the new code: passes."),
        ("Worker.runReplayHistory({ workflowsPath: code('unsafe') }, v1History),",
         "The unsafe change is caught <b>in CI</b>, before any production order breaks."),
        ("const fresh = { maxCachedWorkflows: 0 };",
         "Without a cache every task replays from history, like a freshly deployed "
         "worker. (The time-skipping server doesn't reroute sticky tasks from a stopped "
         "worker; a real server does after ~5 s.)"),
        ("assert.deepEqual(steps('A'), ['reserve', 'fraud-check', 'charge']);",
         "The in-flight order took the <b>new</b> path &mdash; and replay stayed "
         "deterministic."),
        ("Worker.runReplayHistory({ workflowsPath: code('v3') }, v1History),",
         "Deprecating while v1 orders still run would break them: wait until they "
         "finish."),
    ],
    # ---------------------------------------------------------------- helpers
    'test/helpers.ts': [
        ("export async function startWorker(",
         "One background worker per test file, stopped in " + c("after()") + "."),
        ("extra: Partial<WorkerOptions> = {},",
         "Per-test worker options (e.g. " + c("maxCachedWorkflows") + ")."),
        ("export function rootCause(err: unknown): Error | undefined {",
         "Failures are nested (Workflow &rarr; Activity &rarr; Application); tests "
         "assert on the root."),
    ],
}
