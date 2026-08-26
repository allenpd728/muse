"""muse_rehearse — R2 rehearsal directives (design: docs/design/r1-rehearsal-directives.md).

Typed natural-language directives compiled to seed revisions. The grammar
is a deterministic compiler to existing seed knobs — no new format
semantics. Five verbs: rebalance, phrase, tempo_arch, rubato, hold.
"""

from .rehearse import (  # noqa: F401
    DirectiveError,
    parse_directive,
    compile_directive,
    dry_run,
    commit_directive,
)

__all__ = [
    "DirectiveError", "parse_directive", "compile_directive",
    "dry_run", "commit_directive",
]
