"""Generates the design-draft images (img/draft_*.png) used in the process book
and as placeholders on the site. Uses the cleaned data; drawn in 'sketch' style
on purpose so they read as drafts, not finished views."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data/el1000_clean.csv")
OUT = ROOT / "img"; OUT.mkdir(exist_ok=True)
BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#0b0b0b", "#898781"
AGE = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
BANDS = ["0–11 mo", "12–23 mo", "24–35 mo", "36–48 mo"]

# residual child speech after age, age^2, adult talk
X = np.column_stack([np.ones(len(df)), df.age_mo, df.age_mo**2, df.adult_voc_hr])
b, *_ = np.linalg.lstsq(X, df.child_voc_hr, rcond=None)
df["resid"] = df.child_voc_hr - X @ b

def ci(s):
    m = s.mean(); se = s.std(ddof=1) / np.sqrt(len(s)); return m, 1.96 * se

# ---- Draft A: background panels ----
with plt.xkcd(scale=0.6, length=120, randomness=1.5):
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), gridspec_kw={"width_ratios": [2, 2, 5]})
    panels = [("Sex", "sex", ["Girl", "Boy"]), ("Language", "language_bg", ["Monolingual", "Multilingual"]),
              ("Mother's education", "ses_code", [1, 2, 3, 4, 5])]
    labels5 = ["<HS", "HS", "Some\ncoll.", "College", "Adv."]
    for ax, (title, col, levels) in zip(axes, panels):
        for i, lv in enumerate(levels):
            s = df.loc[df[col] == lv, "resid"]; m, e = ci(s)
            ax.errorbar(i, m, yerr=e, fmt="o", color=INK, ms=8, capsize=6, lw=2)
            ax.text(i, -62, f"n={len(s)}", ha="center", fontsize=9, color=MUTED)
        ax.axhline(0, color=ORANGE, lw=2, ls="--")
        ax.set_xticks(range(len(levels)))
        ax.set_xticklabels(labels5 if col == "ses_code" else levels, fontsize=10)
        ax.set_ylim(-70, 70); ax.set_xlim(-0.6, len(levels) - 0.4); ax.set_title(title, fontsize=13)
    axes[0].set_ylabel("child voc./hr vs. expected\n(same age & adult talk)")
    fig.suptitle("DRAFT · Vis 4: 'Same age, same talk' comparison panels  (toggle: raw medians <-> adjusted)", fontsize=13)
    axes[2].annotate("dashed line = what age + adult talk\npredict; intervals crossing it =\nno clear difference", xy=(3, 0), xytext=(2.6, 45), fontsize=9,
                     arrowprops=dict(arrowstyle="->", color=MUTED))
    fig.tight_layout(); fig.savefig(OUT / "draft_background_panels.png", dpi=130); plt.close(fig)

# ---- Draft B: within-child slope chart ----
multi = df[df.n_recordings_child > 1]
pairs = []
for cid, g in multi.groupby("child_id"):
    if g.age_mo.max() - g.age_mo.min() > 2: continue          # same child, roughly same age
    lo, hi = g.loc[g.adult_voc_hr.idxmin()], g.loc[g.adult_voc_hr.idxmax()]
    if lo.recording_id == hi.recording_id: continue
    pairs.append((lo.child_voc_hr, hi.child_voc_hr, lo.age_band))
with plt.xkcd(scale=0.6, length=120, randomness=1.5):
    fig, ax = plt.subplots(figsize=(7, 5.2))
    up = 0
    for lo, hi, band in pairs:
        c = AGE[BANDS.index(band)]; up += hi > lo
        ax.plot([0, 1], [lo, hi], color=c, alpha=0.35, lw=1)
    ax.plot([0, 1], [np.median([p[0] for p in pairs]), np.median([p[1] for p in pairs])], color=ORANGE, lw=4)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["child's QUIETEST\nrecorded day", "child's most\nTALKATIVE day (adults)"])
    ax.set_ylabel("child voc./hr"); ax.set_xlim(-0.3, 1.3)
    ax.set_title(f"DRAFT · Vis 6: Same child, different days\n{up} of {len(pairs)} children say more on their high-talk day", fontsize=12)
    fig.tight_layout(); fig.savefig(OUT / "draft_within_child.png", dpi=130); plt.close(fig)

# ---- Draft C: quintile staircase (diminishing returns?) ----
with plt.xkcd(scale=0.6, length=120, randomness=1.5):
    fig, axes = plt.subplots(1, 4, figsize=(13, 4.2), sharey=True)
    for ax, band, c in zip(axes, BANDS, AGE):
        q = df[df.age_band == band].groupby("talk_quintile").child_voc_hr.median()
        ax.step(np.arange(1, 7) - 0.5, list(q.values) + [q.values[-1]], where="post", color=c, lw=3)
        for i, v in enumerate(q.values, 1): ax.text(i, v + 8, f"{v:.0f}", ha="center", fontsize=9)
        ax.set_title(band); ax.set_xticks(range(1, 6)); ax.set_xlabel("fifth of adult talk")
    axes[0].set_ylabel("median child voc./hr"); axes[0].set_ylim(0, 380)
    fig.suptitle("DRAFT · Vis 7: Talk staircase: does extra talk stop mattering?  (babies plateau; 3–4 yr olds keep climbing)", fontsize=12)
    fig.tight_layout(); fig.savefig(OUT / "draft_staircase.png", dpi=130); plt.close(fig)
print("drafts written", len(pairs), "pairs")
