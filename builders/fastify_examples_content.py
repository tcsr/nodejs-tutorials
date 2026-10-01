# Real-world example sections for the Fastify tutorial. Executed inside the builder:
# only defines functions; the builder calls them at the right places.
import callouts_fastify_examples

from paths import project
FX = project('fastify-examples')


def fx_file(path, caption=None):
    """Embed a fastify-examples file verbatim, annotated when notes exist."""
    src = open(os.path.join(FX, path), encoding='utf8').read().rstrip('\n')
    body = '// ' + path + '\n' + src
    notes = callouts_fastify_examples.FASTIFY_EXAMPLES.get(path)
    if notes:
        for f in annotated(body, caption, notes, path, CODE, BODY, ACCENT, CAPTION):
            story.append(f)
    else:
        _plain_code(body, caption)


def fx_scenario(num, title, situation, why):
    h2(f"{num} Real-world example: {title}")
    p("<b>The situation.</b> " + situation)
    p("<b>Why it works well in Fastify:</b>")
    bullets(why)


def fx_proves(test_file, rows):
    p("<b>What the tests prove</b> (" + c(f"test/{test_file}") + ", all passing):")
    table([["Test", "Verified behaviour"]] + rows, [62 * mm, 108 * mm])


def fx_catalog(num):
    fx_scenario(num, "an e-commerce catalog API",
        "A shop exposes products by SKU, category pages of any depth, and a price "
        "endpoint whose response format changed (v1 cents, v2 money object) while old "
        "mobile apps are still in use. The old PHP site's links must keep working.",
        ["Regex parameters reject malformed IDs at the router.",
         "Version constraints serve two contracts on one URL.",
         "Prefixes and redirects keep URL design flexible."])
    fx_file('src/catalog/app.ts')
    fx_proves('catalog.test.ts', [
        ["a well-formed SKU matches the product route", "PHN-10021 &rarr; 200; "
         "unknown but valid SKU &rarr; handler's 404."],
        ["a malformed SKU never reaches the handler",
         c("/api/products/phone") + " &rarr; router 404 (\"Route ... not found\")."],
        ["the wildcard turns a category path into a breadcrumb",
         "[electronics, phones, android]."],
        ["Accept-Version selects the contract; no header gets the latest",
         c("1.x") + " &rarr; cents, " + c("2.x") + " and no header &rarr; money object."],
        ["legacy URLs are permanently redirected",
         c("/item.php?id=LAP-20450") + " &rarr; 301 to the API URL."],
    ])


def fx_downloads(num):
    fx_scenario(num, "CSV exports and cacheable product data",
        "Accounting downloads a month of orders as CSV (hundreds of thousands of rows); "
        "the storefront polls product data that rarely changes.",
        ["Return a stream and Fastify pipes it: constant memory for any export size.",
         "Headers (" + c("Content-Disposition") + ", " + c("ETag") + ") are one call "
         "each.",
         "HEAD requests are answered automatically."])
    fx_file('src/downloads/app.ts')
    fx_proves('downloads.test.ts', [
        ["streams a CSV attachment with correctly escaped cells",
         "1,000 rows streamed; attachment filename; " + c('Smith, "Jo"') + " escaped."],
        ["rejects an invalid date range before touching the database",
         c("from=yesterday") + " &rarr; 400; the source was never called."],
        ["conditional GET: a matching ETag gets 304 with no body", "304, empty body."],
        ["HEAD requests are answered automatically, without a body",
         "200 with the ETag header, no body."],
    ])


def fx_tracking(num):
    fx_scenario(num, "live order tracking (Server-Sent Events)",
        "Customers keep the tracking page open while the order moves from PLACED to "
        "DELIVERED. Couriers and the warehouse report status changes.",
        ["SSE needs only " + c("reply.hijack()") + " and a few headers; browsers "
         "reconnect by themselves.",
         "Simpler than WebSockets for one-way server-to-browser updates.",
         "Cleaning up on disconnect is the part people forget &mdash; it's tested."])
    fx_file('src/order-tracking/app.ts')
    fx_file('test/order-tracking.test.ts')
    fx_proves('order-tracking.test.ts', [
        ["the tracking page receives every status change as it happens",
         "PLACED (current state) then four live updates; the stream ends at DELIVERED."],
        ["closing the page unsubscribes (no leaked listeners)",
         "Listener count goes 1 &rarr; 0 after the client aborts (~240 ms with a "
         "200 ms ping)."],
    ])


