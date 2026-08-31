---
key: pr-tool-owns-create-and-update
title: A tool that gates an action must own every route to it, not just the first one
tags: [harness, tooling, gates, permissions, pull-request]
seen_in: [#10, PR #9]
---

## Problem

open_pr.py validated a PR body against the issue's Gherkin scenarios and the template, and 'gh pr create' was denied so the tool was the only way in. But 'gh pr edit' was denied too and the tool could only create. The moment a body needed correcting - a reviewer asks for a clearer table, a rename lands - there was no sanctioned route at all, so the choice was to leave a validated body to rot or to widen the permission file. The gate guaranteed the exact drift it existed to prevent.

## Solution

Give the tool a subcommand per route ('pr.py create' / 'pr.py update') sharing ONE validate() function, and let update resolve the PR from the current branch so nobody has to look up a number. Update is not a lighter path: an update that skipped the checks is just the denied command wearing a hat. Name the tool for the noun it owns (pr) rather than the one verb it started with (open_pr) - a verb in the name is what made the gap invisible.

## Why

The failure mode is structural, not specific to PRs: whenever you deny a command and route it through a tool, enumerate EVERY command the deny list covers. Denying create+edit while the tool implements only create leaves a hole that looks like a missing feature but is actually an unguarded state transition. Note also that .claude/settings.json is Edit-denied, so the allow-rule rename cannot be done by the agent - a human has to make that one-line change, which is the permission model working, not a bug.
