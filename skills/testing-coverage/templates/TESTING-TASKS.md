# Testing Tasks — {{PROJECT_NAME}}

**Plan:** `TESTING-PLAN.md`
**Produced by:** `/testing-plan` · **Executed by:** `/testing-implement`
**Progress:** {{done}}/{{total}} tasks · Current phase: **{{n}}**

> **Execution rules.** Phases run strictly in order. Within a phase, tasks marked
> `[P]` may run in parallel; all others are sequential. Every phase ends with a
> `GATE` task that must be green before the next phase starts. Mark `[x]` only
> after the task's test has actually been run.
>
> Task ID format: `T###`. Never renumber — append.

**Legend:** `[ ]` todo · `[x]` done · `[P]` parallel-safe · `[!]` blocked (reason
in the note) · `GATE` phase gate

---

## Phase 0 — Harness

*Nothing in later phases can run until this gate passes.*

- [ ] **T001** Create the test directory structure per plan §3
- [ ] **T002** Add the layer command for {{L1}} — must run and report 0 tests
- [ ] **T003** Add the layer command for {{L4}} — must run and report 0 tests
- [ ] **T004** Add the disposable service definition ({{file}}, ports {{…}})
- [ ] **T005** Add seed profile `test` with deterministic IDs for {{records}}
- [ ] **T006** Add the seed safety guard (allowlist of environment names)
- [ ] **T007** Add factory → fixture → scenario skeleton for {{core entities}}
- [ ] **T008** Add the auth-in-test helper ({{strategy}})
- [ ] **T009** Add the orchestration script: up → reset → seed → wait → run
- [ ] **T010** Pin determinism: timezone, locale, clock, RNG, animations
- [ ] **T011** Document in README: how to start the environment and run each layer
- [ ] **T012** `GATE` — cold start: environment up, seeded, health green, every
      layer command runs cleanly at 0 tests. Record in `EVIDENCE-LOG.md`.

## Phase 1 — {{L0 Static gates}}

- [ ] **T013** [P] Enable {{typecheck}} and fix or baseline existing violations
- [ ] **T014** [P] Enable {{lint}} with the agreed rule set
- [ ] **T015** [P] Add {{boundary/architecture}} rules
- [ ] **T016** [P] Add committed-secret scan
- [ ] **T017** `GATE` — `{{command}}` exits 0, zero violations. Record.

## Phase 2 — {{L1 Unit}}

*Group tasks by module. One task ≈ one test file ≈ one unit of behaviour.*

- [ ] **T018** [P] {{module}}: ordinary cases + every boundary, both sides
- [ ] **T019** [P] {{module}}: every rejection asserts the specific error
- [ ] **T020** [P] {{state machine}}: full legal/illegal transition matrix
- [ ] **T021** [P] {{money/date logic}}: rounding, timezone, DST, leap day
- [ ] **T022** `GATE` — `{{command}}` green. Falsifiability check on {{the most
      important test}}: break {{what}}, confirm red, restore, confirm green.
      Record both outcomes.

## Phase 3 — {{L3 Contract}}

- [ ] **T023** Validate real {{endpoint}} responses against the shared schema
- [ ] **T024** Assert the schema *rejects* a malformed payload
- [ ] **T025** Assert the error envelope shape
- [ ] **T026** Add generated-artifact freshness check (regenerate → diff empty)
- [ ] **T027** `GATE` — `{{command}}` green. Record.

## Phase 4 — {{L4 Integration}}

*Per endpoint: success + persistence, each validation failure, not-found,
conflict, stale version. Assert the datastore, not just the response.*

- [ ] **T028** {{POST /resource}}: success — assert status, body, **and persistence**
- [ ] **T029** [P] {{POST /resource}}: each validation failure → field-level error
- [ ] **T030** [P] {{GET /resource/:id}}: found, not-found, and no existence
      disclosure for someone else's record
- [ ] **T031** [P] {{PATCH /resource/:id}}: success, conflict, stale version
- [ ] **T032** {{auth}}: no enumeration difference between existing and
      non-existing accounts on register / reset
- [ ] **T033** Side effects: {{email}} reached the sink; {{job}} was enqueued
- [ ] **T034** `GATE` — `{{command}}` green, zero unexplained skips.
      Falsifiability check recorded.