def fx_signup(num):
    fx_scenario(num, "user sign-up",
        "A sign-up form posts email, password, name, country and a marketing opt-in. "
        "The form wants every error at once; the API must never return the password "
        "hash; partners need OpenAPI docs.",
        ["One TypeBox schema validates, coerces, documents and types the handler.",
         "Response schemas whitelist output fields.",
         "OpenAPI is generated from the same schemas &mdash; it can't drift."])
    fx_file('src/signup/app.ts')
    fx_proves('signup.test.ts', [
        ["valid sign-up: 201, defaults applied, password hash never sent",
         "Email lower-cased, opt-in defaulted to false, no hash or password in the "
         "response."],
        ["every invalid field is reported at once",
         "email, password, name and country all listed."],
        ["unknown properties are stripped: no setting internal fields",
         c("id: 'admin'") + " in the body is ignored."],
        ["query strings are coerced to the schema types",
         c("optedIn=true") + " filters as a boolean; " + c("limit=500") + " &rarr; 400."],
        ["the same schemas generate the OpenAPI document",
         "Required fields and " + c("minLength: 12") + " appear in the spec."],
    ])


def fx_tenant(num):
    fx_scenario(num, "a multi-tenant SaaS (plugins + decorators)",
        "One deployment serves many companies: " + c("acme.app.example.com") + ", "
        + c("globex.app.example.com") + ". Every request must be tied to a tenant, "
        "each tenant sees only its data, and an admin area per tenant needs its own key.",
        ["A shared " + c("fp()") + " plugin resolves the tenant once and decorates the "
         "request.",
         "Encapsulation keeps the admin hook and decorator out of the public API.",
         "The structure is visible in the code: shared infrastructure, then feature "
         "plugins."])
    fx_file('src/multi-tenant/tenants.ts')
    fx_file('src/multi-tenant/app.ts')
    fx_proves('multi-tenant.test.ts', [
        ["the subdomain selects the tenant; each tenant sees only its data",
         "Acme sees Website; Globex sees Rocket."],
        ["an unknown workspace is rejected by the shared hook", "404."],
        ["the admin hook protects only the admin area",
         "No key 401, other tenant's key 401, right key 201; audit entry recorded."],
        ["encapsulation: the admin decorator is invisible to public routes",
         c("hasDecorator('audit')") + " is false in the public plugin; "
         + c("tenants") + " is visible app-wide."],
    ])


def fx_observability(num):
    fx_scenario(num, "production observability with hooks",
        "Operations needs to trace a request across services, see server timing, audit "
        "every change, switch the API into maintenance mode, and be sure no password "
        "or token ever lands in the logs.",
        ["Each concern is one hook at the right lifecycle stage.",
         "Pino redaction is declarative.",
         c("onResponse") + " work never delays the client."])
    fx_file('src/observability/app.ts')
    fx_proves('observability.test.ts', [
        ["the caller's request ID is propagated, server timing is exposed",
         "Incoming " + c("x-request-id") + " echoed; otherwise a UUID; "
         + c("server-timing") + " present."],
        ["secrets are redacted; every log line carries the request ID",
         "Authorization header and password show [REDACTED]; " + c("hunter2")
         + " appears nowhere."],
        ["mutating requests are audited after the response",
         "POST audited with status 200; GET not audited."],
        ["maintenance mode answers 503 early but keeps /health up",
         "503 + Retry-After 120; health still 200; back to normal when switched off."],
    ])


def fx_problems(num):
    fx_scenario(num, "bank transfers with RFC 9457 problem details",
        "A banking API must return machine-readable errors that client apps can branch "
        "on (insufficient funds, unknown account), without leaking internals when "
        "something breaks.",
        ["Domain errors are classes with codes; handlers just throw.",
         "One error handler and one not-found handler define the whole error contract.",
         "The same shape for validation errors, domain errors, 404s and 500s."])
    fx_file('src/problem-details/app.ts')
    fx_proves('problem-details.test.ts', [
        ["a valid transfer moves money", "201; balances updated."],
        ["domain errors become RFC 9457 problem details",
         "422 " + c("application/problem+json") + " with type, title, status, detail, "
         "instance; unknown account 404."],
        ["validation errors list the invalid parameters",
         "400 with " + c("invalid-params") + "."],
        ["unexpected errors hide their details from clients",
         "500 with a generic detail; the password in the error message is not sent."],
        ["unknown routes get a problem document too", "404 route-not-found problem."],
    ])


