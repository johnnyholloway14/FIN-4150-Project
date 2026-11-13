# SG Electronics — Financial Analysis and Planning

FIN 4150 case C5. Johnny Holloway (individual assignment).

**Recommendation:** SG is profitable, but its plan does not fit the $150,000
Pioneer line. It breaks the debt-to-equity covenant in Q2 and Q3 20x1 (0.81, 0.65),
never meets the clean-up clause, and its Q2 seasonal borrowing tops the line every
year from 20x2, reaching about $321,000 in 20x5. Renegotiate before April: a
$350,000 seasonal line, a 20x1 debt-to-equity waiver, a clean-up clause SG can
meet, and hold the dividend at $110,000.

## Submission files

| File | What it is |
| --- | --- |
| `data/SG Electronics - Johnny Holloway.xlsx` | The forecast workbook |
| `memo/SG Electronics Memo - Johnny Holloway.docx` | One-page memo to Mr. Hosfeld (Questions 1–4) |
| `SKILL.md` | Claude skill: build this forecast for any company |

## Supporting files

| File | What it does |
| --- | --- |
| `verify_forecast.py` | Rebuilds the forecast from the case text alone and reconciles it to the workbook; also runs the quarterly 20x2–20x5 view and the scenarios |
| `memo/make_chart.py` | Draws the memo's bank-loan chart from `verify_forecast.py` |
| `memo/make_memo.js` | Builds the memo .docx (`node memo/make_memo.js`, needs the `docx` npm package) |

```bash
python verify_forecast.py --quarterly --scenarios
```

## Verification result

All 13 reconciled lines (sales, EBIT, net income, receivables, inventory, net
plant, payables, bank loan, retained earnings, total assets, both covenant
ratios and operating cash flow) match the workbook to the dollar in all eight
columns. The cash delta is zero in every column.

## Assumptions beyond the case text

- The quarterly view of 20x2–20x5 is not in the workbook. It carries the 20x1
  method forward: interest on the prior quarter's loan, seasonal percents of
  annual sales. It is there to show the in-year peak that the year-end columns hide.
- The equipment purchases appear as investing outflows, with the vendor loans as
  financing inflows in the same quarter (gross presentation).
- Inflation scenario: 3% a year on prices and on fixed cash costs from 20x2. The
  20x4 equipment cost and depreciation are left at historical cost.
