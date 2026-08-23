"""muse_assert — S3.5 assertions validator.

Assertion vocabulary: must_contain, register, form, invariants. A
performance (mockup/event stream) validates against a seed's assertions;
fail loudly on violation.
"""

from .asserts import validate_assertions, AssertionError

__all__ = ["validate_assertions", "AssertionError"]
