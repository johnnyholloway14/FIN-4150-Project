"""Chart for the memo: quarterly bank loan vs the $150,000 line (from verify_forecast.py)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from verify_forecast import build, LINE

rows = build("quarterly")
labels = [r["label"] for r in rows]
loans = [r["loan"] / 1000 for r in rows]
INK, MUTED, GRID, BLUE, ORANGE = "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6", "#eb6834"

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8})
fig, ax = plt.subplots(figsize=(6.6, 2.15), dpi=220)
colors = [ORANGE if v * 1000 > LINE else BLUE for v in loans]
ax.bar(range(len(loans)), loans, width=0.72, color=colors, edgecolor="white", linewidth=1)
ax.axhline(LINE / 1000, color=INK, lw=1.2, ls=(0, (4, 3)))
ax.text(2.5, LINE / 1000 + 8, "$150K credit line", color=INK, fontsize=7.5, va="bottom", ha="center")
for i, (l, v) in enumerate(zip(labels, loans)):
    if l.startswith("Q2"):
        if v * 1000 > LINE:  # label only the peaks that break the line
            ax.text(i, v + 6, "$%dK" % round(v), ha="center", va="bottom", fontsize=7, color=INK)
ax.set_xticks(range(len(loans)))
ax.set_xticklabels([l.replace(" 20x", "\n'x") if l.startswith("Q1") else l.split()[0] for l in labels],
                   fontsize=6.5, color=MUTED)
ax.set_ylabel("Bank loan ($000)", color=MUTED, fontsize=7.5)
ax.set_ylim(0, 360)
ax.yaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(MUTED)
ax.tick_params(axis="y", colors=MUTED, labelsize=7, length=0)
ax.tick_params(axis="x", length=0)
ax.set_title("Quarterly bank loan, 20x1-20x5 (orange = above the $150K line)",
             loc="left", fontsize=8.5, color=INK, fontweight="bold")
fig.tight_layout(pad=0.4)
fig.savefig(Path(__file__).parent / "loan_chart.png")
print("ok")
