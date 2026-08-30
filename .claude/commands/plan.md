---
description: Plan a unit of work — spec and tests before any implementation
---

Plan the following work. **Do not write or edit any production code in this session.**

$ARGUMENTS

Produce, in order:

1. **Outcome** — one sentence: what is true afterwards that isn't true now.
2. **Risk tier** — 1, 2 or 3, with one line of justification. Tier 3 stops here and waits
   for a human.
3. **Acceptance criteria** — Gherkin. Every boundary condition gets its own scenario.
   If you cannot express a requirement as a scenario, say so instead of guessing; that
   means the ticket is not ready.
4. **Blast radius** — every file you expect to touch, and why.
5. **The failing test you will write first** — the actual test name and what it asserts.
6. **Architecture check** — does this cross a slice boundary (`owner` <-> `vet`, or
   anything into `model`)? If yes, STOP and say so. That is a design decision, not an
   implementation detail.

Then stop and wait for approval. A plan that ends with code is not a plan.
