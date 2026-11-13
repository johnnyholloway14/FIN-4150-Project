---
name: pro-forma-forecast
description: Builds a pro forma financial forecast in Excel for any company, with the bank loan (or line of credit) as the plug that funds the gap. Produces an assumptions tab, pro forma income statements and balance sheets, a statement of cash flows, and the loan covenant tests, quarterly for the first year and annually after that. Use it when the user gives a company's financial statements plus growth and cost assumptions and asks for a forecast, external funding needed (AFN), future borrowing needs, or a covenant check.
---
# Pro forma forecast

You build a forecast that follows one fixed layout every time. The bank loan is
the **plug**: it absorbs whatever financing the plan needs, so the balance sheet
always balances. A forecast is only finished when it passes the checks in step 8.

## 1. Ask the user for inputs before building anything

Ask for whatever is missing, and do not invent a number. If the user tells you to
assume something, write it on the Assumptions tab and label it as an assumption.

- **Opening balance sheet.** Every line on the last actual date.
- **Sales.** Sales for the first forecast year by quarter (or a total plus
  seasonal percents), the growth rate for later years, and the horizon (usually
  5 years). Ask whether growth is real or nominal.
- **Working capital.**
  - Collection pattern: the share collected in the quarter of sale versus later.
  - Inventory policy, for example "buy next quarter's materials this quarter".
  - Payables pattern: the share of purchases paid now versus next quarter.
- **Costs.**
  - Variable costs as a percent of sales (materials, labor, commissions).
  - Fixed cash costs per quarter and how they step up each year.
  - Maintenance.
- **Fixed assets.** Existing depreciation, planned capital spending (date, cost,
  life, salvage), and how each purchase is paid for (cash, a vendor loan, or a
  term loan).
- **Debt.**
  - Bank rate, and whether interest is charged on the opening or the average balance.
  - Term loans and mortgages: balance, rate and principal payment schedule.
- **Cash policy.** The minimum cash balance, and where surplus cash goes (repay
  the bank first, then marketable securities).
- **Tax and dividends.** Tax rate and payment timing, the dividend amount and its
  growth.
- **Covenants.** Size of the credit line, minimum current ratio, maximum debt to
  equity, and how "debt" is defined (total liabilities or interest-bearing debt
  only). Also any clean-up clause and the cure period.
- **Items that stay flat.** Other assets, accruals and common stock. Confirm
  these with the user.

## 2. Workbook layout

Use the same sheets every time.

1. **Assumptions.** One input per row: label, value, unit, and the source
   sentence or "assumption". These are the only cells holding typed numbers, and
   they are formatted as inputs (blue text).
2. **Pro Forma.** The columns are: last actual | Q1–Q4 of year 1 | year 1 total |
   years 2…N | year N+1 sales only (needed for year N inventory). The rows, top to
   bottom, are:
   - Income Statement
   - Balance Sheet
   - Bank Loan Plug (AFN)
   - Covenant Tests
   - Sustainable Growth Rate
   - Statement of Cash Flows

Every cell on the Pro Forma sheet is a formula that points to Assumptions or to
another formula cell. Never type a number into it.

## 3. Forecast each line

**Sales**
- Year 1 quarters come straight from the inputs.
- Later years: prior year × (1 + growth).
- Quarterly sales in later years: annual sales × seasonal percent.

**Income statement**
- Variable costs = percent × that period's sales.
- Fixed costs come from the assumptions.
- Depreciation = existing + (cost ÷ life) for each asset already on line. An
  asset installed on April 1 starts depreciating in Q2.
- Bank interest = rate × opening loan balance. Use rate ÷ 4 for a quarter and
  the full rate for a year. Using the opening balance avoids a circular
  reference.
- Term loan and mortgage interest = rate ÷ 4 × each quarter's opening balance.
  An annual column sums those four quarters.
- Tax = rate × EBT. If tax is paid in the same quarter, taxes payable stays at
  zero.
