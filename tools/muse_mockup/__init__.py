"""muse_mockup — L1 mockup harness (session file: tempo, curves, velocities, balance).

Generate → validate → fix loop, bounded retries. Validated against seed
assertions. The mockup is dense DNA, not sketches (spike lesson).
"""

from .mockup import Note, Mockup, add_note, validate_mockup, dump_mockup, load_mockup, MockupError

__all__ = ["Note", "Mockup", "add_note", "validate_mockup", "dump_mockup", "load_mockup", "MockupError"]