## Phase 5 — {{L5 Authorization matrix}}

- [ ] **T035** Build the actor table: anonymous, {{roles}}, wrong-owner,
      suspended, missing CSRF, expired credential
- [ ] **T036** [P] Matrix rows for {{route group A}}
- [ ] **T037** [P] Matrix rows for {{route group B}}
- [ ] **T038** Assert 401 vs 403 is used correctly throughout
- [ ] **T039** Meta-test: enumerate the app's real route table and fail on any
      protected route with no matrix row
- [ ] **T040** `GATE` — `{{command}}` green. Falsifiability: remove one
      authorization check, confirm the matrix catches it. Record.

## Phase 6 — {{L2 Component}}

- [ ] **T041** [P] {{component}}: empty, loading, error, populated, disabled
- [ ] **T042** [P] {{component}}: interaction → visible outcome, queried by role
- [ ] **T043** `GATE` — `{{command}}` green. Record.

## Phase 7 — {{L6 End-to-end}}

*One test per critical journey. Condition-based waits only. Pre-authenticated
sessions for setup; API for data setup.*

- [ ] **T044** Journey: {{sign up → verify → first action}}
- [ ] **T045** Journey: {{sign in → core read path}}
- [ ] **T046** Journey: {{core create/submit action → confirmation → appears for
      the other actor}}
- [ ] **T047** Protected routes redirect unauthenticated users, preserving the
      return destination
- [ ] **T048** `GATE` — `{{command}}` green across {{browsers/viewports}}, zero
      retries needed. Record.

## Phase 8 — {{L7 Non-functional UI}}

- [ ] **T049** [P] Accessibility per page: one `h1`, one `main`, labelled inputs,
      keyboard reachable, visible focus, dialog focus trap
- [ ] **T050** [P] Runtime cleanliness: fail on console errors / uncaught errors /
      unhandled rejections, with a justified allowlist
- [ ] **T051** [P] Responsive: no horizontal overflow at {{breakpoints}}
- [ ] **T052** Visual regression baselines ({{themes}} × {{viewports}}) — only if
      the strategy adopted it
- [ ] **T053** `GATE` — `{{command}}` green. Record.

## Phase 9 — {{L8 Resilience}}

*Every test in this phase needs its own falsifiability check.*

- [ ] **T054** Race: {{N}} concurrent {{operations}} on {{limited resource}} —
      assert the invariant, not the absence of a 500
- [ ] **T055** Idempotency: duplicate {{request / webhook redelivery}} → one effect
- [ ] **T056** Partial failure: {{side effect}} fails after the write — assert the
      recoverable state
- [ ] **T057** Query/transaction budget on {{critical path}} — measured, not
      restated
- [ ] **T058** `GATE` — `{{command}}` green. Falsifiability recorded for **every**
      test in this phase.

## Phase 10 — {{L9 Load}}

- [ ] **T059** Define thresholds: p95 {{ms}}, error rate {{%}}, {{n}} concurrent
- [ ] **T060** Seed the performance profile at realistic volume
- [ ] **T061** Write the scenario with think time and a realistic endpoint mix
- [ ] **T062** `GATE` — thresholds hold; environment recorded alongside results.

## Phase 11 — {{L10 Guardrails + CI}}

- [ ] **T063** [P] Drift guard: {{hand-written DB object / config rule}}
- [ ] **T064** [P] Sync guard: {{forged auth vs app signer / duplicated enum}}
- [ ] **T065** [P] Budget guard: {{payload / bundle size}}
- [ ] **T066** CI: one named job per layer, with services and failure artifacts
- [ ] **T067** CI: generated-artifact freshness job
- [ ] **T068** Add the aggregate command and document every layer in the README
- [ ] **T069** `GATE` — full CI run green; clone → green verified from scratch.

---

## Defects found

Populated during implementation. Each entry means a test found a real bug.

| # | Phase | Defect | Test that catches it | Status |
| --- | --- | --- | --- | --- |
| | | | | reported / fixed / accepted |

## Deviations from the plan

| Task | What changed | Why |
| --- | --- | --- |
| | | |
