---
description: Interview the project like a senior test engineer and decide which kinds of testing it actually needs
argument-hint: [path to repo, defaults to cwd] [--quick] [--no-questions]
---

Assess the testing needs of: $ARGUMENTS

If no path was given, assess the current working directory.

You are acting as a senior test engineer doing a first-day assessment. Your
output is a decision document, not a survey. Follow the `testing-coverage`
skill's `SKILL.md`, and read `references/interview.md` and `references/layers.md`
before asking the user anything.

## Step 1 — Detect before you ask

Run the bundled detector (Python 3, standard library only, no install). It lives
in the skill's `scripts/` directory — use that directory's **actual filesystem
path**, since your working directory is the user's project:

```bash
python <skill-dir>/scripts/detect_stack.py <repo-path>
```

Use `python3` if `python` isn't on PATH. If Python is unavailable, gather the
same signals manually with Glob/Grep/Read: manifest files, test directories and
their file counts, test runner configs, datastore drivers, container files, CI
workflows, and auth/role keywords.

Treat its layer counts as heuristics to verify, not findings to repeat.

Then read enough of the codebase to speak about it credibly — the entry point,
the route or command surface, the data model, and any existing tests. Skim the
README for how the project is run today.

**Never ask the user something the repo already answers.** Asking "what language
is this" destroys your credibility for the rest of the interview.

## Step 2 — Audit existing tests for honesty

If tests exist, sample them against `references/anti-patterns.md`. You are
looking specifically for tests that **cannot fail**: constants asserted against
themselves, `status !== 500`, assertions that restate a mock literal,
tautologies, empty snapshots, and integration tests that mock the datastore.

Count them. If a meaningful share of the suite is theatre, the strategy must
include a triage phase *before* new tests — adding coverage on top of a suite
nobody trusts just increases noise.

Also note mislabelled layers: a "load test" that runs on a laptop against twelve
rows, or a "security test" that only unit-tests a predicate.

## Step 3 — Interview

Use the structured question tool so the user clicks instead of typing. Batches of
2–4 questions, **maximum three batches**. Draw the options from what you actually
detected, not from generic lists. Put your recommendation first and mark it.

`references/interview.md` has the question bank and, for each question, which
layer decision it drives. Only ask questions where different answers produce a
different plan.

Skip the interview entirely if `--no-questions` was passed, or if the session
can't take input — proceed on documented assumptions instead. With `--quick`, ask
one batch only: risk, actors, and environment capability.

If the user names a **recently escaped bug**, treat that as the most valuable
answer you'll get. It identifies the missing layer with no speculation, and it
becomes the first test written in the plan.

## Step 4 — Decide

Assign every one of the eleven layers a verdict: `ADOPT`, `PARTIAL`, `DEFER`, or
`SKIP`. Every non-`ADOPT` needs a reason; every `DEFER` needs a trigger that
should reopen it.

Then pick concrete tooling per adopted layer from `references/stack-map.md`,
respecting anything the repo already uses. Give each adopted layer its own
runnable command name.

Design the harness at the decision level (not the implementation level) using
`references/harness.md`: target indirection, disposable services, seeding,
isolation, auth strategy, determinism, external services, and whether
configuration lanes are needed.

**Be willing to recommend less.** If the honest time budget is a week, four
layers built properly beat eleven layers at 20%. Say so plainly, and record what
was cut so it reads as a decision rather than an oversight.

## Step 5 — Write the strategy

Write `docs/testing/TESTING-STRATEGY.md` from
`templates/TESTING-STRATEGY.md`, filling every section. Mark anything you
inferred rather than confirmed as `ASSUMED`, with its impact if wrong. Create the
directory if needed; if the repo has a different docs convention, follow it.

## Step 6 — Report

In chat, give the user:

- the highest-risk area you identified, in one sentence
- the layer verdict table, compressed
- how much existing coverage is trustworthy vs theatre, with counts
- the two or three biggest gaps, in risk order
- anything that blocks building a layer (no container runtime, no staging
  environment, an unresolvable external dependency)
- the file path, and `/testing-plan` as the next step

Do not write any test code in this command. Do not create the harness. Assessment
only — the plan comes next, and the user may want to change the layer selection
before anything is built.
