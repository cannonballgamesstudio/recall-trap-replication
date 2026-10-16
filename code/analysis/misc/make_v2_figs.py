import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
OUT = "results/figures/"
plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif","Liberation Serif","Times New Roman"], "font.size": 9, "pdf.fonttype": 42, "ps.fonttype": 42, "mathtext.fontset": "dejavuserif"})

# ---- Forest: wild-cluster (Webb) 95% CIs, from t1_clustered.md ----
rows = [  # label, delta, lo, hi, class
    ("Qwen3.6-27B (P)", 3.61, 0.5, 5.2, "conf"),
    ("gpt re-run (P)", 5.40, 3.2, 11.3, "conf"),
    ("gpt discovery (D)", 7.60, -2.5, 15.8, "disc"),
    ("DeepSeek-v4 (D)", 6.21, 3.2, 11.6, "supp"),
    ("gpt, dense (PP)", 5.67, -2.2, 10.5, "ctrl"),
    ("gpt, BM25 (E)", -3.20, -7.1, 0.2, "ctrl"),
]
sty = {"conf": dict(color="#1f4e79", marker="o", mfc="#1f4e79"),
       "disc": dict(color="#1f4e79", marker="o", mfc="white"),
       "supp": dict(color="#3d6f73", marker="s", mfc="#3d6f73"),
       "ctrl": dict(color="#6f6f6f", marker="D", mfc="white")}
fig, ax = plt.subplots(figsize=(3.45, 2.2))
n = len(rows)
for i, (lab, d, lo, hi, c) in enumerate(rows):
    y = n - 1 - i
    s = sty[c]
    ax.plot([lo, hi], [y, y], color=s["color"], lw=1.4)
    ax.plot([d], [y], marker=s["marker"], color=s["color"], mfc=s["mfc"], ms=5, mew=1.2)
    ax.text(20.5, y, f"{d:+.1f}", va="center", ha="right", fontsize=7.5)
ax.axvline(0, ls="--", color="k", lw=0.8)
ax.axhline(3.5, color="#bbbbbb", lw=0.6)
ax.set_yticks(range(n))
ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=7.5)
ax.set_xlim(-8.5, 20.8)
ax.set_xticks([-5, 0, 5, 10, 15])
ax.set_ylim(-0.6, n - 0.4)
ax.set_xlabel(r"$\Delta$ resolve, OFF $-$ ON (pp)", fontsize=8)
ax.tick_params(axis="x", labelsize=7.5)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
fig.subplots_adjust(left=0.37,right=0.99,top=0.98,bottom=0.19)
fig.savefig(OUT + "forest_v2.pdf")
fig.savefig(OUT + "forest_v2.png", dpi=200)

# ---- Pack schematic: ON / T / OFF ----
fig, ax = plt.subplots(figsize=(3.45, 1.75))
ax.set_xlim(0, 30)
ax.set_ylim(-0.6, 13.6)
ax.axis("off")
cols = ["#4a6fa5", "#8a5a44", "#5f7d55", "#8c6d3a", "#3e6e74"]


def slot(x, y, c, w=7.2, h=0.78):
    ax.add_patch(Rectangle((x, y), w, h, color=c, lw=0))


for k in range(12):
    slot(1, 11.6 - k * 0.98, cols[k] if k < 5 else "#b4bfcc")
for k in range(5):
    slot(11.4, 11.6 - k * 0.98, cols[k])
y = 11.6
for f, m in enumerate([1, 2, 2, 3, 4]):
    for j in range(m):
        slot(21.8, y, cols[f])
        y -= 0.98
ax.text(4.6, 12.9, "dedup-ON", ha="center", weight="bold", fontsize=8.5)
ax.text(15.0, 12.9, "trimmed breadth T", ha="center", weight="bold", fontsize=8.5)
ax.text(25.4, 12.9, "dedup-OFF", ha="center", weight="bold", fontsize=8.5)
ax.annotate("", xy=(11.0, 6.3), xytext=(8.6, 6.3), arrowprops=dict(arrowstyle="->", lw=0.9))
ax.annotate("", xy=(21.4, 6.3), xytext=(19.0, 6.3), arrowprops=dict(arrowstyle="->", lw=0.9))
ax.text(9.8, 7.0, "trim", ha="center", fontsize=7, style="italic")
ax.text(20.2, 7.0, "depth", ha="center", fontsize=7, style="italic")
fig.tight_layout(pad=0.1)
fig.savefig(OUT + "packs_v2.pdf")
fig.savefig(OUT + "packs_v2.png", dpi=200)
print("ok")
