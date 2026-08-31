---
key: clock-dependent-tests
title: LocalDate.now() in production code makes tests midnight-flaky
tags: [testing, flakiness, clock, dates, time]
seen_in: [PR #2, PR #6, "#7", "#8"]
---

## Problem

A test computing 'today' or 'tomorrow' against code that calls LocalDate.now() can fail if the clock rolls over mid-run.

## Solution

For a test that only needs *a* date, use a literal: LocalDate.of(2020, 1, 15). This is now enforced — see deterministic-test-dates — so it is not a preference.

For a test that must control what production believes 'today' is, a literal is not enough on its own, because production reads the clock internally. Production has to take an injected Clock. Whether to do that is a judgement call about ripple: injecting Clock into PetValidator means changing PetController, which constructs it with new PetValidator(). Under a 'change PetValidator only' constraint that is out of scope, and a known, stated limitation beats an unrequested refactor — but say so in the PR rather than leaving it silent.

## Why

The advice above changed in one direction and it matters which. Accepting a wall-clock call used to be the default for anything small; since the gate landed it is the exception, allowed only where it predates the baseline or carries an explicit `// allow-wall-clock: <reason>`. Being 'a small validator' is no longer on its own a reason — the ratchet means a file that already has a violation is not a licence to add another. The residual production-side calls are tracked in issue #8; the decision is recorded in docs/adr/0002-deterministic-time-in-tests.md.
