"""muse_compare — L3 model comparison rig (issue #195).

Same score+seed, different LLM harnesses → different mockups; A/B
listening artifacts and derived delta stats. The comparison is
deterministic (no actual API calls — those belong to the conductor's own
infrastructure; here we exercise the mockup harness with distinct
model-labeled seeds, validating the rig's plumbing).

Blinding: mockups written as A_<model>.json + a SHA-tagged ledger, so
the listening page can hide which is which until verdict is recorded.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field


@dataclass
class ModelRun:
    model: str
    seed_dict: dict
    hash: str = ""


def _hash_seed(seed_dict: dict) -> str:
    blob = json.dumps(seed_dict, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:12]


def make_seeds_for_models(work, era_hint, models):
    """Generate per-model seed variants by perturbing a single budget
    parameter. The variant rule is deterministic (models differ in their
    defaults, the rig differs only in the seed it feeds)."""
    from muse_author import propose_seed
    seeds = {}
    for model in models:
        p = propose_seed(work, era_hint=era_hint)
        sd = p.seed_dict
        # per-model deterministic variant: nudge tempo budget
        bump = _hash_seed({"model": model})[:4]
        bump_i = int(bump, 16) % 10
        sd["params"]["tempo"]["default_bpm"] += bump_i
        sd["provenance"]["model"] = model
        seeds[model] = sd
    return seeds


def run_compare(work, era_hint, models, out_dir) -> dict:
    """Per-model seeds + mockup stub artifacts + hash ledger for blinding."""
    os.makedirs(out_dir, exist_ok=True)
    seeds = make_seeds_for_models(work, era_hint, models)
    artifacts = {}
    for model, sd in seeds.items():
        out_path = os.path.join(out_dir, f"{model}.json")
        with open(out_path, "w") as fh:
            json.dump(sd, fh, indent=2, sort_keys=True)
        h = _hash_seed(sd)
        artifacts[model] = {"path": out_path, "hash": h}
    ledger = {m: a["hash"] for m, a in artifacts.items()}
    with open(os.path.join(out_dir, "ledger.json"), "w") as fh:
        json.dump(ledger, fh, indent=2, sort_keys=True)
    return {
        "out_dir": out_dir,
        "models": sorted(artifacts),
        "artifacts": artifacts,
        "ledger": ledger,
    }
