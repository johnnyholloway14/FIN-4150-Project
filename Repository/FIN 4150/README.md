# Star River Electronics, Part 1 — verification

FIN 4150 team case. Should Star River buy the packaging machine now, or wait
three years? **Wait.** Waiting is worth SGD173,264.58 in present value at an 11%
cost of capital — SGD25,669.32 a year.

This repository holds the verification half of the submission: an independent
recompute of the decision and a structural audit of the team's Excel model.

## Setup

```bash
pip install -r requirements.txt
```

On this machine Python lives at `%USERPROFILE%\anaconda3\python.exe`; plain
`python` is a dead Microsoft Store alias.

## Run

```bash
python verification.py --sensitivities
```

Rebuilds both scenarios from Exhibit 4 of the case, reconciles every cash flow
against `data/Final - Star River Project Analysis.xlsx`, then checks the memo's
sensitivity claims. Exits 1 if anything fails to reconcile.

```bash
python verification.py --sources     # every input with the sentence it came from
python audit_workbook.py             # typed numbers, input provenance, memo provenance
python whatif.py --wacc 0.14 --predict lower
```

## Current state

The base case reconciles to the cent — all 28 free cash flows and all six summary
figures. Three findings are open:

1. The memo's SGD34,000 break-even on unquantified benefits should be SGD93,910.
2. None of the memo's twelve sensitivity figures exist anywhere in the workbook.
3. The "replace in 2003" sensitivity (SGD117,100) cannot be reproduced under any
   treatment of the old machine we tried.

None of the three changes the recommendation. All three are written up in
[PROCESS.md](PROCESS.md).

## Layout

```
verification.py            independent recompute + reconciliation  (submission item 3)
audit_workbook.py          structural audit of the workbook
whatif.py                  change one input, predict, check yourself
CLAUDE.md                  agent instructions and the case's traps
.claude/agents/            the figure-checker agent definition
data/                      the team's workbook and the original template
PROCESS.md                 the written record  (submission item 4)
```

The case PDF is copyrighted (Darden / McGraw-Hill) and is not committed.
