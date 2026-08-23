"""muse_probes — W-B1 seed-iteration probe engine (issue #185).

Per seed revision, compute the probe set (param diff, budget fit, assertion
pass/fail, mockup coverage, delta curves, determinism, score-fidelity
guard) and emit a deterministic JSON artifact the workbench page renders.
Read-only over the S3/C1/C3/L1 toolchain; nothing new is generated.
"""

from .probes import ProbeError, ProbeReport, compute_probes

__all__ = ["ProbeError", "ProbeReport", "compute_probes"]
