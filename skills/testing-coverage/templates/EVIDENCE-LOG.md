# Evidence Log — {{PROJECT_NAME}}

**Append-only.** One entry per gate attempt, **including failures**. A log with
only successes is a press release, not evidence.

Never edit or delete a past entry. If a gate later regresses, add a new entry.

---

## Entry template

Copy this block for each gate attempt.

```markdown
### Phase {{n}} — {{layer}} — {{PASS | FAIL}}

**Date:** {{YYYY-MM-DD}}
**Command:** `{{exact command, including any environment prefix}}`
**Environment:** {{local / CI}} · {{OS}} · {{runtime version}} · {{live services if any}}

**Output (verbatim tail):**
```
{{paste the real summary lines — test count, pass/fail/skip, duration.
 Do not paraphrase. Do not write "all green".}}
```

**Counts:** {{n}} passed · {{n}} failed · {{n}} skipped · {{duration}}

**Skips, with reasons:**
| Test | Reason |
| --- | --- |
| {{name}} | {{feature flag off / platform-specific / external service — never "was failing"}} |

**Falsifiability check:**
- Test: `{{test name}}`
- Broke: {{what was temporarily changed in production code}}
- Result with break: **FAILED** — `{{the failure message}}`
- Result after restore: **PASSED**

**Defects found:**
| Defect | Reproducing test | Reported | Resolution |
| --- | --- | --- | --- |
| {{description}} | `{{test}}` | yes | {{fixed / user deferred / accepted}} |

**Notes:** {{anything a future reader needs — flakiness observed, timing,
environment quirks}}
```

---

## Entries

<!-- Newest last. Append below this line. -->
