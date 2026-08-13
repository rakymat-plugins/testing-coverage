# Phase Gates

A phase is one layer. A gate is the proof that the layer is done. No phase
begins until the previous phase's gate is recorded.

This file is the authority `/testing-implement` enforces.

---

## The gate definition

A phase passes its gate when **all five** hold:

1. **The layer has its own command**, runnable from the repo root, documented in
   the plan, and it exits zero.
2. **Every task in the phase is checked off** in `TESTING-TASKS.md`.
3. **Real command output is pasted** into `EVIDENCE-LOG.md` — the actual test
   count, pass count, and duration. Not a summary. Not "all green".
4. **Zero unexplained skips.** Every skipped or pending test has a written reason
   in the evidence log (feature flag off, platform-specific, external service
   unavailable). "Skipped because it was failing" is not a reason.
5. **At least one test in the phase has been proven able to fail.** See
   "Falsifiability check" below.

Anything less is red. Red means stop.

---

## Falsifiability check

The most important and most-skipped step. A test that cannot fail is worse than
no test: it converts an unknown into a false assurance.

Once per phase, pick the phase's most important test and prove it catches the
thing it claims to catch:

- Temporarily break the production code it covers (invert a condition, remove the
  lock, delete the authorization check, drop the constraint).
- Run the test. **It must fail**, and the failure message must point at the real
  cause.
- Restore the code. Run again. It must pass.
- Record both outcomes in the evidence log, naming what you broke.

For concurrency tests (L8) this is mandatory for *every* test, not one per phase
— a race test that passes against an unlocked implementation is the single most
common form of testing theatre.

---

## When a test fails: the decision

A failing test means exactly one of two things. Decide which **before** touching
anything, and say which out loud.

| | The app is wrong | The test is wrong |
| --- | --- | --- |
| Signal | the behaviour genuinely violates a documented or agreed requirement | the test asserts something the system never promised, or the fixture/setup is faulty |
| Action | **stop and report to the user.** Do not silently fix production code during a testing task | fix the test |
| Record | log it as a found defect with evidence | fix and move on; no ceremony needed |

Finding real bugs is a success of this process, not an obstacle to it. Report
each one plainly, with the reproducing test, and ask whether to fix it now or
record it. Do not fold an app fix into a testing commit without saying so.

---

## Forbidden routes to green

Every one of these is a gate violation. If any appears, the phase is red no
matter what the runner prints.

- Deleting or commenting out a failing test.
- Adding `skip` / `xfail` / `@Ignore` to a failing test without a written,
  non-failure reason.
- Loosening an assertion (`toBe(3)` → `toBeGreaterThan(0)`, exact match →
  `not.toBeNull()`, `assertEqual` → `assertTrue`) so it stops failing.
- Wrapping the assertion in `try`/`catch` and swallowing.
- Adding a retry to hide non-determinism instead of removing the non-determinism.
- Increasing a timeout to mask a real hang.
- Running with `--passWithNoTests` (or equivalent) in a phase that is supposed to
  contain tests.
- Reporting the phase green from a *partial* run (a filtered subset, a single
  file) instead of the whole layer command.
- Asserting on a constant the test itself declared.

**Weakening an assertion to reach green is the same class of act as deleting the
test.** If an assertion is genuinely wrong, that's the "test is wrong" branch
above — fix it deliberately and say what you changed and why.

---

## Flaky tests

A test that passes and fails on the same code is not a passing test. Do not gate
a phase on a flaky test, and do not paper over it with retries.

Order of attack:

1. Identify the non-deterministic input — clock, ordering, network, animation,
   shared state, or a timing assumption. `references/harness.md` §8 lists them.
2. Remove it. Wait on a condition, freeze the clock, sort the collection, isolate
   the data.
3. Only if the source is genuinely external and outside your control: quarantine
   the test into a separate non-gating lane, with a comment naming the cause and
   what would let it rejoin the main lane.

Retries as a *reporting* aid in CI are acceptable. Retries as a way to pass a
gate are not.

---

## Recording evidence

`EVIDENCE-LOG.md` is append-only. One entry per gate attempt, including the
failures — a log with only successes is not evidence, it's a press release.

Each entry carries: phase, layer, date, exact command, verbatim output tail,
counts, skips with reasons, the falsifiability result, and any defects found.

The template is in `templates/EVIDENCE-LOG.md`.

---

## Phase ordering

Default order, adjusted by the strategy file's risk findings:

| Phase | Contents | Why here |
| --- | --- | --- |
| 0 | Harness & scaffolding | nothing else can run without it |
| 1 | L0 static gates | cheapest defect-per-minute; fix the noise before adding tests |
| 2 | L1 unit | fast feedback, no infrastructure |
| 3 | L3 contract | locks the shapes the later layers assume |
| 4 | L4 integration | the highest-value layer; needs phase 0 |
| 5 | L5 authorization | needs the app mountable; reuses phase 4 harness |
| 6 | L2 component | independent; can move earlier if UI-heavy |
| 7 | L6 end-to-end | needs the full stack |
| 8 | L7 non-functional UI | reuses phase 7 harness |
| 9 | L8 resilience | needs phase 4 harness; often finds real bugs |
| 10 | L9 load | needs a production-like environment |
| 11 | L10 guardrails + CI wiring | encodes everything learned above |

**The one override that matters:** whatever the strategy file named as the
highest-risk area gets its layer moved as early as its dependencies allow. If
payments are the risk, L8 for payments happens in phase 5, not phase 9.

**Phase 0 is not optional and not merge-able into phase 1.** Its own gate is:
the empty layer commands all run and report "0 tests" cleanly, and the disposable
environment starts, seeds, and passes its health check from a cold start. Prove
the harness before writing tests that depend on it.

---

## Definition of done, for the whole effort

- Every adopted layer has a passing command and a gate entry.
- Every `SKIP`/`DEFER` from the strategy file is still recorded, with its trigger.
- A single aggregate command runs the layers that can run unattended.
- CI runs each layer as its own named job.
- `README` (or the contributing guide) documents how to run each layer and how to
  start the disposable environment.
- A new contributor can go from clone to green with one documented command.

That last one is the real test of the test suite.
