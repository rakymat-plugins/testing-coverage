# The Interview

Used by `/testing-assess`. The goal is to reach a defensible layer selection in
**under ten minutes of the user's attention**, not to run a questionnaire.

## Rules

1. **Detect before you ask.** Run `scripts/detect_stack.py` and read the repo
   first. Never ask what you can observe. Asking "is this a TypeScript project"
   destroys credibility instantly.
2. **Ask in small batches.** Two to four questions at a time, using the
   structured question tool so the user clicks instead of typing. Maximum three
   batches.
3. **Only ask what changes the plan.** Every question must map to a layer
   decision. If both answers lead to the same plan, don't ask it.
4. **Offer a recommendation.** Put your recommended option first and mark it.
   The user often does not know — a senior engineer proposes, then adjusts.
5. **State assumptions instead of asking** when the answer is low-stakes and
   inferable. "Assuming CI is GitHub Actions since `.github/workflows` exists."
6. **Never block.** If the user stops answering, proceed with documented
   assumptions and mark them `ASSUMED` in the strategy file.

## Batch 1 — Risk (always ask)

These decide which layers are mandatory.

**Q: What breaks the business if it silently stops working?**
Options should be drawn from what you detected — e.g. "Checkout / payments",
"Sign-in and accounts", "The public catalogue / SEO pages", "Admin moderation
tools", "Data pipeline output correctness".
→ The chosen area gets the deepest coverage and its layers come first in the
plan, regardless of what's cheapest.

**Q: What's in the system that you can't just re-run if it goes wrong?**
Options: "Money movement / invoices", "Personal or regulated data", "Irreversible
external actions (emails, shipments, third-party writes)", "Nothing — it's all
recomputable".
→ Money or irreversible actions makes **L8 mandatory**. Regulated data makes
**L5 mandatory** and adds leak-shape assertions.

**Q: Who are the actors, and can one of them see another's data?**
Options: "Single user / no auth", "Users with roles (admin/staff/customer)",
"Multi-tenant — hard isolation between orgs", "Public + one admin".
→ Anything but the first makes **L5 mandatory**, sized by role count.

## Batch 2 — Environment (ask what detection couldn't answer)

These decide whether L4/L6/L9 are *buildable*.

**Q: Can tests create and destroy a real datastore, and where?**
Options: "Yes — Docker/containers available locally and in CI (recommended)",
"CI only — local devs can't run containers", "No containers — needs
embedded/in-memory", "No datastore at all".
→ Determines the L4 harness design in `references/harness.md`. "CI only" means
the local command must degrade gracefully with a clear message, not a cryptic
connection error.

**Q: Which external services does the code call, and what may tests touch?**
Multi-select: payment provider, email/SMS, object storage, auth provider, maps/
geocoding, AI/LLM APIs, internal services, none.
→ Each one needs a decision: provider test-mode, local sink, in-process fake, or
recorded fixtures. Unresolved external calls are the #1 cause of flaky suites.

**Q: Does the app have configurations that change behaviour — feature flags,
plans/tiers, locales, or a shelved module?**
→ If yes, the plan needs **lanes**: the same suite run under each configuration,
plus runtime capability probing instead of hardcoded expectations.

**Q: Where do tests have to pass, and who watches?**
Options: "CI on every PR, blocking (recommended)", "CI, non-blocking for now",
"Locally only", "Nothing set up yet".
→ Decides whether the plan includes a CI phase and whether the runtime budget
must be kept tight.

## Batch 3 — Scope and trust (ask when relevant)

**Q: The existing tests — what's your honest read?** (skip if there are none)
Options: "Trustworthy, just incomplete", "They pass but I don't trust them",
"Flaky — people re-run until green", "I don't know".
→ "Don't trust" or "flaky" inserts a **triage phase before any new tests**:
audit the existing suite against `references/anti-patterns.md`, and quarantine or
delete tests that cannot fail. Adding tests on top of a suite nobody believes
just increases the noise.

**Q: How much do you want built now?**
Options: "A solid core I can extend (L0+L1+L4+L5) — recommended", "Everything
the risk profile calls for, however long it takes", "Just enough to unblock CI",
"Only the highest-risk area, deeply".
→ Directly sets the phase count. Depth in fewer layers beats breadth across all.

**Q: Does visual fidelity matter enough to review image diffs on PRs?**
→ The only honest gate for adopting visual regression. If nobody will review
diffs, don't build it — say so in the strategy file.

**Q: What's the developer OS mix?**
→ Decides whether orchestration scripts must be cross-platform. Default to
cross-platform (Node/Python/`make`) unless the whole team is on one OS.

## Questions worth asking only in specific cases

| Situation detected | Ask |
| --- | --- |
| Monorepo with many packages | Which packages are actually deployed, vs internal-only? |
| Public API / SDK consumers | Are there external consumers whose breakage you'd hear about? |
| Data pipeline / ETL | Is the pipeline expected to be idempotent on re-run? |
| Mobile app | Which two journeys gate a release? |
| Legacy code, no tests, active refactor plan | Do you need characterization tests before refactoring? |
| Known load targets or a launch date | What p95 and concurrency must hold, and where can we generate load? |
| Existing high coverage % but bugs escaping | Which recent bug should a test have caught? Use it as the first test. |

That last one is the single most valuable question in this document. A real
escaped bug tells you exactly which layer is missing, with no speculation.

## Turning answers into a layer selection

Fill this table in the strategy file. Every layer gets a verdict — `ADOPT`,
`PARTIAL`, `DEFER`, or `SKIP` — and every non-`ADOPT` gets a reason and, if
deferred, a trigger that should reopen it.

| Layer | Verdict | Why | Trigger to revisit |
| --- | --- | --- | --- |
| L9 Load | DEFER | No staging environment; traffic under 100 req/min | Before public launch, or when p95 complaints appear |

A `SKIP` with a reason is a professional decision. A layer silently absent is a
gap that will surprise someone at 2am. The difference is only this table.
