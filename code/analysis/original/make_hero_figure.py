#!/usr/bin/env python3
"""Generate the "recall trap" hero figure for the paper draft.

Design intent (restrained, paper-consistent, not flashy):
  Two 12-slot context packs stand side by side under a shared "fixed 12-slot
  budget" bracket, making the zero-sum budget the visual premise.
    - LEFT  (dedup-ON, the recall-maximizer): the budget is spent as 12 distinct
      files, ONE thin shallow chunk each. Rendered in a single cool blue-gray
      hue so the eye reads "many of the same, broad but shallow". Annotated
      "higher file recall@k" (gold file present in 0.878 of packs).
    - RIGHT (dedup-OFF): the same 12 slots spent on ~5 files with STACKED chunks
      (4,3,2,2,1). Each file is a distinct muted hue with thin separators, so the
      eye reads "fewer files, deeper coverage". Annotated "higher resolve".
  A slim arrow between them carries the paradox line. Muted palette keyed to the
  paper (ink #111, link-blue #1a4a7a); DejaVu Serif to match the Georgia body.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif", "Georgia", "Times New Roman"],
    "text.color": "#111111",
    "axes.edgecolor": "#111111",
})

INK = "#111111"
SUB = "#444444"
LINK = "#1a4a7a"
ON_HUE = "#93a9bd"        # single cool blue-gray for the 12 shallow ON chunks
ON_HUE_ALT = "#aebfcd"    # faint alternation so distinct files stay legible
# five muted, harmonious hues for the OFF file groups (desaturated, print-safe)
OFF_HUES = ["#3f6d78", "#8a6d3b", "#5f7a54", "#7a4f46", "#4a5a7a"]

fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=170)
ax.set_xlim(0, 12)
ax.set_ylim(0, 12.7)
ax.axis("off")

# ---- geometry ----
COL_W = 2.9
GAP = 0.10          # slot gap
BASE_Y = 0.9
TOP_Y = 9.6
H = TOP_Y - BASE_Y  # total stack height for 12 slots
slot_h = (H - 11 * GAP) / 12.0
ON_X = 1.35
OFF_X = 7.75


def draw_slot(x, y, h, color, edge="#ffffff", lw=1.1, inner=None):
    ax.add_patch(Rectangle((x, y), COL_W, h, facecolor=color, edgecolor=edge,
                           linewidth=lw, joinstyle="round"))


# ---- LEFT: dedup-ON, 12 files x 1 chunk (broad, shallow) ----
for i in range(12):
    y = BASE_Y + i * (slot_h + GAP)
    draw_slot(ON_X, y, slot_h, ON_HUE if i % 2 == 0 else ON_HUE_ALT)
# file tick labels on a few slots to signal "distinct file each"
ax.text(ON_X + COL_W / 2, TOP_Y + 0.82, "dedup-ON", ha="center", va="bottom",
        fontsize=12.5, fontweight="bold", color=INK)
ax.text(ON_X + COL_W / 2, TOP_Y + 0.42, "the recall-maximizer", ha="center",
        va="bottom", fontsize=9.5, style="italic", color=SUB)
ax.text(ON_X + COL_W / 2, BASE_Y - 0.32, "12 files  x  1 chunk each",
        ha="center", va="top", fontsize=9.5, color=INK)
ax.text(ON_X + COL_W / 2, BASE_Y - 0.72, "broad, shallow", ha="center",
        va="top", fontsize=9.0, style="italic", color=SUB)

# ---- RIGHT: dedup-OFF, ~5 files x stacked chunks (deep) ----
# Own slot height so the 5 groups (with inter-group spacing) end exactly at TOP_Y,
# matching the ON column's height rather than overshooting it.
groups = [4, 3, 2, 2, 1]   # sums to 12
INTER = 0.20               # extra breathing room between file groups
n_within = sum(n - 1 for n in groups)      # within-group chunk boundaries
n_inter = len(groups) - 1                  # file-group boundaries
off_slot_h = (H - n_within * GAP - n_inter * (GAP + INTER)) / 12.0
y = BASE_Y
for g, n in enumerate(groups):
    group_h = n * off_slot_h + (n - 1) * GAP
    # thin internal chunk separators within the same-file group
    for j in range(n):
        yy = y + j * (off_slot_h + GAP)
        draw_slot(OFF_X, yy, off_slot_h, OFF_HUES[g], edge="#ffffff", lw=0.9)
    # group outline to read the file boundary
    ax.add_patch(Rectangle((OFF_X - 0.08, y - 0.06), COL_W + 0.16, group_h + 0.12,
                           facecolor="none", edgecolor=OFF_HUES[g], linewidth=1.6))
    y += group_h + GAP + INTER
ax.text(OFF_X + COL_W / 2, TOP_Y + 0.82, "dedup-OFF", ha="center", va="bottom",
        fontsize=12.5, fontweight="bold", color=INK)
ax.text(OFF_X + COL_W / 2, TOP_Y + 0.42, "breadth traded for depth", ha="center",
        va="bottom", fontsize=9.5, style="italic", color=SUB)
ax.text(OFF_X + COL_W / 2, BASE_Y - 0.32, "~5 files  x  stacked chunks",
        ha="center", va="top", fontsize=9.5, color=INK)
ax.text(OFF_X + COL_W / 2, BASE_Y - 0.72, "fewer files, deeper coverage",
        ha="center", va="top", fontsize=9.0, style="italic", color=SUB)

# ---- shared "12-slot budget" bracket over both columns ----
# Lifted well clear of the bold dedup-ON/OFF labels (which rise ~0.55 units above
# their baseline at TOP_Y+0.82) so the horizontal rule never touches the text.
bracket_y = TOP_Y + 2.05
lx, rx = ON_X - 0.05, OFF_X + COL_W + 0.05
ax.plot([lx, lx, rx, rx], [bracket_y - 0.16, bracket_y, bracket_y, bracket_y - 0.16],
        color=INK, lw=1.0)
ax.text((lx + rx) / 2, bracket_y + 0.06, "fixed 12-slot context budget",
        ha="center", va="bottom", fontsize=10.5, color=INK)

# ---- annotation callouts (recall@k vs resolve), on legibility chips ----
# Solid "cards" floating over each stack: identical size + center-y so they read
# as a matched pair, a white keyline + soft shadow so the overlay is clearly
# intentional (not a clipped bar), and even side margins framing the card.
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe

CHIP_W = COL_W - 0.7      # even colored margin on both sides frames the card
CHIP_H = 1.6
CHIP_CY = (BASE_Y + TOP_Y) / 2


def chip(cx, cy, w, h, face):
    p = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                       boxstyle="round,pad=0.02,rounding_size=0.14",
                       facecolor=face, edgecolor="#ffffff", linewidth=2.0, zorder=5)
    p.set_path_effects([pe.withSimplePatchShadow(offset=(2, -2), alpha=0.28)])
    ax.add_patch(p)


on_cx = ON_X + COL_W / 2
chip(on_cx, CHIP_CY, CHIP_W, CHIP_H, "#2e3f4c")
ax.text(on_cx, CHIP_CY, "higher\nfile recall@k\n0.878", ha="center", va="center",
        fontsize=9.6, color="#ffffff", fontweight="bold", linespacing=1.25, zorder=6)
off_cx = OFF_X + COL_W / 2
chip(off_cx, CHIP_CY, CHIP_W, CHIP_H, "#1f2b33")
ax.text(off_cx, CHIP_CY, "higher\nresolve", ha="center", va="center", fontsize=10.2,
        color="#ffffff", fontweight="bold", linespacing=1.25, zorder=6)

# paradox arrow between the columns
mid_y = (BASE_Y + TOP_Y) / 2
arr = FancyArrowPatch((ON_X + COL_W + 0.18, mid_y), (OFF_X - 0.18, mid_y),
                      arrowstyle="-|>", mutation_scale=14, color=LINK, lw=1.4)
ax.add_patch(arr)
ax.text((ON_X + COL_W + OFF_X) / 2, mid_y + 0.45, "the paradox", ha="center",
        va="bottom", fontsize=9.2, style="italic", color=LINK)
ax.text((ON_X + COL_W + OFF_X) / 2, mid_y - 0.42, "+7.6pp\nresolve",
        ha="center", va="top", fontsize=9.0, color=LINK, linespacing=1.2)

plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
out = Path(__file__).resolve().parents[2] / "docs" / "paper" / "figures" / "recall_trap_hero.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=170, bbox_inches="tight", pad_inches=0.12, facecolor="white")
print(f"wrote {out} ({out.stat().st_size} bytes)")
