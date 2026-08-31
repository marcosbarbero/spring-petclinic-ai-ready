---
key: deterministic-test-dates
title: Tests must use literal dates, never LocalDate.now() — and a gate enforces it
tags: [testing, dates, time, clock, flaky, determinism, gate]
seen_in: [#7, #8]
---

## Problem

A test that needs a date reaches for LocalDate.now(), Instant.now(), new Date() or System.currentTimeMillis(). It passes locally and is dated by whenever it happened to run, so it fails at a midnight rollover or in another timezone, on a machine nobody is watching. Because the failure is intermittent it reads as a flake and gets re-run rather than fixed. Writing the test this way is the default reflex, so knowing the rule after the fact does not help - it has to be known BEFORE the test is written.

## Solution

Use a literal date: LocalDate.of(2020, 1, 15). If the test needs to control what PRODUCTION thinks today is - a boundary test for 'not in the future', say - a literal is not enough on its own, because production calls LocalDate.now() internally; production must take an injected java.time.Clock and the test passes Clock.fixed(instant, ZoneOffset.UTC). If a call genuinely must read the wall clock, end the line with '// allow-wall-clock: <reason>'; the marker requires a reason, not a bare tag. This is enforced by .claude/tools/check_wall_clock_in_tests.py, bound to the validate phase, so ./mvnw verify fails on a new violation.

## Why

The gate is a ratchet, not a wall: a committed baseline grandfathers the calls that already existed so it could land without breaking the tree, and the per-file count can only go DOWN - removing a violation without lowering the baseline also fails. That means a pre-existing file is NOT a licence to add another one there. See docs/adr/0002-deterministic-time-in-tests.md, backlog issue #8, and the related entry clock-dependent-tests.

## Example

```java
// wrong - dated by when it ran:  pet.setBirthDate(LocalDate.now());
// right - literal:              pet.setBirthDate(LocalDate.of(2020, 1, 15));
// right - test controls production time:
//   var clock = Clock.fixed(Instant.parse("2026-08-31T12:00:00Z"), ZoneOffset.UTC);
//   new PetValidator(clock);
```
