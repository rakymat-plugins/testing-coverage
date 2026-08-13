# The Layer Catalogue

Eleven layers. Each entry states what the layer proves, **what it cannot
prove** (the reason the next layer exists), its real cost, and when to skip it.

Skipping is normal. A static marketing site needs L0, L2, L7. A payments API
needs L0, L1, L3, L4, L5, L8, L10 and probably no L2 at all. Recording the
skip and the reason is as valuable as the tests you write.

---

## L0 — Static gates

**Proves:** the code compiles, types are sound, lint rules hold, module
boundaries aren't violated, no secret or credential is committed, formatting is
uniform.

**Cannot prove:** that anything behaves correctly.

**Cost:** hours to set up, seconds to run, near-zero maintenance.

**Skip when:** never. This is the cheapest defect-per-minute layer that exists.
Even a shell-script project gets `shellcheck`.

**Content ideas beyond the obvious:** architectural boundary rules (UI layer may
not import the database layer), import cycle detection, dependency license/audit
checks, dead-code detection.

---

## L1 — Unit

**Proves:** pure logic in isolation — money arithmetic, date and timezone
handling, validation rules, parsers and serializers, permission *predicates*,
state machine transitions, formatters, slug generation, retry/backoff math.

**Cannot prove:** that the units are wired together, that the database accepts
what you built, that the HTTP layer passes the right arguments.

**Cost:** minutes per test, milliseconds to run.

**Skip when:** the codebase is genuinely a thin pass-through with no branching
logic of its own. Rare. Usually people *think* this and are wrong — search for
`if`, `switch`, arithmetic on money, and date math before believing it.

**High-value targets people miss:** the exact boundary of every validation rule
(max length + 1, zero, negative, empty string, unicode), timezone/DST edges,
rounding direction on money, and every state transition that must be *rejected*.

---

## L2 — Component

**Proves:** one UI unit renders its states (empty, loading, error, populated,
disabled) and responds correctly to user interaction, in a host DOM.

**Cannot prove:** that the component receives real data, that routing reaches
it, that it looks right.

**Cost:** moderate. Sensitive to UI framework churn.

**Skip when:** no UI, or the UI is thin enough that L6 covers it more cheaply.
Prefer L2 over L6 for combinatorial state (a table with 9 status badges is 9
fast component tests, not 9 browser runs).

**Rule:** assert on what the user perceives — visible text, roles, labels,
enabled/disabled — never on internal state or private methods.

---

## L3 — Contract

**Proves:** producer and consumer agree. Three distinct flavours, don't conflate
them:

1. **Schema conformance** — the response actually matches the declared
   type/schema shared between client and server.
2. **Generated-artifact freshness** — the committed OpenAPI / GraphQL schema /
   protobuf / typed client is regenerated and identical. This belongs in CI as a
   "regenerate and diff must be empty" job.
3. **Consumer-driven contracts** — a separately deployed consumer's expectations
   are verified against the provider (Pact and equivalents). Only worth it with
   independently deployed services.

**Cannot prove:** that the values are correct, only that the shape is.

**Cost:** low for 1 and 2, high for 3.

**Skip when:** monolith with no external consumers and no generated artifacts —
then flavour 1 is often already covered by L4 assertions.

---

## L4 — Integration

**Proves:** the real application process, speaking its real transport (HTTP,
gRPC, queue message, CLI invocation), against a real datastore, produces the
right result and the right persisted state.

This is the highest-value layer in most projects and the most commonly missing.

**Cannot prove:** that the UI calls it correctly, or that roles are enforced
across *every* route (that's L5's combinatorial job).

**Cost:** high setup (disposable services, seeding, isolation), seconds to
minutes to run.

**Skip when:** genuinely impossible to stand up a datastore — but read
`references/harness.md` first; embedded/in-memory/containerized options usually
exist. A "unit tests with everything mocked" substitute does not cover this
layer and must not be recorded as if it did.

**Assert both sides:** the response *and* the persisted state. A create endpoint
that returns 201 and writes nothing passes a response-only test.

---

## L5 — Authorization matrix

**Proves:** for every protected action, every actor class gets the right answer.
Actor classes, at minimum: anonymous, each role, wrong-tenant/wrong-owner,
deactivated/suspended, valid session with missing CSRF or anti-forgery token,
expired or revoked credential.

Structure it as an explicit matrix so gaps are visible. A route added without a
matrix row is the single most common source of real-world data leaks.

**Cannot prove:** the business logic behind the authorized action.

**Cost:** moderate, and it parallelizes and templates extremely well — one
table-driven test can cover dozens of route × role pairs.

**Skip when:** there is no authentication and no multi-user data at all.

**Cheap trick:** this layer often does not need a real database. Mount the real
routing + middleware stack with the data layer faked, and you get a fast,
deterministic authorization suite that runs anywhere. Assert *status codes*, not
bodies.

**Also assert:** that a denied request is denied with the right code (401 vs 403
matters), and that the denial leaks nothing — no existence disclosure, no
enumeration difference between "not found" and "not yours".

---

## L6 — End-to-end

**Proves:** a real client (browser, mobile driver, CLI) completes a real user
journey through the whole stack.

