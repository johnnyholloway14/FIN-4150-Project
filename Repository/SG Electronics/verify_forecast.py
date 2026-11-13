"""SG Electronics -- independent rebuild of the pro forma forecast.

Every input below is typed from the case text (C5 SG Electronics), not read
from the workbook. The script builds the forecast on its own, then reads the
workbook's cached values and reconciles them line by line. Agreement only means
something because the two were built from separate sources.

    python verify_forecast.py              # reconcile the workbook
    python verify_forecast.py --quarterly  # 20 quarters, shows in-year peaks
    python verify_forecast.py --scenarios  # dividend, sales and inflation tests

Exits 1 if any reconciled figure is off by more than $1.
"""
import argparse
import sys
from pathlib import Path

import openpyxl

WORKBOOK = Path(__file__).parent / "data" / "SG Electronics - Johnny Holloway.xlsx"

# ---- Inputs, each with the case sentence it comes from --------------------
SALES_20X1 = [330_000, 480_000, 400_000, 300_000]  # Exhibit II
SEASONAL = [0.22, 0.32, 0.26, 0.20]   # "use the rounded percent-of-annual figures in Exhibit II"
REAL_GROWTH = 0.08                    # "real sales growth ... eight percent per year through 20x5"
COLLECT_SAME_Q = 0.30                 # "30 percent ... collected during the quarter of the sale"
MATERIAL = 0.45                       # "Raw materials average 45 percent of sales"
PAY_SAME_Q = 0.50                     # "pays for one-half of these purchases in the quarter ordered"
LABOR = 0.10                          # "direct labor expenses run at 10 percent of sales"
COMMISSION = 0.15                     # "commission basis which averages 15 percent of sales"
ADMIN_Q_20X1, ADMIN_STEP = 18_000, 2_000  # "$18,000 per quarter ... grow at $2,000 per quarter per year"
MISC_Q_20X1, MISC_STEP = 5_000, 1_000     # "$5,000 per quarter ... increase by $1,000 per quarter per year"
DEP_EXISTING_Q = 10_000               # "Depreciation currently amounts to $10,000 per quarter"
EQUIP1, EQUIP2 = 250_000, 300_000     # "on line April 1, 20x1" / "early January 20x4"
EQUIP_LIFE_Q = 40                     # "10 years via straight line" to zero salvage
VENDOR_PMT_Q = 25_000                 # "$25,000 per quarter beginning the quarter following installation"
BANK_RATE = 0.1075                    # "prime plus two percent, or 10-3/4 percent"
MORT_RATE, MORT_PRIN_Q = 0.09, 9_000  # "amortized at $9,000 per quarter ... fixed rate of nine percent"
MIN_CASH = 70_000                     # "the minimum level of cash"
TAX = 0.35                            # paid each quarter on that quarter's income -> payable stays 0
DIV_Q_20X1, DIV_GROWTH = 27_500, 0.10 # "$27,500 per quarter ($110,000 for the year)"
LINE, MIN_CR, MAX_DE = 150_000, 1.50, 0.60  # covenants

# Exhibit I, 12/31/20x0
OPEN = dict(ar=194_000, inv=148_500, ppe=504_000, other=285_000, matpay=74_250,
            accr=10_000, loan=31_000, mort=244_000, stock=75_000, re=767_250)


def maint_q(year, q):
    """$5,000 existing; $7,000 once new equipment is on line April 1 20x1; $9,000 from Jan 20x4."""
    if year == 1 and q == 0:
        return 5_000
    return 9_000 if year >= 4 else 7_000


def quarter_sales(div_growth=DIV_GROWTH, sales_mult=1.0, inflation=0.0):
    """Sales for 20x1 Q1 .. 20x6 Q1, plus annual totals 20x1..20x6."""
    annual = {1: sum(SALES_20X1)}
    for y in range(2, 7):
        annual[y] = annual[y - 1] * (1 + REAL_GROWTH) * (1 + inflation)
    for y in range(2, 7):
        annual[y] *= sales_mult
    q = {(1, i): SALES_20X1[i] for i in range(4)}
    for y in range(2, 7):
        for i in range(4):
            q[(y, i)] = SEASONAL[i] * annual[y]
    return annual, q


