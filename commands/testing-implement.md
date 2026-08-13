---
description: Execute the testing plan phase by phase, running each layer and proving it green before moving to the next
argument-hint: [phase number or "next", defaults to the first unfinished phase] [--phase-only]
---

Implement the testing plan: $ARGUMENTS

Follow the `testing-coverage` skill's `SKILL.md`. Read `references/gates.md`
before starting — it is the authority on what "done" means — plus
`references/writing-tests.md` for the current phase's layer and
`references/anti-patterns.md` before writing any assertion.

## Step 1 — Load state

Read `docs/testing/TESTING-PLAN.md`, `TESTING-TASKS.md`, and `EVIDENCE-LOG.md`.

**If the task file doesn't exist, stop and tell the user to run `/testing-plan`.**

Determine the current phase: the first phase whose `GATE` task is unchecked. If an
argument named a specific phase, use it — but if earlier phases aren't gated,
**say so and ask** before skipping ahead. A phase built on an ungated harness
tends to fail for reasons that look like test bugs.

Use the todo tool to track the current phase's tasks so progress is visible.

## Step 2 — Work one phase

**One phase at a time. Never start the next phase in the same run unless every
gate up to it is green.** With `--phase-only`, stop after this phase's gate
regardless.

Before writing tests: confirm the phase's layer command exists and runs. A layer
whose command errors out on invocation is a phase-0 defect, not a test-writing
problem — fix that first.

For each task, in order (respecting `[P]` for parallelizable ones):

1. Write the test. Follow `references/writing-tests.md` for the layer.
2. **Run it immediately.** One test, one run. Never write ten and run once — you
   get a wall of failures with tangled causes.
3. Watch it pass for the right reason. Ask the anti-pattern question every time:
   *if the feature were broken, would this fail?* If you can't answer yes with
   confidence, the test is theatre — rewrite it.
4. Mark the task `[x]` in `TESTING-TASKS.md`. The file is the source of truth for
   progress, so keep it current as you go, not at the end.

Deviations from the plan go in the task file's "Deviations" table with a reason.

## Step 3 — When a test fails

Decide which of two things is true, and **say which out loud** before changing
anything:

**The app is wrong** — the behaviour genuinely violates a documented or agreed
requirement. **Stop. Report it to the user** with the reproducing test. Ask
whether to fix it now or log it. Do not silently fix production code inside a
testing task; the user needs to know their app had a bug.

**The test is wrong** — it asserts something the system never promised, or the
fixture/setup is faulty. Fix the test, note it, move on. No ceremony.

Log every real defect in the task file's "Defects found" table and in the
evidence log entry for the phase.

### Never take these routes to green

Each one is a gate violation, regardless of what the runner prints:

- deleting or commenting out a failing test
- adding skip/xfail/ignore without a written, non-failure reason
- loosening an assertion so it stops failing (`toBe(3)` → `toBeGreaterThan(0)`,
  exact match → `not.toBeNull()`)
- wrapping the assertion in try/catch and swallowing
- adding a retry to hide non-determinism instead of removing the non-determinism
- raising a timeout to mask a real hang
- running with `--passWithNoTests` in a phase that should contain tests
- reporting the phase green from a filtered subset instead of the whole command

**Weakening an assertion to reach green is the same class of act as deleting the
test.** If an assertion is genuinely wrong, that's the "test is wrong" branch —
fix it deliberately and state what changed and why.

If a test is flaky, find and remove the non-deterministic input
(`references/harness.md` §8). Do not gate a phase on a flaky test.

## Step 4 — The gate

Run the phase's **full layer command**, not a subset. Then verify all five gate
conditions from `references/gates.md`:

1. the command exits zero
2. every task in the phase is checked off
3. real output is recorded — actual counts and duration, verbatim
4. zero unexplained skips; each skip has a written reason that isn't "it failed"
5. the falsifiability check is done and recorded

**Falsifiability check** — once per phase (every test in the resilience phase):
temporarily break the production code the test covers (invert the condition,
remove the lock, delete the authorization check), confirm the test **fails** with
a message pointing at the real cause, restore the code, confirm it passes again.
Record both outcomes and name what you broke. A test never seen failing is not
evidence.

Append the entry to `EVIDENCE-LOG.md` using its template — **including failed
attempts.** The log is append-only; never edit or remove a past entry.

Then check the `GATE` task and report the phase complete.

## Step 5 — Stop and report if

- a real application bug is found → report, ask before fixing
- the harness or environment won't start → report with the service logs; do not
  work around it by mocking the thing that was supposed to be real
- a layer turns out not to be buildable as planned → report the alternative
- a test can't be made to pass without weakening it → report; this usually means
  the requirement was never actually agreed
- the phase would need production code changed to be testable → report the
  refactor needed and ask; don't refactor the app unannounced

## Step 6 — Report

After each phase:

- the phase and layer completed
- the verbatim gate output — counts and duration
- what the falsifiability check proved, and what you broke to prove it
- defects found, if any, with the test that reproduces them
- skips and their reasons
- the next phase, its task count, and anything it needs that doesn't exist yet

Then either continue to the next phase or stop, per `--phase-only` and whether
the user asked for a single phase.

**Never report a layer as passing without having run it in this session and
pasted the output.** If you didn't run it, say you didn't run it.
