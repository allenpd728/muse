"""Rehearsal directive compiler (R2, #283; grammar per R1 #282).

parse_directive: text → Directive (verb + operands).
compile_directive: Directive + base seed → candidate Seed (the compiled delta).
dry_run: candidate vs base → param_diff (seed-to-seed; no mockup).
commit_directive: write directive file + revision, stamp extends/operation.

The grammar compiles conductor language to existing seed knobs — it
invents no new format semantics (R1 format-first review).
"""

from __future__ import annotations

import copy
import hashlib
import os
import re
from dataclasses import dataclass, field


class DirectiveError(ValueError):
    """A directive fails the grammar (unknown verb, bad region, no part)."""


VERBS = ("rebalance", "phrase", "tempo_arch", "rubato", "hold")

# direction words → signed degree multiplier (fraction of the era budget
# midpoint shift); "up"/"down" pick the sign from the verb's axis.
_DIRECTIONS = {
    "up": 1.0, "louder": 1.0, "bring": 1.0, "lean-in": 1.0,
    "down": -1.0, "quieter": -1.0, "back-off": -1.0, "broader": -1.0,
}
_REGION_RE = re.compile(
    r"(?:region|at|into|on|ticks?)\s+(\d+)(?:\s*[-–]\s*(\d+))?")
_BAR_RE = re.compile(r"\bbars?\s+(\d+)(?:\s*[-–]\s*(\d+))?", re.IGNORECASE)


def bar_onsets(work) -> list:
    """Bar onset ticks from the IR meter map (R1: bars are computed, not
    stored). Walks `work.maps.meter` accumulating numerator×(4/denominator)×ppq
    ticks per bar. Raises DirectiveError if the work carries no meter map."""
    meter = getattr(getattr(work, "maps", None), "meter", None) or []
    if not meter:
        raise DirectiveError(
            "work carries no meter map — bar references can't be resolved "
            "(degenerate MIDI with no time signature)")
    ppq = work.meta.ppq
    meter = sorted(meter, key=lambda m: m[0])
    onsets = [0]
    cursor = 0
    for i, (tick, num, den) in enumerate(meter):
        next_tick = meter[i + 1][0] if i + 1 < len(meter) else work.duration_ticks()
        ticks_per_bar = round(num * (4 / den) * ppq)
        if ticks_per_bar <= 0:
            continue
        while cursor + ticks_per_bar <= next_tick:
            cursor += ticks_per_bar
            onsets.append(cursor)
    return onsets


@dataclass
class Directive:
    verb: str
    text: str
    parts: list = field(default_factory=list)
    direction: float = 0.0       # -1..1 signed degree; 0 = neutral (hold/tempo_arch settle)
    region: tuple = None         # (start_tick, end_tick) or None = whole work
    region_label: str = ""       # variation-point label when named
    shape: str = ""              # tempo_arch: wider|narrower|settle
    degree: float = None         # explicit numeric 0..1 when given


def parse_directive(text: str, seed=None, work=None) -> Directive:
    """Text → Directive. Raises DirectiveError on grammar violations."""
    text = text.strip()
    if not text:
        raise DirectiveError("empty directive")
    first = text.split(":", 1)[0].split()[0].lower().rstrip(":")
    if first not in VERBS:
        raise DirectiveError(
            f"unknown verb {first!r}; valid verbs: {', '.join(VERBS)}")
    rest = text[len(first):].lstrip(": ").strip()
    # one verb per directive (R1 parse rule)
    for v in VERBS:
        if v != first and re.search(rf"\b{v}\b", rest):
            raise DirectiveError(
                f"one verb per directive; found {first!r} and {v!r} — "
                "split into two directives")
    d = Directive(verb=first, text=text)
    d.region, d.region_label = _parse_region(rest, seed, work)
    d.parts = _parse_parts(rest, seed, work)
    d.direction, d.degree = _parse_direction(rest, first)
    if first == "tempo_arch":
        d.shape = _parse_shape(rest)
    return d


