---
key: raising-a-validator-limit-breaks-its-old-boundary-test
title: Raising a validation limit invalidates the existing boundary test
tags: [validation, testing, briefs]
---

## Problem

Issue #14 raised the pet name limit 30 -> 50 with the constraint 'do not modify existing tests', and asserted PetValidatorTests.validateWithLongPetName would stay green. It cannot: it feeds "A".repeat(31) and asserts a name error, and 31 is valid once the maximum is 50. The constraint and the requirement are mutually unsatisfiable.

## Solution

Retarget the existing boundary test to the new limit ("A".repeat(MAX_NAME_LENGTH + 1)) so it still asserts the same behaviour - a name over the maximum is rejected - and report the constraint conflict rather than deleting or disabling the test.

## Why

A boundary test encodes the old limit as a fact. Any change to the limit is by definition a change to that fact, so 'add tests, never touch existing ones' cannot hold for the one test that pins the boundary being moved. Spotting this early avoids a green-looking build that silently dropped the regression guard.
