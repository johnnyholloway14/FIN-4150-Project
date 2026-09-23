"""Independent verification of the Star River packaging-machine decision.

WHAT THIS IS
    Submission item 3. It recomputes the decision FROM THE CASE EXHIBITS and
    then reconciles against the team's workbook. It does not read the model's
    formulas, and it does not ask an AI whether the model is right.

WHY IT IS BUILT THIS WAY
    The assignment warns: if the check and the model agree to the dollar, say
    how you know that is not just because both came from the same source. The
    answer here is structural. Every input below is typed from Exhibit 4 of the
    Bruner case PDF, with the sentence it came from quoted beside it. The cash
    flow shape -- when depreciation starts, when the maintenance contract is
    priced, which years carry overtime -- was derived from the plant manager's
    memo before the workbook was opened. A structural error in either model
    would surface as a mismatch in particular years, not as a uniform offset,
    which is why the year-by-year reconciliation matters more than the NPV.

USAGE
    python verification.py
    python verification.py --workbook "path\\to\\Final - Star River Project Analysis.xlsx"
    python verification.py --sensitivities     # also check the memo's Exhibit B

    Exit code 0 = everything reconciles, 1 = at least one figure does not.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, replace

DEFAULT_WORKBOOK = r"data\Final - Star River Project Analysis.xlsx"
TOLERANCE = 0.01          # SGD. The workbook carries full precision, so this is tight.


# ---------------------------------------------------------------------------
# INPUTS -- every one traceable to a case exhibit
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Assumptions:
    """All figures in SGD. Sources are quoted in EXHIBIT_SOURCES below."""

    tax: float = 0.245
    wacc: float = 0.11
    inflation: float = 0.015          # labor and maintenance
    escalation: float = 0.05          # equipment price and the maintenance contract

    price: float = 1_820_000.0        # new machine, today
    life: int = 10                    # depreciable life, straight line
    maint_new_first_year: float = 3_640.0

    old_book_value: float = 218_400.0
    old_remaining_life: int = 3
    old_salvage: float = 0.0
    maint_old_2002: float = 15_470.0
    labor_regular: float = 63_700.0
    labor_actual: float = 81_900.0    # regular + overtime

    replace_t: int = 3                # forced replacement, end of 2004
    horizon: int = 13                 # t = 0..13, i.e. 2001..2014
    base_year: int = 2001

    # Modelling switches, not case facts. See the notes on each.
    writeoff_on_early_replacement: bool = False
    # False mirrors the team's workbook, which drops the old machine's
    # remaining book value if replacement is brought forward. True credits the
    # tax shield on that writeoff, which is the correct treatment and is what
    # the buy-now scenario already does. See FINDING 3 in PROCESS.md.

    extra_benefit: float = 0.0
    # Annual pre-tax value of the new machine's unquantified advantages
    # (reliability, packaging flexibility). Earned in every year the NEW
    # machine is running, which is why it only moves the answer in years
    # 1..replace_t. See FINDING 1.

    labor_saving: float | None = None
    # Overrides the overtime premium, for the break-even in the memo's risk
    # section. None = use the premium implied by Exhibit 4.

    @property
    def overtime(self) -> float:
        """Exhibit 4 gives regular pay and actual pay; the premium is the gap."""
        return self.labor_actual - self.labor_regular

    @property
    def price_deferred(self) -> float:
        return self.price * (1 + self.escalation) ** self.replace_t


EXHIBIT_SOURCES = {
    "tax": "Exhibit 4: 'The marginal tax rate for this investment would be 24.5 percent.'",
    "wacc": "GIVEN in the assignment prompt. Exhibit 5 supplies the comparables to derive it.",
    "inflation": "Exhibit 4: 'labor and maintenance costs will continue to rise due to "
                 "inflation at approximately 1.5 percent per year'",
    "escalation": "Exhibit 4: 'increasing its prices at about 5 percent per year'",
    "price": "Exhibit 4: 'The new equipment currently costs SGD1.82 million'",
    "life": "Exhibit 4: 'which we would depreciate over 10 years at SGD182,000 per year'",
    "maint_new_first_year": "Exhibit 4: 'a price of SGD3,640 for the initial year'. The "
                            "contract price then rises with the equipment price, not inflation.",
    "old_book_value": "Exhibit 4: 'on the tax and reporting books at SGD218,400'",
    "old_remaining_life": "Exhibit 4: 'will be fully depreciated in three years time'",
    "old_salvage": "Exhibit 4: 'we believe the equipment has no salvage value at all'",
    "maint_old_2002": "Exhibit 4: 'In 2002 we will pay about SGD15,470 per year for maintenance'",
    "labor_regular": "Exhibit 4: 'The operator is paid SGD63,700 per year for his regular time'",
    "labor_actual": "Exhibit 4: 'he has been averaging SGD81,900 per year because of the overtime'",
    "replace_t": "Exhibit 4: 'the current equipment will not be able to handle our packaging "
                 "needs by the end of 2004' -- replacement is unavoidable at t=3.",
    "horizon": "Both streams converge at t=13; see convergence() below.",
    "base_year": "Case opens 5 July 2001. Exhibit 4 prices maintenance 'in 2002', so t=1 = 2002.",
}


# ---------------------------------------------------------------------------
# CASH FLOWS
# ---------------------------------------------------------------------------

def wait_flows(a: Assumptions) -> list[float]:
    """Keep the old machine, buy the new one at t = replace_t.

    The old machine carries its maintenance, its overtime and its remaining
    depreciation until it goes. The new machine's maintenance contract is
    priced off the equipment price in the year it starts, so a contract
    beginning in 2005 opens at 3,640 x 1.05^3, not at 3,640.
    """
    f = [0.0] * (a.horizon + 1)
    dep_new = a.price_deferred / a.life

    for t in range(1, a.horizon + 1):
        labor = a.labor_regular * (1 + a.inflation) ** (t - 1)

        if t <= a.replace_t:                                  # old machine still running
            maint = a.maint_old_2002 * (1 + a.inflation) ** (t - 1)
            premium = a.overtime if a.labor_saving is None else a.labor_saving
            overtime = premium * (1 + a.inflation) ** (t - 1)
            dep = a.old_book_value / a.old_remaining_life if t <= a.old_remaining_life else 0.0
            benefit = 0.0
        else:                                                 # new machine running
            maint = a.maint_new_first_year * (1 + a.escalation) ** (t - 1)
            overtime = 0.0
            dep = dep_new if t <= a.replace_t + a.life else 0.0
            benefit = a.extra_benefit

        total_cost = maint + labor + overtime + dep
        f[t] = -(total_cost * (1 - a.tax) - dep) + benefit * (1 - a.tax)

    f[a.replace_t] -= a.price_deferred

    if a.writeoff_on_early_replacement and a.replace_t < a.old_remaining_life:
        # Scrapping the old machine early leaves book value unrecovered. The
        # writeoff shelters that amount, exactly as the buy-now case does at t=0.
        unrecovered = a.old_book_value * (1 - a.replace_t / a.old_remaining_life)
        f[a.replace_t] += unrecovered * a.tax

    return f


def now_flows(a: Assumptions) -> list[float]:
    """Buy the new machine at t = 0 and write off the old one immediately."""
    f = [0.0] * (a.horizon + 1)
    f[0] = -a.price + (a.old_book_value - a.old_salvage) * a.tax

    for t in range(1, a.horizon + 1):
        maint = a.maint_new_first_year * (1 + a.escalation) ** (t - 1)
        labor = a.labor_regular * (1 + a.inflation) ** (t - 1)
        dep = a.price / a.life if t <= a.life else 0.0
        total_cost = maint + labor + dep
        f[t] = -(total_cost * (1 - a.tax) - dep) + a.extra_benefit * (1 - a.tax)

    return f


# ---------------------------------------------------------------------------
# VALUATION
# ---------------------------------------------------------------------------

def npv(flows: list[float], rate: float) -> float:
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(flows))


def annuity_factor(rate: float, periods: int) -> float:
    return (1 - (1 + rate) ** -periods) / rate


def summarise(a: Assumptions = Assumptions()) -> dict:
    """The six figures the memo reports, plus the flows behind them."""
    w, b = wait_flows(a), now_flows(a)
    pv_wait, pv_now = npv(w, a.wacc), npv(b, a.wacc)
    af = annuity_factor(a.wacc, a.horizon)
    return {
        "flows_wait": w,
        "flows_now": b,
        "pv_wait": pv_wait,
        "pv_now": pv_now,
        "advantage": pv_wait - pv_now,
        "eac_wait": pv_wait / af,
        "eac_now": pv_now / af,
        "advantage_annual": (pv_wait - pv_now) / af,
    }


def advantage(a: Assumptions = Assumptions(), **overrides) -> float:
    """Advantage of waiting, in PV. Positive means waiting costs less."""
    if overrides:
        a = replace(a, **overrides)
    return summarise(a)["advantage"]


def break_even(field: str, lo: float, hi: float, a: Assumptions = Assumptions()) -> float:
    """Bisect on one assumption until waiting and buying now are worth the same."""
    def f(x: float) -> float:
        return advantage(a, **{field: x})

    if f(lo) * f(hi) > 0:
        raise ValueError(f"no sign change for {field} between {lo} and {hi}")
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def convergence(a: Assumptions = Assumptions(), years_past_horizon: int = 3) -> list[tuple]:
    """Prove the horizon does not drive the answer.

    Past the last depreciation year both scenarios run the same machine on the
    same contract with the same operator, so the difference must be zero. If it
    is not, the horizon is cutting off a real difference and 13 years is wrong.
    """
    out = []
    for extra in range(1, years_past_horizon + 1):
        long = replace(a, horizon=a.horizon + extra)
        w, b = wait_flows(long), now_flows(long)
        t = a.horizon + extra
        out.append((t, a.base_year + t, w[t], b[t], w[t] - b[t]))
    return out


# ---------------------------------------------------------------------------
# RECONCILIATION AGAINST THE TEAM'S WORKBOOK
# ---------------------------------------------------------------------------

WORKBOOK_CELLS = {
    "pv_wait": ("Project Analysis", "D29"),
    "pv_now": ("Project Analysis", "D47"),
    "advantage": ("Project Analysis", "D50"),
    "advantage_annual": ("Project Analysis", "D55"),
    "eac_wait": ("Project Analysis", "D58"),
    "eac_now": ("Project Analysis", "D59"),
}
FLOW_ROWS = {"flows_wait": 27, "flows_now": 45}
FLOW_COLS = list("DEFGHIJKLMNOPQ")           # t = 0..13


def read_workbook(path: str) -> dict:
    """Cached values only. We never read the model's formulas to build our own."""
    try:
        import openpyxl
    except ImportError:
        sys.exit("openpyxl is required: pip install openpyxl")

    wb = openpyxl.load_workbook(path, data_only=True)
    model = {}
    for name, (sheet, cell) in WORKBOOK_CELLS.items():
        model[name] = wb[sheet][cell].value
    for name, row in FLOW_ROWS.items():
        model[name] = [wb["Project Analysis"][f"{c}{row}"].value for c in FLOW_COLS]
    return model