**Cannot prove:** anything about edge cases economically. E2E is for *journeys*,
not for permutations.

**Cost:** highest. Slowest, flakiest, most maintenance.

**Budget rule:** pick the handful of journeys where "this being broken" means
"the product is down" — sign up, sign in, the core create action, the core
purchase/submit action, and the primary read path. Ten to twenty of these is a
healthy suite. Two hundred is a maintenance sinkhole; push the rest down to L4.

**Non-negotiable:** no fixed sleeps, ever. Wait on conditions. See
`references/anti-patterns.md`.

---

## L7 — Non-functional UI

Four separate concerns often lumped together. Adopt them independently.

- **Accessibility** — landmarks, one `h1`, every input labelled, keyboard
  reachable, focus visible and trapped in dialogs, contrast. Automated checks
  catch roughly a third of real issues; that third is still worth automating.
- **Runtime cleanliness** — fail the test on any uncaught error, unhandled
  rejection, or console error, with a small explicit allowlist. Extremely cheap,
  catches hydration and null-deref bugs users would hit immediately.
- **Visual regression** — pixel snapshots per theme × viewport. Powerful and
  genuinely painful: expect churn, require a diff-review step, pin fonts,
  disable animations, freeze dynamic content. Only adopt when visual fidelity is
  a stated requirement and someone will own the baselines.
- **Responsive** — layout integrity at defined breakpoints; no horizontal
  overflow, no clipped controls.

**Skip visual regression when** no one is committed to reviewing diffs. Orphaned
baselines get blanket-updated, which is worse than not having them.

---

## L8 — Resilience & concurrency

**Proves:** the system stays correct when things happen at once or go wrong.

Concrete targets:

- **Races** — fire N simultaneous requests at a limited resource (last seat,
  last unit of stock, a unique slug) and assert the invariant: exactly one wins,
  the counter never goes negative, no duplicate row exists.
- **Idempotency** — the same request twice (double-click, client retry, webhook
  redelivery) produces one effect.
- **Partial failure** — the datastore write succeeds but the email/payment call
  fails: what state is the system left in? Inject the failure and assert.
- **Transaction budgets** — a critical write path stays inside its expected
  number of statements/round-trips, so an N+1 regression fails loudly.

**Cannot prove:** behaviour at real production concurrency (that's L9).

**Skip when:** no shared mutable resource, no external side effects, single
user. Adopt immediately when money, inventory, seats, or quotas exist.

**Verify the test can fail.** A race test is worthless if it passes against a
known-broken implementation. Temporarily remove the lock/constraint, confirm the
test goes red, restore it. Record that you did.

---

## L9 — Load

**Proves:** defined throughput and latency thresholds hold under concurrency —
p95 under X ms, error rate under Y%, at Z concurrent users.

**Cannot prove:** correctness. Never use load tests as functional tests.

**Cost:** moderate to run, high to interpret. Needs a production-like
environment and realistic data volume to mean anything; results from a laptop
against 12 seeded rows are noise.

**Skip when:** traffic is low and predictable, or no production-like environment
exists. Deferring this is usually the right call for pre-launch products — but
record the deferral, with the trigger that should un-defer it.

---

## L10 — Guardrails & drift

The most underrated layer. Cheap tests that fail when something *silently*
regresses. Each one is typically 10–30 lines and pays for itself once.

Patterns worth stealing:

- **Migration drift** — assert that a hand-written database object (a partial
  index, a trigger, a check constraint) the ORM's schema language *cannot
  express* still exists in migration history. Without this, the next generated
  migration can silently drop it.
- **Config drift** — assert the production config still has the header, cache
  rule, or security setting a past incident added.
- **Generated-artifact freshness** — regenerate, diff must be empty (see L3).
- **Enum/constant sync** — an enum defined in two places stays in sync.
- **Budget guards** — payload size, bundle size, query count, dependency count.
- **Fixture-shape guards** — the shared DTO fixture stays within a size budget,
  so nobody quietly adds a heavy field to a hot list response.

**Naming honesty:** if a guardrail asserts on documentation text or config
files, name it a *drift guard* or *freshness check*, not a test of the behaviour
the doc describes. Mislabelling it creates false confidence that the behaviour
is covered.

**Skip when:** never — but only write these in response to something real (a
past incident, a fragile hand-written object, a budget someone cares about).
Speculative guardrails are noise.

---

## Choosing layers: the fast heuristic

Answer these, then take the union:

| If the project has… | Adopt |
| --- | --- |
| any code at all | L0, L10 |
| branching logic, calculations, validation | L1 |
| a UI with per-state components | L2 |
| a shared schema, generated client, or external consumer | L3 |
| a datastore or any persistence | L4 |
| login, roles, tenants, or ownership | L5 |
| a user-facing product with a critical journey | L6 |
| accessibility or brand-fidelity requirements | L7 |
| money, inventory, quotas, webhooks, or retries | L8 |
| known traffic targets and a staging environment | L9 |

Then cut. If the honest time budget is one week, ship L0 + L1 + L4 + L5
completely rather than all eleven at 20% each. Depth in the layers that matter
beats a thin veneer everywhere — and record what was cut so the next person
knows it's a gap, not an oversight.
