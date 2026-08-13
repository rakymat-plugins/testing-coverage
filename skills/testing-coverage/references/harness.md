# The Harness

Everything that must exist *before* a single L4+ test can be written. Skipping
this is why most test suites end up running on exactly one machine.

A harness is judged by one question: **can a new contributor clone the repo and
get the integration suite green with one command?**

---

## 1. Target indirection

Never hardcode where the system under test lives. Every test resolves its target
from an environment variable with a local default.

```
target = env("TEST_API_URL")  or  "http://127.0.0.1:4000"
```

This one line is what lets the same test file run against a local dev server, a
disposable container stack on a different port, a CI service, and a deployed
staging environment — with no edits.

Recommended variable names (pick a set, document it, never deviate):

| Variable | Meaning |
| --- | --- |
| `TEST_API_URL` | base URL of the API under test |
| `TEST_WEB_URL` | base URL of the web app under test |
| `TEST_DATABASE_URL` | datastore the harness may reset and seed |
| `TEST_MAIL_URL` | local mail sink API, for asserting deliveries |

**Hostname warning:** `localhost` and `127.0.0.1` are *different hosts* to a
cookie jar. If the harness mints a cookie for one and a test calls the other, the
request silently sends no credentials and you debug a phantom 401. Pick one
spelling and use it in every variable, every config, every script.

---

## 2. Disposable services

The test datastore must be creatable and destroyable without touching anyone's
development data.

**Use a separate compose/stack file with offset ports and its own volume.**

| | Dev stack | Test stack |
| --- | --- | --- |
| Postgres | 5432 | **5434** |
| App/API | 4000 | **4110** |
| Mail sink | 1025 / 8025 | **1026 / 8026** |
| Volume | `dev-data` | `test-data` |
| Database name | `app_dev` | `app_test` |

Offsetting matters more than it looks: if the test stack reuses a dev port, the
dev stack's container fails to bind, and everything that depends on it dies —
which presents as an unrelated broken dev environment an hour later.

**Alternatives when containers aren't available**, in order of preference:

1. Language-native ephemeral database (`sqlx::test`, `pytest-postgresql`,
   Respawn, transaction-per-test rollback).
2. A real datastore installed on the machine, with a dedicated `*_test` database.
3. Embedded/in-memory engine — **only** if it's the same engine family. Swapping
   Postgres for SQLite hides constraint, type, concurrency, and JSON behaviour
   differences and produces tests that pass while production breaks.

---

## 3. Readiness gating

Never `sleep 10` and hope. Poll a real signal, with a bounded timeout, and on
timeout **dump the service logs** before failing — otherwise every CI failure is
an unactionable "did not become healthy".

```
for attempt in 1..N:
    if GET /health returns 200: proceed
    sleep 500ms
else:
    print service logs (last 100 lines)
    fail with a message naming what wasn't ready
```

**Capability gating** — one level beyond health. If the app has feature flags,
don't assume the running instance is configured how you think. Expose a
`/capabilities` (or equivalent) endpoint returning the flag states, and have the
harness assert the instance matches the lane it claims to be. Tests can then
`skip` rather than fail when a feature is off, which keeps one suite honest
across configurations.

Pair it with an `*_EXPECTED` variable so a misconfigured lane fails loudly
instead of silently skipping everything and reporting green.

---

## 4. Seeding

**Named profiles, not one giant seed.** A profile is a function that builds a
known world:

| Profile | Purpose |
| --- | --- |
| `test` | minimum deterministic data the suite asserts against; fast |
| `development` | comfortable data for humans clicking around |
| `demo` | pretty, realistic data for showing people |
| `performance` | high volume, for L9 and query-budget work |

**Deny-by-default safety guard.** Seeding usually truncates. Guard it with an
allowlist of environment names and fail on anything unrecognized:

```
SAFE = {"development", "test", "demo", "performance"}
if env("APP_ENV") not in SAFE: abort
```

An allowlist, not a `!= "production"` check — a blocklist passes on an empty or
misspelled environment, which is exactly the situation where someone truncates
the wrong database.

**Deterministic identity for anything a test targets by name.** Fixed UUIDs and
fixed slugs for the handful of records that E2E and visual tests navigate to:

```
STABLE_SCHOOL_ID   = "00000000-0000-4000-8000-000000000001"
STABLE_SCHOOL_SLUG = "acme-academy"
```

Random IDs for everything else, so tests can't accidentally depend on data they
didn't create.

---

## 5. Test data: factory → fixture → scenario

Three layers, each built on the one before. This is the difference between a
suite that survives a schema change and one that requires 200 edits.

1. **Factory** — a function returning one valid object with every field
   defaulted, accepting partial overrides:
   `makeUser({ role: "ADMIN" })`. When a required field is added to the model,
   you fix the factory once.
2. **Fixture** — a named, frozen instance for readability:
   `fixtures.suspendedOwner`.
3. **Scenario** — a composed multi-entity world with the relationships a test
   needs: `scenarioOwnerWithTwoApprovedSchools()`.

**Never** copy a literal object between test files. **Never** let two tests share
a mutable fixture instance — freeze them or return fresh copies.

---

## 6. Authentication in tests

Three strategies. Most projects need two of them.

| Strategy | How | Use for | Cost |
| --- | --- | --- | --- |
| **Real login** | drive the actual login endpoint/form, keep the cookies | the auth flow itself; a few smoke journeys | slow, but proves the real thing |
| **Mint with the app's own signer** | import the app's token-signing function | L5 matrices, L4 setup | fast, stays correct automatically |
| **Forge externally** | re-implement the signing algorithm in the harness | when importing app code drags in config validation, DI, or env schemas | fast, but *must* be kept in sync |

