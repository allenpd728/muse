# Test spec — #77: schema v0.3 mix topology

**Source task:** #77 (production/mixing terms: spec §2.6 v0.3 mix-topology
paragraph + `schema/renditions.schema.json` params.mix + r.chamber routes)
**Code under test:** `schema/renditions.schema.json` `params.mix`;
cross-ref of `routes[].bus` against declared `buses[].id` (a new refs-lint
surface, if the harness extends).

## Behaviors to verify

- **Acceptance:** r.chamber's mix block validates (harness examples scan —
  pin explicitly): group + send bus, three routes, one rangeable send level.
- **Rejection paths:**
  - bus missing `id` or `kind`; `kind` outside `group|send`
  - route missing `part` or `bus`
  - `send`/`amount` as a 3-element array or out-of-0..1 values (levelOrRange)
  - unknown property anywhere in the mix objects (all sealed)
- **Cross-ref lint surface (decision for the implementer):** `routes[].bus`
  should resolve against `buses[].id` — either extend `tools/refs.mjs`
  `danglingRefs` with this surface or pin that it's out of harness scope
  (rendition-internal, not material/section refs). Pick one and test it.
- **Spec ↔ schema parity:** `buses`, `routes`, `sidechains` keys named in
  §2.6's mix-topology bullets match the schema's `mix.properties` (same
  parse-the-spec pattern as role-vocabulary parity).

## How to run

Extend or sibling `tests/renditions.test.mjs`; `npm test` picks it up.

---

## Closed — 2026-08-22 (issue #87)

Coverage landed: `tests/mix-topology.test.mjs` — 18 checks:

- Acceptance: r.chamber's mix block explicitly, group+send buses with
  routes and rangeable send, scalar send/amount, sidechains.
- Rejection: bus missing id/kind, kind outside group|send, route missing
  part/bus, 3-element or out-of-range send/amount, sealed violations on
  bus/route/sidechain/mix.
- **Cross-ref decision (implementer's call, per the spec):** `routes[].bus`
  IS a harness lint surface — `tools/refs.mjs` `danglingRefs` extended:
  a route to an undeclared bus dangles (rendition-internal resolution).
  A `bus.ghost` route is flagged live; the full example's routes resolve.
- **Spec ↔ schema parity:** §2.6's mix-topology bullets (buses/routes/
  sidechains, written with nested backticks) set-equal the schema's
  `mix.properties`.

Run: `npm test`.
