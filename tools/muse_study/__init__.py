"""muse_study — R3 conductor-training study scripts + directive-survival feedback.

Design: docs/design/r1-rehearsal-directives.md §What R3 builds. A study
script is a precomposed directive sequence keyed to a known interpretive
issue ("quiet the cellos into the development"); the survival check asks,
per directive, whether the compiled delta actually shows up in the
mockup's measured interpretation — that's how the ear gets trained
without live musicians.
"""

from .study import (  # noqa: F401
    StudyError,
    SCRIPTS,
    run_script,
    check_survival,
    VERB_MEASURES,
)

__all__ = ["StudyError", "SCRIPTS", "run_script", "check_survival",
           "VERB_MEASURES"]
