# Testing Strategy — {{PROJECT_NAME}}

**Created:** {{DATE}}
**Author:** {{AUTHOR}}
**Status:** Draft | Agreed
**Produced by:** `/testing-assess`
**Next step:** `/testing-plan`

> Fill every section. Where the user didn't answer, write the assumption and mark
> it `ASSUMED` — an unmarked guess is indistinguishable from a decision.

---

## 1. What this project is

| | |
| --- | --- |
| Purpose | {{one sentence — what it does and for whom}} |
| Languages | {{detected}} |
| Frameworks | {{detected}} |
| Package manager / build | {{detected}} |
| Datastores | {{detected}} |
| External services | {{detected}} |
| Deployment target | {{detected or ASSUMED}} |
| CI | {{detected or "none"}} |
| Repo shape | single package / monorepo ({{n}} packages) |
| Developer OS mix | {{answer}} |

## 2. Risk profile

**Highest-risk area:** {{what breaks the business if it silently stops working}}

**Irreversible or sensitive operations:**

| Operation | Why it matters | Layer that must cover it |
| --- | --- | --- |
| {{e.g. invoice generation}} | {{money, non-reversible}} | L8 + L4 |

**Actors and isolation:**

| Actor | Can see | Must never see |
| --- | --- | --- |
| {{role}} | {{scope}} | {{scope}} |

**Recent escaped bugs** (if any were named — these become the first tests written):

| Bug | Layer that would have caught it |
| --- | --- |
| {{description}} | {{L4 / L5 / L8 …}} |

## 3. Existing coverage — honest assessment

| Layer | Files found | Trustworthy? | Notes |
| --- | --- | --- | --- |
| L0 Static | {{n}} | | |
| L1 Unit | {{n}} | | |
| L2 Component | {{n}} | | |
| L3 Contract | {{n}} | | |
| L4 Integration | {{n}} | | |
| L5 Authorization | {{n}} | | |
| L6 E2E | {{n}} | | |
| L7 Non-functional | {{n}} | | |
| L8 Resilience | {{n}} | | |
| L9 Load | {{n}} | | |
| L10 Guardrails | {{n}} | | |

**Triage needed before adding tests:** yes / no
{{If yes: list the specific existing tests that cannot fail, per
references/anti-patterns.md, and whether to fix, quarantine, or delete each.}}

## 4. Layer decisions

Every layer gets a verdict. `ADOPT` = build it now. `PARTIAL` = build a named
subset. `DEFER` = valuable, not now, with a trigger. `SKIP` = not applicable,
with a reason.

| Layer | Verdict | Rationale | Trigger to revisit |
| --- | --- | --- | --- |
| L0 Static gates | | | |
| L1 Unit | | | |
| L2 Component | | | |
| L3 Contract | | | |
| L4 Integration | | | |
| L5 Authorization | | | |
| L6 End-to-end | | | |
| L7 Non-functional UI | | | |
| L8 Resilience | | | |
| L9 Load | | | |
| L10 Guardrails | | | |

## 5. Tooling per adopted layer

One command per layer. These become the phase gate commands in the plan.

| Layer | Tool | Command | Needs a live environment? |
| --- | --- | --- | --- |
| {{L1}} | {{tool}} | `{{command}}` | no |
| {{L4}} | {{tool}} | `{{command}}` | yes — {{what}} |

**Aggregate command:** `{{command that runs every unattended layer}}`

**Incumbent tooling respected:** {{what already existed and is being extended
rather than replaced}}

## 6. Harness design

| Concern | Decision |
| --- | --- |
| Target indirection variables | {{TEST_API_URL, …}} |
| Disposable datastore | {{container / native ephemeral / in-memory}} |
| Port offsets from dev | {{table or "n/a"}} |
| Readiness signal | {{health endpoint / log line / port open}} |
| Seed profiles | {{names}} |
| Deterministic fixed IDs | {{what needs them}} |
| Isolation strategy | {{unique-per-test / rollback / truncate}} |
| Auth-in-test strategy | {{real login / mint with app signer / forge}} |
| Clock, RNG, timezone, locale | {{how pinned}} |
| Rate limits / bot defenses | {{how handled; is a second lane needed?}} |
| External services | see table below |
| Orchestration script language | {{node / python / make / shell}} |

**External service handling:**

| Service | Approach | Notes |
| --- | --- | --- |
| {{email}} | local sink | assert delivery, don't trust the call |

**Configuration lanes** (feature flags, tiers, locales — omit if none):

| Lane | Configuration | What it proves |
| --- | --- | --- |
| A | {{flag off}} | the shipped product is correct |
| B | {{flag on}} | the gated module hasn't rotted |

## 7. Explicitly out of scope

State what this effort is *not* covering, so nobody later assumes it was.

- {{e.g. no load testing until a staging environment exists}}
- {{e.g. no visual regression — nobody is committed to reviewing image diffs}}

## 8. Assumptions

| # | Assumption | Impact if wrong |
| --- | --- | --- |
| 1 | | |

## 9. Success criteria

- [ ] Every `ADOPT` layer has a green command recorded in `EVIDENCE-LOG.md`
- [ ] Each layer runs as its own named CI job
- [ ] A new contributor can go clone → green with one documented command
- [ ] {{project-specific: e.g. every route in the authorization matrix}}
- [ ] {{project-specific: e.g. the {{highest-risk}} path has L4 + L8 coverage}}
