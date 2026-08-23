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


@dataclass
class RenderResult:
    path: str
    parts_rendered: list            # part ids actually drawn
    events: int                     # note events drawn


def pitch_value(note) -> int:
    """Map a note to its piano-roll y. None-pitch events (rests/unpitched)
    map to sentinels: rest -1, unpitched -2. The landed IR (tools/ir) marks
    unpitched percussion via the 'unpitched' notation flag."""
    if note.pitch is None:
        return -2 if "unpitched" in note.notations else -1
    return note.pitch


def build_title(work, part_ids, n_events) -> str:
    label = getattr(work, "title", None) or ""
    return f"{label} ({len(part_ids)} parts, {n_events} events)"


def render(work, config: PianoRollConfig | None = None):
    """Render work.parts to PNG; return a RenderResult."""
    cfg = config or PianoRollConfig()
    parts = cfg.parts if cfg.parts else [p.id for p in work.parts]

    _, n_count = 0, 0
    rendered = []
    fig_h = min(cfg.max_height_in, max(2.0, len(parts) * 1.2))
    fig, axes = plt.subplots(len(parts), 1, figsize=(14, fig_h), sharex=False)
    if len(parts) == 1:
        axes = [axes]

    cmap = plt.get_cmap("tab20")
    for ax, pid in zip(axes, parts):
        part = next((p for p in work.parts if p.id == pid), None)
        if part is None:
            continue
        rendered.append(pid)
        y = [pitch_value(n) for n in part.notes]
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
    fig.suptitle(cfg.title or build_title(work, parts, n_count), fontsize=10)
    fig.tight_layout()
    fig.savefig(cfg.out, dpi=110)
    plt.close(fig)
    return RenderResult(path=cfg.out, parts_rendered=rendered, events=n_count)
