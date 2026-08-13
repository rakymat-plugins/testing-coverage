---
name: testing-coverage
description: Use when a project needs a test suite designed, expanded, or rescued — no tests at all, tests that only pass on one machine, unclear what kinds of testing the project actually needs, coverage numbers that don't reflect real risk, flaky or theatrical tests, missing integration/authorization/end-to-end/visual/load coverage, or a request to plan testing phases, write a testing plan and task list, or implement a testing plan layer by layer with a green gate between layers. Works in any language, framework, or stack.
---

# Testing Coverage

## What this is

A three-command workflow that turns "we should add tests" into a designed,
layered, verifiable test suite — in any stack.

| Command | Question it answers | Writes |
| --- | --- | --- |
| `/testing-assess` | What kinds of testing does *this* project actually need, and why? | `docs/testing/TESTING-STRATEGY.md` |
| `/testing-plan` | What exactly gets built, in what order, with what exit criteria? | `docs/testing/TESTING-PLAN.md` + `TESTING-TASKS.md` |
| `/testing-implement` | Build it, one layer at a time, proving each layer green before the next. | test code + `EVIDENCE-LOG.md` |

Run them in that order. Each one reads the file the previous one wrote, so a
different person (or a fresh session) can pick up at any stage.

They are also reachable in plain language — "plan testing for this project",
"what tests do I need here", "implement the testing plan".

## The core principle

**Coverage percentage is not a goal. Layers are.**

A project with 90% line coverage from unit tests alone still ships broken
logins, because no test ever spoke HTTP to a real database. A project with
40% coverage spread deliberately across unit → integration → authorization →
end-to-end catches nearly everything that actually reaches users.

So this skill never asks "what % should we hit". It asks "which layers does
this project's risk profile require, and what does each one prove that no
other layer can".

## The layer catalogue

Eleven layers exist. **Almost no project needs all eleven.** Choosing which
to skip — and recording why — is the main output of `/testing-assess`.

| # | Layer | Proves | Needs |
| --- | --- | --- | --- |
| L0 | Static gates | It compiles, lints, types check, boundaries hold, no secrets committed | nothing |
| L1 | Unit | Pure logic, calculations, validation, parsing, state transitions | nothing |
| L2 | Component | One UI unit renders and responds to interaction | UI + DOM/host env |
| L3 | Contract | Producer and consumer agree on shapes; generated specs are fresh | shared schema |
| L4 | Integration | Real process + real datastore over the real transport | disposable services |
| L5 | Authorization | Every role × every protected action, including anonymous and revoked | auth system |
| L6 | End-to-end | A real client drives the real app through a real user journey | full stack running |
| L7 | Non-functional UI | Accessibility, zero runtime console errors, visual regression, responsive | L6 harness |
| L8 | Resilience | Races, idempotency, retries, partial failure, transaction budgets | L4 harness |
| L9 | Load | Throughput and latency thresholds under concurrency | full stack running |
| L10 | Guardrails | Drift: migrations silently dropped, config regressed, budgets exceeded | nothing |

Full detail — what each layer *cannot* prove, cost, and when to skip it — is in
`references/layers.md`. Stack-specific tooling for every layer is in
`references/stack-map.md`.

## Two non-negotiable rules

**1. One command per layer.** Every layer a project adopts must be runnable
alone, by name, from the repo root (`npm run test:integration`, `pytest -m
authz`, `go test ./... -run Integration`). A suite you can only run all-or-
nothing cannot be gated, cannot be debugged, and will be abandoned.

**2. Green gate between layers.** A layer is done when its own command exits
zero and that output is recorded as evidence. Not "mostly passing". Not
"failing for unrelated reasons". `/testing-implement` enforces this and will
stop rather than proceed on red — see `references/gates.md`.

## Reference map

Load these as needed; don't read them all up front.

| File | Read it when |
| --- | --- |
| `references/layers.md` | Choosing layers, or writing a layer's first test |
| `references/stack-map.md` | Picking concrete tools for the detected stack |
| `references/interview.md` | Running `/testing-assess` — the question bank |
| `references/harness.md` | Designing the disposable environment, fixtures, auth, determinism |
| `references/gates.md` | Defining or enforcing phase exit criteria |
| `references/writing-tests.md` | Actually writing tests for a given layer |
| `references/anti-patterns.md` | Before writing any assertion; also when a test won't go green |

## The accelerator

`scripts/detect_stack.py` (Python 3 standard library only, no install) reads a
repo and reports: languages, package managers, frameworks, existing test runners
and configs, existing test file counts bucketed by layer guess, datastores,
container setup, CI lanes, and which core layers have no coverage at all.

```bash
python <skill-dir>/scripts/detect_stack.py /path/to/repo         # human summary
python <skill-dir>/scripts/detect_stack.py /path/to/repo --json  # machine readable
```

Use the skill directory's **actual filesystem path** (shown in the skill context
when this skill loads) — your working directory is the user's project, not this
skill. Use `python3` where `python` isn't on PATH.

Run it before the interview so you ask informed questions instead of "what stack
is this". It is an accelerator, not a requirement — if Python is unavailable,
gather the same signals with Glob/Grep/Read.

**Its layer counts are path heuristics.** Confirm by reading a sample before
trusting them: a file named `*.integration.test.ts` that mocks the database is a
unit test wearing a costume, and no path heuristic can see that.

## Guardrails

- **Never invent a passing test.** A test that cannot fail is worse than no
  test, because it converts an unknown into a false assurance. See
  `references/anti-patterns.md`.
- **Never weaken an assertion to reach green.** If a test fails, either the app
  is wrong or the test is wrong — decide which, fix that, and say which it was.
- **Never claim a layer passes without running it.** Paste real command output.
- **Don't build layers the project can't run.** No container runtime means L4
  needs a different plan (embedded/in-memory datastore, or a shared CI-only
  lane), not a suite nobody can execute.
- **Respect existing conventions.** If the repo already has a test directory,
  naming scheme, or runner, extend it — do not introduce a parallel one.
