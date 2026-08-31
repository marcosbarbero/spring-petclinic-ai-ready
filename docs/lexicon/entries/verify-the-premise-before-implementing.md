---
key: verify-the-premise-before-implementing
title: Prove the gap exists before you fill it
tags: [process, tickets, tdd, harness]
seen_in: [#1, PR #2]
---

## Problem

A ticket asserts that behaviour is missing. It isn't — it already exists somewhere the
ticket didn't mention. The work gets done anyway: duplicated logic, a second error code
for the same rule, and every gate green.

## Solution

Before implementing, write a test that asserts the CURRENT behaviour the ticket claims is
broken, at the level a user actually hits it. If that test passes, the ticket is wrong —
stop and say so. Only start once you have seen the gap with your own test.

## Why

Issue #1 claimed pets could be saved with future birth dates. `PetValidator` really did
only check for null, so a test written against `PetValidator` really did fail, and TDD
really did go red-green. It was all correct and all pointless: `PetController` had
rejected future dates on both form paths for years, and `PetControllerTests` already
asserted it.

Two harness features combined to cause this rather than prevent it. The brief is declared
the single source of truth, so its Context was trusted rather than checked. And the
constraint "change PetValidator only" told the agent where to work, which is also a
statement about where NOT to look. An unharnessed agent, given no brief and no scope,
explored — and found the existing code immediately.

Every gate passed. Coverage, mutation, architecture, the reviewer. They all check HOW the
work was done; none of them ask whether it should have been done at all. A scope
constraint moves the bug out of the code and into the spec, where no gate can see it.
