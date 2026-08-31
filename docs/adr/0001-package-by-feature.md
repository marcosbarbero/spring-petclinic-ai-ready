# ADR 0001 — Package by feature, not by layer

**Status:** accepted · **Date:** 2026-08-30 · **Approved by:** Marcos Barbero (4a698c4)

## Context

Layered packages (`controller/`, `service/`, `repository/`) group code by what it *is*.
Every real change then touches three packages, and nothing tells you where a feature
begins or ends. Coding agents make this worse: with no boundary to respect, the shortest
path to compiling is always another import.

## Decision

Organise by feature slice: `owner`, `vet`, `system`, with `model` as a shared kernel.
A slice owns its entities, controllers, repositories and validators.

Slices must not depend on each other. `model` must not depend on any slice.

## Consequences

- A feature is one directory. Deleting it is one `rm -rf`.
- Cross-feature reuse becomes a visible decision instead of a quiet import — it either
  moves into `model` or gets a new shared slice, and either way somebody chose it.
- **Enforced, not documented.** `ArchitectureRulesTest` fails the build on violation.
  A rule that lives only in a wiki page is a rule that is already being broken.

## Notes for agents

If a change appears to require `owner` to know about `vet`, stop and say so. That is a
design conversation. Do not add the import and do not edit the rule.
