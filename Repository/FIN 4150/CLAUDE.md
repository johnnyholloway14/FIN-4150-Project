# Star River, Part 1 — verification agent

## What this repository is

The team's deliverable for the Star River packaging-machine case. This repo holds
the **verification** half: an independent recompute of the decision and a
structural audit of the team's Excel model.

The model and the memo were produced by other members. Nothing here should treat
either as authoritative. The job is to check them.

## The rule that governs everything in here

**Never verify a model by reading the model.** Every figure in `verification.py`
is derived from Exhibit 4 of the case PDF — the plant manager's memo — and the
exhibit sentence is quoted next to each input. If the check and the model agree,
that agreement has to mean something, and it only means something if the two were
built from separate sources.

When adding a check, ask: would this catch the error, or does it assume the model
is right and merely restate it? A check that reads a workbook cell and compares it
to itself proves nothing.

## Layout

| File | What it does |
| --- | --- |
| `verification.py` | Rebuilds both scenarios from Exhibit 4, reconciles against the workbook cell by cell, checks the memo's sensitivity claims. Submission item 3. |
| `audit_workbook.py` | Structural audit: typed numbers, input provenance against Exhibit 4, and whether each memo figure exists anywhere in the workbook. |
| `whatif.py` | Change one input, predict the effect, check yourself. Pre-submission drill and quiz practice. |
| `data/` | The team's workbook and the original template. |
| `PROCESS.md` | The written record. Required submission. |

The case PDF is a copyrighted Darden/McGraw-Hill case and is deliberately **not**
committed. Read it from the course files.

## Running things

```bash
python verification.py --sensitivities    # the full check
python verification.py --sources          # every input with its exhibit quote
python audit_workbook.py                  # structural audit
python whatif.py --wacc 0.14 --predict lower
```

`verification.py` exits 1 while any figure fails to reconcile. It currently exits
1 on purpose — three findings are open, recorded in `PROCESS.md`. Do not "fix"
this by loosening the tolerance or deleting a check.

## The case, in one paragraph

Star River can buy a packaging machine now for SGD1.82m or wait three years and
buy it in 2004, when growth forces replacement anyway. This is a **cost
comparison between two dates**, not an is-the-NPV-positive problem — both paths
end with the same machine running indefinitely, so there is no revenue line.
What differs is the timing of the purchase, three years of the old machine's
maintenance and overtime, and the depreciation schedules. At an 11% cost of
capital, waiting is worth SGD173,264.58 in present value, or SGD25,669.32 a year.

## Things that are easy to get wrong here

These are the traps. A generic capital-budgeting prompt gets several of them
wrong in a way that looks convincing.

- **The horizon is 13 years and that is not arbitrary.** Both streams converge in
  2015, when the new machine is fully depreciated under both paths and the two
  scenarios are running the same machine on the same contract. Stopping at year
  10 understates the advantage of waiting by SGD44,425.
- **The maintenance contract escalates at 5%, not at 1.5%.** Exhibit 4: the price
  rises "by the same percentage as the rate of increase of the price of new
  equipment." Labor inflates at 1.5%. Two different rates.
- **A contract starting in 2005 opens at 3,640 × 1.05³, not at 3,640.**
- **Do not apply a replication-style equivalent annual cost.** Textbook EAC
  assumes the asset is repeated indefinitely. Exhibit 4 rules that out: this is
  "the last packaging equipment we will ever have to purchase." Annualising each
  alternative over its own asset life overstates the answer by 2.6×.
- **Benefits of the new machine only differ for three years.** Both scenarios run
  it from 2005 onward. Any per-year benefit figure has to respect that.
- **The old machine's unrecovered book value shelters tax when it is scrapped.**
  The buy-now case credits this (SGD53,508 at t=0). The early-replacement
  sensitivity in the workbook does not. That asymmetry is FINDING 3.

## Style

- Plain Python, standard library plus `openpyxl`. No pandas, no framework.
- Every constant carries its source. A number without a source is a defect.
- Print tables the reader can scan: label, this check, the model, the difference.
- Comments explain *why a treatment is correct under the case facts*, not what
  the line does.
- ASCII in script output — the Windows console encoding mangles the rest.