def reconcile(path: str) -> bool:
    a = Assumptions()
    mine, model = summarise(a), read_workbook(path)
    ok = True

    print("=" * 76)
    print("HEADLINE FIGURES")
    print("=" * 76)
    print(f"{'':24}{'this check':>16}{'the model':>16}{'difference':>16}")
    for key in ("pv_wait", "pv_now", "advantage", "eac_wait", "eac_now", "advantage_annual"):
        diff = mine[key] - model[key]
        flag = "" if abs(diff) < TOLERANCE else "   <-- MISMATCH"
        ok &= abs(diff) < TOLERANCE
        print(f"{key:24}{mine[key]:16,.2f}{model[key]:16,.2f}{diff:16,.2f}{flag}")

    print()
    print("=" * 76)
    print("YEAR BY YEAR -- the part that would expose a structural error")
    print("=" * 76)
    print(f"{'t':>3}{'year':>7}{'wait (check)':>16}{'wait (model)':>16}"
          f"{'now (check)':>16}{'now (model)':>16}")
    for t in range(a.horizon + 1):
        w_me, w_them = mine["flows_wait"][t], model["flows_wait"][t]
        b_me, b_them = mine["flows_now"][t], model["flows_now"][t]
        bad = abs(w_me - w_them) > TOLERANCE or abs(b_me - b_them) > TOLERANCE
        ok &= not bad
        print(f"{t:3}{a.base_year + t:7}{w_me:16,.2f}{w_them:16,.2f}"
              f"{b_me:16,.2f}{b_them:16,.2f}{'  <-- MISMATCH' if bad else ''}")

    print()
    print("=" * 76)
    print("CONVERGENCE -- is the 13-year horizon doing any work?")
    print("=" * 76)
    for t, year, w, b, d in convergence(a):
        note = "identical" if abs(d) < TOLERANCE else "STILL DIFFERENT -- horizon too short"
        print(f"  t={t} ({year}): wait {w:12,.2f}   now {b:12,.2f}   diff {d:8,.2f}   {note}")
        ok &= abs(d) < TOLERANCE

    return ok


