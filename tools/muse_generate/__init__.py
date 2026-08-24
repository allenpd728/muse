"""muse_generate — L1.3 generate → validate → fix loop (issue #208).

seed + score (IR) → prompt assembly → provider → mockup (schema v1) →
validate (schema + assertions) → bounded retry on violation. Stock model
steered by prompt; the assertion layer bounds generation; bounded retries
fail loudly with the violation record.

    from muse_generate.generate import generate_mockup
    mockup = generate_mockup(seed, work, provider)
"""

from .generate import GenerateError, assemble_prompt, generate_mockup

__all__ = ["GenerateError", "assemble_prompt", "generate_mockup"]
