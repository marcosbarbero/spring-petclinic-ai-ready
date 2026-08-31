---
key: mutation-survivor-means-no-assertion
title: A surviving mutant means the test ran the code without checking it
tags: [testing, mutation-testing]
seen_in: [PR #2]
---

## Problem

Coverage is high, the mutation gate fails, and it is unclear what to add.

## Solution

Run .claude/tools/mutation_survivors.py. For each survivor, assert the behaviour the mutation changed — do not add more tests that merely call the method.

## Why

Coverage proves a line executed; mutation proves someone would notice if it changed. Adding tests without assertions raises coverage and leaves the mutation score exactly where it was.

## Example

```java
.claude/tools/mutation_survivors.py --limit 10
```
