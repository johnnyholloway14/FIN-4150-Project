"""Structural audit of the team's workbook.

verification.py asks "are the numbers right?". This asks a different question:
"is the model built the way it says it is?" A model can produce correct figures
and still fail the assignment -- requirement 2 is that every input trace to a
case exhibit, with no hard-coded numbers appearing from nowhere.

Three checks:
  1. Typed numbers. The Inputs sheet claims the Project Analysis sheet holds no
     constants, only formulas. Verified by walking every cell.
  2. Input provenance. Each constant on the Inputs sheet is compared against the
     value stated in Exhibit 4.
  3. Memo provenance. Every figure asserted in the memo is searched for in the
     workbook. A memo figure with no cell behind it cannot be defended by
     pointing at the model.

USAGE
    python audit_workbook.py
    python audit_workbook.py --workbook "path\\to\\file.xlsx"
"""

from __future__ import annotations

import argparse
import re

DEFAULT_WORKBOOK = r"data\Final - Star River Project Analysis.xlsx"

# Row/col references are not numbers we care about; nor are small integers used
# as exponents or bounds. Anything else inside a formula is a magic number.
NUMERIC_LITERAL = re.compile(r"(?<![A-Za-z0-9_$:.])(\d+\.?\d*)(?![0-9]*\s*[:!])")
BENIGN = {"0", "1", "2", "3", "4", "10", "100"}

# What Exhibit 4 actually says, independent of what the workbook claims.
EXHIBIT_4_VALUES = {
    "C5": (0.245, "marginal tax rate 24.5 percent"),
    "C7": (0.015, "inflation approximately 1.5 percent per year"),
    "C8": (0.05, "prices rising about 5 percent per year"),
    "C11": (1_820_000, "new equipment currently costs SGD1.82 million"),
    "C12": (10, "depreciate over 10 years"),
    "C16": (3_640, "SGD3,640 for the initial year"),
    "C19": (218_400, "on the books at SGD218,400"),
    "C20": (3, "fully depreciated in three years time"),
    "C22": (0, "no salvage value at all"),
    "C23": (3, "cannot handle our packaging needs by the end of 2004"),
    "C24": (15_470, "SGD15,470 per year for maintenance costs"),
    "C25": (63_700, "SGD63,700 per year for his regular time"),
    "C26": (81_900, "averaging SGD81,900 per year because of the overtime"),
}

# Every figure the memo asserts, with where it appears.
MEMO_FIGURES = {
    "PV advantage of waiting": 173_264.58,
    "Advantage per year": 25_669.32,
    "PV of costs, wait": -1_702_230.14,
    "PV of costs, buy now": -1_875_494.72,
    "Sensitivity: WACC 14%": 281_813,
    "Sensitivity: WACC 8%": 56_677,
    "Sensitivity: WACC 6%": -25_238,
    "Sensitivity: WACC 5.06%": -64_777,
    "Sensitivity: escalation 8%": 57_208,
    "Sensitivity: escalation 12%": -107_892,
    "Sensitivity: inflation 5%": 171_199,
    "Sensitivity: replace 2003": 117_100,
    "Sensitivity: replace 2002": 58_455,
    "Break-even: unquantified benefit": 34_000,
    "Break-even: labor saving": 110_811,
    "Saving in purchase price": 286_878,
}


def load(path: str):
    try:
        import openpyxl
    except ImportError:
        raise SystemExit("openpyxl is required: pip install openpyxl")
    return (openpyxl.load_workbook(path, data_only=False),
            openpyxl.load_workbook(path, data_only=True))


