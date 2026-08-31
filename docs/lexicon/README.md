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
| `clock-dependent-tests` | A test computing 'today' or 'tomorrow' against code that calls LocalDate.now() can fail if the clock rolls over mid-run. | For a test that only needs *a* date, use a literal: LocalDate.of(2020, 1, 15). This is now enforced — see deterministic-test-dates — so it is not a preference.

For a test that must control what production believes 'today' is, a literal is not enough on its own, because production reads the clock internally. Production has to take an injected Clock. Whether to do that is a judgement call about ripple: injecting Clock into PetValidator means changing PetController, which constructs it with new PetValidator(). Under a 'change PetValidator only' constraint that is out of scope, and a known, stated limitation beats an unrequested refactor — but say so in the PR rather than leaving it silent. |
| `deterministic-test-dates` | A test that needs a date reaches for LocalDate.now(), Instant.now(), new Date() or System.currentTimeMillis(). It passes locally and is dated by whenever it happened to run, so it fails at a midnight rollover or in another timezone, on a machine nobody is watching. Because the failure is intermittent it reads as a flake and gets re-run rather than fixed. Writing the test this way is the default reflex, so knowing the rule after the fact does not help - it has to be known BEFORE the test is written. | Use a literal date: LocalDate.of(2020, 1, 15). If the test needs to control what PRODUCTION thinks today is - a boundary test for 'not in the future', say - a literal is not enough on its own, because production calls LocalDate.now() internally; production must take an injected java.time.Clock and the test passes Clock.fixed(instant, ZoneOffset.UTC). If a call genuinely must read the wall clock, end the line with '// allow-wall-clock: <reason>'; the marker requires a reason, not a bare tag. This is enforced by .claude/tools/check_wall_clock_in_tests.py, bound to the validate phase, so ./mvnw verify fails on a new violation. |
| `docker-tests-must-be-opt-in` | ./mvnw verify fails on a fresh clone with 'docker compose up' errors, on a machine where Docker is fine. | Exclude *IntegrationTests from the default surefire run; restore them with -Pcontainers, which CI uses. |
| `duplicated-validation-resurrects-mutants` | PetController.processCreationForm (L115-118) and processUpdateForm (L158-161) already contained an inline 'birthDate is after LocalDate.now()' check with the same typeMismatch.birthDate code. After adding the same rule to PetValidator, PIT's 'removed call to BindingResult::rejectValue' mutant at PetController L117 flipped from KILLED to SURVIVED: with two code paths producing the same rejection, deleting one no longer changes any observable outcome, so the controller test could not tell. The survivor appears in a file the change never touched, which reads like an unrelated regression. | Before implementing a validation rule, grep the slice for the same error code (grep -rn 'typeMismatch.birthDate' src/main/java) - a duplicate elsewhere means the new mutation survivor is expected, not a gap in your tests. Confirm your own code is clean by listing the class's mutants directly from target/pit-reports/mutations.xml rather than only reading the survivor summary, then report the redundant path as a scope decision for the reviewer instead of silently deleting it. |
| `form-validation-lives-in-validator` | Adding a rule to a form and reaching for a jakarta.validation annotation on the entity. | Put form rules in the slice's Validator (e.g. PetValidator). Leave the entity's annotations alone. |
| `inclusive-date-boundary` | A date rule says "must not be in the future" and the boundary is ambiguous: is today allowed? | Default to inclusive — today valid, tomorrow invalid — and use isAfter(LocalDate.now()). Say so explicitly in the ticket. |
| `mutation-survivor-means-no-assertion` | Coverage is high, the mutation gate fails, and it is unclear what to add. | Run .claude/tools/mutation_survivors.py. For each survivor, assert the behaviour the mutation changed — do not add more tests that merely call the method. |
| `pit-needs-1-19-on-jdk-21` | ./mvnw -Pmutation verify dies with 'Coverage generator Minion exited abnormally due to UNKNOWN_ERROR'. | Use pitest-maven 1.19.6 with pitest-junit5-plugin 1.2.3. |
| `pr-tool-owns-create-and-update` | open_pr.py validated a PR body against the issue's Gherkin scenarios and the template, and 'gh pr create' was denied so the tool was the only way in. But 'gh pr edit' was denied too and the tool could only create. The moment a body needed correcting - a reviewer asks for a clearer table, a rename lands - there was no sanctioned route at all, so the choice was to leave a validated body to rot or to widen the permission file. The gate guaranteed the exact drift it existed to prevent. | Give the tool a subcommand per route ('pr.py create' / 'pr.py update') sharing ONE validate() function, and let update resolve the PR from the current branch so nobody has to look up a number. Update is not a lighter path: an update that skipped the checks is just the denied command wearing a hat. Name the tool for the noun it owns (pr) rather than the one verb it started with (open_pr) - a verb in the name is what made the gap invisible. |
| `spring-error-codes-are-expanded` | A test asserts a field error code equals the one passed to errors.rejectValue(...), and fails with a longer, unfamiliar code. | Assert that FieldError.getCodes() CONTAINS your code. Do not assert getCode() equals it. |
| `verify-the-premise-before-implementing` | A ticket asserts that behaviour is missing. It isn't — it already exists somewhere the
ticket didn't mention. The work gets done anyway: duplicated logic, a second error code
for the same rule, and every gate green. | Before implementing, write a test that asserts the CURRENT behaviour the ticket claims is
broken, at the level a user actually hits it. If that test passes, the ticket is wrong —
stop and say so. Only start once you have seen the gap with your own test. |

## Adding an entry

Write one whenever something was non-obvious, surprising, or cost you a wrong
turn. The bar is low on purpose — a minute now, recalled forever.

```bash
.claude/tools/lexicon.py add \
  --key spring-error-codes-are-expanded \
  --title "..." --problem "..." --solution "..." --why "..." \
  --tags spring,validation
```