def fx_webhooks(num):
    fx_scenario(num, "payment-provider webhooks",
        "The payment provider POSTs events (payment succeeded, refund created) to the "
        "API. Requests must be authenticated by an HMAC signature over the raw body, "
        "replays must be refused, and retried deliveries processed only once.",
        ["An encapsulated content-type parser keeps the raw body for this route only.",
         "Signature, freshness and idempotency are each a few lines.",
         "The rest of the app keeps normal JSON parsing."])
    fx_file('src/webhooks/app.ts')
    fx_file('test/webhooks.test.ts')
    fx_proves('webhooks.test.ts', [
        ["a correctly signed event is accepted and handled once", "200, handled."],
        ["a retried delivery is acknowledged, not re-processed",
         "200 duplicate: true; handler not called again."],
        ["a tampered body is rejected (the signature covers the raw bytes)",
         "Changed amount &rarr; 401; re-formatted identical JSON &rarr; 401."],
        ["a replayed request older than 5 minutes is rejected", "401 stale timestamp."],
        ["the raw-body parser is encapsulated: other routes parse JSON",
         c("/echo") + " receives an object."],
    ])


def fx_inventory(num):
    fx_scenario(num, "inventory reservations in SQL",
        "Checkout reserves stock for every line of an order. If any line is short, "
        "nothing may be reserved; two simultaneous checkouts must never oversell.",
        ["A database plugin owns the connection lifecycle (open at boot, close on "
         "shutdown).",
         "A transaction plus conditional UPDATEs make the reservation atomic.",
         "Domain errors map to precise HTTP codes (409, 404)."])
    fx_file('src/inventory/db.ts')
    fx_file('src/inventory/app.ts')
    fx_proves('inventory.test.ts', [
        ["an order reserves stock for every line", "MUG 10 &rarr; 7, TEE 2 &rarr; 1."],
        ["one short line rolls back the whole order",
         "409 \"Only 1 of TEE left, 5 requested\"; MUG unchanged at 7."],
        ["unknown products are a 404, and nothing is reserved", "MUG unchanged."],
        ["the database is closed when the app closes",
         "Using " + c("app.db") + " after " + c("app.close()") + " throws."],
    ])


def fx_auth(num):
    fx_scenario(num, "login, roles and refresh-token rotation",
        "A B2B dashboard: people log in (short-lived access tokens + refresh tokens), "
        "admins can delete users, analysts see revenue, and a nightly ETL job reads "
        "reports with an API key.",
        ["Authentication in " + c("onRequest") + ", authorization in "
         + c("preHandler") + ": 401 vs 403 fall out naturally.",
         c("@fastify/auth") + " combines JWT and API keys on one route.",
         "Refresh rotation with reuse detection stops stolen refresh tokens."])
    fx_file('src/auth-rbac/app.ts')
    fx_file('test/auth-rbac.test.ts')
    fx_proves('auth-rbac.test.ts', [
        ["authentication: no token 401, valid token identifies the user", "/me &rarr; u1."],
        ["authorization: users get 403 on admin routes, admins get through",
         "403 vs 204."],
        ["refresh tokens rotate; reusing an old one revokes the session",
         "New pair on refresh; replaying the old token &rarr; 401 and the newer token "
         "is revoked too."],
        ["reports accept a JWT with the analyst role OR a service API key",
         "Admin+analyst 200, plain user 403, API key 200, wrong key 401."],
    ])


def fx_security(num):
    fx_scenario(num, "hardening a public API",
        "A storefront's API runs behind a load balancer and is called from the shop's "
        "own web app. Bots try password lists against the login.",
        ["Helmet, CORS and rate limiting are one " + c("register()") + " each.",
         "Per-route options tighten limits exactly where needed.",
         "The tests caught a limiter that would have locked out whole offices."])
    fx_file('src/security/app.ts')
    fx_proves('security.test.ts', [
        ["security headers are set on every response",
         "HSTS, nosniff, CSP present; no " + c("x-powered-by") + "."],
        ["CORS: the storefront may call the API, other sites may not",
         "Allowed origin echoed with credentials; other origin gets no CORS headers."],
        ["behind a proxy, request.ip is the real client", c("203.0.113.9") + "."],
        ["brute force: the 6th login for one user from one IP gets 429",
         "5 &times; 200 then 429 + Retry-After; another user and another IP still 200."],
        ["oversized bodies get 413 before reaching the handler", "2 KB to a 1 KB route."],
    ])


