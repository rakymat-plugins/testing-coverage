# Testing Plan — {{PROJECT_NAME}}

**Created:** {{DATE}}
**Strategy:** `TESTING-STRATEGY.md` ({{status}})
**Produced by:** `/testing-plan`
**Next step:** `/testing-implement`

> This file is the *design*. `TESTING-TASKS.md` is the *checklist*. Do not put
> task-by-task detail here, and do not put design rationale in the task file.

---

## 1. Goal

{{Two or three sentences. What will be true when this is done that isn't true
now. Written so a stakeholder who won't read the rest understands the outcome.}}

## 2. Layers in scope

| Layer | Phase | Command | Live env? | Est. tests |
| --- | --- | --- | --- | --- |
| {{L0}} | 1 | `{{cmd}}` | no | n/a |
| {{L1}} | 2 | `{{cmd}}` | no | ~{{n}} |
| {{L4}} | 4 | `{{cmd}}` | yes | ~{{n}} |

Out of scope, per the strategy: {{list}}

## 3. Directory and naming conventions

```
{{tests/
  unit/
  integration/
  authz/
  e2e/
  load/
  fixtures/
  support/}}
```

| Convention | Value |
| --- | --- |
| Test file naming | {{e.g. `*.unit.test.ts`, `test_*.py`, `*_test.go`}} |
| Layer selection mechanism | {{separate configs / markers / build tags / dirs}} |
| Shared helper location | {{path}} |
| Fixture/factory location | {{path}} |

**If the repo already has conventions, they are recorded above unchanged.**
New conventions are only introduced where none existed.

## 4. Harness build-out

What phase 0 must deliver, in build order:

1. {{Layer command skeletons — every adopted layer runs and reports 0 tests}}
2. {{Disposable service definition — file, ports, volumes}}
3. {{Seed profiles}}
4. {{Factory → fixture → scenario skeleton}}
5. {{Auth helper}}
6. {{Orchestration script per live-env layer}}
7. {{Determinism setup — clock, timezone, locale, animation}}

**Phase 0 exit criteria:** from a cold start, one command brings up the
environment, seeds it, passes its health check, and every layer command runs
cleanly reporting zero tests.

### Environment contract

| Variable | Default | Used by |
| --- | --- | --- |
| `{{TEST_API_URL}}` | `{{default}}` | L4, L5 |

### Service topology

| Service | Dev port | Test port | Reset method |
| --- | --- | --- | --- |
| {{postgres}} | {{5432}} | {{5434}} | {{migrate reset + seed}} |

## 5. Phases

One phase per layer, ordered by dependency with the highest-risk area pulled as
early as its dependencies allow.

| # | Phase | Layer | Depends on | Exit criteria |
| --- | --- | --- | --- | --- |
| 0 | Harness | — | — | cold start → all commands run, 0 tests, health green |
| 1 | {{Static gates}} | L0 | 0 | `{{cmd}}` exits 0 with zero violations |
| 2 | {{Unit}} | L1 | 0 | `{{cmd}}` green; falsifiability check recorded |
| … | | | | |
| N | {{CI + guardrails}} | L10 | all | every layer a named CI job; drift guards green |

**Risk-driven reordering applied:** {{which phase moved earlier and why, or
"none — default order"}}

## 6. Coverage targets by area

Not a percentage. A list of what must be covered, so the task file can be
generated from it and gaps are visible.

| Area / module | Layers | Specific cases that must exist |
| --- | --- | --- |
| {{auth}} | L1, L4, L5 | {{login success, wrong password, locked account, expired token, no enumeration difference}} |
| {{payments}} | L4, L8 | {{double-charge prevention, webhook redelivery idempotency, refund reversal}} |

## 7. CI design

| Job | Layers | Trigger | Services | Artifacts on failure |
| --- | --- | --- | --- | --- |
| {{fast}} | L0, L1 | every push | none | — |
| {{integration}} | L4, L5 | every PR | {{postgres, redis}} | service logs |
| {{e2e}} | L6, L7 | PR to main | full stack | traces, screenshots, videos |

Blocking: {{which jobs block merge}}
Target runtime: {{fast lane under N minutes}}

## 8. Risks to this plan

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| {{no container runtime on some machines}} | | {{CI-only lane + clear local error message}} |
| {{forged auth drifts from app signer}} | | {{L10 sync guardrail}} |

## 9. Defects expected to surface

Writing real tests against untested code finds bugs. That is a success, not a
delay. Policy for this effort:

- A test that fails because the **app** is wrong → stop, report, ask before
  changing production code.
- A test that fails because the **test** is wrong → fix the test, note it, move on.
- Neither is ever resolved by weakening the assertion.

Log every found defect in `EVIDENCE-LOG.md` under the phase that found it.

## 10. Effort

| Phase | Estimate | Notes |
| --- | --- | --- |
| 0 | {{}} | usually the largest single phase |

**Total:** {{}}
**Biggest unknown:** {{}}
