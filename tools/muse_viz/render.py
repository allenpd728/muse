"""Piano-roll renderer for W1 IR. matplotlib; no runtime service deps."""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


@dataclass
class PianoRollConfig:
    parts: list | None = None       # subset of part ids to render
    out: str = "piano_roll.png"
    title: str | None = None
    max_height_in: float = 12.0
    alpha: float = 0.6              # per-note alpha (thinning on dense works)


def render(work, config: PianoRollConfig | None = None):
    """Render work.parts to PNG; return the output path."""
    cfg = config or PianoRollConfig()
    parts = cfg.parts if cfg.parts else [p.id for p in work.parts]

    _, n_count = 0, 0
    fig_h = min(cfg.max_height_in, max(2.0, len(parts) * 1.2))
    fig, axes = plt.subplots(len(parts), 1, figsize=(14, fig_h), sharex=False)
    if len(parts) == 1:
        axes = [axes]

    cmap = plt.get_cmap("tab20")
    for ax, pid in zip(axes, parts):
        part = next((p for p in work.parts if p.id == pid), None)
        if part is None:
            continue
        # robust to None-pitch rests/unpitched (sibling IR) — map to -1/-2
        vals = []
        for n in part.notes:
            p_ = n.pitch
            if p_ is None:
                p_ = -2 if getattr(n, "is_unpitched", False) else -1
            vals.append(p_)
        y = vals
        x0 = [n.onset for n in part.notes]
        w_ = [max(n.duration, 1) for n in part.notes]
        n_count += len(y)
        ax.bar(x0, [1] * len(y), width=w_, bottom=[v - 0.5 for v in y],
               color=cmap(hash(pid) % 20), alpha=cfg.alpha, edgecolor="none")
        ax.set_ylabel(pid, fontsize=7)
        ax.set_yticks([])
        if y and any(v >= 0 for v in y):
            ax.set_ylim(min(y) - 5, max(y) + 5)

    axes[-1].set_xlabel("onset (ticks)")
    title = cfg.title or f"{getattr(work, 'title', None) or ''} ({len(parts)} parts, {n_count} events)"
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(cfg.out, dpi=110)
    plt.close(fig)
    return cfg.out
