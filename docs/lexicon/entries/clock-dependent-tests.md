---
key: clock-dependent-tests
title: LocalDate.now() in production code makes tests midnight-flaky
tags: [testing, flakiness]
seen_in: [PR #2]
---

## Problem

A test computing 'today' or 'tomorrow' against code that calls LocalDate.now() can fail if the clock rolls over mid-run.

## Solution

Accept it for a small validator; inject a Clock only when the ripple is worth it. Either way, flag it in the PR rather than leaving it silent.

## Why

Injecting Clock into PetValidator means changing PetController, which constructs it with new PetValidator(). That exceeds a 'change PetValidator only' constraint. A known, stated limitation beats an unrequested refactor.
