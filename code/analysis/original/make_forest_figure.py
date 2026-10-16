#!/usr/bin/env python3
"""Figure 2 — single-shot Δ(resolve) forest plot for The Recall Trap.

Draws dedup-OFF minus dedup-ON resolve-rate deltas (percentage points) with
repository-cluster-bootstrap 95% CIs and McNemar exact p-values, arms grouped by
pre-registered status. Replaces the placeholder forest_deltas.png so the figure
DRAWS the intervals + status markers the caption already states.

Numbers are the frozen §5.1 / caption values (Ruling 1 froze this figure's
contents: K=12 stays the confirmatory open-weights row; the clean-model K=4/K=40
dose-response is a SEPARATE figure, not this one).

Style matches make_hero_figure.py (DejaVu Serif, ink #111, link-blue #1a4a7a).
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, SUB, LINK = "#111111", "#444444", "#1a4a7a"
CONF = "#1a4a7a"   # confirmatory: link-blue, filled
SUPP = "#3f6d78"   # supportive (producibility channel): muted teal
CTRL = "#8a8f98"   # replication control (includes zero): gray

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Georgia", "Times New Roman"],
    "text.color": INK, "axes.edgecolor": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
})

# (label, delta, ci_lo, ci_hi, p_text, status_text, color, marker, filled)
# Ordered top->bottom; drawn bottom->top so confirmatory sits at the top.
ARMS = [
    ("DENSE-1 (dense)",     5.7, -0.9,  8.6, "p=0.0097", "Replication control (post-primary, dense)", CTRL, "o", False),
    ("DeepSeek-v4",      6.2,  3.9, 10.0, "p=0.0004", "Supportive (producibility channel)",        SUPP, "s", True),
    ("Qwen3.6-27B",      3.6,  0.9,  4.9, "p=0.0133", "Confirmatory (pre-registered, open-weights)", CONF, "o", True),
    ("gpt-5.6-sol",      7.6,  0.8, 13.1, "p=0.0003", "Confirmatory",                              CONF, "o", True),
]

fig, ax = plt.subplots(figsize=(7.2, 3.5), dpi=170)
ys = list(range(len(ARMS)))
for y, (label, d, lo, hi, ptxt, status, color, marker, filled) in zip(ys, ARMS):
    ax.plot([lo, hi], [y, y], color=color, lw=1.6, solid_capstyle="round", zorder=2)
    for x in (lo, hi):  # whisker caps
        ax.plot([x, x], [y - 0.11, y + 0.11], color=color, lw=1.6, zorder=2)
    ax.scatter([d], [y], s=58, marker=marker, zorder=3,
               facecolor=(color if filled else "white"), edgecolor=color, linewidths=1.6)
    ax.text(hi + 0.5, y + 0.17, f"{label}", va="bottom", ha="left", fontsize=10.5, color=INK)
    ax.text(hi + 0.5, y - 0.20, f"Δ +{d:.1f}pp, {ptxt}", va="top", ha="left", fontsize=8.5, color=SUB, style="italic")

ax.axvline(0, color=INK, lw=1.0, ls=(0, (4, 3)), zorder=1)  # no-effect line
ax.text(0, len(ARMS) - 0.35, "no effect", rotation=90, va="top", ha="right",
        fontsize=8, color=SUB)

ax.set_ylim(-0.7, len(ARMS) - 0.1)
ax.set_xlim(-4, 21)
ax.set_yticks([])
ax.set_xlabel("Δ resolve rate  (dedup-OFF − dedup-ON, percentage points)", fontsize=10)
ax.set_xticks([-2.5, 0, 2.5, 5, 7.5, 10, 12.5])
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(INK)
ax.tick_params(axis="x", labelsize=9)

# status legend (small, unobtrusive)
from matplotlib.lines import Line2D
leg = [
    Line2D([0],[0], marker="o", color="white", markerfacecolor=CONF, markeredgecolor=CONF, markersize=8, lw=0, label="Confirmatory (pre-registered)"),
    Line2D([0],[0], marker="s", color="white", markerfacecolor=SUPP, markeredgecolor=SUPP, markersize=8, lw=0, label="Supportive (producibility channel)"),
    Line2D([0],[0], marker="o", color="white", markerfacecolor="white", markeredgecolor=CTRL, markersize=8, lw=0, label="Replication control (CI includes 0)"),
]
ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3,
          fontsize=8, frameon=False, handletextpad=0.4, columnspacing=1.4)

fig.tight_layout()
out = Path(__file__).resolve().parents[2] / "docs" / "paper" / "figures" / "forest_deltas.png"
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("wrote", out)
