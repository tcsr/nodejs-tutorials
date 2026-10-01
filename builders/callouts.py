"""Callout notes for the end-to-end project listings. Anchors are exact substrings of a line,
matched in order; the build fails if an anchor no longer matches the project code."""

M = "<font face='Courier'>%s</font>"


def c(t):
    return M % t


TEMPORAL = {
    'src/activities.ts': [
        ("const stock = new Map",
         "Demo state lives in the worker process. In production this is a database call "
         "&mdash; activities are exactly where I/O belongs."),
        ("throw ApplicationFailure.nonRetryable(",
         "A <b>business</b> error: retrying won't help, so it is non-retryable with a "
         "<i>type</i> (" + c("OutOfStock") + ") the workflow can inspect."),
        ("const { attempt } = activityInfo();",
         c("activityInfo()") + " exposes the attempt number, workflow ID and heartbeat "
         "details of the current execution."),
        ("throw new Error('Payment gateway timeout');",
         "A plain " + c("Error") + " is treated as transient and retried with the workflow's "
         "retry policy &mdash; attempts 1 and 2 fail, attempt 3 succeeds."),
        ("return `txn-${orderId}`;",
         "Real payment calls must be <b>idempotent</b>: pass " + c("orderId") + " as the "
         "gateway's idempotency key so a retry never charges twice."),
    ],
    'src/workflows.ts': [
        ("import type * as activities from './activities';",
         "<b>Type-only</b> import: the workflow sandbox never loads activity code, only its "
         "signatures."),
        ("} = proxyActivities<typeof activities>({",
         "Typed proxies. Calling " + c("chargePayment()") + " schedules an activity task; the "
         "call returns when a worker has run it."),
        ("retry: { initialInterval: '1 second', backoffCoefficient: 2, maximumAttempts: 5 },",
         "Retries at 1s, 2s, 4s, 8s &mdash; this is why the flaky gateway eventually succeeds "
         "without any retry code."),
        ("export const approveOrder = defineSignal",
         "Message definitions are exported so the API can call "
         + c("handle.signal(approveOrder, ...)") + " with full type checking."),
        ("setHandler(getStatus, () => status);",
         "Register handlers <b>before the first await</b> so no early signal or query is "
         "missed."),
        ("const decided = await condition(() => approvedBy !== undefined || cancelled,",
         "Durable wait: survives worker restarts and costs nothing. Returns " + c("false")
         + " if 2 minutes pass without approval or cancellation."),
        ("compensations.unshift(() => releaseInventory(input.orderId, input.sku,",
         "Saga step: after a step succeeds, register its undo. " + c("unshift")
         + " makes compensations run in <b>reverse</b> order."),
        ("checkCancelled();",
         "Cancellation checkpoint between steps: throws a non-retryable failure so the "
         + c("catch") + " block rolls back."),
        ("await CancellationScope.nonCancellable(async () => {",
         "Cleanup must finish even if the workflow itself is being cancelled."),
        ("throw err;",
         "Re-throwing an " + c("ApplicationFailure") + " marks the execution <b>FAILED</b>; "
         "the client sees " + c("WorkflowFailedError") + " (the API maps it to 422)."),
    ],
    'src/api.ts': [
        ("const client = new Client({ connection, namespace: 'default' });",
         "Create <b>one</b> client per process and reuse it for every request."),
        ("workflowId: `order-${input.orderId}`,",
         "Business ID as Workflow ID: a duplicate start for the same order is rejected by "
         "the server."),
        ("res.status(202).json({ workflowId: handle.workflowId });",
         c("start()") + " returns as soon as the server has recorded the workflow &mdash; "
         "hence " + c("202 Accepted") + "."),
        (".withDeadline(Date.now() + 5_000, () => handle.query(getStatus))",
         "Queries are answered by a worker. Without one they would hang, so the call is "
         "bounded to 5 s."),
        (".signal(approveOrder, req.body.approver ?? 'admin');",
         "Signals are stored by the server even when no worker is running; the workflow "
         "receives it when a worker picks it up."),
        ("const result = await client.workflow.getHandle(req.params.id).result();",
         c("result()") + " long-polls until the workflow completes (or throws if it failed)."),
        ("if (err instanceof WorkflowFailedError) {",
         "A failed workflow is a business outcome: unwrap the cause chain and return 422 "
         "with the real reason, e.g. " + c("Out of stock: LAPTOP") + "."),
    ],
}

