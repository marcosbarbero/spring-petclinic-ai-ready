# 2. Tests do not read the wall clock

Date: 2026-08-31

## Status

Accepted. Enforced by `.claude/tools/check_test_determinism.py`, bound to the Maven
`validate` phase. Backlog tracked in issue #8.

## Context

A test that calls `LocalDate.now()` is dated by whenever it happens to run. It passes all
day and fails at a midnight rollover, in a timezone nobody is awake in, on a machine
nobody is watching. Because the failure is intermittent, it reads as a flake and gets
re-run rather than fixed — which is the expensive part. A flaky test does not just cost
the time to diagnose it; it teaches everyone that a red build is negotiable.

We already knew this. `docs/lexicon/entries/clock-dependent-tests.md` recorded it after
PR #2, and ten wall-clock calls existed across four test files anyway. That is the whole
lesson: a rule that binds by author discipline is a suggestion. Writing
`LocalDate.now()` is the default reflex when a test needs a date, and an agent or a
person reaches for it long before anyone reviews the diff.

## Decision

Wall-clock time sources are banned in `src/test/java` and the ban is enforced by the
build, not by review.

**As a ratchet, not a wall.** A committed baseline —
`.claude/tools/test_determinism_baseline.json` — records how many violations each file
had when the gate landed. The gate does not judge whether a violation is acceptable; it
judges whether the count went up. On day one actual equals baseline everywhere, the build
is green, and no existing file changed. Adding one more fails, *including in a file that
already has some*: a pre-existing violation is not a licence to add another beside it.

Removing a violation without lowering the baseline also fails. Without that rule the
number could drift back up to its old ceiling silently, and the ratchet would be a
decoration.

A baseline entry naming a file that no longer exists fails too, so the manifest cannot rot
as files move.

**Not merge-base scoped.** The obvious alternative — compare against `origin/main` and
require only new lines to comply — was rejected because it needs full git history, and CI
checks out shallow by default. A gate that quietly degrades to "no violations found" on a
shallow clone is worse than no gate, because it reports as verified. A committed baseline
needs no history at all.

**One entry point.** The gate binds at Maven's `validate` phase, so `./mvnw verify` runs
it. The pre-push hook runs `./mvnw verify` and CI runs `./mvnw -B verify -Pcontainers`,
so both execute the same script rather than two definitions of passing. Nothing was added
to `.githooks/pre-push`; it inherits the gate for free.

**An escape hatch that costs something.** A line ending `// allow-wall-clock: <reason>` is
skipped. The marker requires a reason, so the exception is a decision recorded at the call
site rather than an invisible allowance in a JSON file.

## Consequences

`./mvnw verify` now requires `python3`. That is already true of the hooks and every tool in
`.claude/tools/`, so it is not a new dependency for this repo, but it is a real one for
anyone building it without the harness. The gate fails rather than skips when it cannot
find its inputs, per the rule that a check must never pass by accident.

**A known gap: production still reads the clock.** Six wall-clock calls remain in
`src/main/java` — `PetValidator`, `PetController`, `VisitController` and `Visit` — and they
are *not* gated. This is deliberate but not comfortable, and it has a concrete cost: a test
that must pin what production believes "today" is cannot use a literal date, because
production resolves "now" internally. Two such tests exist (`PetValidatorTests`,
added in PR #6). They can only comply once production takes an injected `java.time.Clock`.

We did not do that here because it would drag four production classes and their
construction sites into a change whose subject is the gate. The decision of whether to
inject `Clock` is the first requirement of issue #8, and until it is answered those two
tests stay baselined with that as their recorded reason. If the answer is no, that is a
legitimate outcome — but it should be a decision someone made, not a gap nobody noticed.

## Alternatives considered

**A Checkstyle rule** (`RegexpSinglelineJava` with `includeTestSourceDirectory`). Cheapest
to add, since Checkstyle already runs. Rejected because Checkstyle suppression is per-file:
grandfathering `ClinicServiceTests` would exempt it permanently, so nothing would stop the
sixth wall-clock call being added next to the fifth. Counting is what makes the ratchet
work, and Checkstyle cannot count.

**Warning-only reporting.** Rejected on the general principle that a signal which never
blocks becomes decoration — and specifically because we already ran that experiment: the
lexicon entry was the warning, and the count went up anyway.

**Banning `.now()` in production too, in this change.** The more rigorous rule, and the
only version that makes the test-side ban fully satisfiable. Deferred to issue #8 rather
than dropped, because it is an architectural decision about constructor signatures across
four classes, and bundling it here would have meant one change doing two jobs.
