---
name: Unit of work
about: One self-contained change, small enough for a single agent session
title: ''
labels: 'tier-1'
---

<!--
RISK TIER — set the label, it decides how the change lands:
  tier-1  low     DTOs, mappers, validation, docs        -> gates decide, auto-merge
  tier-2  medium  CRUD endpoints, internal services      -> auto-merge, notify
  tier-3  high    authn/authz, payments, migrations, API -> PR + human sign-off, never auto
-->

## Outcome
<!-- One sentence. What is true after this ships that isn't true now? -->

## Acceptance criteria
```gherkin
Scenario:
  Given
  When
  Then
```

## Constraints
<!-- Files to touch, patterns to follow, and explicitly what NOT to change.
     "Do not modify existing tests" belongs here almost every time. -->

## Out of scope

## Definition of done
- [ ] `./mvnw verify` green (format, arch rules, tests, coverage)
- [ ] `./mvnw -Pmutation test` above threshold
- [ ] Tests named for behaviour, not method