def equipment(year, q):
    """Depreciation on new equipment and the vendor-loan balance at quarter end."""
    t = (year - 1) * 4 + q          # 0 = Q1 20x1
    dep, bal, cur = 0.0, 0.0, 0.0
    for start_t, cost in ((1, EQUIP1), (12, EQUIP2)):   # Q2 20x1, Q1 20x4
        if t >= start_t:
            dep += cost / EQUIP_LIFE_Q
            paid = max(0, t - start_t) * VENDOR_PMT_Q   # payments start the following quarter
            b = max(0.0, cost - paid)
            bal += b
            cur += min(b, 4 * VENDOR_PMT_Q)
    return dep, bal, cur


def ppe_capex(year, q):
    t = (year - 1) * 4 + q
    return EQUIP1 if t == 1 else EQUIP2 if t == 12 else 0


def build(mode="case", div_growth=DIV_GROWTH, sales_mult=1.0, inflation=0.0):
    """mode='case': quarterly 20x1 then annual 20x2-20x5 (the assignment's method).
    mode='quarterly': all 20 quarters on the 20x1 method (shows in-year peaks)."""
    annual, qs = quarter_sales(div_growth, sales_mult, inflation)
    periods = []
    if mode == "case":
        periods = [("Q%d 20x1" % (i + 1), [(1, i)]) for i in range(4)]
        periods += [("20x%d" % y, [(y, i) for i in range(4)]) for y in range(2, 6)]
    else:
        periods = [("Q%d 20x%d" % (i + 1, y), [(y, i)]) for y in range(1, 6) for i in range(4)]

    s = dict(OPEN)
    out = []
    for label, qtrs in periods:
        y_last, q_last = qtrs[-1]
        nxt = (y_last, q_last + 1) if q_last < 3 else (y_last + 1, 0)
        sales = sum(qs[k] for k in qtrs)
        # Inflation scenario: fixed cash costs rise with prices too, from 20x2.
        px = lambda y: (1 + inflation) ** (y - 1)
        adm = sum((ADMIN_Q_20X1 + ADMIN_STEP * (y - 1)) * px(y) for y, _ in qtrs)
        misc = sum((MISC_Q_20X1 + MISC_STEP * (y - 1)) * px(y) for y, _ in qtrs)
        mnt = sum(maint_q(y, q) * px(y) for y, q in qtrs)
        dep = sum(DEP_EXISTING_Q + equipment(y, q)[0] for y, q in qtrs)
        # Interest on the opening balance: prior quarter in 20x1, prior year after.
        bank_int = BANK_RATE * len(qtrs) / 4 * s["loan"]
        # Mortgage: 9% on each quarter's opening balance (= average of the four for a year).
        mort_open = [s["mort"] - MORT_PRIN_Q * k for k in range(len(qtrs))]
        mort_int = sum(MORT_RATE / 4 * b for b in mort_open)
        ebit = sales * (1 - MATERIAL - LABOR - COMMISSION) - adm - dep - mnt - misc
        ebt = ebit - bank_int - mort_int
        ni = ebt * (1 - TAX)
        div = sum(DIV_Q_20X1 * (1 + div_growth) ** (y - 1) for y, _ in qtrs)

        ar = (1 - COLLECT_SAME_Q) * qs[(y_last, q_last)]
        inv = MATERIAL * qs[nxt]                 # bought one quarter ahead
        matpay = (1 - PAY_SAME_Q) * inv          # half of this quarter's purchase unpaid
        ppe = s["ppe"] + sum(ppe_capex(y, q) for y, q in qtrs) - dep
        _, eq_bal, eq_cur = equipment(y_last, q_last)
        mort = s["mort"] - MORT_PRIN_Q * len(qtrs)
        re = s["re"] + ni - div

        assets_x_ts = MIN_CASH + ar + inv + ppe + s["other"]
        liab_x_loan = matpay + s["accr"] + eq_bal + mort + s["stock"] + re
        afn = assets_x_ts - liab_x_loan          # + borrow, - buy Treasuries
        loan, ts = max(afn, 0.0), max(-afn, 0.0)

        ca = MIN_CASH + ar + inv + ts
        cl = matpay + s["accr"] + loan + eq_cur + min(mort, 4 * MORT_PRIN_Q)
        tl = matpay + s["accr"] + loan + eq_bal + mort
        eqty = s["stock"] + re
        capex = sum(ppe_capex(y, q) for y, q in qtrs)
        cfo = ni + dep + (matpay - s["matpay"]) - (ar - s["ar"]) - (inv - s["inv"])
        cff = (loan - s["loan"]) + (eq_bal - s.get("eq", 0.0)) - MORT_PRIN_Q * len(qtrs) - div
        cash_delta = cfo - capex - (ts - s.get("ts", 0.0)) + cff

        out.append(dict(label=label, sales=sales, ebit=ebit, bank_int=bank_int, mort_int=mort_int,
                        ni=ni, div=div, ar=ar, inv=inv, ppe=ppe, matpay=matpay, loan=loan, ts=ts,
                        eq=eq_bal, mort=mort, re=re, ta=assets_x_ts + ts, tl=tl, eqty=eqty,
                        cr=ca / cl, de=tl / eqty, cfo=cfo, cash_delta=cash_delta))
        s.update(ar=ar, inv=inv, ppe=ppe, matpay=matpay, loan=loan, ts=ts, eq=eq_bal, mort=mort, re=re)
    return out


