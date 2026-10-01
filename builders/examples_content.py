# Real-world example sections for the Temporal tutorial. Executed inside the builder:
# only defines functions; the builder calls them at the right places.
import callouts_examples

from paths import project
EX = project('temporal-examples')


def ex_file(path, caption=None):
    """Embed a temporal-examples file verbatim, annotated when notes exist."""
    src = open(os.path.join(EX, path), encoding='utf8').read().rstrip('\n')
    body = '// ' + path + '\n' + src
    notes = callouts_examples.EXAMPLES.get(path)
    if notes:
        for f in annotated(body, caption, notes, path, CODE, BODY, ACCENT, CAPTION):
            story.append(f)
    else:
        _plain_code(body, caption)


def scenario(num, title, situation, why):
    h2(f"{num} Real-world example: {title}")
    p("<b>The situation.</b> " + situation)
    p("<b>Why Temporal fits:</b>")
    bullets(why)


def proves(test_file, rows):
    p("<b>What the tests prove</b> (" + c(f"test/{test_file}") + ", all passing):")
    table([["Test", "Verified behaviour"]] + rows, [62 * mm, 108 * mm])


# ------------------------------------------------------------------ chapter 6
def ex_payments(num):
    scenario(num, "charging a card",
        "A checkout calls a payment provider. Providers have bad minutes: 503s, "
        "timeouts, rate limits. Some failures are final (card declined, invalid amount) "
        "and must not be retried; others are transient and must be &mdash; without ever "
        "charging the customer twice.",
        ["Retries with exponential back-off are configuration, not code.",
         "Typed failures separate <i>declined</i> (a business result) from "
         "<i>broken</i> (an error).",
         "A stable payment ID doubles as the provider's idempotency key, so retries "
         "are safe."])
    ex_file('src/payments/activities.ts')
    ex_file('src/payments/workflows.ts')
    ex_file('test/payments.test.ts')
    proves('payments.test.ts', [
        ["transient gateway errors are retried until the charge succeeds",
         "Two 503s, then success: exactly 3 gateway calls, receipt sent, result PAID."],
        ["a declined card is a business outcome, not a failure",
         "Workflow <b>completes</b> with DECLINED; 1 call only (non-retryable)."],
        ["an invalid amount fails the workflow without calling the gateway",
         "Workflow FAILED; root cause " + c("InvalidAmount") + "; 0 gateway calls."],
    ])


# ------------------------------------------------------------------ chapter 7
def ex_travel(num):
    scenario(num, "flight search across providers",
        "A travel site queries three airline/aggregator APIs for every search and "
        "shows the cheapest offer. Each API takes ~500 ms; one is down today.",
        ["Parallel activities with " + c("Promise.allSettled") + " &mdash; fan-out and "
         "fan-in in plain TypeScript.",
         "A local activity validates the query without a task-queue round trip.",
         "One failing provider degrades the result instead of breaking the search."])
    ex_file('src/travel-search/workflows.ts')
    proves('travel-search.test.ts', [
        ["searches providers in parallel and returns the cheapest offer",
         "Three 500 ms providers finish in &lt; 1.5 s (concurrent); cheapest from "
         + c("jetnow") + "; " + c("budgetfly") + " reported as failed."],
        ["an invalid query is rejected by the local activity",
         "Same origin and destination: workflow FAILED with the validation message."],
    ])


# ----------------------------------------------------------------- chapter 11
def ex_cart(num):
    scenario(num, "a shopping cart",
        "Each shopper's cart is a workflow (ID " + c("cart-{userId}") + "). The "
        "storefront adds and removes items, shows the cart, applies coupons and checks "
        "out. Abandoned carts get one reminder after 24 hours and expire after 48.",
        ["Signals for fire-and-forget changes, a query for the cart page, updates for "
         "operations that need an answer (coupon %, order ID).",
         "Update validators reject bad requests before they touch history.",
         "Idle detection with " + c("condition") + " + timeout: no cron, no sweeper job."])
    ex_file('src/shopping-cart/workflows.ts')
    ex_file('test/shopping-cart.test.ts')
    proves('shopping-cart.test.ts', [
        ["signals change the cart, queries read it, updates reply",
         "Merged quantities, removal, invalid coupon rejected, SAVE10 = 10 %, checkout "
         "returns the order ID, total 2700."],
        ["an abandoned cart gets one reminder, then expires",
         "Exactly one reminder e-mail, result EXPIRED (48 h skipped)."],
        ["checkout of an empty cart is rejected",
         "Validator rejects; nothing recorded."],
    ])