- Net income − dividends = addition to retained earnings.

**Balance sheet at the end of a period**
- Cash = minimum cash.
- Receivables = the uncollected share × the last quarter's sales. For a year-end
  column, that is the share × Q4 seasonal % × annual sales.
- Inventory = what the purchasing rule leaves on hand. For "buy next quarter's
  needs": material % × next quarter's sales. At year end, that is material % ×
  Q1 % × next year's sales.
- Payables = the unpaid share × this quarter's purchases.
- Net plant = prior + capital spending − depreciation.
- Vendor and term loans: prior balance + new borrowing − principal paid. Split
  each one into a current portion (the next four quarters' payments) and a
  long-term portion.
- Mortgage: prior balance − principal paid, with the same current/long-term
  split.
- Retained earnings = prior + addition to retained earnings.
- Other assets, accruals and stock stay at their opening levels unless told
  otherwise.

## 4. The bank loan plug

1. **Trial assets** = every asset except marketable securities, with cash at
   the minimum.
2. **Trial claims** = every liability and equity item except the bank loan.
3. **AFN** = trial assets − trial claims.
4. If AFN > 0, the **bank loan** = AFN and **securities** = 0.
5. If AFN < 0, the **bank loan** = 0 and **securities** = −AFN. In Excel:
   `=MAX(AFN,0)` and `=MAX(-AFN,0)`.

Because interest is charged on the opening balance, the plug never feeds back
into its own period. No iterative calculation is needed.

## 5. Statement of cash flows (indirect method)

**Operating**
- Net income + depreciation
- \+ increase in payables, taxes payable and accruals
- − increase in receivables and inventory

**Investing**
- − capital spending
- − increase in marketable securities

**Financing**
- \+ change in bank loan, vendor loans and term loans
- − mortgage principal
- \+ new stock
- − dividends

**Cash delta** = (operating + investing + financing) − (ending cash − beginning
cash). It must be zero in every column.

## 6. Covenant tests

For each period, compute and flag each failure:
- Current ratio vs. its minimum.
- Debt to equity vs. its maximum, using the bank's definition of debt.
- Bank loan vs. the credit line.
- The clean-up test: did the loan reach zero at least once that year?

Also compute the sustainable growth rate, SGR = margin × turnover × leverage ×
retention, and compare it with planned growth. When growth is above the SGR,
borrowing has to rise.

**Do not trust year-end columns alone.** For a seasonal business, annual figures
hide the peak. Rerun the later years quarter by quarter, at minimum the peak
quarter, and report the highest loan and the worst ratios.

## 7. Scenarios to run and report

- Sales ± the forecaster's stated error (for example ±15%).
- The dividend held flat.
- Inflation: add expected inflation to sales growth and to fixed costs, and note
  that depreciation stays at historical cost.

For each scenario, give the peak loan and the first covenant breach.

## 8. Checks. Run all of them before you say the forecast is done.

1. Total assets = total liabilities + equity in every column (difference < $1).
2. The cash delta is zero in every column.
3. Retained earnings roll forward: prior + net income − dividends.
4. The bank loan and marketable securities are never both positive.
5. There are no typed numbers on the Pro Forma sheet. Scan each cell and list
   any constant that is not a 0 or 1.
6. Recompute three or four lines (sales, receivables, the bank loan, one ratio)
   from the raw inputs in code, separately from the workbook. Compare them to the
   workbook's values. Agreement only counts if the two were built separately.
7. The year-1 quarters add up to the year-1 annual column for every
   income-statement line.

If any check fails, fix the model. Do not loosen the check.

## 9. Report

Start with the recommendation: is the current credit line enough, and if not,
what should change? Then give:
- The peak loan and when it happens.
- Each covenant breach, with its period and value.
- The SGR versus planned growth.
- The scenario results.
- How inflation would change the picture.

Write in short, plain sentences and include one chart of the loan by period
against the credit line.
