---
description: Turn the testing strategy into a spec-driven plan plus a phased, gated task list
argument-hint: [path to TESTING-STRATEGY.md, auto-detected if omitted]
---

Write the testing plan and task list for: $ARGUMENTS

Follow the `testing-coverage` skill's `SKILL.md`. Read `references/gates.md` and
`references/layers.md` before planning, and `references/stack-map.md` while
choosing commands.

## Step 1 — Load the strategy

Find `docs/testing/TESTING-STRATEGY.md` (or the path given). Read it fully.

**If it doesn't exist, stop and tell the user to run `/testing-assess` first.**
Do not invent a strategy — the layer selection is the user's decision, and
guessing it wastes the whole plan.

If it exists but is stale (the repo has changed materially since it was written),
say so, list what changed, and ask whether to re-assess or proceed.

## Step 2 — Verify the strategy against reality

Before planning, confirm each adopted layer is actually buildable:

- Does the chosen tool exist for this project's language and version?
- Can the disposable environment actually start here? If the strategy assumed
  containers, check for a container runtime.
- Do the commands the strategy names collide with existing scripts?

Any layer that isn't buildable as specified gets flagged now, with an
alternative, rather than becoming a blocked task in phase 6.

## Step 3 — Write the plan

Write `docs/testing/TESTING-PLAN.md` from `templates/TESTING-PLAN.md`.

The plan is the **design**: goal, layers in scope with their commands, directory
and naming conventions, harness build-out, phase table with exit criteria,
coverage targets per area, CI design, risks, defect policy, and effort.

Key decisions to get right:

- **Conventions.** If the repo already has a test directory, naming scheme, or
  runner, record it unchanged and extend it. Never introduce a parallel
  convention.
- **Phase order.** Default order is in `references/gates.md`. Apply one override:
  the highest-risk area from the strategy moves as early as its dependencies
  allow. If payments are the risk, resilience testing for payments is phase 5,
  not phase 9.
- **Coverage targets as lists, not percentages.** For each area, enumerate the
  specific cases that must exist. This is what makes the task file generatable
  and gaps visible.
- **Phase 0 is never merged into phase 1.** Its gate is: cold start brings the
  environment up, seeds it, health-checks green, and every layer command runs
  cleanly at zero tests.

## Step 4 — Write the tasks

Write `docs/testing/TESTING-TASKS.md` from `templates/TESTING-TASKS.md`.

Requirements:

- **One phase per layer**, in the plan's order. Phase 0 is the harness.
- **Sequential IDs** `T001…`, never renumbered. Append-only.
- Each task states what it must **prove**, not just what file to create. "Add
  tests for the booking endpoint" is not a task; "assert a booking request with a
  past date returns 422 with a `date` field error" is.
- Mark `[P]` only where tasks are genuinely independent — different files, no
  shared fixture being created, no ordering dependency.
- **Every phase ends with a `GATE` task** naming: the exact command, that zero
  unexplained skips are allowed, and which test gets the falsifiability check.
- Phase 9 (resilience) requires a falsifiability check on **every** test, not one
  per phase — a race test that was never seen failing proves nothing.
- Size tasks so one is a sensible commit. Split anything that would touch more
  than a handful of files.
- Include the closing tasks: CI job per layer, README documentation, and a
  clone-to-green verification.

Derive the task list from the plan's coverage-target table, so every enumerated
case maps to at least one task. Then check the reverse: every task traces to a
coverage target or a harness requirement. Anything that traces to neither is
scope creep — cut it.

## Step 5 — Seed the evidence log

Create `docs/testing/EVIDENCE-LOG.md` from `templates/EVIDENCE-LOG.md`, empty
except for the template block. `/testing-implement` appends to it.

## Step 6 — Report

Give the user:

- the phase list with task counts per phase
- total task count and the effort estimate
- which phase carries the most risk, and why
- anything the strategy specified that turned out not to be buildable, with the
  alternative you chose
- the file paths, and `/testing-implement` as the next step

Write no test code in this command. Create no harness files. The plan and the task
list are the deliverable — the user should be able to read them and disagree
before anything is built.
