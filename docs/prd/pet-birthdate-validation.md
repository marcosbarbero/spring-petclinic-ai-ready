# PRD — Reject future birth dates for pets

**Status:** ready · **Slice:** `owner` · **Risk tier:** 1 (low — validation only, no data
migration, no auth surface). Tier 1 means the gates decide; no human sign-off required.

## Problem

`PetValidator` requires `birthDate` to be present, but accepts any value. A pet can be
registered as born in 2087. Nothing downstream rejects it, so the bad row reaches the
database and every age calculation built on it is wrong from then on.

## Outcome

A pet cannot be saved with a birth date later than today.

## Acceptance criteria

```gherkin
Feature: Pet birth date must not be in the future

  Scenario: a birth date in the past is accepted
    Given a pet named "Leo" with birth date 2020-01-15
    When the pet is validated
    Then there are no errors on "birthDate"

  Scenario: today is accepted
    Given a pet named "Leo" with birth date of today
    When the pet is validated
    Then there are no errors on "birthDate"

  Scenario: tomorrow is rejected
    Given a pet named "Leo" with birth date of tomorrow
    When the pet is validated
    Then "birthDate" has error code "typeMismatch.birthDate"

  Scenario: a missing birth date is still required
    Given a pet named "Leo" with no birth date
    When the pet is validated
    Then "birthDate" has error code "required"
```

## Constraints

- Change `PetValidator` only. Do **not** add constraints to the `Pet` entity — this is
  form validation, and the entity is shared with the import path.
- Reuse the existing `errors.rejectValue(field, code, message)` pattern already in the
  class.
- Do not modify existing tests. Add new ones to `PetValidatorTests`.
- The boundary is inclusive: **today is valid, tomorrow is not.** Get this wrong and
  mutation testing will catch it.

## Out of scope

- Any UI/template change. Server-side validation only.
- Backfilling or correcting existing bad rows.

## Definition of done

- `./mvnw verify` green, including the architecture rules and the coverage gate.
- `./mvnw -Pmutation test` ≥ 75% on `owner`.
- Tests name the behaviour, not the method.
