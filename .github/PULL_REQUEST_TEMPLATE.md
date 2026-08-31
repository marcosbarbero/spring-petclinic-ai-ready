<!--
  Do not open PRs by hand. Use:  .claude/tools/pr.py create --issue N --body-file <draft>
  It validates this template, cross-checks the linked issue, and verifies the gates
  actually ran. `gh pr create` is denied in .claude/settings.json for exactly that reason.

  This body is for a human reading INTENT and EVIDENCE. Nobody is going to read the diff
  line by line — that is what the gates were for. Give them what the gates cannot:
  what you decided, what you interpreted, and what you are unsure about.
-->

Closes #<!-- issue number — must be an OPEN issue; a PR with no ticket has no agreed definition of done -->

**Tier:** <!-- tier-1 / tier-2 / tier-3, copied from the issue. Decides how this lands. -->
**Area:** <!-- the feature slice, e.g. owner -->

## Workflow used

<!-- Which path produced this: /work gh#N end to end, partially assisted, or by hand.
     Say it plainly. A reviewer reads a fully-autonomous PR differently from a hand-written
     one, and pretending otherwise wastes their attention. -->

## Requirement → scenario → test

<!-- One row per numbered requirement in the issue. Every requirement needs a scenario,
     and every scenario needs a test that asserts its Then. A row without a test is not
     ready for review. -->

| # | Requirement | Scenario | Test |
|---|---|---|---|
| 1 |  |  |  |

## Evidence

<!-- Paste real output, not claims. "Tests pass" is not evidence. -->

| Gate | Result |
|---|---|
| `./mvnw verify` |  |
| `./mvnw -Pmutation verify` |  |
| Mutation score |  |
| Survivors in changed code |  |
| Architecture rules |  |

## Constraints honoured

<!-- Quote each constraint from the issue and state how it held. The most common one -
     "do not modify existing tests" - is exactly what a stuck agent breaks first. -->

- [ ] Existing tests unmodified
- [ ] Only the files named in the issue were changed
- [ ] Nothing implemented that the issue did not ask for

## Judgement calls

<!-- Anything you had to interpret because the ticket did not settle it: an ambiguous
     boundary, a framework behaviour that forced a different assertion, a trade-off you
     took deliberately. THIS IS THE MOST VALUABLE SECTION. The gates cannot check it, so
     it is the one part that genuinely needs a human.
     Write "none" if there were none - do not leave it blank. -->

## Lexicon

<!-- Entries added under docs/lexicon/entries/, or "none - nothing was non-obvious".
     If something cost you a wrong turn and is not recorded here, the next session pays
     for it again. -->

## Notes for the reviewer

<!-- What to look at first, what you are least sure about, anything deliberately left
     for a follow-up. Optional, but a PR that says "check the boundary handling" gets a
     better review than one that says nothing. -->
