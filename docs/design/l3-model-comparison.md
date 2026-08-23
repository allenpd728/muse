# L3 — Model comparison rig (design doc, scaffold)

**Phase 4 — The product. Status: scaffold.**

## Purpose

Same score + seed, different LLMs → different mockups → blind A/B listening.
The culture experiment: different models are different conductors, and the
format preserves the difference.

## Dependencies

- **Upstream:** L1 (harness), L2 (rendered comparison).
- **Downstream:** E1 (chooses the event's conductor), craft feedback to C2.

## Scope (pin in draft)

- **Inputs:** one `.mu`, N model endpoints.
- **Outputs:** comparable renders + listening page (spike listener
  graduated).
- **Non-goals:** automated musicality metrics (the founder's ear decides).

## Open questions

- Model roster; blinding protocol.

## Acceptance criteria (when promoted to draft)

- Produces comparable renders from 2+ models; blind listening recorded.
