# S3 — Decomposed sub-tasks (design doc)

**Phase 1 — Format spec. Status: draft.** S3 (the critical-path spec) broken
into sub-tasks an agent can claim in one run; each has a **tester/validator**
hook per the C-series validator-session plan.

$$
\text{S3 (aggregating)}\;=\;\text{S3.container}\;+\;\text{S3.parameters}\;+\;\text{S3.philosophy}\;+\;\text{S3.variation}\;+\;\text{S3.assertions}\;+\;\text{S3.example-work}
$$

## Sub-tasks (each claimable ~ under an hour)

| Sub-task | Scope | Validator/tester hook |
|---|---|---|
| **S3.1 — Container & encoding** | YAML-or-JSON subset; top-level key schema; machine/development encoding; byte-fair; C1 format of seed bytes | Spec-level schema check: C1 reads/writes valid bytes |
| **S3.2 — Parameters + ranges** | tempo/energy/density/variation fields with calibrated bounds (Vienna/Magaloff/delta) | Budget validator: ranges authored within measured ranges |
| **S3.3 — Philosophy fields** | typed-lite vocab (style/era/practice) + free-text escape; provenance | Philosophy-vocabulary validator |
| **S3.4 — Variation points** | region/kind/budget/assertions structure | Constraint schema validator |
| **S3.5 — Assertions** | must_contain / register / form / invariants | Assertion validator: mockup fail-if-unsatisfied |
| **S3.6 — Example seed** | Bach chorale fragment or Byrd Kyrie seed exercising the Schema | Self-validates |

Sub-tasks are independent (any of #1–#5 can claim in parallel); the
three-legged sequence is: parameters ranges → philosophy → example seed
(else the example carries unfaithful budgets).

## Critical-path note

S3_2 (parameters + budgets) is the critical-path head toward C1's
validator; it calibrates mockups it then validates. C2's generator-
validator loop, C3's budget-suggestion engine, all a
C1-reader/writer + C1-validator micro-pipeline consumes.