# ----------------------------------------------------------------- chapter 12
def ex_trial(num):
    scenario(num, "a 14-day free trial",
        "Every SaaS sign-up starts a trial: welcome e-mail, reminder on day 11, "
        "downgrade on day 14 &mdash; unless the customer upgrades first.",
        ["One workflow per sign-up holds the whole lifecycle; no nightly batch job.",
         "Timers survive deploys and outages and cost nothing while waiting.",
         "Tests run 14 days in seconds."])
    ex_file('src/free-trial/workflows.ts')
    ex_file('test/free-trial.test.ts')
    proves('free-trial.test.ts', [
        ["14 silent days: reminder on day 11, downgrade on day 14",
         "E-mails and downgrade in the right order; whole run &lt; 10 s."],
        ["upgrading on day 5 converts immediately, no reminder",
         "Query shows TRIAL_ACTIVE on day 5; signal converts; no downgrade."],
    ])


def ex_reports(num):
    scenario(num, "the nightly sales report",
        "Finance wants yesterday's sales per region in their inbox at 02:30 India time, "
        "every day, even if the server was briefly down at that moment.",
        ["Schedules replace cron: time zones, overlap and catch-up policies, "
         "pause/trigger from code, CLI or UI.",
         "Each run is an ordinary workflow with retries and history."])
    ex_file('src/reports/workflows.ts')
    ex_file('src/reports/schedule.ts')
    ex_file('test/reports.test.ts')
    proves('reports.test.ts', [
        ["nightly schedule: next run 02:30 IST, trigger, pause, delete",
         "Next action time is 21:00 UTC; a manual trigger e-mails both recipients; "
         "pause sets " + c("state.paused") + ". Runs on the real dev server."],
    ])


# ----------------------------------------------------------------- chapter 13
def ex_loan(num):
    scenario(num, "a loan application",
        "An application is validated, scored by a credit bureau (2-second SLA), "
        "fraud-checked and decided. The bureau sometimes hangs.",
        ["Three kinds of outcome, three mechanisms: <b>invalid input</b> fails the "
         "workflow, <b>business rules</b> return a decision, <b>infrastructure "
         "trouble</b> is caught and routed to a human.",
         "Timeouts are typed (" + c("TimeoutFailure") + ") and can be handled like any "
         "other error."])
    ex_file('src/loan-application/workflows.ts')
    proves('loan-application.test.ts', [
        ["good credit is approved at the best rate", "Score 780 &rarr; APPROVED, 8.5 %."],
        ["low credit is a rejection (a result, not an error)",
         "Score 540 &rarr; REJECTED; the workflow <b>completes</b>."],
        ["high fraud risk goes to manual review", "MANUAL_REVIEW."],
        ["a bureau timeout degrades to manual review instead of failing",
         "Bureau sleeps 3 s vs. 2 s SLA, twice &rarr; MANUAL_REVIEW. (Takes ~4 s of "
         "real time: activity timeouts are not skipped while the activity runs.)"],
        ["invalid input fails the workflow with a typed error",
         "Loan &gt; 5&times; income &rarr; FAILED, root " + c("InvalidApplication") + "."],
    ])


# ----------------------------------------------------------------- chapter 14
def ex_video(num):
    scenario(num, "video transcoding",
        "Uploaded videos are transcoded chunk by chunk (minutes to hours). Workers can "
        "crash mid-job, and users can cancel. Scratch storage must always be freed.",
        ["Heartbeats detect a dead worker in seconds even for 4-hour jobs.",
         "Heartbeat details are a checkpoint: the retry resumes where the crash happened.",
         "Cancellation reaches the running activity; cleanup still runs."])
    ex_file('src/video-transcoding/activities.ts')
    ex_file('src/video-transcoding/workflows.ts')
    proves('video-transcoding.test.ts', [
        ["a crash mid-job resumes from the last heartbeat, not from zero",
         "Chunk 6 crashes once; the log shows " + c("resumeFrom: 6") + "; all 10 chunks "
         "encoded, far fewer than 20 calls; workspace released."],
        ["cancelling the job stops encoding and still frees the workspace",
         "Cancel after ~1 s of a 10 s job: result is " + c("CancelledFailure") + ", only "
         "part of the 100 chunks encoded, workspace released."],
    ])
    note("The worker logs that keeping heartbeat details on activity <b>failure</b> needs "
         "Temporal Server 1.16+. The time-skipping test server doesn't advertise it (the "
         "test still passed); the dev server (1.32) and Temporal Cloud guarantee it.")


