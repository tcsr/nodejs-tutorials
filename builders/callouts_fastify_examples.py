"""Callout notes for fastify-examples/ (anchors: exact substrings, matched in order)."""
from callouts import c

FASTIFY_EXAMPLES = {
    # ---------------------------------------------------------------- catalog
    'src/catalog/app.ts': [
        ("app.get('/products/:sku(^[A-Z]{3}-\\\\d{5}$)', async (request, reply) => {",
         "Regex parameter: " + c("/products/phone") + " doesn't even match this route "
         "&mdash; no handler code needed to reject it."),
        ("app.get('/categories/*', async (request) => {",
         "Wildcard: everything after " + c("/categories/") + " arrives in "
         + c("params['*']") + "."),
        ("constraints: { version: '1.0.0' },",
         "Version constraint: matched against the " + c("Accept-Version") + " header "
         "(semver ranges like " + c("1.x") + " work)."),
        ("app.get('/prices/:sku', { schema: { params: PriceParams } }, async (request) =>",
         "The unversioned twin answers clients that send no header &mdash; here with the "
         "latest contract."),
        ("await app.register(catalogRoutes, { prefix: '/api' });",
         "A prefix applies to every route in the plugin."),
        ("reply.redirect(`/api/products/${encodeURIComponent(request.query.id)}`, 301),",
         "301 keeps search-engine ranking when URLs change; always encode user input "
         "placed in a URL."),
    ],
    # -------------------------------------------------------------- downloads
    'src/downloads/app.ts': [
        ("orders(from: string, to: string): AsyncIterable<Order>;",
         "Rows come from an async iterator (DB cursor): memory stays flat for any "
         "export size."),
        ("/[\",\\n]/.test(String(v)) ? `\"${String(v).replace(/\"/g, '\"\"')}\"` : String(v);",
         "CSV escaping: quotes, commas and newlines inside a value must be quoted "
         "(tested with " + c('Smith, "Jo"') + ")."),
        ("from: Type.String({ format: 'date' }),",
         "Bad dates are rejected before any database work starts."),
        ("`attachment; filename=\"orders-${from}_${to}.csv\"`,",
         c("Content-Disposition: attachment") + " makes browsers download instead of "
         "display."),
        ("return Readable.from(lines()); // a stream is sent as it is produced",
         "Return a stream and Fastify pipes it to the socket chunk by chunk."),
        ("const etag = `\"${hash.digest('base64url')}\"`;",
         "An ETag fingerprints the representation..."),
        ("if (request.headers['if-none-match'] === etag) return reply.code(304).send();",
         "...so a client that already has it gets 304 with no body: less bandwidth, "
         "faster pages."),
    ],
    # ---------------------------------------------------------- order tracking
    'src/order-tracking/app.ts': [
        ("// Disconnects are only noticed on the next write: the ping interval bounds how",
         "Measured: with a 15 s ping, a closed tab stayed subscribed 15 s; with 200 ms "
         "it was cleaned up in ~240 ms."),
        ("const bus = new EventEmitter();",
         "In-process only. With several instances, publish through Redis/NATS so every "
         "instance can notify its own subscribers."),
        ("status: Type.Union(STATUSES.map((s) => Type.Literal(s))),",
         "Only known statuses are accepted from the courier systems."),
        ("reply.hijack(); // we write the response ourselves",
         c("hijack()") + ": Fastify stops managing this response; we own "
         + c("reply.raw") + "."),
        ("'content-type': 'text/event-stream',",
         "The SSE media type; the browser's " + c("EventSource") + " reconnects "
         "automatically."),
        ("if (latest.has(id)) send(latest.get(id)!); // current state first",
         "Late subscribers first get the current state, then live updates."),
        ("reply.raw.on('close', () => {",
         "Always unsubscribe on close, or every visit leaks a listener."),
    ],
    'test/order-tracking.test.ts': [
        ("base = await app.listen({ port: 0, host: '127.0.0.1' });",
         "Streaming needs a real socket: listen on a random free port."),
        ("const reader = res.body!.pipeThrough(new TextDecoderStream()).getReader();",
         "Read the event stream incrementally with " + c("fetch") + ", like a browser."),
        ("controller.abort(); // user closes the tab",
         "Simulate the user leaving; then assert the listener is gone."),
    ],
    # ---------------------------------------------------------------- signup
    'src/signup/app.ts': [
        ("email: Type.String({ format: 'email', maxLength: 254 }),",
         "Formats (email, date, uri, uuid...) are checked by Ajv."),
        ("pattern: '^(?=.*[A-Za-z])(?=.*\\\\d).*$',",
         "Password policy in the schema: length + at least one letter and one digit."),
        ("marketingOptIn: Type.Optional(Type.Boolean({ default: false })),",
         "Found while testing: with " + c("default") + " but without "
         + c("Optional") + ", OpenAPI listed the field as <b>required</b>."),
        ("{ additionalProperties: false },",
         "Unknown fields (e.g. " + c("id") + ", " + c("passwordHash") + ") are "
         "stripped before the handler runs."),
        ("ajv: { customOptions: { allErrors: true } },",
         "Report every invalid field at once (default stops at the first)."),
        ("fields: error.validation.map((v) => ({",
         "Turn Ajv errors into a list the form can show next to each input."),
        ("schema: { body: SignupBody, response: { 201: User, 409: ErrorReply } },",
         "Declare <b>every</b> status the route returns. Found by the compiler: without "
         "409 here, " + c("reply.code(409)") + " was a type error."),
        ("return user; // passwordHash is not in the 201 schema: never sent",
         "The response schema is a whitelist: the hash cannot leak, even by accident."),
        ("const { country, optedIn, limit } = request.query; // already typed and coerced",
         c("?optedIn=true&limit=5") + " arrives as a boolean and a number, with a "
         "default for limit."),
    ],
    # ---------------------------------------------------------- multi-tenant
    'src/multi-tenant/tenants.ts': [
        ("interface FastifyRequest {",
         "Type the request decorator so every handler sees " + c("request.tenant") + "."),
        ("export default fp<{ store: TenantStore }>(",
         c("fp()") + " breaks encapsulation on purpose: the hook and decorators apply to "
         "the whole app."),
        ("app.decorateRequest('tenant', null); // null, never a shared object",
         "Initialize with " + c("null") + ": a shared object would leak between "
         "requests (Fastify 5 refuses it)."),
        ("request.hostname.split('.')[0];",
         c("acme.app.example.com") + " &rarr; " + c("acme") + "; the header form is "
         "for API clients and tests."),
        ("return reply.code(404).send({ message: `Unknown workspace \"${slug}\"` });",
         "Unknown tenants never reach a route."),
    ],
    'src/multi-tenant/app.ts': [
        ("const adminArea: FastifyPluginAsync = async (admin) => {",
         "Not wrapped in " + c("fp()") + ": a separate context."),
        ("admin.decorate('audit', (entry: string) => {",
         "Exists only inside the admin context (and its children)."),
        ("admin.addHook('onRequest', async (request, reply) => {",
         "The admin-key check runs for admin routes only."),
        ("if (given.length !== expected.length || !timingSafeEqual(given, expected)) {",
         "Constant-time comparison; each tenant has its own key."),
        ("projects: api.tenants.projects(request.tenant!.id), // only this tenant's data",
         "Data access is always scoped by the resolved tenant."),
        ("hasAudit: api.hasDecorator('audit'),",
         "Proof of encapsulation: " + c("false") + " here (see the test)."),
        ("await app.register(tenants, { store }); // shared: every route has request.tenant",
         "Registration order: shared infrastructure first, then feature plugins."),
    ],
    # --------------------------------------------------------- observability
    'src/observability/app.ts': [
        ("logSink: (line: string) => void; // stdout in production, an array in tests",
         "Logs go to any writable; tests capture them to assert on content."),
        ("paths: ['headers.authorization', 'headers.cookie', 'body.password'],",
         "Redaction paths: secrets never reach log storage."),
        ("requestIdHeader: 'x-request-id', // reuse the ID from the gateway / caller...",
         "Correlate one request across gateway, API and downstream services."),
        ("disableRequestLogging: true, // we log one structured line ourselves",
         "Replace the two default lines (incoming/completed) with one richer line."),
        ("app.addHook('onRequest', async (request, reply) => {",
         "Earliest hook: the maintenance switch answers before parsing or validation."),
        ("app.addHook('onSend', async (request, reply, payload) => {",
         c("onSend") + ": add headers to every response; must return the payload."),
        ("app.addHook('onResponse', async (request, reply) => {",
         c("onResponse") + " runs after the client has the response: logging and "
         "auditing never slow it down."),
        ("{ headers: request.headers, body: request.body },",
         "Logged deliberately with secrets inside &mdash; the test proves they come out "
         "redacted."),
    ],
    # ------------------------------------------------------- problem details
    'src/problem-details/app.ts': [
        ("export const AccountNotFound = createError(",
         c("@fastify/error") + ": a stable machine code, a message template and the "
         "HTTP status in one class."),
        ("app.setErrorHandler((error: FastifyError, request, reply) => {",
         "One error handler shapes every failure as RFC 9457 problem details."),
        ("title: status >= 500 ? 'Internal Server Error' : (error.code ?? 'Error'),",
         "Clients branch on the stable code, never on the human message."),
        ("status >= 500 ? 'Something went wrong, it has been logged' : error.message,",
         "5xx details (here a password in an error message!) stay in the logs."),
        ("problem['invalid-params'] = error.validation.map((v) => ({",
         "Validation failures use the RFC's " + c("invalid-params") + " extension."),
        ("reply.code(status).type('application/problem+json').send(problem);",
         "The dedicated media type tells clients what they are parsing."),
        ("app.setNotFoundHandler((request, reply) => {",
         "Unknown routes return the same shape."),
        ("throw new InsufficientFunds(from, available, amountCents);",
         "Handlers just throw domain errors; the mapping lives in one place."),
    ],
    # --------------------------------------------------------------- webhooks
    'src/webhooks/app.ts': [
        ("toleranceSec?: number; // reject replays of old requests",
         "A captured request replayed later is rejected by its timestamp."),
        ("export function sign(secret: string, timestamp: number, rawBody: string) {",
         "The provider's algorithm: HMAC-SHA256 over " + c("timestamp.rawBody") + "."),
        ("const seen = new Set<string>(); // a DB unique index in production",
         "Providers deliver at least once: remember processed event IDs."),
        ("hooks.addContentTypeParser(",
         "Inside this plugin only, JSON bodies stay raw " + c("Buffer") + "s..."),
        ("(request, body, done) => done(null, body),",
         "...because re-serializing parsed JSON changes the bytes and breaks the "
         "signature (the test proves it)."),
        ("if (!timestamp || Math.abs(now() - timestamp) > (opts.toleranceSec ?? 300)) {",
         "Check freshness first: cheap, and blocks replays."),
        ("if (given.length !== expected.length || !timingSafeEqual(given, expected)) {",
         "Constant-time comparison prevents timing attacks on the signature."),
        ("if (seen.has(event.id)) return { received: true, duplicate: true };",
         "Duplicates get 200 so the provider stops retrying."),
    ],
    'test/webhooks.test.ts': [
        ("const res = await deliver(body, sign(SECRET, NOW, body));",
         "Sign exactly like the provider; a fixed clock makes the test deterministic."),
        ("const reformatted = JSON.stringify(event, null, 2);",
         "Same data, different bytes: rejected."),
    ],
    # -------------------------------------------------------------- inventory
    'src/inventory/db.ts': [
        ("import { DatabaseSync } from 'node:sqlite';",
         "Node's built-in SQLite (no install). The plugin pattern is identical for "
         "Postgres, MySQL or an ORM."),
        ("stock INTEGER NOT NULL CHECK (stock >= 0)",
         "The database enforces the invariant too."),
        ("for (const sql of MIGRATIONS) db.exec(sql);",
         "Migrations at boot (real projects use a migration tool)."),
        ("app.addHook('onClose', async () => db.close());",
         "Closed on " + c("app.close()") + " &mdash; verified by the last test."),
    ],
    'src/inventory/app.ts': [
        (".run(sku, name, stock); // parameters, never string concatenation",
         "Bound parameters: no SQL injection."),
        ("app.db.exec('BEGIN IMMEDIATE'); // take the write lock up front",
         "One transaction for the whole order."),
        ("if (reserve.run(qty, sku, qty).changes === 0) {",
         c("UPDATE ... WHERE stock >= ?") + ": the check and the decrement happen in "
         "one statement, so two checkouts can't oversell."),
        ("throw new OutOfStock(row.stock, sku, qty);",
         "A 409 with a precise message: " + c("Only 1 of TEE left, 5 requested") + "."),
        ("app.db.exec('ROLLBACK'); // earlier lines are released again",
         "All or nothing: the MUG reserved by the first line is given back."),
    ],
    # -------------------------------------------------------------- auth-rbac
    'src/auth-rbac/app.ts': [
        ("user:",
         c("request.user") + " is either a person (JWT) or a service (API key)."),
        ("await app.register(jwt, { secret, sign: { expiresIn: '15m' } }); // short-lived",
         "Short-lived access tokens limit the damage of a leaked token."),
        ("// family = one login session; reusing a rotated token revokes the whole family.",
         "Refresh-token rotation with reuse detection (OAuth 2.0 security BCP)."),
        ("const verifyApiKey = async (request: FastifyRequest) => {",
         "Machine clients use API keys, compared in constant time."),
        ("const requireRole = (role: Role) => async (request: FastifyRequest) => {",
         "Authorization is a separate, reusable step after authentication."),
        ("if (stored.used) {",
         "A used refresh token presented again means it was copied: revoke the whole "
         "session."),
        ("preHandler: [requireRole('admin')], // authorization after authN",
         c("onRequest") + " authenticates (401), " + c("preHandler") + " authorizes "
         "(403)."),
        ("preHandler: app.auth([verifyJwt, verifyApiKey]), // either is enough",
         c("@fastify/auth") + ": the first strategy that succeeds wins."),
    ],
    'test/auth-rbac.test.ts': [
        ("const replay = await refresh(first.refreshToken); // attacker's copy",
         "An attacker replays the old refresh token..."),
        ("'the legitimate session is revoked too',",
         "...and the session is dead for both: the user logs in again, the attacker is "
         "out."),
    ],
    # --------------------------------------------------------------- security
    'src/security/app.ts': [
        ("trustProxy: true, // behind a load balancer: request.ip from X-Forwarded-For",
         "Without it every client looks like the load balancer, and one IP-based limit "
         "blocks everybody."),
        ("await app.register(helmet); // HSTS, nosniff, frame-options, CSP...",
         "Secure headers on every response, " + c("x-powered-by") + " removed."),
        ("origin: allowedOrigins, // exact allowlist, never \"*\" with credentials",
         "Only the storefront's origin gets CORS headers; other sites get none."),
        ("await app.register(rateLimit, { max: 300, timeWindow: '1 minute' });",
         "A global safety net per client IP."),
        ("hook: 'preHandler',",
         "Found by the test: in the default " + c("onRequest") + " hook the body isn't "
         "parsed, so the key had no username and blocked <b>every</b> user on that IP."),
        ("`${request.ip}:${(request.body as { username?: string }).username}`,",
         "Key = IP + username: an attacker can't lock out other users."),
        ("app.post('/feedback', { bodyLimit: 1024 }, async () => ({ thanks: true }));",
         "Per-route body limit: 413 before any parsing work."),
    ],
    # ---------------------------------------------------------------- uploads
    'src/uploads/app.ts': [
        ("const SIGNATURES: Record<string, Buffer> = {",
         "Magic bytes identify the real file type; the client's Content-Type and "
         "extension are just claims."),
        ("limits: { fileSize: maxBytes, files: 1, fields: 5 },",
         "Hard limits: size, number of files and fields."),
        ("const chunks = file.file[Symbol.asyncIterator]();",
         "Read only the first chunk to sniff the type, then keep streaming."),
        ("file.file.resume(); // drain and discard",
         "Rejected uploads are drained so the connection stays usable."),
        ("const name = `${randomUUID()}.${ext}`;",
         "A random name: " + c("../../etc/passwd.png") + " can't escape the directory "
         "(tested)."),
        ("await pipeline(async function* () {",
         "Stream to disk: memory use doesn't grow with file size."),
        ("if (file.file.truncated) {",
         "Size limit hit mid-stream: delete the partial file, answer 413."),
    ],
    # ------------------------------------------------------------------- chat
    'src/chat/app.ts': [
        ("await app.register(websocket, { options: { maxPayload: 16 * 1024 } });",
         "Cap message size: a 100 MB frame can't exhaust memory."),
        ("const rooms = new Map<string, Map<WebSocket, string>>(); // room -> socket -> user",
         "Room membership in memory; multiple instances need a shared pub/sub."),
        ("preValidation: async (request, reply) => {",
         "Regular hooks run on the HTTP upgrade request: authenticate <b>before</b> the "
         "socket opens."),
        ("const text = String(raw).trim().slice(0, 2000);",
         "Never trust message content: trim and bound it."),
        ("socket.on('close', () => {",
         "Clean up membership and tell the room."),
    ],
    # -------------------------------------------------------- graceful shutdown
    'src/graceful-shutdown/app.ts': [
        ("forceCloseConnections: 'idle', // drop idle keep-alive sockets on close",
         "Idle keep-alive sockets are closed when shutdown starts..."),
        ("app.get('/ready', async (_request, reply) =>",
         "Readiness probe flips to 503 so the load balancer stops routing here."),
        ("app.addHook('preClose', async () => {",
         c("preClose") + " runs first, while the server still serves in-flight "
         "requests."),
        ("app.addHook('onSend', async (_request, reply, payload) => {",
         "...but sockets that become idle <i>later</i> are not. Found by the test: close "
         "took 71 s until responses sent " + c("Connection: close") + "."),
        ("app.addHook('onClose', async () => {",
         "Flush and close resources only after the last request finished."),
    ],
    'test/graceful-shutdown.test.ts': [
        ("const inFlight = fetch(`${base}/reports/monthly`).then(async (r) => {",
         "A slow request is in flight when the deploy starts."),
        ("const closing = app.close().then(() => events.push('closed'));",
         "What " + c("close-with-grace") + " does on SIGTERM."),
        ("assert.equal(report.rows, 12_840);",
         "The in-flight request completed fully."),
        ("await assert.rejects(fetch(`${base}/ready`));",
         "New connections are refused after close."),
    ],
}
