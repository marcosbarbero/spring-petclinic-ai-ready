# PetClinic — agent instructions

Spring Boot 4.x / Java 17 / Maven. This repo is **harnessed**: the gates below run
without a human, and they are author-blind. If the pipeline is green, the change is
ready — regardless of who or what wrote it.

Keep this file short. It is loaded into every session, so every line here costs context
on every turn. Anything that can be a *test* should be a test, not a sentence in this
file. **An instruction is a suggestion. A failing build is not.**

## Architecture — look it up, don't explore

Package **by feature**, not by layer. Slices are independent; `model` is the shared
kernel. **Do not glob the tree to find things** — the structure is a fact, and it is
recorded:

```bash
.claude/tools/arch_map.py list          # slices + what each is responsible for
.claude/tools/arch_map.py get owner     # paths, owned classes, dependency rules
.claude/tools/arch_map.py rules         # what may depend on what
```

The work brief already inlines the map entry for the issue's `area:` label, so in a
`/work` session you usually need none of these — you have been told where to work.

Rules are enforced by `ArchitectureRulesTest`, not by this file. If a change seems to
need a cross-slice dependency (`owner` ↔ `vet`, or anything into `model`), **stop and say
so** — that is a design decision. See `docs/adr/0001-package-by-feature.md`.

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

Coverage ≥ 90% line / 78% branch (JaCoCo, enforced at `verify`).
Mutation score ≥ 80% on `owner` and `model` (PIT, `-Pmutation verify`).
Docker-dependent tests are excluded by default; `-Pcontainers` restores them (CI uses it).

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

## Memory

Relevant prior knowledge is **injected automatically** — a `UserPromptSubmit` hook scores
every prompt against the project lexicon and prepends anything that matches. You do not
need to remember to look; if something applies, it is already above.

To go deeper on a recalled entry, or to check something the hook did not surface:

```bash
.claude/tools/lexicon.py search "<topic>"
.claude/tools/lexicon.py get <key>
```

**Record what surprised you.** This half cannot be automated — no script can tell whether
something was non-obvious — so it is on you, and a `Stop` hook will ask if this session
changed production code without recording anything:

```bash
.claude/tools/lexicon.py add --key <slug> --title "..." \
  --problem "..." --solution "..." --why "..." --tags a,b
```

One file per entry under `docs/lexicon/entries/`, so two branches recording lessons never
conflict. The bar is low on purpose: a minute now, recalled free forever.

## Tooling rule

**Do not write inline or throwaway scripts.** No `python3 -c '...'` buried in a command,
no one-off shell pipelines to parse a report.

If you need a script once, write it as a file and say why. **If you need it twice, it
becomes a reusable tool in `.claude/tools/` with a docstring and `--help`.** An inline
script is written once, debugged never, and duplicated forever — and every duplicate
costs tokens to re-derive and can drift from the other copies.

This repo applies that to itself: both hooks parse the same JSON payload, so that parsing
lives in `.claude/hooks/hook_io.py` rather than in each hook.

## Tools — look them up, don't guess

Deterministic scripts live in `.claude/tools/`. **Discover them by key, not by reading
the directory:**

```bash
.claude/tools/tool_mapping.py list        # keys + one-line summaries
.claude/tools/tool_mapping.py get <key>   # detail for the one you need
```

Run `list` once when a task needs tooling, then recall by key. That is cheaper than
re-reading prose every turn, and it cannot drift — `tool_mapping.py check` runs in
pre-push and fails if a tool exists on disk but is not registered.

Before you read a generated report or write a one-off script, check the registry.
**Deterministic first. Agent on failure.**

## Workflow

`/work gh#42` runs the whole thing: brief → plan → tech-lead implements test-first →
reviewer validates against the issue's scenarios → cycle (bounded at 3 rounds) → gates →
PR. The prompt is an issue number; this repo supplies everything else.

Run any of them with `--help`. If you find yourself about to read a generated report,
check `ls .claude/tools/` first — the answer is probably already extracted.

**Deterministic first. Agent on failure.**

> These tools are NOT auto-discovered by the agent — `.claude/tools/` is a convention of
> this repo, not of the harness runtime. This list is how they get found, which is why it
> lives in the always-on file. Add a line here when you add a tool, or nobody will use it.

## Commands

```bash
./mvnw verify                 # format, checkstyle, arch rules, tests, coverage gate
./mvnw test -Dtest=ClassName  # one test class
./mvnw -Pmutation verify      # mutation score (slow — before pushing, not per edit)
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
