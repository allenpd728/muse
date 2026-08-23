"""muse_author — C2: AI-assisted authoring workbench.

LLM analyzes IR → proposes a seed draft. Generate → validate → fix loop,
validated by C1's validator. Bounded retries, fail loudly.
"""

from .author import propose_seed, AuthorError

__all__ = ["propose_seed", "AuthorError"]
