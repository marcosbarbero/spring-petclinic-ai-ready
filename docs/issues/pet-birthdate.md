**Tier:** tier-1 — validation only, no auth surface, no data migration. Gates decide; auto-merge eligible.

## Outcome

A pet can no longer be saved with a birth date in the future.

## Acceptance criteria

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
  validation and the entity is shared with the import path.
- Reuse the existing `errors.rejectValue(field, code, message)` pattern.
- The boundary is inclusive: today is valid, tomorrow is not.

## Out of scope

- Any UI or template change. Server-side validation only.
- Backfilling existing rows with bad dates.