def _parse_region(rest, seed, work=None):
    """Region: a variation-point label, a bar reference (resolved via the
    IR meter map), or a tick range. Unresolvable → parse error."""
    bar = _BAR_RE.search(rest)
    if bar:
        if work is None:
            raise DirectiveError(
                "bar reference needs the work loaded (no meter map without it)")
        start_bar = int(bar.group(1))
        end_bar = int(bar.group(2)) if bar.group(2) else start_bar
        onsets = bar_onsets(work)
        if start_bar < 1 or start_bar > len(onsets):
            raise DirectiveError(
                f"bar {start_bar} out of range; the work has {len(onsets)} bars")
        start_tick = onsets[start_bar - 1]
        end_tick = (onsets[end_bar] if end_bar < len(onsets)
                    else work.duration_ticks())
        return (start_tick, end_tick), ""
    label = _match_variation_label(rest, seed)
    if label:
        return None, label
    m = _REGION_RE.search(rest)
    if m:
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start + 1
        return (start, end), ""
    return None, ""  # whole work


def _match_variation_label(rest, seed):
    if seed is None:
        return ""
    for vp in getattr(seed, "variation_points", []) or []:
        label = vp.get("label") if isinstance(vp, dict) else getattr(vp, "label", "")
        if label and re.search(rf"\b{re.escape(label)}\b", rest, re.IGNORECASE):
            return label
    return ""


def _parse_parts(rest, seed, work):
    """Named parts must exist (in the seed's part map or the work)."""
    found = re.findall(r"\b(P\d+|celli?|violin[s]?|viola[s]?|horn[s]?|flute[s]?|oboe[s]?|bass(?:es)?|soprano|alto|tenor)\b",
                       rest, re.IGNORECASE)
    if not found:
        return []
    known = set()
    if work is not None:
        known |= {getattr(p, "id", "") for p in getattr(work, "parts", [])}
    if seed is not None:
        known |= set(getattr(seed, "params", {}).get("part_gains", {}) or [])
    if known:
        bad = [p for p in found if p not in known and not p.lower().startswith("p")]
        # instrument names (celli, horns) are aliases; only hard-fail Pn ids
        bad = [p for p in found if re.fullmatch(r"P\d+", p) and p not in known]
        if bad:
            raise DirectiveError(
                f"unknown part(s) {bad}; the work has {sorted(known)}")
    return found


def _parse_direction(rest, verb):
    degree = None
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", rest)
    if m:
        degree = min(1.0, float(m.group(1)) / 100.0)
    for word, sign in _DIRECTIONS.items():
        if re.search(rf"\b{re.escape(word)}\b", rest, re.IGNORECASE):
            return sign, degree
    return 0.0, degree  # neutral (hold, tempo_arch settle)


def _parse_shape(rest):
    for shape in ("wider", "narrower", "settle"):
        if re.search(rf"\b{shape}\b", rest, re.IGNORECASE):
            return shape
    return "wider"


def compile_directive(directive: Directive, seed, era="baroque", work=None):
    """Directive + base seed → candidate Seed (the compiled delta)."""
    from muse_seed.params import ERA_BUDGETS

    candidate = copy.deepcopy(seed)
    budget = ERA_BUDGETS.get(era, ERA_BUDGETS["baroque"])
    if directive.verb == "rebalance":
        _apply_rebalance(candidate, directive)
    elif directive.verb == "phrase":
        _apply_phrase(candidate, directive, work)
    elif directive.verb == "tempo_arch":
        _apply_tempo_arch(candidate, directive, budget)
    elif directive.verb == "rubato":
        _apply_rubato(candidate, directive, budget)
    elif directive.verb == "hold":
        _apply_hold(candidate, directive)
    return candidate


def _degree_or_default(directive, default=0.1):
    return directive.degree if directive.degree is not None else default


def _apply_rebalance(seed, d):
    gains = seed.params.setdefault("part_gains", {})
    delta = _degree_or_default(d) * (d.direction or 1.0)
    for part in d.parts or ["all"]:
        gains[part] = round(max(0.0, min(2.0, gains.get(part, 1.0) + delta)), 3)


