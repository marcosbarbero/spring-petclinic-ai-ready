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

Then take the branch:

```bash
git switch -c issue-<number>
```

## 2 · Plan, and break down if needed

Produce, before touching any code:

- the **Outcome**, restated in one sentence
- a numbered list of the **scenarios**, each with the test name you will write for it
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

Dispatch the **reviewer** subagent with the brief and the diff. Its only question is
whether the implementation satisfies the **product requirements and test scenarios** —
not whether the code is pretty. Formatting, architecture, coverage and mutation are
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

Then open the PR with `gh pr create`, and in the body:

- `Closes #<number>`
- a table mapping **each scenario → the test that proves it**
- the mutation score, and any surviving mutants in touched code with justification
- the review verdict and how many rounds it took

The PR body is for a human reading **intent and evidence**, not diffs. Assume nobody
will read the code line by line — that is what the gates were for.

---

## Do not

- Fill in missing requirements by guessing. Refuse the ticket instead.
- Touch `.githooks/`, `.claude/hooks/`, `ArchitectureRulesTest`, or threshold config.
- Implement anything the brief did not ask for.
- Report success while any gate is red.
