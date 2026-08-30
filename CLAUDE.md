# PetClinic — agent instructions

Spring Boot 4.x / Java 17 / Maven. This repo is **harnessed**: the gates below run
without a human, and they are author-blind. If the pipeline is green, the change is
ready — regardless of who or what wrote it.

Keep this file short. It is loaded into every session, so every line here costs context
on every turn. Anything that can be a *test* should be a test, not a sentence in this
file. **An instruction is a suggestion. A failing build is not.**

## Architecture

Package **by feature**, not by layer:

```
petclinic/
  owner/    Owner, Pet, Visit + their controllers, repositories, validators
  vet/      Vet, Specialty + controller and repository
  system/   cross-cutting web/cache config, error pages
  model/    shared kernel: BaseEntity, NamedEntity, Person
```

Rules, enforced by `ArchitectureRulesTest`:

- `owner` and `vet` **must not** depend on each other.
- `model` **must not** depend on any feature package. It is the shared kernel.
- No cycles between packages.
- Constructor injection only. Never `@Autowired` on a field.
- `*Repository` types are interfaces, inside a feature package.

If a change seems to need a cross-feature dependency, **stop and say so**. That is a
design decision, not an import. See `docs/adr/0001-package-by-feature.md`.

## Testing

**Tests first. This is enforced by a hook, not by good intentions.**
`.claude/hooks/require-test-first.sh` rejects edits to `src/main/java` when the branch
has no new or changed test. If you are blocked by it, you skipped a step — write the
failing test.

- Unit tests: plain JUnit 5 + AssertJ. No Spring context unless the test needs one.
- Web slice: `@WebMvcTest`, never `@SpringBootTest`, for controller behaviour.
- Name tests for the behaviour, not the method: `rejectsBirthDateInTheFuture`,
  not `testValidate2`.
- Cover the boundary, not just the happy path. A validator test that only passes a
  valid value proves nothing — mutation testing will fail you for it.

Coverage ≥ 70% line / 60% branch (JaCoCo, enforced at `verify`).
Mutation score ≥ 75% on `owner` and `model` (PIT, `-Pmutation`).

## Style

- `./mvnw spring-javaformat:apply` before finishing. Formatting is not a matter of taste
  here; the build fails on it.
- No magic numbers, no methods over 60 lines, no cyclomatic complexity over 10, no
  concatenated SQL/JPQL, no `printStackTrace`, no field injection. These are **enforced**
  by `src/checkstyle/quality-checkstyle.xml`, not requested.
- No `http://` URLs anywhere — checkstyle's nohttp rule fails the build.
- Formatting is applied for you by a `PostToolUse` hook. Do not spend tokens on it.
- Prefer the smallest change that satisfies the acceptance criteria. Do not refactor
  adjacent code you were not asked to touch.

## Tools — prefer these over reading artifacts

Deterministic scripts that answer a question in a few hundred tokens instead of making
you read a multi-megabyte report. Use them before reasoning about coverage or mutation.

```bash
.claude/tools/mutation_survivors.py   # which mutants survived, and where
.claude/tools/coverage_gaps.py        # uncovered lines, scoped to your diff
.claude/tools/check_issue.py <file>   # is this ticket implementable at all?
```

If you find yourself about to read a generated report, check whether a tool already
extracts the answer. **Deterministic first. Agent on failure.**

## Commands

```bash
./mvnw verify                 # format, checkstyle, arch rules, tests, coverage gate
./mvnw test -Dtest=ClassName  # one test class
./mvnw -Pmutation test        # mutation score (slow — run before pushing, not per edit)
git push                      # runs .githooks/pre-push: the full gate, locally
```

## Hard rules

- **Never** weaken, skip, `@Disabled`, or delete a test to make a build pass. If a test
  fails, either the code is wrong or the test encodes a requirement you have not met.
  Say which. Changing the assertion to match the output is the one unforgivable move.
- **Never** use `git push --no-verify`, or edit `.githooks/`, `pom.xml` gate config, or
  `ArchitectureRulesTest` to get green. Those are the gate. Moving the gate is not
  passing it.
- One unit of work per session. If the ticket contains "and", it is probably two tickets.
