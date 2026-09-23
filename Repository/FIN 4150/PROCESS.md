# PROCESS.md — Star River Electronics, Part 1

**Team:** Aidan Kunert, Britten Hager, Johnny Holloway, Matt Anderson
**Case:** Bruner Case 24, Star River Electronics Ltd.
**Recommendation:** Wait and buy the packaging machine in 2004. Waiting is worth
SGD173,264.58 in present value at an 11% cost of capital, or SGD25,669.32 a year.

> **DRAFT.** The verification sections are written and accurate. Sections marked
> `[TODO]` belong to other members and must be written by the person who did the
> work — the individual quiz asks you to explain whatever this file says you
> owned, so do not let someone else write your entry.

---

## 1. How we built the agent

`[TODO — model and memo]` How the model and memo were produced: what the agent
was told, what it read, what was wrong on the first attempt, and what changed.

**Verification (Johnny Holloway).** The checking layer is two scripts plus an
agent definition, built on a single rule: never verify a model by reading the
model.

- `verification.py` rebuilds both scenarios from Exhibit 4 of the case PDF. Every
  input is typed from the plant manager's memo with the source sentence quoted
  beside it (`python verification.py --sources` prints them). The cash flow
  structure — when depreciation starts, when the maintenance contract is priced,
  which years carry overtime — was derived from the exhibit before the team's
  workbook was opened. Only then does it read the workbook's cached values and
  reconcile, cell by cell, all 28 free cash flows plus six summary figures.
- `audit_workbook.py` asks a different question: is the model built the way it
  says it is? It walks every cell for typed numbers, compares each input on the
  Inputs sheet against Exhibit 4, and searches the workbook for every figure the
  memo asserts.
- `.claude/agents/figure-checker.md` defines the agent that runs a single claimed
  figure to ground. It is constrained to reproduce a number independently before
  calling it verified, and to report what it tried when it cannot.

What changed after the first attempt: the first version of the benefit
break-even applied the unquantified benefit to the wrong years — every year past
the replacement date instead of the three years before it. It returned SGD53,293,
which matched neither the memo nor the corrected figure. The error was caught by
perturbation: injecting a benefit and printing which years' *gap between
scenarios* moved. The answer was years 1–3 only, which is the whole point, and it
is now asserted in the script rather than assumed.

---

## 2. Division of labor

| Member | Owned | Commits |
| --- | --- | --- |
| Aidan Kunert | `[TODO]` | `[TODO]` |
| Britten Hager | `[TODO]` | `[TODO]` |
| Johnny Holloway | Independent verification: `verification.py`, `audit_workbook.py`, `whatif.py`, the `figure-checker` agent, and findings 1–3 below | `[TODO — fill in after committing]` |
| Matt Anderson | `[TODO]` | `[TODO]` |

---

## 3. How we checked the output

Not "we reviewed it." Each check below names the figure tested and what it was
tested against.

**Base case, reconciled to the cent.** `verification.py` reproduces the model's
six headline figures and all 28 year-by-year free cash flows from Exhibit 4:

| | Independent check | The model |
| --- | --- | --- |
| PV of costs, wait | (1,702,230.14) | (1,702,230.14) |
| PV of costs, buy now | (1,875,494.72) | (1,875,494.72) |
| Advantage of waiting | 173,264.58 | 173,264.58 |
| Advantage per year | 25,669.32 | 25,669.32 |

**Why that agreement is not circular.** The assignment asks how we know the two
did not simply come from the same source. Three reasons. The check was built from
the case PDF, not from the workbook, and it never reads the workbook's formulas —
only its cached values, and only after computing its own. The reconciliation is
year by year, so a structural error (depreciation starting a year early, the
maintenance contract escalating at 1.5% instead of 5%) would show up in specific
years rather than as a uniform offset; all 28 match. And the check disagrees with
the memo in three places, which a check that merely echoed its source could not do.

**Structural audit.** The Inputs sheet claims the Project Analysis sheet contains
no typed numbers, only formulas. Verified across all 60 rows: the only literals
are a zero on the year axis (`D9`) and a `0.01` rounding tolerance in a
cross-check. All 13 inputs traceable to Exhibit 4 match the exhibit's stated
values.

