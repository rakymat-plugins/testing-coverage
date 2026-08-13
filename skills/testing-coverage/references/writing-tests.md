# Writing the Tests

Per-layer playbooks: what to actually assert, in what order, and the cases people
forget. Read the section for the phase you're in.

**Universal shape**, in every layer and language:

```
Arrange — build the world explicitly. No hidden setup the reader must hunt for.
Act     — one action. If there are two, it's two tests.
Assert  — the observable outcome, AND the persisted/side effect where one exists.
```

**Universal naming:** `<expected behaviour> when <condition>`. A failure should be
diagnosable from the name alone.

**Universal rule:** write one test, run it, watch it pass, move on. Never write
twenty and run them once.

---

## L0 — Static gates

Not tests, but the same discipline: each check gets its own command and must exit
non-zero on violation.

Setup order that avoids a wall of noise: turn a check on, fix or explicitly
baseline the existing violations, *then* make it blocking. A gate everyone
bypasses is worse than no gate.

Worth adding beyond the defaults: architectural boundary rules (which layer may
import which), import-cycle detection, and a committed-secret scan.

---

## L1 — Unit

Test the **behaviour of the rule**, not the shape of the function.

For every rule, cover:

| Case | Example |
| --- | --- |
| the ordinary case | valid input → expected output |
| every boundary, both sides | max length and max+1; zero; -1; empty; single item |
| every rejection | each invalid input hits the *specific* error, not just "throws" |
| the type/format edges | unicode, emoji, RTL text, leading/trailing whitespace, `null` vs missing |
| the domain edges | money rounding direction, timezone/DST, leap day, negative amounts |

For state machines, the valuable half is the **rejected** transitions. Enumerate
the full matrix and assert every illegal move is refused:

```js
for (const [from, to] of ALL_PAIRS) {
  const legal = LEGAL_TRANSITIONS[from]?.includes(to) ?? false;
  it(`${legal ? "allows" : "rejects"} ${from} → ${to}`, () => {
    expect(canTransition(from, to)).toBe(legal);
  });
}
```

Table-driven tests are strongly preferred here: one row per case, the runner
reports each row separately, and adding a case is one line.

---

## L2 — Component

Cover the **states**, not the props: empty, loading, error, populated, disabled,
and any permission-conditional variant.

Assert what a user perceives — visible text, accessible role, label, enabled
state. Query by role and label, not by CSS class or test id, so the test also
verifies accessibility. Reach for a test id only when there is genuinely no
semantic handle.

For interaction: act like a user (click, type, tab, press Enter), then assert the
resulting *visible* change. Never assert internal state.

---

## L3 — Contract

Three separate jobs, all cheap:

1. **Shape conformance** — validate a real response against the shared schema, and
   assert it *rejects* a malformed one too (otherwise the validator may be a
   no-op).
2. **Freshness** — regenerate the committed artifact, diff must be empty. Belongs
   in CI with the exact regeneration command in the failure message.
3. **Coverage of the surface** — assert the spec contains every route group and a
   minimum path count, so a route added without spec regeneration fails.

Also assert the *error* envelope shape, not just success. Clients break on
unexpected error formats more often than on success formats.

---

## L4 — Integration

The template, in any language:

```
1. Arrange — seed exactly the rows this test needs, with unique identifying data
2. Authenticate — as the actor the test is about
3. Act — one real request over the real transport
4. Assert status — the exact code
5. Assert body — the fields this test is about
6. Assert persistence — read the datastore back; the state actually changed
7. Assert side effects — the mail sink received it, the queue got the job
```

**Step 6 is the one people skip, and it's the one that catches real bugs.** An
endpoint that returns `201` and writes nothing passes a body-only test.

Cases to cover per endpoint:

- success, with persistence verified
- each validation failure → correct field-level error
- not-found → 404, and it must not disclose existence of others' data
- conflict / duplicate → 409 with a usable message
- optimistic-concurrency / stale-version rejection, if the app has versioning
- unauthorized and forbidden (or delegate these entirely to L5 — decide once and
  be consistent)

Use unique data per test (timestamped emails, random slugs) so the suite doesn't
depend on execution order.

**Assert error messages don't leak.** Registration and password reset must respond
identically for existing and non-existing accounts, or you've built an account
enumeration oracle. This is a real test, easy to write, and routinely missing.

---

## L5 — Authorization matrix

Build it as a table, one row per (action, actor) pair, and let the runner report
each pair separately:

```js
const ACTORS = [
  ["anonymous",        () => ({})],
  ["parent",           () => headersFor("PARENT")],
  ["owner",            () => headersFor("OWNER")],
  ["other owner",      () => headersFor("OWNER", otherOwnerId)],
  ["admin",            () => headersFor("ADMIN")],
  ["suspended admin",  () => headersFor("ADMIN", { status: "SUSPENDED" })],
];

const CASES = [
  ["GET  /admin/users",  { anonymous: 401, parent: 403, owner: 403,
                           "other owner": 403, admin: 200, "suspended admin": 403 }],
];
```

Cover, for every protected action:

