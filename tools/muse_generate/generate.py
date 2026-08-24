"""The generate → validate → fix loop.

assemble_prompt(seed, work) builds the LLM's instructions from S3 seed
fields + work structure (parts, maps) + era budgets. generate_mockup calls
the provider, validates the result against schema v1 + the work's
assertions, and retries up to max_attempts with the violation appended to
the prompt. Deterministic with a RecordedProvider.
"""

from __future__ import annotations

from muse_mockup.schema import SchemaError, validate_mockup_schema


class GenerateError(ValueError):
    """The loop exhausted its retries or the provider failed."""

    def __init__(self, message, violations=None):
        super().__init__(message)
        self.violations = violations or []


def assemble_prompt(seed, work, era="baroque", prior_violation=None):
    """Build the LLM prompt from the seed + work structure.

    The seed declares the sanctioned space (S3); the work is the fixed
    structure it must realize. Assertions and budgets bound the outcome.
    """
    parts_desc = ", ".join(f"{p.id} ({p.name}, {len(p.notes)} notes)" for p in work.parts)
    last_tick = max((n.onset + n.duration for p in work.parts for n in p.notes),
                    default=0)
    maps_desc = [f"  tick domain: 0..{last_tick} (ppq={getattr(work.meta, 'ppq', '?')}) "
                 f"— all ticks you emit must stay inside it"]
    if work.maps.tempo:
        marks = [f"  tempo: {len(work.maps.tempo)} marks, first {work.maps.tempo[0][1] / 100} bpm at tick {work.maps.tempo[0][0]}"]
        maps_desc.append(marks[0])
    if work.maps.meter:
        maps_desc.append(f"  meter: {work.maps.meter[0][1]}/{work.maps.meter[0][2]}")
    if work.maps.key:
        maps_desc.append(f"  key: {work.maps.key[0][1]} fifths, {work.maps.key[0][2]}")
    params = getattr(seed, "params", {})
    philosophy = getattr(seed, "philosophy", {})
    violations = prior_violation or []
    prompt = f"""You are the interpreter for a musical work. Produce a mockup (session file, schema v1) for:

work: {getattr(seed, 'work_id', 'unknown')}
parts: {parts_desc}
{chr(10).join(maps_desc)}

seed (the sanctioned space — stay inside it):
  params: {params}
  philosophy: {philosophy}
  era budget: {era}

Return ONLY valid JSON matching mockup schema v1 (exact shapes):
  work_id: string
  tempo_map: [{{"tick": int, "bpm": number > 0}}, ...] ordered by tick
  dynamics: [{{"tick": int, "level": 0..1}}, ...] optional, ordered by tick
  balance: [{{"part": part_id, "gain": number >= 0}}, ...] optional
  parts: {{part_id: [{{"i": int, "velocity": 1..127,
                        "attack_sec"?: number >= 0, "release_sec"?: number >= 0,
                        "swell"?: [[position 0..1, level 0..1], ...],
                        "onset_offset_ms"?: number}}]}}
  seed (embedded provenance object)

Constraints (violating any is a retry-level failure):
- preserve every score note's onset and pitch (fidelity guard)
- FULL coverage: one entry for EVERY note of every part (index i = the
  note's position in that part, 0-based, including repeated pitches) —
  a partial or exemplary mockup is a retry-level failure
- respect the seed's assertions and the era's measured budgets
- expressive devices (attack_sec, swell, onset_offset_ms) must stay within believable human ranges
{f'Prior violation to fix: {violations[0]!r}' if violations else ''}"""
    return prompt


def _validate(mockup, work):
    """Schema + assertions. Returns a list of violations (empty = pass)."""
    violations = []
    try:
        validate_mockup_schema(mockup)
    except SchemaError as e:
        violations.append(f"schema: {e}")
        return violations
    assertions = getattr(work, "assertions", None) or {}
    if not assertions:
        # tick domain: marks beyond the work's last tick are dead data —
        # the model guessed the wrong ppq (live-loop lesson, 2026-08-24)
        last_tick = max((n.onset + n.duration for p in work.parts for n in p.notes),
                        default=0)
        for field in ("tempo_map", "dynamics"):
            for e in mockup.get(field, []):
                if e.get("tick", 0) > last_tick:
                    violations.append(
                        f"fidelity: {field} tick {e['tick']} beyond the work's "
                        f"last tick {last_tick}")
        # score-fidelity: full DNA density (D9) — every score note must be
        # present, and every reference must land on a real pitched note
        parts = mockup.get("parts", {})
        for p in work.parts:
            expected = {j for j, n in enumerate(p.notes)
                        if n.pitch is not None and "unpitched" not in n.notations}
            got = {note.get("i") for note in parts.get(p.id, [])}
            missing = expected - got
            if missing:
                violations.append(
                    f"fidelity: {p.id} missing {len(missing)} of "
                    f"{len(expected)} notes (e.g. i={sorted(missing)[:3]})")
        for part_id, notes in parts.items():
            src = next((p for p in work.parts if p.id == part_id), None)
            for note in notes:
                if src is not None and note.get("i") is not None and note["i"] < len(src.notes):
                    ref = src.notes[note["i"]]
                    if ref.pitch is None:
                        violations.append(f"fidelity: {part_id}[{note['i']}] is a rest")
                else:
                    violations.append(f"fidelity: {part_id}[{note.get('i')}] out of range")
    return violations


def generate_mockup(seed, work, provider, era="baroque", max_attempts=3):
    """Run the loop. Returns (mockup, attempts). Fails loudly on exhaustion."""
    violations = []
    prompt = assemble_prompt(seed, work, era=era)
    for attempt in range(1, max_attempts + 1):
        try:
            mockup = provider.generate(prompt)
        except Exception as e:
            raise GenerateError(f"provider failed on attempt {attempt}: {e}",
                                violations=violations)
        violations = _validate(mockup, work)
        if not violations:
            return mockup, attempt
        prompt = assemble_prompt(seed, work, era=era, prior_violation=violations)
    raise GenerateError(
        f"mockup failed validation after {max_attempts} attempts",
        violations=violations,
    )
