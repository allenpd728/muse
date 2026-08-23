# muse_mockup — L1 mockup harness

Session file: tempo map, curves, velocities, balance, per-note devices
(chord spread, attack/release, swell). Generate → validate → fix loop,
validated by C1's validator. Design doc:
[docs/design/l1-mockup-harness.md](../../docs/design/l1-mockup-harness.md).

## Usage

```bash
python3 tools/muse_mockup/cli.py <work> [--out file.mockup.json]
```

Generates a complete mockup (all pitched notes, all parts) from the IR;
validates via muse_assert register bounds.

## Architecture

Iterator-safe getattr checks (sibling IR's None-pitch/sentinel field
handling); title-fidelity stays in naming (the L-series mocks are dense
DNA, not sketches, per the spike lesson).

## Tests

Test spec: [tests/open_20260823-235000_l1-mockup.md](../../tests/open_20260823-235000_l1-mockup.md).
