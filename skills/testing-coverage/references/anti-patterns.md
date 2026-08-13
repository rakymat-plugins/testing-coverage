# Anti-Patterns

Read before writing assertions, and again when a test won't go green.

Every pattern below has been shipped by real teams, passes CI, raises coverage
numbers, and proves nothing. They are worse than missing tests, because a missing
test is a known unknown.

**The single test to apply to any test you write: if the feature were broken,
would this fail?** If you can't answer yes with confidence, you're writing
theatre.

---

## Tests that cannot fail

### Asserting a constant against itself

```js
const BUDGETS = { listQueryCount: 3 };
it("keeps the query budget", () => {
  expect(BUDGETS.listQueryCount).toBeLessThanOrEqual(3);   // ❌ measures nothing
});
```

The test declared the value it asserts. The production code could issue 400
queries and this stays green. **Fix:** measure the real thing — hook the query
event, count statements during a real request, assert on the count. If you truly
can't measure it, the constant is documentation; move it to a doc and don't call
it a test.

### The tautology family

```js
expect(true).toBe(true);
expect(result).toBeDefined();          // on a function that always returns an object
expect(typeof x).toBe("object");
expect(() => doThing()).not.toThrow(); // when doThing never throws
expect(list.length).toBeGreaterThanOrEqual(0);  // always true
```

### Asserting only "not a server error"

```js
expect(response.status).not.toBe(500);           // ❌
expect(statuses.every(s => s < 500)).toBe(true); // ❌
```

Passes for 200, 201, 401, 403, and 404 alike. Common in concurrency tests, where
it is most dangerous: the race is unproven, but the test looks like it covers it.
**Fix:** assert the exact expected status *and* the invariant — "exactly one 201,
one 409, and precisely one row exists".

### Testing against data that doesn't exist

A test that POSTs to a resource under a random ID and accepts 404 as success
never reaches the logic it claims to test. Seed the resource first.

### Snapshot of nothing

Committing a snapshot of an empty render, a loading spinner, or `undefined` — and
it stays green forever because it captured the broken state as the baseline.
Always look at what a new snapshot actually contains before committing it.

---

## Tests that test the mock

```js
vi.mock("./repo", () => ({ getUser: () => ({ id: 1, name: "A" }) }));
it("returns the user", async () => {
  expect((await service.getUser(1)).name).toBe("A");   // ❌ asserts the mock literal
});
```

Everything between input and assertion is fake, so the test passes if the service
is deleted and replaced with a pass-through. **Signal you've crossed the line:**
the expected value in your assertion is the same literal you wrote in the mock,
with no transformation between them.

**Fix:** mock at the *boundary* (network, clock, filesystem, third-party SDK) and
let your own code run. If mocking your own modules is the only way to test a unit,
that's a design signal — the unit has too many collaborators.

---

## Over-specification

### Asserting implementation details

```js
expect(component.state.isOpen).toBe(true);      // ❌ internal
expect(await screen.findByRole("dialog")).toBeVisible();  // ✅ user-perceivable
```

```js
expect(spy).toHaveBeenCalledWith(exactInternalShape);  // ❌ breaks on refactor
expect(await db.orders.count()).toBe(1);               // ✅ asserts the outcome
```

Tests coupled to internals fail on every safe refactor and pass through real
behavioural breaks. They train the team to ignore red.

### Full-object equality on a large response

`expect(body).toEqual(hugeObject)` fails on any unrelated field addition. Assert
the fields the test is about; use schema validation for shape.

### Snapshot sprawl

Snapshotting whole pages so every copy change breaks fifty tests. Nobody reads
those diffs; they get bulk-accepted, and the snapshots stop meaning anything.
Snapshot small, stable, meaningful units.

---

## Non-determinism

### Fixed sleeps

```js
await page.click("#save");
await page.waitForTimeout(2000);        // ❌ flaky and slow, forever
await expect(page.getByText("Saved")).toBeVisible();  // ✅ waits on the condition
```

A sleep is a bet that the machine is never slower than today. It loses in CI. It
is also pure added runtime on every fast run. There is a condition-based wait for
every case: element state, network idle, response received, database row present,
log line emitted. Use it.

### Real time

`expect(result.createdAt).toBe(new Date().toISOString())` — passes except when a
millisecond ticks between the two calls. Freeze the clock or assert a range.

### Order dependence

Tests that pass only in file order, because test A creates what test B reads.
Randomize execution order once to find these; then make every test create what it
needs.

### Shared mutable fixtures

One exported object mutated by several tests. Passes alone, fails in the suite,
or worse — passes in the suite and fails alone. Freeze fixtures or return fresh
copies from a factory.

### Asserting on unordered results

`expect(rows[0].name).toBe("Alice")` with no `ORDER BY`. Databases are not
obligated to be consistent about this. Sort, or assert set membership.

---

## Mislabelled tests

| Named | Actually | Why it's harmful |
| --- | --- | --- |
| "integration test" that mocks the database | a unit test | the integration layer reads as covered when nothing crosses a process boundary |
| "retention policy test" that greps a markdown doc | a doc-freshness guard | the policy itself is unenforced, and the row in the coverage table lies |
| "security test" asserting a helper returns `false` | a unit test of a predicate | the route may never call the helper |
| "E2E test" that stubs every network call | a component test | nothing end-to-end was exercised |
| "load test" run against 12 seeded rows on a laptop | noise | produces confident numbers with no relationship to production |

Guardrails and doc-freshness checks are genuinely valuable — see L10. The sin is
only in the label, and the label is what someone trusts when deciding whether a
risk is covered. Name it for what it verifies.

---

## Coverage theatre

- **Chasing a percentage.** 100% coverage with no assertions on behaviour is
  achievable and worthless. Coverage tells you what code *ran*, never whether it
  was correct.
- **Testing generated code, config objects, DTOs, and getters** to lift the
  number.
- **One giant test** exercising twelve behaviours; when it fails you learn only
  that "checkout is broken". Prefer many small tests with names that state the
  expected behaviour.
- **Excluding the hard files from the coverage config** so the number looks good.
- **Asserting the happy path only.** The bugs live in the empty state, the
  boundary value, the concurrent case, the permission denial, and the malformed
  input.

Use coverage as a *finder of untested areas*, never as a goal. "Which
authorization branches has no test ever entered" is the useful question.

---

## Bad test names

```
it("works")                          ❌
it("test user 2")                    ❌
it("handles the thing correctly")    ❌
it("rejects a booking when the last seat is already taken")   ✅
it("returns 403 for an owner requesting another owner's school")  ✅
```

The name is what a future engineer reads at 2am from a CI log. It should state
the expected behaviour and the condition, so a failure is diagnosable without
opening the file.

---

## Process anti-patterns

- **Writing all the tests, then running them once at the end.** You get a wall of
  failures with tangled causes. Run each test as you write it.
- **Building all layers to 20%** instead of the important layers to 100%. Depth
  beats breadth; see `references/layers.md`.
- **Adding tests on top of a suite nobody trusts.** Triage first — a suite with
  known-fake tests teaches the team that red means "re-run".
- **Testing the framework.** Assume the ORM saves, the router routes, and the
  validator validates. Test *your* rules.
- **Deferring the harness.** Every "I'll parameterize the URL later" becomes a
  suite that runs on one laptop.
