---
description: Implement a GitHub issue end to end — brief, plan, TDD, review cycle, PR
argument-hint: gh#42 (or just 42)
---

Implement issue **$ARGUMENTS** end to end.

The prompt is an issue number and nothing else. Everything you need is in this repo:
the issue carries the requirements and test scenarios, `CLAUDE.md` carries the
architecture and conventions, and the gates carry the definition of done. If something
is missing, that is a defect in the ticket — say so and stop. Do not fill gaps by
guessing.

**Deterministic first. Agent on failure.** Every step below that a script can do, a
script does. You are used only where judgement is genuinely required.

---

## 1 · Brief  (deterministic — no judgement)

```bash
.claude/tools/issue_context.py $ARGUMENTS
```

- **exit 1** → the issue is not implementable. Print the reasons and **stop.** Do not
  attempt to repair the ticket yourself.
- **exit 2** → tier 3. Produce the plan from step 2, then **stop and wait for a human.**
  High-risk work is never auto-implemented.
- **exit 0** → continue. The brief it printed is now your single source of truth; prefer
  it over re-reading the issue.

The brief has five parts, and they are not interchangeable:

| | |
|---|---|
| **Context** | what is broken today and why it matters — read it, it is why the change exists |
| **Outcome** | one sentence: what is true afterwards |
| **Requirements** | numbered. **The specification** — what the system must do |
| **Test scenarios** | Gherkin. **The verification** — how you prove each requirement |
| **Constraints** | what must not change |

Requirements and scenarios are different things. A requirement with no scenario will not
get tested; a scenario with no requirement is scope creep. `issue_context.py` already
refused the ticket if there are fewer scenarios than requirements — but it cannot tell
whether they line up *semantically*. That is your job in step 2.

Then take the branch:

```bash
git switch -c issue-<number>
```

## 2 · Plan, and break down if needed

Produce, before touching any code:

- the **Outcome**, restated in one sentence
- a **requirement → scenario → test** table. One row per requirement, naming the scenario
  that proves it and the test you will write. **If a requirement has no scenario that
  covers it, stop and say so** — that is a gap in the ticket, not something to improvise
  around.
- the **blast radius** — every file you expect to touch
- an explicit **architecture check**: does this cross a slice boundary
  (`owner` ↔ `vet`, or anything into `model`)? If yes, **stop and say so.**

**Break down if the brief needs it.** If the scenarios describe more than one coherent
behaviour, split into units and do them one at a time, fully — red, green, reviewed —
before starting the next. Sequential, not parallel: each unit starts from the finished
result of the last one, so there is one merge at the end instead of several fighting
each other.

## 3 · Implement  (delegate to `tech-lead`)

Dispatch the **tech-lead** subagent with the brief and the plan for the current unit.

TDD is not a request here — `.claude/hooks/require-test-first.sh` rejects any edit to
`src/main/java` on a branch with no test change. If the tech lead reports being blocked,
it skipped a step; send it back rather than working around the hook.

## 4 · Review  (delegate to `reviewer`)

Dispatch the **reviewer** subagent with the brief and the diff. Its only question is whether the implementation satisfies the **numbered requirements**,
as proven by the **test scenarios** — not whether the code is pretty. It checks both
links in that chain: requirement → scenario, and scenario → asserting test. Formatting, architecture, coverage and mutation are
already decided by gates; re-reviewing them is the reviewer-fatigue anti-pattern this
whole repo exists to eliminate.

The reviewer returns `APPROVED` or `CHANGES REQUESTED` with numbered defects.

## 5 · The cycle

On `CHANGES REQUESTED`, send the defects back to the tech lead and review again.

**Bounded at 3 rounds.** If it has not converged after three, stop and escalate to a
human with: what is still failing, which scenario it belongs to, and what you think the
ticket got wrong. A loop that will not converge is nearly always an ambiguous
requirement, not a stubborn bug — and burning tokens on round seven will not fix a ticket
that was never clear.

## 6 · Gate

```bash
./mvnw verify
./mvnw -Pmutation verify
```

Both green, or you are not done. Never weaken a test or a threshold to get there.

## 7 · Pull request

```bash
git push -u origin issue-<number>
```

The pre-push hook runs the whole gate locally. If it rejects the push, fix the cause —
never `--no-verify` (it is denied anyway).

Then draft the PR body against `.github/PULL_REQUEST_TEMPLATE.md` and open it with:

```bash
.claude/tools/pr.py create --issue <number> --body-file <draft> --dry-run   # check first
.claude/tools/pr.py create --issue <number> --body-file <draft>
```

**`gh pr create` is denied.** Not as a formality — the tool checks things a reviewer
cannot reasonably check by eye:

- the PR closes an issue, and that issue is still **open**
- every required section exists and is non-empty
- **every Gherkin scenario in the issue appears in your coverage table.** Nobody
  cross-references four scenarios against a markdown table at 6pm; this does.
- a mutation report exists and is above threshold
- **tier-3 is refused outright** — high-risk work is opened by a human, not an agent

If it refuses, fix the body. The gates already proved the code works; this proves a human
can review the *intent* without reading the diff.

---

## Do not

- Fill in missing requirements by guessing. Refuse the ticket instead.
- Touch `.githooks/`, `.claude/hooks/`, `ArchitectureRulesTest`, or threshold config.
- Implement anything the brief did not ask for.
- Report success while any gate is red.