If you forge, the forging code needs a prominent comment naming the exact source
file it mirrors, plus a guardrail test (L10) that fails when the two diverge.
Otherwise a rotated algorithm turns every mutation into an opaque 403.

**Don't forget the second factor of web auth.** CSRF/anti-forgery tokens, SameSite
cookie rules, and `Secure` flags all break forged sessions in ways that look like
authorization bugs. Assert the harness can perform *one* successful mutation
before writing fifty tests on top of it.

**Pre-authenticated state, once.** For browser E2E, mint sessions once in a global
setup step and save one storage-state file per role; individual tests load a role
instead of logging in. Cuts minutes off every run.

---

## 7. Isolation

Pick one strategy per suite and state it explicitly:

| Strategy | How | Good | Bad |
| --- | --- | --- | --- |
| **Unique data per test** | timestamp/uuid in emails, slugs, names | no cleanup needed, parallel-safe | database grows during a run |
| **Transaction rollback** | wrap each test, roll back after | fastest, perfectly clean | breaks when the app manages its own transactions or spans connections |
| **Truncate between tests** | wipe tables in FK order | simple, thorough | slow; forbids parallelism |
| **Reset between phases** | full reset at suite boundaries | cheap | tests within a phase can pollute each other |

Default recommendation: **unique data per test** for L4/L5, plus a **full reset
between phases** (in particular before visual tests, which need a pristine
world). Serialize the suite (`fileParallelism: false` or equivalent) until it's
green, then introduce parallelism deliberately.

---

## 8. Determinism

Every non-deterministic input is a future flake. Neutralize all of them:

- **Clock** — freeze or inject it. Never assert on `now()`. Beware tests that
  pass except near midnight, month end, or a DST boundary.
- **Randomness** — seed it, or inject the generator.
- **Timezone & locale** — pin both in the runner's environment. A suite that
  passes in UTC and fails in `Asia/Dubai` is a config bug, not a test bug.
- **Network** — no test may reach the public internet. Fake, record, or point at
  a local sink. One unstubbed call makes the whole suite depend on someone
  else's uptime.
- **Animation & fonts** (visual/E2E) — disable transitions, pin or embed fonts,
  wait for font load. Remote fonts are the top cause of screenshot churn.
- **Ordering** — never assert on unordered collection order. Sort, or assert set
  membership.
- **Dynamic content** — mask or freeze timestamps, "2 minutes ago" strings, and
  randomized ads/recommendations before snapshotting.

---

## 9. Rate limits, bot defenses, and other production guards

Production protections sabotage test suites, because a suite hammers one IP.

**Two-lane pattern:**

- **Main lane** — start the app with limiting disabled, *and* set the same flag in
  the test runner's own environment so rate-limit-specific tests self-skip
  instead of asserting a 429 that can never arrive.
- **Dedicated lane** — a second instance with limiting *on*, running only the
  rate-limit tests, ideally on its own port.

The subtle half is mirroring the flag into the runner. Without it, either the
main lane fails on limit tests or the limit tests silently never run — and the
second failure mode is invisible.

Same pattern for CAPTCHAs, bot detection, IP allowlists, and email
send-suppression.

---

## 10. External side effects

| Dependency | Test approach |
| --- | --- |
| Email / SMS | local sink (Mailpit, Mailhog, or an in-process outbox) and *assert the delivery*, don't just trust the call |
| Payments | provider test mode for the contract; deterministic in-process fake for logic |
| Object storage | local S3-compatible container, or a filesystem adapter |
| Third-party HTTP | recorded fixtures (VCR-style) with an explicit re-record command |
| AI / LLM APIs | fake by default; a tiny opt-in lane hitting the real API, never in the default suite |
| Queues / workers | run the worker in-process and drain it synchronously, so tests don't sleep |
| Webhooks inbound | POST the real signed payload shape to the endpoint; include a bad-signature case |

**Guard against real sends.** Add a non-production check that refuses to deliver
to any address outside the test domains, and assert that guard exists (L10). One
suite run that emails real customers is a career-defining incident.

---

## 11. Orchestration

One script per layer that needs a live environment. The script owns the whole
lifecycle so no human has to remember the order:

```
start services  →  reset & seed database  →  wait for health (+ capability)
→  clear stale build cache  →  run the layer's tests  →  report
```

Cross-platform by default (Node, Python, or `make`) unless the entire team is on
one OS. Every script must be idempotent — running it twice in a row from any
state must work.

Details that repeatedly matter:

- **Clear stale build artifacts** before browser runs. A long-lived dev server's
  cached chunks produce failures that look like application bugs.
- **Use a separate build output directory** for the test lane so it can't collide
  with the dev server's.
- **Reset the database between the functional and visual phases** — visual tests
  need a pristine world, and functional tests deliberately dirty it.
- **Exit with the test runner's exit code**, not the last command's.

---

## 12. CI

**One workflow (or job) per layer.** A single "tests" job that runs everything
tells you only that *something* broke. Per-layer jobs name the failure on the
PR page before anyone opens a log.

Baseline per job: pin the language and package-manager versions, cache
dependencies, provide datastores as CI services, and upload failure artifacts —
screenshots, traces, videos, visual diffs, service logs.

Two jobs earn their keep beyond the obvious:

- **Generated-artifact freshness** — regenerate the committed spec/client/schema
  and fail if the diff is non-empty.
- **Boundary/architecture rules** — cheap, and prevents the layering erosion that
  makes testing hard later.

Keep the fast layers (L0, L1) on a separate, always-run job so contributors get
feedback in under two minutes.