def check_no_typed_numbers(wf) -> bool:
    print("=" * 76)
    print("CHECK 1 -- does the calculation sheet contain typed numbers?")
    print("=" * 76)
    ok = True
    for ws in wf.worksheets:
        constants, magic, tolerances = [], [], []
        for row in ws.iter_rows():
            for c in row:
                v = c.value
                if v is None:
                    continue
                if isinstance(v, str) and v.startswith("="):
                    lits = [n for n in NUMERIC_LITERAL.findall(v) if n not in BENIGN]
                    if not lits:
                        continue
                    # A small literal inside an ABS() comparison is a rounding
                    # tolerance in a cross-check, not an input smuggled into the
                    # arithmetic. Report it, but it does not break the claim.
                    if "ABS(" in v.upper() and all(float(n) < 1 for n in lits):
                        tolerances.append((c.coordinate, lits, v))
                    else:
                        magic.append((c.coordinate, lits, v))
                elif isinstance(v, (int, float)):
                    constants.append((c.coordinate, v))

        print(f"\n  {ws.title}")
        print(f"    typed constants           {len(constants)}")
        print(f"    formulas w/ magic numbers {len(magic)}")
        print(f"    rounding tolerances       {len(tolerances)}")
        for coord, lits, _ in tolerances:
            print(f"      tolerance {coord} {lits} -- in a cross-check, benign")
        if ws.title == "Project Analysis":
            # This is the sheet the claim is about.
            offenders = [(c, v) for c, v in constants if v not in (0, 0.0)]
            if offenders or magic:
                ok = False
                for c, v in offenders:
                    print(f"      TYPED NUMBER {c} = {v}")
                for c, lits, f in magic:
                    print(f"      MAGIC NUMBER {c} {lits} in {f[:60]}")
            else:
                print("    -> claim holds: no typed numbers except a zero on the year axis")
        else:
            for c, v in constants[:25]:
                print(f"      {c:>5} = {v}")
            if len(constants) > 25:
                print(f"      ... {len(constants) - 25} more")
    return ok


def check_input_provenance(wv) -> bool:
    print("\n" + "=" * 76)
    print("CHECK 2 -- do the inputs match what Exhibit 4 says?")
    print("=" * 76)
    ws = wv["Inputs"]
    ok = True
    print(f"  {'cell':>6}{'in model':>16}{'in Exhibit 4':>16}   source")
    for cell, (expected, quote) in EXHIBIT_4_VALUES.items():
        actual = ws[cell].value
        agrees = actual is not None and abs(float(actual) - expected) < 0.005
        ok &= agrees
        print(f"  {cell:>6}{actual if actual is not None else 'EMPTY':>16}"
              f"{expected:>16}   {quote}{'' if agrees else '   <-- MISMATCH'}")
    return ok


def check_memo_provenance(wv) -> bool:
    print("\n" + "=" * 76)
    print("CHECK 3 -- can every figure in the memo be pointed at in the model?")
    print("=" * 76)
    hits = {label: [] for label in MEMO_FIGURES}
    for ws in wv.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, (int, float)) and not isinstance(c.value, bool):
                    for label, target in MEMO_FIGURES.items():
                        if abs(c.value - target) <= max(1.0, abs(target) * 0.0005):
                            hits[label].append(f"{ws.title}!{c.coordinate}")

    missing = 0
    for label, target in MEMO_FIGURES.items():
        where = ", ".join(hits[label][:3]) if hits[label] else "NOT IN WORKBOOK"
        if not hits[label]:
            missing += 1
        print(f"  {label:36}{target:>14,.0f}   {where}")

    print(f"\n  {missing} of {len(MEMO_FIGURES)} memo figures have no cell behind them.")
    if missing:
        print("  Those were computed outside the model. Either bring them into the")
        print("  workbook as a sensitivity block, or say in the memo where they came")
        print("  from -- 'every number in the memo should be findable in the model'.")
    return missing == 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--workbook", default=DEFAULT_WORKBOOK)
    args = p.parse_args()

    wf, wv = load(args.workbook)
    print(f"WORKBOOK: {args.workbook}")
    print(f"SHEETS:   {wf.sheetnames}\n")

    ok = check_no_typed_numbers(wf)
    ok &= check_input_provenance(wv)
    ok &= check_memo_provenance(wv)

    print()
    print("RESULT:", "no structural problems found" if ok else
          "structural problems found -- see the flags above")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