# ---- Reconciliation against the workbook's cached values -------------------
ROWS = {  # label in column A of 'Pro Forma w CF' -> key in build()
    "Expected Sales": "sales", "EBIT": "ebit", "EAT (Net Income)": "ni",
    "Accounts Receivable": "ar", "Raw Material Inventory": "inv",
    "Net Plant & Equipment": "ppe", "Material Payable": "matpay",
    "Bank Loan (PLUG) ($150,000 line)": "loan", "Retained Earnings": "re",
    "TOTAL ASSETS": "ta", "Current Ratio (must be at least 1.50)": "cr",
    "Total Liabilities / Equity (must be under 0.60)": "de",
    "Cash Flow from Operations": "cfo",
}
COLS = ["C", "D", "E", "F", "H", "I", "J", "K"]   # Q1-Q4 20x1, 20x2-20x5


def reconcile():
    wb = openpyxl.load_workbook(WORKBOOK, data_only=True)["Pro Forma w CF"]
    rows = {}
    for r in range(1, wb.max_row + 1):
        a = wb["A%d" % r].value
        if isinstance(a, str) and a.strip() in ROWS and a.strip() not in rows:
            rows[a.strip()] = r
    mine = build("case")
    worst, fails = 0.0, 0
    print("%-48s %10s %s" % ("Line", "max |diff|", "status"))
    for label, key in ROWS.items():
        r = rows[label]
        diffs = [abs((wb["%s%d" % (c, r)].value or 0) - p[key]) for c, p in zip(COLS, mine)]
        tol = 0.0005 if key in ("cr", "de") else 1.0
        ok = max(diffs) <= tol
        fails += not ok
        print("%-48s %10.4f %s" % (label, max(diffs), "ok" if ok else "MISMATCH"))
    print("\nCash delta (independent build), max |delta|: %.6f" %
          max(abs(p["cash_delta"]) for p in mine))
    return fails


def table(rows, title):
    print("\n" + title)
    print("%-9s %10s %10s %7s %7s %10s" % ("Period", "Sales", "Bank loan", "CR", "TL/E", "Net inc."))
    for p in rows:
        flag = []
        if p["cr"] < MIN_CR: flag.append("CR")
        if p["de"] >= MAX_DE: flag.append("TL/E")
        if p["loan"] > LINE: flag.append("LINE")
        print("%-9s %10.0f %10.0f %7.3f %7.3f %10.0f  %s" % (
            p["label"], p["sales"], p["loan"], p["cr"], p["de"], p["ni"], " ".join(flag)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quarterly", action="store_true")
    ap.add_argument("--scenarios", action="store_true")
    a = ap.parse_args()
    fails = reconcile()
    table(build("case"), "Base case (assignment method)")
    if a.quarterly:
        table(build("quarterly"), "All 20 quarters (20x1 method carried forward)")
    if a.scenarios:
        table(build("case", div_growth=0.0), "Dividend held at $110,000 a year")
        table(build("case", sales_mult=0.85), "Sales 15% below plan from 20x2")
        table(build("case", sales_mult=1.15), "Sales 15% above plan from 20x2")
        table(build("case", inflation=0.03), "3% inflation on sales and fixed costs from 20x2")
        table(build("quarterly", div_growth=0.0), "Quarterly, dividend held flat")
        table(build("quarterly", inflation=0.03), "Quarterly, 3% inflation")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