def _apply_phrase(seed, d, work=None):
    region = list(d.region) if d.region else None
    if region is None:
        # whole-work: a phrase directive with no region names the full
        # tick extent (S3.4 forbids empty regions — [0,0) is invalid).
        extent = work.duration_ticks() if work is not None else 1
        region = [0, max(1, extent)]
    vp = {"region": region, "kind": "tempo_flex",
          "budget": _degree_or_default(d, 0.2), "assertions": {}}
    if d.region_label:
        vp["label"] = d.region_label
    seed.variation_points = list(getattr(seed, "variation_points", []) or []) + [vp]


def _apply_tempo_arch(seed, d, budget):
    tempo = seed.params.setdefault("tempo", {})
    default = tempo.get("default_bpm", 96)
    nominal = budget["tempo_pct"] * default
    widen = 1.0 + _degree_or_default(d) * (1.0 if d.shape == "wider" else -0.5)
    if d.shape == "settle":
        widen = 1.0 - _degree_or_default(d)
    tempo["min_bpm"] = max(30, round(default - nominal * widen))
    tempo["max_bpm"] = min(300, round(default + nominal * widen))


def _apply_rubato(seed, d, budget):
    art = seed.params.setdefault("articulation", {})
    base = art.get("rubato_pstdev_ms", 0.0) or budget["chord_spread_ms"]
    art["rubato_pstdev_ms"] = round(base * (1.0 + (d.direction or 1.0) * _degree_or_default(d)), 2)


def _apply_hold(seed, d):
    tempo = seed.params.get("tempo", {})
    default = tempo.get("default_bpm", 96)
    seed.assertions = dict(getattr(seed, "assertions", {}) or {})
    seed.assertions["tempo_bounds"] = {
        "min_bpm": round(default * 0.97), "max_bpm": round(default * 1.03)}


def dry_run(directive: Directive, base_seed, era="baroque", work=None):
    """Compile + param_diff (seed-to-seed, no mockup). Returns
    (candidate, diff). Writes nothing."""
    from muse_probes.probes import probe_param_diff
    candidate = compile_directive(directive, base_seed, era, work)
    return candidate, probe_param_diff(candidate, base_seed)


def commit_directive(directive: Directive, base_seed_path: str, slug: str,
                     out_seed_path: str = None, era="baroque", repo_root: str = None,
                     work=None):
    """Write the directive file + the compiled revision, stamping lineage.

    Directive file: seeds/<work>.directives/<slug>.directive.txt (R1).
    Revision extends = sha256(directive bytes); operation = muse_rehearse@1.
    Returns (directive_path, revision_path).
    """
    from muse_seed import load_seed, dump_seed
    from muse_lineage.lineage import sha256_file

    repo = repo_root or os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", ".."))
    base_seed = load_seed(open(base_seed_path).read(), fmt="yaml")
    work_id = base_seed.work_id
    directives_dir = os.path.join(repo, "seeds", f"{work_id}.directives")
    os.makedirs(directives_dir, exist_ok=True)
    directive_path = os.path.join(directives_dir, f"{slug}.directive.txt")
    with open(directive_path, "w") as fh:
        fh.write(directive.text + "\n")

    candidate = compile_directive(directive, base_seed, era, work)
    candidate.provenance = dict(getattr(candidate, "provenance", {}) or {})
    candidate.provenance["extends"] = sha256_file(directive_path)
    candidate.provenance["operation"] = "muse_rehearse@1"
    candidate.provenance.setdefault("source",
                                    base_seed.provenance.get("source", ""))
    candidate.provenance.setdefault("author",
                                    base_seed.provenance.get("author", ""))
    candidate.provenance.setdefault("ai_assisted",
                                    base_seed.provenance.get("ai_assisted", True))

    if out_seed_path is None:
        existing = [f for f in os.listdir(os.path.join(repo, "seeds"))
                    if re.fullmatch(rf"{re.escape(work_id)}\.v\d+\.seed\.yaml", f)]
        n = max([int(re.search(r"\.v(\d+)\.", f).group(1)) for f in existing] or [0]) + 1
        out_seed_path = os.path.join(repo, "seeds", f"{work_id}.v{n}.seed.yaml")
    with open(out_seed_path, "w") as fh:
        fh.write(dump_seed(candidate, fmt="yaml"))
    return directive_path, out_seed_path