# ----------------------------------------------------------------- chapter 15
def ex_onboarding(num):
    scenario(num, "employee onboarding",
        "A new hire needs accounts (IT), a laptop (Facilities) and payroll (Finance), "
        "plus a records clean-up 30 days later. Departments own their parts.",
        ["Child workflows give each department its own execution, history and UI page.",
         "Children run in parallel; a failing child is handled, not fatal.",
         c("ParentClosePolicy.ABANDON") + " lets the 30-day child outlive the parent."])
    ex_file('src/onboarding/workflows.ts')
    proves('onboarding.test.ts', [
        ["departments run as child workflows; the parent combines results",
         "Summary has all accounts, the right laptop and payroll; " + c("...-it")
         + " is COMPLETED, " + c("...-retention") + " is still RUNNING."],
        ["a failing child is handled by the parent, onboarding continues",
         "Missing bank details &rarr; payroll PENDING_HR, HR notified with the root "
         "cause."],
    ])


def ex_loyalty(num):
    scenario(num, "a loyalty-points account (entity workflow)",
        "Every customer has a points balance and tier. Orders arrive as events (with "
        "occasional duplicates), customers redeem points, and the account lives for "
        "years.",
        ["One workflow per customer is the account: no separate state table.",
         "Updates validate redemptions; queries serve the balance.",
         "Continue-as-new keeps the history small forever."])
    ex_file('src/loyalty/workflows.ts')
    ex_file('test/loyalty.test.ts')
    proves('loyalty.test.ts', [
        ["one workflow per customer, continued-as-new to stay small",
         "12 orders + 1 duplicate &rarr; 120 points, SILVER, one tier e-mail; new run "
         "ID; counter reset; over-redeem rejected; redeem 50 &rarr; 70."],
    ])


def ex_campaign(num):
    scenario(num, "an e-mail campaign",
        "Marketing sends a campaign to a mailing list. The provider allows limited "
        "concurrency, some addresses are invalid, and lists can have millions of "
        "entries.",
        ["Bounded fan-out: batches of parallel activities.",
         "Pagination + continue-as-new handle lists of any size.",
         "A query gives the dashboard live progress."])
    ex_file('src/email-campaign/workflows.ts')
    proves('email-campaign.test.ts', [
        ["sends to every valid address in bounded batches, skips bad ones",
         "120 recipients, 3 invalid: 117 sent, 3 failed, nobody twice, never more than "
         "10 in flight, progress query correct."],
    ])


# ----------------------------------------------------------------- chapter 16
def ex_trip(num):
    scenario(num, "booking a trip (saga)",
        "A trip needs a flight, a hotel and a rental car from three different "
        "suppliers. If the car is sold out, the flight and hotel must be cancelled "
        "&mdash; even if the hotel's cancellation API is flaky.",
        ["No distributed transactions across suppliers: compensate instead.",
         "Compensations are activities with their own (unlimited) retry policy.",
         "The order of undo is guaranteed by plain code."])
    ex_file('src/trip-booking/workflows.ts')
    proves('trip-booking.test.ts', [
        ["all three suppliers confirm: the trip is booked",
         "Flight, hotel, car booked in order."],
        ["car sold out: hotel and flight are cancelled in reverse order",
         "Journal is book flight, book hotel, cancel hotel, cancel flight; the hotel "
         "cancellation failed twice and was retried; workflow fails with "
         "\"rolled back\"."],
    ])


def ex_expense(num):
    scenario(num, "expense approval with escalation",
        "Employees submit expenses. Small ones are auto-approved; others need the "
        "manager within 2 days, then the director within 3 more, else they are "
        "auto-rejected.",
        ["Days-long waits are just " + c("condition") + " with a timeout.",
         "Signals carry decisions from the finance UI; a query shows who is "
         "blocking.",
         "The whole policy is readable top-to-bottom in one function."])
    ex_file('src/expense-approval/workflows.ts')
    proves('expense-approval.test.ts', [
        ["small expenses are approved by policy without bothering anyone",
         "35 &rarr; PAID by \"policy\"."],
        ["the manager approves within 2 days", "State WAITING_FOR_MANAGER, then PAID."],
        ["a silent manager escalates to the director, who rejects",
         "After 49 h: ESCALATED_TO_DIRECTOR; rejection recorded; notifications to "
         "manager, director, employee."],
        ["nobody decides within 5 days: auto-rejected", "AUTO_REJECTED."],
    ])


def ex_kyc(num):
    scenario(num, "identity verification (polling)",
        "A fintech submits a customer's documents to a KYC provider that has no "
        "webhooks. The verdict can take minutes or days; after a deadline the case "
        "goes to manual review.",
        ["The retry policy <i>is</i> the polling loop: fixed interval, total deadline.",
         "No sleeping activities, no hand-written loops.",
         "One subtle detail about deadlines, found by the test (callout 4)."])
    ex_file('src/kyc-verification/activities.ts')
    ex_file('src/kyc-verification/workflows.ts')
    proves('kyc-verification.test.ts', [
        ["polls the provider every minute until the verdict arrives",
         "3 &times; PENDING then VERIFIED: exactly 4 polls."],
        ["no verdict before the deadline: falls back to manual review",
         "10-minute deadline, 1-minute interval: ~10 polls, then MANUAL_REVIEW."],
    ])