# ---------------------------------------------------------------------------
# THE MEMO'S RISK SECTION
# ---------------------------------------------------------------------------

def check_memo_claims() -> bool:
    """Every number the memo asserts that is NOT in the workbook.

    The workbook contains no sensitivity machinery, so none of these can be
    traced to a cell. They are checked here instead.
    """
    a = Assumptions()
    claims = [
        ("WACC 14%",                advantage(a, wacc=0.14),        281_813),
        ("WACC 8%",                 advantage(a, wacc=0.08),         56_677),
        ("WACC 6%",                 advantage(a, wacc=0.06),        -25_238),
        ("WACC 5.06% (bank debt)",  advantage(a, wacc=0.0506),      -64_777),
        ("Escalation 8%",           advantage(a, escalation=0.08),   57_208),
        ("Escalation 12%",          advantage(a, escalation=0.12),  -107_892),
        ("Inflation 5%",            advantage(a, inflation=0.05),   171_199),
        ("Replace 2003, as modelled",
         advantage(a, replace_t=2),                                 117_100),
        ("Replace 2002, as modelled",
         advantage(a, replace_t=1),                                  58_455),
        ("Replace 2003, with writeoff",
         advantage(a, replace_t=2, writeoff_on_early_replacement=True), 117_100),
        ("Replace 2002, with writeoff",
         advantage(a, replace_t=1, writeoff_on_early_replacement=True),  58_455),
    ]

    print("=" * 76)
    print("MEMO EXHIBIT B -- none of these figures appear in the workbook")
    print("=" * 76)
    print(f"{'':32}{'this check':>15}{'memo says':>15}{'difference':>15}")
    ok = True
    for label, mine, memo in claims:
        diff = mine - memo
        flag = "" if abs(diff) < 5 else "  <-- CHECK"
        ok &= abs(diff) < 5
        print(f"{label:32}{mine:15,.2f}{memo:15,.2f}{diff:15,.2f}{flag}")

    print()
    print("BREAK-EVENS")
    r = break_even("wacc", 0.001, 0.30)
    e = break_even("escalation", 0.001, 0.30)
    b = break_even("extra_benefit", 0.0, 1_000_000.0)
    lab = break_even("labor_saving", 0.0, 2_000_000.0)
    rows = [
        ("Cost of capital",      f"{r:.4%}",  "6.61%",   abs(r - 0.0661) < 5e-4),
        ("Equipment escalation", f"{e:.4%}",  "9.42%",   abs(e - 0.0942) < 5e-4),
        ("Unquantified benefit", f"{b:,.0f}", "34,000",  abs(b - 34_000) < 50),
        ("Labor saving",         f"{lab:,.0f}", "110,811", abs(lab - 110_811) < 50),
    ]
    print(f"{'':28}{'this check':>14}{'memo says':>14}")
    for label, mine, memo, agrees in rows:
        print(f"{label:28}{mine:>14}{memo:>14}{'' if agrees else '  <-- CHECK'}")
        ok &= agrees

    print()
    print("Note on the benefit break-even: a benefit of the new machine is earned")
    print("in every year that machine is running. Both scenarios run it from 2005,")
    print("so the two differ only in 2002-2004. Grossing up the 13-year annualised")
    print("advantage instead assumes a 13-year gap, and understates the hurdle.")
    return ok


# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workbook", default=DEFAULT_WORKBOOK,
                   help="path to the team's .xlsx")
    p.add_argument("--sensitivities", action="store_true",
                   help="also check the memo's Exhibit B and its break-evens")
    p.add_argument("--sources", action="store_true",
                   help="print each input with the exhibit sentence it came from")
    args = p.parse_args()

    if args.sources:
        a = Assumptions()
        print("INPUTS AND THEIR SOURCES")
        print("=" * 76)
        for field, quote in EXHIBIT_SOURCES.items():
            print(f"  {field:24} = {getattr(a, field)}")
            print(f"  {'':24}   {quote}")
        print(f"  {'overtime':24} = {a.overtime:,.0f}   DERIVED = actual pay - regular pay")
        print(f"  {'price_deferred':24} = {a.price_deferred:,.2f}   "
              f"DERIVED = price x (1 + escalation)^replace_t")
        return 0

    ok = reconcile(args.workbook)
    if args.sensitivities:
        print()
        ok &= check_memo_claims()

    print()
    print("RESULT:", "everything reconciles" if ok else
          "at least one figure does not reconcile -- see the flags above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