**Horizon.** The 13-year horizon was tested rather than assumed. Extending to
2015, 2016 and 2017 and recomputing each year's cash flows independently gives a
difference of exactly zero in every year, so no longer horizon can change the
answer. Truncating to 10 years understates the advantage of waiting by SGD44,425.

**Sensitivities.** Ten of the memo's twelve Exhibit B rows reproduce within
SGD0.50, as do both break-even rates (6.61% cost of capital, 9.42% equipment
escalation). The exceptions are finding 3.

---

## 4. Two things the agent got wrong

### Finding 1 — the SGD34,000 break-even is understated by about 2.8×

The memo's risk section says unquantified benefits worth "more than about
SGD34,000 a year, pre-tax, in perpetuity" would overturn the recommendation, and
frames that as a low hurdle — "a little over 0.03% of sales."

The correct figure is **SGD93,910**.

The error: 34,000 is the equivalent annual advantage (25,669.32) divided by
(1 − 0.245). That grosses up a 13-year annualised figure as though the benefit
gap lasted all 13 years. It does not. Both scenarios are running the new machine
from 2005 onward, so the benefit only differs in 2002, 2003 and 2004. Confirmed
by perturbation: injecting a benefit of 1,000 moves the gap between the two
scenarios in years 1, 2 and 3 and in no other year.

The memo's own labor break-even (SGD110,811) uses the correct three-year logic
and reconciles exactly, so the model contradicts itself on this point.

**What we did about it:** `verification.py` computes the break-even by bisection
rather than by grossing up, and asserts the three-year property. The memo figure
`[TODO — corrected / to be corrected]`. The correction *strengthens* the
recommendation: a benefit of SGD93,910 a year is much harder for the plant
manager to claim than SGD34,000.

### Finding 2 — none of the memo's sensitivity figures exist in the model

All twelve rows of the memo's Exhibit B, both break-even rates and both
break-even hurdles were searched for across every cell of the workbook. **None of
them is there.** The workbook contains no sensitivity machinery at all — the
Unequal Lives sheet tests horizons and convergence and nothing else.

Ten of the twelve are nevertheless correct; we reproduced them independently. But
as submitted, no one can point at a cell and say where any of them came from, and
the briefing is explicit that every number in the memo should be findable in the
model.

**What we did about it:** `audit_workbook.py` check 3 reports this as a standing
gap. Fix by `[TODO — add a sensitivity block to the workbook, or state in the
memo that Exhibit B was computed in verification.py]`.

---

## 5. What we are still unsure about

**The "replace in 2003" sensitivity, SGD117,100, cannot be reproduced.** This is
finding 3, and it is unresolved rather than fixed.

The memo reports that if growth forces replacement in 2003 rather than 2004,
waiting still wins by SGD117,100. Running the model's own logic with the
replacement year set to 2003 gives **SGD101,828**, because the workbook's wait
scenario simply drops the old machine's remaining book value when replacement is
brought forward — no writeoff, no tax shield. Crediting that shield gives
SGD116,304, still SGD796 short. Five different treatments of the old machine were
tried; none lands on 117,100.

The neighbouring row is the odd part. "Replace in 2002" reconciles to the cent at
SGD58,455 — but only *with* the writeoff the model does not implement. So the two
rows appear to have been computed on different bases, and at least one of them
was not computed in the workbook at all.

The asymmetry is real and worth stating plainly: the buy-now scenario does credit
the writeoff on the old machine (SGD53,508 at t=0, cell `D34`). Only the wait
scenario's early-replacement path omits it.

**This does not change the recommendation.** Waiting wins under every treatment
we tried, by between SGD26,318 and SGD117,100. What we cannot currently do is
defend the specific figure printed in the memo.

**Also unresolved:** the equivalent annual cost divides a present value that
includes a t=0 cash flow by a 13-period ordinary annuity factor. Both
alternatives are treated identically so the comparison is sound, and the NPV in
row 50 is what actually decides the case, but the per-year figures are a
restatement and should be described that way rather than as the decision rule.