- anonymous → 401 (not 403 — the distinction tells clients whether to re-login)
- each wrong role → 403
- correct role, wrong tenant/owner → 403 or 404, decided deliberately and applied
  consistently
- suspended/deactivated with a still-valid token → 403
- valid session, missing or invalid CSRF/anti-forgery token → 403
- expired or revoked credential → 401

Assert **status codes only.** Bodies belong to L4. This keeps the matrix fast and
lets it run with the data layer faked.

Add one meta-test that enumerates the app's actual route table and fails when a
protected route has no matrix row. Without it, the matrix silently rots as routes
are added — this single test is what keeps L5 alive over years.

---

## L6 — End-to-end

One test per **journey**, not per screen. Write it as the user's narrative and
assert at each meaningful checkpoint, so a failure localizes.

```
sign in → search → open a result → submit the enquiry
→ assert the confirmation is visible
→ assert it appears in the owner's inbox
→ assert the notification email reached the sink
```

Rules:

- **Never** a fixed sleep. Condition-based waits only.
- Query by role/label/text — the same locators that make the app accessible.
- Load a pre-authenticated session for setup; only the auth journey itself should
  actually type credentials.
- Create the data the journey needs through the API, not through the UI. Driving
  the UI for setup triples the runtime and couples unrelated tests together.
- Keep the suite small enough that everyone runs it. Push permutations to L4.

---

## L7 — Non-functional UI

**Accessibility** — per page: exactly one `h1`, one `main`, every input labelled
(`for`/`aria-label`/wrapping label), all interactive elements keyboard reachable
in a sensible order, visible focus, dialogs trap focus and restore it on close,
images have `alt` (empty for decorative). Run an automated engine over each page
*and* keep the structural assertions — they catch different things.

**Runtime cleanliness** — attach listeners for console errors, uncaught errors,
and unhandled rejections; fail the test on any that aren't in a small, commented
allowlist. Keep the allowlist regex-based and justify each entry, or it becomes a
dumping ground.

**Visual regression** — before the first snapshot: pin/embed fonts, disable
animations and transitions, freeze or mask dynamic content, use a fixed seeded
dataset, and set an explicit device scale factor. Snapshot per theme × viewport.
Set a small tolerance (~1–2%) so antialiasing noise doesn't fail the build.
Baselines are OS- and browser-specific: generate them where CI runs, or accept
that local runs will differ.

**Responsive** — at each breakpoint assert no horizontal overflow
(`scrollWidth <= clientWidth`), primary actions visible without scrolling, and
navigation reachable.

---

## L8 — Resilience & concurrency

**Race template:**

```js
it("allows exactly one booking for the last seat", async () => {
  const school = await seedSchoolWithSeats(1);

  const results = await Promise.all(
    Array.from({ length: 5 }, () => bookSeat(school.id))
  );

  expect(results.filter(r => r.status === 201)).toHaveLength(1);   // exactly one wins
  expect(results.filter(r => r.status === 409)).toHaveLength(4);   // the rest lose cleanly
  expect(await seatsRemaining(school.id)).toBe(0);                 // never negative
  expect(await bookingCount(school.id)).toBe(1);                   // no duplicate row
});
```

Assert the **invariant**, not just the absence of a 500. Then run the
falsifiability check from `references/gates.md`: remove the lock or constraint and
confirm the test goes red. A race test that was never seen failing is not
evidence of anything.

**Idempotency:** send the identical request twice — same payload, same
idempotency key, same webhook event id — and assert exactly one effect. Cover
double-click, client retry, and provider redelivery.

**Partial failure:** make the second side effect fail (mail server down, payment
provider timeout) and assert the resulting state is one you can recover from —
either fully rolled back, or persisted with a retryable marker. Assert which one
deliberately; "it depends" means nobody has decided.

**Transaction/query budgets:** count statements during a critical write path and
assert a ceiling. This is the only cheap defense against N+1 regressions. It must
*measure*, not restate a constant.

---

## L9 — Load

Define thresholds before running, or the results are unfalsifiable: p95 latency,
error rate, and target concurrency. Encode them as the tool's pass/fail
thresholds so the run itself is a gate.

Model realistic behaviour — think time between requests, a mix of endpoints,
varied parameters. A tight loop on one URL measures your cache, not your app.

Run against production-like data volume. Tag requests by endpoint so the report
attributes latency. Record the environment alongside the numbers; a result
without its environment is not comparable to anything.

---

## L10 — Guardrails

Each guardrail is a few lines, written in response to something real.

- **Migration drift** — read all migration files, assert the hand-written object
  still exists, and that the *most recent* action on it was create rather than
  drop. Comment it with the incident or risk that motivated it.
- **Config drift** — assert the production config still contains the security
  header or cache rule a past incident added.
- **Constant sync** — assert two independently-defined enums or lists match.
- **Budget guards** — payload/bundle/dependency size ceilings.
- **Forged-auth sync** — if the harness re-implements a signing algorithm, assert
  it still matches the application's.

Write the *reason* in the test file, not just the assertion. A guardrail whose
motivation is forgotten gets deleted the first time it's inconvenient — the
comment is what makes it survive.
