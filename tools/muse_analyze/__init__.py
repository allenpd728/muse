"""muse_analyze — W3 pattern analyzer.

IR → pattern report: exact/transposed repeats, sequences, mirror/retrograde
candidates, ostinati, imitative entries. Per-phrase delta curves. Full-corpus
→ docs/analysis-report.md. Algorithms: point-set (onset, pitch) matching per
SIATEC tradition; rhythm algorithms as complement.
"""

from .patterns import analyze, PatternReport

__all__ = ["analyze", "PatternReport"]
