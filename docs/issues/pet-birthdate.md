**Tier:** tier-1 (low) — validation only. Worst case if wrong: a form accepts or rejects a
date it shouldn't. No auth surface, no data migration, no money. Merges on green.

## Context

`PetValidator` requires `birthDate` to be present, but accepts any value. A pet can be
registered as born in 2087. Nothing downstream rejects it, so the bad row reaches the
database — and every age calculation built on that row is wrong from then on, silently.

This surfaces in the new-pet and edit-pet forms, which are the only paths that create
pets from user input. It has been possible since the form was introduced; we have no
evidence of it happening in production, but nothing would tell us if it had.

## Outcome

A pet can no longer be saved with a birth date in the future.

## Requirements

1. A birth date strictly after today must be rejected with error code
   `typeMismatch.birthDate`.
2. A birth date of today must be accepted — the boundary is inclusive.
3. A birth date in the past must continue to be accepted.
4. A missing birth date must continue to be rejected with error code `required`, and must
   not be reported as a future date.

## Test scenarios

```gherkin
Scenario: a birth date in the past is accepted
  Given a pet named "Leo" with birth date 2020-01-15
  When the pet is validated
  Then there are no errors on "birthDate"

Scenario: today is accepted
  Given a pet named "Leo" with a birth date of today
  When the pet is validated
  Then there are no errors on "birthDate"

Scenario: tomorrow is rejected
  Given a pet named "Leo" with a birth date of tomorrow
  When the pet is validated
  Then "birthDate" has error code "typeMismatch.birthDate"

Scenario: a missing birth date is still required
  Given a pet named "Leo" with no birth date
  When the pet is validated
  Then "birthDate" has error code "required"
```

## Constraints

- Do not modify existing tests.
- Change `PetValidator` only. Do NOT add constraints to the `Pet` entity — this is form
  validation, and the entity is shared with the import path.
- Reuse the existing `errors.rejectValue(field, code, message)` pattern.
- The boundary is inclusive: today is valid, tomorrow is not.

## Out of scope

- Any UI or template change. Server-side validation only.
- Backfilling or correcting existing rows that already hold future dates.
- Validating birth dates that are implausibly far in the past (e.g. 1850) — separate
  ticket if we want it.
