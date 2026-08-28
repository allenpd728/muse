"""A/B/C letter strip rendered under the piano roll (F2 #297).

Renders a single-axis letter-sequence strip (muse_form.FormCurve) colored by
A (green), B (amber), C (red) — tick-aligned with the piano-roll notes axis.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
from muse_form.form import FormCurve

LETTER_COLORS = {"A": "#3fb950", "B": "#d29922", "C": "#f85149"}


def render_form_track(curve: FormCurve, out: str, title: str | None = None):
    ax_rows = [w for w in curve.windows]
    fig, ax = plt.subplots(1, 1, figsize=(14, 1.2))
    for w in curve.windows:
        ax.bar(x=w.start, height=0.9, width=w.end - w.start,
               color=LETTER_COLORS[w.letter], edgecolor="none")
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlim(0, curve.windows[-1].end)
    ax.set_xlabel("tick", color="#8b949e")
    ax.set_title(title or f"{curve.work_id} form curve", fontsize=9)
    ax.set_facecolor("#0d1117")
    ax.spines["left"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    fig.savefig(out, dpi=110)
    plt.close(fig)