FASTIFY = {
    'src/schemas/task.ts': [
        ("export const Task = Type.Object({",
         "One TypeBox schema drives validation, response serialization, Swagger docs "
         "<b>and</b> TypeScript types."),
        ("export type Task = Static<typeof Task>;",
         c("Static") + " derives the TypeScript type from the schema &mdash; no duplicate "
         "interface to keep in sync."),
        ("export const CreateTask = Type.Object({ title: Title }, { additionalProperties: false });",
         "Unknown fields are stripped (Ajv " + c("removeAdditional") + "), so clients can't "
         "set " + c("ownerId") + " or " + c("done") + " on create."),
        ("{ additionalProperties: false, minProperties: 1 },",
         c("minProperties: 1") + " rejects an empty PATCH body with a 400."),
        ("limit: Type.Integer({ minimum: 1, maximum: 100, default: 20 }),",
         "Query strings are coerced (" + c('"10"') + " &rarr; 10), defaulted and bounded "
         "before your handler runs."),
    ],
    'src/plugins/store.ts': [
        ("const hashPw = (pw: string, salt: string) => scryptSync(pw, salt, 32);",
         "Passwords are stored as salted scrypt hashes, never in plain text."),
        ("return timingSafeEqual(u.hash, hashPw(password, u.salt)) ? u : undefined;",
         c("timingSafeEqual") + " prevents timing attacks when comparing hashes."),
        ("declare module 'fastify' { interface FastifyInstance { store: Store } }",
         "Declaration merging types " + c("app.store") + " everywhere."),
        ("app.decorate('store', new Store());",
         "Wrapped in " + c("fp()") + ", so the decorator is shared app-wide. Swap this plugin "
         "for a database-backed one without touching routes."),
    ],
    'src/plugins/auth.ts': [
        ("declare module '@fastify/jwt' {",
         "Types what you sign (" + c("payload") + ") and what " + c("request.user")
         + " holds after verification."),
        ("await app.register(jwt, { secret: app.config.JWT_SECRET, sign: { expiresIn: '1h' } });",
         "Secret comes from validated env config; tokens expire after one hour."),
        ("await request.jwtVerify();",
         "Checks signature and expiry, then sets " + c("request.user") + "."),
        ("throw app.httpErrors.unauthorized('Invalid or missing token');",
         "Any failure becomes a clean 401 via " + c("@fastify/sensible") + "."),
        ("}, { name: 'auth', dependencies: ['env'] });",
         "Plugin metadata: Fastify verifies that " + c("env") + " was registered first."),
    ],
    'src/routes/auth.ts': [
        ("config: { rateLimit: { max: 5, timeWindow: '1 minute' } },",
         "Per-route rate limit against brute force: the 6th attempt in a minute gets 429."),
        ("const { username, password } = request.body;",
         c("request.body") + " is typed from the schema by the TypeBox type provider."),
        ("return { token: app.jwt.sign({ sub: user.id, username: user.username }) };",
         "Sign only what you need; " + c("sub") + " identifies the user on later requests."),
    ],
    'src/routes/tasks.ts': [
        ("app.addHook('onRequest', app.authenticate);",
         "Encapsulated hook: protects every route in <b>this</b> plugin only; "
         + c("/health") + " and " + c("/auth") + " stay public."),
        ("const common = { tags: ['tasks'], security: [{ bearerAuth: [] }] };",
         "Shared Swagger metadata: groups the routes and shows the lock icon in "
         + c("/docs") + "."),
        ("if (!task || task.ownerId !== request.user.sub) {",
         "Authorization: another user's task returns <b>404, not 403</b>, so IDs can't be "
         "probed."),
        ("}, async (request) => app.store.listTasks(request.user.sub, request.query));",
         c("request.query") + " is already typed, coerced and defaulted."),
        ("reply.code(201);",
         "Set the status, then just return the object; the 201 response schema serializes it."),
        ("return reply.code(204).send(null);",
         "With a " + c("Type.Null()") + " 204 schema, " + c("send") + " needs an explicit "
         + c("null") + "."),
    ],
    'src/app.ts': [
        ("const app = Fastify(opts).withTypeProvider<TypeBoxTypeProvider>();",
         "Enables schema-to-type inference for every route registered on this instance."),
        ("await app.register(env);",
         "Order matters: config first, because later plugins read " + c("app.config") + "."),
        ("await app.register(swagger);",
         "Swagger must be registered before the routes it documents."),
        ("app.setErrorHandler((error: FastifyError, request, reply) => {",
         "One place for error responses: consistent JSON, HTTP status text via "
         + c("STATUS_CODES") + ", and 5xx details hidden from clients."),
        ("await app.register(tasksRoutes, { prefix: '/tasks' });",
         "Feature plugins get a URL prefix and their own encapsulated hooks."),
    ],
    'src/server.ts': [
        ("redact: ['req.headers.authorization'],",
         "Bearer tokens never reach the logs."),
        ("trustProxy: true,",
         "Behind a load balancer: " + c("request.ip") + " and rate limits use the real "
         "client IP."),
        ("closeWithGrace({ delay: 10_000 }, async ({ signal, err }) => {",
         "Graceful shutdown on SIGINT/SIGTERM or crash: stop accepting, finish in-flight "
         "requests, run " + c("onClose") + " hooks."),
        ("await app.listen({ port: app.config.PORT, host: app.config.HOST });",
         c("HOST") + " defaults to " + c("0.0.0.0") + " so the server is reachable inside "
         "containers."),
    ],
    'test/tasks.test.ts': [
        ("process.env.JWT_SECRET = 'test-secret-test-secret-test-secret-123';",
         "Set required config before building the app; env validation runs at boot."),
        ("const res = await app.inject({ method: 'POST', url: '/auth/login',",
         c("inject()") + " runs the full lifecycle (hooks, validation, serialization) with no "
         "network."),
        ("test('validates input', async () => {",
         "Schema rules are part of the contract &mdash; test them like business logic."),
    ],
}