def fx_uploads(num):
    fx_scenario(num, "profile picture uploads",
        "Users upload avatars. Attackers upload scripts named " + c("cat.png") + ", "
        "huge files, and names like " + c("../../etc/passwd.png") + ".",
        ["Streaming multipart: files never sit fully in memory.",
         "Content sniffing (magic bytes) instead of trusting headers.",
         "Random server-side file names."])
    fx_file('src/uploads/app.ts')
    fx_proves('uploads.test.ts', [
        ["a PNG is stored under a random name", "201; one file named "
         + c("<uuid>.png") + " in the upload dir."],
        ["a script renamed to .png is rejected by its content", "415."],
        ["a file over the limit is rejected and the partial file removed",
         "413; no file left behind."],
    ])


def fx_chat(num):
    fx_scenario(num, "support chat rooms (WebSockets)",
        "Customers and support agents chat in a room per ticket. Only authenticated "
        "users may connect; rooms must not see each other's messages.",
        ["WebSocket routes are normal routes: same hooks, same auth.",
         "Rejecting in " + c("preValidation") + " means no socket is ever opened.",
         "Tested with Node's built-in WebSocket client."])
    fx_file('src/chat/app.ts')
    fx_proves('chat.test.ts', [
        ["customer and agent in one ticket room see each other's messages",
         "Join notice, message delivered with the sender, leave notice with online=1."],
        ["rooms are isolated", "A message in ticket-1 never reaches ticket-2."],
        ["an invalid token is refused before the socket opens",
         "The client's connection fails."],
    ])


def fx_shutdown(num):
    fx_scenario(num, "zero-downtime deploys (graceful shutdown)",
        "Kubernetes sends SIGTERM during every rolling deploy. Customers downloading a "
        "report at that moment must get the full response; the database and metrics "
        "must be flushed after the last request.",
        ["Lifecycle hooks: " + c("preClose") + " (stop advertising readiness), "
         + c("onClose") + " (release resources).",
         c("app.close()") + " waits for in-flight requests.",
         "The test measured a 71-second shutdown before the keep-alive fix."])
    fx_file('src/graceful-shutdown/app.ts')
    fx_file('test/graceful-shutdown.test.ts')
    warn("Measured: after " + c("close()") + " started, the in-flight request's "
         "keep-alive socket became idle and held the server open for "
         "<b>71 seconds</b> (Fastify's default " + c("keepAliveTimeout")
         + " is 72 s). Sending " + c("Connection: close") + " during shutdown fixed it "
         "(&lt; 1 s).")


def fx_testing(num):
    h2(f"{num} The real-world examples test suite")
    p("All 14 scenarios live in " + c("fastify-examples/") + ", one test file each, "
      "using Node's test runner. Most use " + c("inject()") + "; streaming, uploads, "
      "WebSockets and shutdown listen on a random port and use " + c("fetch") + " / "
      + c("WebSocket") + ".")
    code("""
npm test        # node --import tsx --test --test-concurrency=4 test/*.test.ts
# tests 54, pass 54, fail 0   (about 10 s on a laptop)
""")
    table([
        ["Test file", "Tests", "Technique worth copying"],
        [c("catalog"), "5", "Assert router 404s vs handler 404s"],
        [c("downloads"), "4", "Async generator as a fake DB cursor"],
        [c("order-tracking"), "2", "Read SSE with fetch; abort and check listeners"],
        [c("signup"), "5", "Inspect " + c("app.swagger()") + " in a test"],
        [c("multi-tenant"), "4", "Host header selects the tenant"],
        [c("observability"), "4", "Capture logs via a custom stream"],
        [c("problem-details"), "5", "Assert the full error contract"],
        [c("webhooks"), "5", "Sign like the provider; fixed clock"],
        [c("inventory"), "4", "In-memory SQLite; verify rollback"],
        [c("auth-rbac"), "4", "Replay a refresh token like an attacker"],
        [c("security"), "5", "X-Forwarded-For to simulate many clients"],
        [c("uploads"), "3", "Real multipart via FormData + Blob"],
        [c("chat"), "3", "Built-in WebSocket client"],
        [c("graceful-shutdown"), "1", "Close during an in-flight request"],
    ], [42 * mm, 14 * mm, 114 * mm])