def ex_review(num):
    scenario(num, "human document review (async completion)",
        "Uploaded contracts are reviewed by a person in an external back-office tool. "
        "The tool calls a webhook when the reviewer decides &mdash; maybe days later.",
        ["The activity hands its task token to the tool and returns without a result.",
         "The webhook completes (or fails) that exact activity from outside.",
         "No polling, no worker slot held while humans think."])
    ex_file('src/document-review/activities.ts')
    ex_file('src/document-review/webhook.ts')
    proves('document-review.test.ts', [
        ["reviewer approves via webhook: the waiting activity completes",
         "Result APPROVED; document archived."],
        ["the reviewer reports the document as unreadable",
         c("client.activity.fail") + " &rarr; workflow handles it &rarr; UNREADABLE."],
    ])


# ----------------------------------------------------------------- chapter 17
def ex_versioning(num):
    scenario(num, "adding a fraud check to live checkouts",
        "Checkout reserves stock, waits for the customer's 3-D Secure confirmation, "
        "then charges. Risk wants a fraud check before charging &mdash; deployed while "
        "orders are waiting.",
        ["Replay tests prove a change is safe <b>before</b> deploying.",
         c("patched()") + " lets old and new histories coexist; "
         + c("deprecatePatch()") + " cleans up later.",
         "The deploy test shows what really happens to in-flight orders."])
    ex_file('src/versioning/workflows-v1.ts', "v1 (in production)")
    ex_file('src/versioning/workflows-unsafe.ts', "v2, done wrong")
    ex_file('src/versioning/workflows-v2.ts', "v2, done right")
    ex_file('src/versioning/workflows-v3.ts', "v3, cleanup")
    ex_file('test/versioning.test.ts')
    proves('versioning.test.ts', [
        ["replay tests catch an unsafe change before it reaches production",
         "A real v1 history replays on v2; on the unsafe version it throws "
         + c("DeterminismViolationError") + "."],
        ["deploy mid-order: the order takes the new path when it gets there",
         "Order A (started on v1, waiting) finishes on v2 <b>with</b> the fraud check; "
         "new order B too."],
        ["deprecatePatch (v3) only after all pre-patch orders finished",
         "v2 histories replay on v3; v1 histories do not."],
    ])
    warn("A common misconception: \"" + c("patched()") + " keeps in-flight workflows on "
         "the old path.\" It only does so for history that already passed that line. A "
         "workflow still waiting <i>before</i> it will run the new code when it gets "
         "there, as the test shows. If in-flight executions must not get the new step, "
         "route them by version explicitly or use Worker Versioning.")


# ----------------------------------------------------------------- chapter 18
def ex_testing(num):
    h2(f"{num} The real-world examples test suite")
    p("All 15 scenarios in this guide live in " + c("temporal-examples/") + " with one "
      "test file each. Every test file starts its own time-skipping server (the "
      "schedule test uses the real dev server) and one worker:")
    ex_file('test/helpers.ts')
    code("""
npm test        # node --import tsx --test --test-concurrency=3 test/*.test.ts
# tests 35, pass 35, fail 0   (about 30 s on a laptop)
npm run format  # prettier; npm run typecheck: tsc --noEmit
""")
    table([
        ["Test file", "Tests", "Technique worth copying"],
        [c("payments"), "3", "Fake gateway that fails on demand; count calls"],
        [c("travel-search"), "2", "Measure wall time to prove parallelism"],
        [c("shopping-cart"), "3", "Signals, queries and updates against one handle"],
        [c("free-trial"), "2", c("env.sleep('5 days')") + ", then signal"],
        [c("reports"), "1", c("createLocal()") + " for features needing a full server"],
        [c("loan-application"), "5", "Slow fake to trigger a real timeout"],
        [c("video-transcoding"), "2", "Crash once, assert resume point; cancel mid-run"],
        [c("onboarding"), "2", "Describe child executions by derived IDs"],
        [c("loyalty"), "1", "Wait for the new run ID after continue-as-new"],
        [c("email-campaign"), "1", "Track max concurrency in the fake provider"],
        [c("trip-booking"), "2", "Journal of side effects; flaky compensation"],
        [c("expense-approval"), "4", "Advance time past each escalation deadline"],
        [c("kyc-verification"), "2", "Count polls; deadline between attempts"],
        [c("document-review"), "2", "Complete an activity from \"outside\""],
        [c("versioning"), "3", "Replay real histories; swap code mid-execution"],
    ], [42 * mm, 14 * mm, 114 * mm])
