# Lexicon — how we solved this before

<!-- GENERATED FROM mapping.json BY .claude/tools/lexicon.py — DO NOT EDIT. -->
<!-- Regenerate: .claude/tools/lexicon.py readme                            -->

Durable memory for recurring problems. Every entry is something that was once
worked out the hard way, written down so it is never worked out again.

Agents should not read this file — they use `lexicon.py search <term>`, which
is cheaper and returns only the relevant entry.

| key | problem | solution |
|---|---|---|
| `checkstyle-needs-execution-id` | Running ./mvnw checkstyle:check reports hundreds of violations that the normal build never mentions. | Invoke the project's execution by id: ./mvnw checkstyle:check@nohttp-checkstyle-validation (or @quality-checkstyle-validation). |
| `clock-dependent-tests` | A test computing 'today' or 'tomorrow' against code that calls LocalDate.now() can fail if the clock rolls over mid-run. | Accept it for a small validator; inject a Clock only when the ripple is worth it. Either way, flag it in the PR rather than leaving it silent. |
| `docker-tests-must-be-opt-in` | ./mvnw verify fails on a fresh clone with 'docker compose up' errors, on a machine where Docker is fine. | Exclude *IntegrationTests from the default surefire run; restore them with -Pcontainers, which CI uses. |
| `form-validation-lives-in-validator` | Adding a rule to a form and reaching for a jakarta.validation annotation on the entity. | Put form rules in the slice's Validator (e.g. PetValidator). Leave the entity's annotations alone. |
| `inclusive-date-boundary` | A date rule says "must not be in the future" and the boundary is ambiguous: is today allowed? | Default to inclusive — today valid, tomorrow invalid — and use isAfter(LocalDate.now()). Say so explicitly in the ticket. |
| `mutation-survivor-means-no-assertion` | Coverage is high, the mutation gate fails, and it is unclear what to add. | Run .claude/tools/mutation_survivors.py. For each survivor, assert the behaviour the mutation changed — do not add more tests that merely call the method. |
| `pit-needs-1-19-on-jdk-21` | ./mvnw -Pmutation verify dies with 'Coverage generator Minion exited abnormally due to UNKNOWN_ERROR'. | Use pitest-maven 1.19.6 with pitest-junit5-plugin 1.2.3. |
| `spring-error-codes-are-expanded` | A test asserts a field error code equals the one passed to errors.rejectValue(...), and fails with a longer, unfamiliar code. | Assert that FieldError.getCodes() CONTAINS your code. Do not assert getCode() equals it. |

## Adding an entry

Write one whenever something was non-obvious, surprising, or cost you a wrong
turn. The bar is low on purpose — a minute now, recalled forever.

```bash
.claude/tools/lexicon.py add \
  --key spring-error-codes-are-expanded \
  --title "..." --problem "..." --solution "..." --why "..." \
  --tags spring,validation
```
