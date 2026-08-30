# Spring PetClinic — harnessed

[![Build](https://github.com/marcosbarbero/spring-petclinic-ai-ready/actions/workflows/maven-build.yml/badge.svg)](https://github.com/marcosbarbero/spring-petclinic-ai-ready/actions/workflows/maven-build.yml)

The standard [Spring PetClinic](https://github.com/spring-projects/spring-petclinic),
with an **AI harness** wrapped around it.

The point of this repo is the harness, not the application. It is the "after" half of a
before/after pair — [spring-petclinic-no-ai](https://github.com/marcosbarbero/spring-petclinic-no-ai)
is the identical app with none of it.

> **An AI harness is not a framework. There is nothing to install.**
> It is the SDLC you already know, made executable — because your new colleague can't be
> trusted, doesn't read the wiki, and works at 3am.
>
> Every gate here is author-blind. If the pipeline is green the change is ready,
> regardless of who or what wrote it.

## Start here

```bash
git clone https://github.com/marcosbarbero/spring-petclinic-ai-ready
cd spring-petclinic-ai-ready
git config core.hooksPath .githooks   # REQUIRED — git cannot set this for you
./mvnw verify                          # ~10s, no Docker needed
```

Then try to break it:

```bash
# ask an agent to make production changes with no test — the hook refuses
# ask it to delete ArchitectureRulesTest — the deny list refuses
# ask it to push with --no-verify — denied
```

## What's in the harness

| | What it does | Why |
|---|---|---|
| `CLAUDE.md` | always-on context: architecture, testing policy, hard rules | short on purpose — it costs context on every turn |
| `.claude/hooks/require_test_first.py` | `PreToolUse`, **exit 2** on `src/main` edits with no test on the branch | asking for TDD gets ~70%; exit code 2 gets 100% |
| `.claude/hooks/format_after_edit.py` | `PostToolUse`, formats Java after every edit | the agent should never spend a token on formatting |
| `.claude/settings.json` | allow/deny — refuses `--no-verify` and edits to the gates | **moving the gate is not passing it** |
| `.claude/tools/` + `mapping.json` | deterministic scripts, discovered by key via `tool_mapping.py` | see below |
| `.claude/agents/` | `tech-lead` implements, `reviewer` validates against the issue | separation is the point |
| `.claude/commands/work.md` | `/work gh#42` — issue in, pull request out | the whole workflow |
| `ArchitectureRulesTest` | 8 ArchUnit rules: slice isolation, no cycles, no field injection | package-boundary violations become build failures |
| `src/checkstyle/quality-checkstyle.xml` | magic numbers, complexity, concatenated SQL, `printStackTrace` | these were prose in CLAUDE.md until they became a gate |
| `.githooks/pre-push` | format → lint → architecture → tests+coverage → mutation | fails on your laptop, not in someone's review queue |
| `pom.xml` | JaCoCo 90%/78%, PIT mutation 80% (`-Pmutation`) | coverage proves a line ran; mutation proves someone would notice if it broke |

**Maven only.** Upstream ships a Gradle build too; it was removed deliberately. Two build
systems mean two definitions of "green", and they drift the moment a gate is added to one
of them. A harness needs exactly one source of truth about what "done" means.

## The toolbox

`.claude/tools/` — deterministic scripts, no model involved. Same input, same output.

They are **discovered by key, not by reading the directory**:

```bash
.claude/tools/tool_mapping.py list        # keys + one-line summaries
.claude/tools/tool_mapping.py get <key>   # detail for the one you need
```

`mapping.json` is the registry; `README.md` in that folder is generated from it, so the
human doc and the machine doc cannot disagree. `tool_mapping.py check` runs in pre-push
and fails if a tool exists on disk but is not registered — **an unregistered tool is an
undiscoverable tool.**

Listing tools in `CLAUDE.md` would also work, but that file is loaded every turn, so the
list would cost tokens forever and still have to be re-read and re-reasoned about. A
registry is looked up once and recalled by key.

These exist because *the answer was always small — only the artifact was big.* An agent
asked to "improve the mutation score" will read a two-megabyte report and burn ~40k
tokens; `mutation-survivors` returns the same finding in a few hundred.

**Deterministic first. Agent on failure.** Use the cheapest tool that can answer the
question; escalate to a model only when it fails.

## The workflow

```
/work gh#42
```

The prompt is an issue number. Everything else lives in the repo.

1. **Brief** — `issue_context.py` validates and extracts context, outcome, requirements,
   scenarios and constraints. Missing context, no numbered requirements, fewer scenarios
   than requirements, no tier → refused before a token is spent.
   **tier-3 → plan only, wait for a human.**
2. **Plan** — a requirement → scenario → test table, blast radius, architecture check.
3. **Implement** — `tech-lead` subagent, test-first (enforced by the hook).
4. **Review** — `reviewer` subagent, read-only, checks *only* whether each requirement is
   covered by a scenario and proven by a test that asserts it. It is explicitly told not to re-review formatting,
   architecture or coverage — gates already decided those.
5. **Cycle** — bounded at 3 rounds, then escalate. A loop that won't converge is almost
   always an ambiguous requirement, not a stubborn bug.
6. **Gate** — `./mvnw verify` and `-Pmutation verify`.
7. **PR** — with a requirement → scenario → test table, so a human reviews intent and
   evidence.

Issues are filed through a GitHub **issue form** (`.github/ISSUE_TEMPLATE/unit-of-work.yml`)
where every field is required. A markdown template is a suggestion people delete; a form
is a gate.

## Commands

```bash
./mvnw verify                 # format, lint, arch rules, tests, coverage   (~10s)
./mvnw -Pmutation verify      # + mutation score                            (~60s)
./mvnw verify -Pcontainers    # + Docker-backed integration tests (CI uses this)
./mvnw test -Dtest=ClassName  # one test class
git push                      # runs the full local gate first
SKIP_MUTATION=1 git push      # same, minus mutation
```

Docker-dependent tests are excluded by default so a fresh clone goes green on any
machine. The local gate optimises for latency; CI optimises for coverage.

## Running the app

```bash
./mvnw spring-boot:run     # http://localhost:8080
```

See the [upstream README](https://github.com/spring-projects/spring-petclinic) for the
application itself — database setup, Docker, IDE configuration.
