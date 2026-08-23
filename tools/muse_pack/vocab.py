"""Flag/articulation bitmasks shared between codec and rebuild. Kept here so
both sides reference the same vocabulary — a drift has test coverage."""

ARTICULATION_VOCAB = tuple(
    sorted(
        [
            "accent", "strong-accent", "staccato", "tenuto", "detached-legato",
            "staccatissimo", "spiccato", "scoop", "plop", "doit", "falloff",
            "breath-mark", "caesura", "stress", "unstress", "soft-accent",
            "other-articulation",
        ]
    )
)


def articulations_to_bits(items):
    bits = 0
    for item in items:
        if item in ARTICULATION_VOCAB:
            bits |= 1 << ARTICULATION_VOCAB.index(item)
    return bits


def bits_to_articulations(bits):
    return sorted(name for i, name in enumerate(ARTICULATION_VOCAB) if bits & (1 << i))
