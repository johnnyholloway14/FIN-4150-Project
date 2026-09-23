"""Change one assumption, predict the result, then check yourself.

This is the Step 4 drill from the assignment briefing: before submitting, each
member changes one input and says out loud what will happen BEFORE recalculating.
It is also the shape of quiz question 3 -- one assumption moves, what happens to
the recommendation, and which input has to stay fixed?

USAGE
    python whatif.py --wacc 0.14
    python whatif.py --escalation 0.12 --predict lower
    python whatif.py --inflation 0.05 --predict same
    python whatif.py --list

With --predict, the script tells you whether your prediction was right. Getting
one wrong before the deadline is free; getting it wrong in the quiz is not.
"""

from __future__ import annotations

import argparse

from verification import Assumptions, advantage, break_even, summarise

FIELDS = {
    "wacc": "cost of capital",
    "escalation": "equipment price escalation, which also drives the maintenance contract",
    "inflation": "labor and maintenance inflation",
    "price": "price of the new machine today",
    "maint_old_2002": "maintenance on the old machine in 2002",
    "labor_regular": "operator's regular pay",
    "labor_actual": "operator's actual pay including overtime",
    "old_book_value": "book value of the old machine",
    "replace_t": "years until the old machine must be replaced",
    "tax": "marginal tax rate",
    "horizon": "analysis horizon in years",
}

# Which inputs move together in reality, and therefore must not be changed alone.
COUPLED = {
    "escalation": "The maintenance contract is priced off the equipment price "
                  "('increased by the same percentage as the rate of increase of "
                  "the price of new equipment'), so escalation moves BOTH the "
                  "deferred purchase price and every maintenance figure. A careless "
                  "analyst changes the price escalation and leaves maintenance at 5%.",
    "labor_actual": "Actual pay is regular pay plus the overtime premium. Change it "
                    "alone and you are changing the overtime saving, not the wage. "
                    "Regular pay (labor_regular) must stay fixed for the premium to "
                    "mean what Exhibit 4 says it means.",
    "labor_regular": "Regular pay appears in BOTH scenarios and mostly cancels. What "
                     "does not cancel is the overtime premium, which is actual minus "
                     "regular -- so raising regular pay alone silently shrinks the "
                     "overtime saving.",
    "old_book_value": "Book value drives the old machine's depreciation AND the "
                      "writeoff tax shield in the buy-now case. Both move together.",
    "replace_t": "Changing the replacement year changes the deferred purchase price "
                 "too, since it escalates for replace_t years. It should also trigger "
                 "a writeoff of the old machine's unrecovered book value -- the "
                 "workbook does not do this. See FINDING 3.",
    "horizon": "The horizon must stay at or beyond the convergence year. Shorten it "
               "and you truncate a real difference; see the convergence test.",
    "tax": "The tax rate moves the after-tax cost of every line AND the value of "
           "every depreciation shield and the writeoff. Nothing stays fixed.",
}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    for f in FIELDS:
        p.add_argument(f"--{f.replace('_', '-')}", type=float, dest=f, default=None)
    p.add_argument("--predict", choices=["higher", "lower", "same", "flips"],
                   help="what you think happens to the advantage of waiting")
    p.add_argument("--list", action="store_true", help="list the inputs you can change")
    args = p.parse_args()

    if args.list:
        print("INPUTS YOU CAN CHANGE\n")
        for f, desc in FIELDS.items():
            print(f"  --{f.replace('_', '-'):<18} {desc}")
        return 0

    changes = {f: v for f, v in vars(args).items()
               if f in FIELDS and v is not None}
    if not changes:
        print("Nothing changed. Try: python whatif.py --wacc 0.14   (or --list)")
        return 1

    for f in ("replace_t", "horizon"):
        if f in changes:
            changes[f] = int(changes[f])

    base = Assumptions()
    base_adv = summarise(base)["advantage"]
    new_adv = advantage(base, **changes)
    delta = new_adv - base_adv

    print("=" * 72)
    print("WHAT CHANGED")
    print("=" * 72)
    for f, v in changes.items():
        print(f"  {f:20} {getattr(base, f):>14,.4f}  ->  {v:>14,.4f}    {FIELDS[f]}")

    print()
    print("=" * 72)
    print("WHAT HAPPENED")
    print("=" * 72)
    print(f"  Advantage of waiting, base     {base_adv:16,.2f}")
    print(f"  Advantage of waiting, changed  {new_adv:16,.2f}")
    print(f"  Movement                       {delta:16,.2f}")
    print(f"  Recommendation                 "
          f"{'WAIT (unchanged)' if new_adv > 0 else 'BUY NOW -- the recommendation flips'}")

    if args.predict:
        if new_adv <= 0:
            actual = "flips"
        elif abs(delta) < 1_000:
            actual = "same"
        elif delta > 0:
            actual = "higher"
        else:
            actual = "lower"
        verdict = "CORRECT" if args.predict == actual else f"WRONG -- it went {actual}"
        print(f"\n  You predicted '{args.predict}'.  {verdict}")
        if args.predict != actual:
            print("  Work out why before you submit. That gap is what the quiz looks for.")

    coupled = [COUPLED[f] for f in changes if f in COUPLED]
    if coupled:
        print()
        print("=" * 72)
        print("WHAT HAS TO STAY FIXED -- and what a careless analyst would also change")
        print("=" * 72)
        for note in coupled:
            print(f"  - {note}")

    if "wacc" in changes:
        r = break_even("wacc", 0.001, 0.30)
        print(f"\n  For reference, the two alternatives break even at a WACC of {r:.4%}.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
