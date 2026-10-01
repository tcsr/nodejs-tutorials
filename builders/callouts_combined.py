"""Callout notes for the Fastify + Temporal combined project (same rules as callouts.py)."""
from callouts import c

COMBINED = {
    'src/plugins/temporal.ts': [
        ("interface FastifyInstance { temporal: Client }",
         "Every route and hook can use " + c("app.temporal") + " with full typing."),
        ("client?: Client;",
         "Dependency injection: tests pass the time-skipping server's client, production "
         "passes an address."),
        ("app.decorate('temporal', opts.client);",
         "An injected client is owned by the caller, so the plugin must not close it."),
        ("const connection = await Connection.connect({ address });",
         "Connect once at boot. The client reconnects on its own after Temporal restarts "
         "(verified: health went 503 &rarr; 200 without restarting the API)."),
        ("app.addHook('onClose', async () => { await connection.close(); });",
         c("app.close()") + " stops HTTP first, then closes the gRPC connection."),
        ("}, { name: 'temporal' });",
         "Wrapped in " + c("fp()") + " so the decorator is visible to all route plugins."),
    ],
    'src/schemas/order.ts': [
        ("}, { additionalProperties: false });",
         "Validated at the edge: bad input never reaches Temporal or creates a workflow."),
        ("'idempotency-key': Type.Optional(Type.String({ pattern: '^[A-Za-z0-9_-]{8,64}$' })),",
         "The key becomes part of the Workflow ID, so it is restricted to a safe charset."),
        ("export const OrderParams = Type.Object({ id: Type.String({ pattern: '^order-' }) });",
         "Only IDs this API created are accepted: " + c("/orders/nope") + " is a 400 without "
         "a round-trip to Temporal."),
        ("status: Type.String(),        // business status from the workflow query",
         "Two statuses: the <b>business</b> state (from the workflow query) and the "
         "<b>execution</b> state (from Temporal)."),
        ("waitSeconds: Type.Integer({ minimum: 0, maximum: 30, default: 0 }),",
         "Optional long-poll, capped at 30 s so HTTP connections are never held "
         "indefinitely."),
    ],
    'src/routes/orders.ts': [
        ("async function view(workflowId: string) {",
         "One place that builds the status view; reused by GET and by 202 responses."),
        (".withDeadline(Date.now() + 5_000, () => handle.query(getStatus))",
         "Queries need a live worker. Bounded to 5 s, then degrade to "
         + c("UNKNOWN") + " instead of hanging the request."),
        ("const key = request.headers['idempotency-key'] ?? randomUUID();",
         "Client-supplied key (or a fresh UUID) becomes the Workflow ID: "
         "<b>Temporal enforces the idempotency</b>, no extra table needed."),
        ("await app.temporal.connection.withDeadline(Date.now() + 5_000, () =>",
         "Without this bound the client retries for ~20 s when Temporal is down "
         "(measured). With it the API answers 503 in ~5 s."),
        ("workflowIdConflictPolicy: 'USE_EXISTING',",
         "Same key while the order is running: attach to the existing run."),
        ("workflowIdReusePolicy: 'REJECT_DUPLICATE',",
         "Same key after it finished: the server refuses a second run..."),
        ("if (!(err instanceof WorkflowExecutionAlreadyStartedError)) throw err;",
         "...which we treat as success. Tests assert the <b>run ID</b> is unchanged."),
        ("reply.code(202).header('location', statusUrl);",
         "Asynchronous request-reply: 202 Accepted + Location; the client polls the "
         "status URL."),
        ("await handle.signal(approveOrder, request.body.approver);",
         "Signals map to POST sub-resources. Stored by the server even if no worker is up; "
         "a missing workflow throws " + c("WorkflowNotFoundError") + " &rarr; 404."),
        ("if (running && request.query.waitSeconds === 0) {",
         "Default is a cheap non-blocking check."),
        ("Date.now() + request.query.waitSeconds * 1000, () => handle.result())",
         "Long-poll for up to " + c("waitSeconds") + ": " + c("result()") + " returns as "
         "soon as the workflow completes."),
        ("if (!isGrpcDeadlineError(err)) throw err;",
         "The deadline error arrives wrapped in a " + c("ServiceError") + "; "
         + c("isGrpcDeadlineError") + " checks the cause chain (checking "
         + c("err.code") + " directly misses it)."),
    ],
    'src/app.ts': [
        ("const GRPC_UNAVAILABLE = 14;",
         "gRPC status UNAVAILABLE: the Temporal Service cannot be reached."),
        ("function temporalUnavailable(err: unknown): boolean {",
         "Both \"unreachable\" and \"too slow\" mean the same to an HTTP client: retry "
         "later."),
        ("temporal?: TemporalPluginOptions;",
         "App options carry Temporal settings, so tests and production build the same app."),
        ("await app.register(temporal, temporalOpts);",
         "Registered before the routes that use " + c("app.temporal") + "."),
        ("if (error instanceof WorkflowNotFoundError) {",
         "Unknown Workflow ID &rarr; 404."),
        ("if (error instanceof WorkflowFailedError) {",
         "A failed workflow is a business outcome &rarr; 422 with the root cause "
         "(e.g. " + c("Out of stock: LAPTOP") + ")."),
        ("return reply.code(503).header('retry-after', '5').send({",
         "Temporal down &rarr; 503 + Retry-After. Safe to retry because POST is idempotent."),
        ("message: status >= 500 ? 'Something went wrong' : error.message,",
         "Everything else: standard Fastify behaviour, 5xx details hidden."),
    ],
    'src/routes/health.ts': [
        ("() => app.temporal.workflowService.getSystemInfo({}));",
         "A cheap call that proves the Temporal Service is reachable."),
        ("return reply.code(503).send({ status: 'degraded', temporal: 'unreachable' });",
         "Readiness probes take the instance out of rotation while Temporal is unreachable."),
    ],
    'src/server.ts': [
        ("address: process.env.TEMPORAL_ADDRESS ?? 'localhost:7233',",
         "Same env variables as the worker, so both processes point at the same "
         "Temporal Service."),
        ("await app.close();",
         "Graceful shutdown order: drain HTTP requests, then run " + c("onClose")
         + " hooks (Temporal connection)."),
        ("await app.listen({",
         "The worker is a <b>separate process</b> (" + c("npm run worker") + "): scale and "
         "deploy API and workers independently."),
    ],
    'test/orders.test.ts': [
        ("env = await TestWorkflowEnvironment.createTimeSkipping();",
         "In-process Temporal test server with time skipping (2-minute timers take ms)."),
        ("workerRun = worker.run();",
         "A real worker runs the real workflow code, with mocked activities."),
        ("app = await buildApp({ temporal: { client: env.client } });",
         "The Fastify app uses the test server's client: HTTP &rarr; workflow end to end, "
         "no ports opened."),
        ("worker.shutdown();",
         "Stop the worker, wait for it, then tear down the server."),
        ("const firstRun = await runId(a.workflowId);",
         "Idempotency is proven by comparing Temporal <b>run IDs</b>, not just the "
         "returned Workflow ID."),
        ("const pending = await app.inject(`${statusUrl}/result`);",
         "Non-blocking check returns 202 while the order waits for approval."),
        ("assert.equal(res.json().message, 'Out of stock: NONE');",
         "The 422 carries the activity's business reason, unwrapped from the failure chain."),
    ],
}
