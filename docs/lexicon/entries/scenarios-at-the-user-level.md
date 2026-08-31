---
key: scenarios-at-the-user-level
title: Write scenarios at the level the user feels, not where you expect the fix
tags: [process, tickets, gherkin, testing]
seen_in: [#14, PR #15]
---

## Problem

A ticket's acceptance criteria pass, every gate is green, and the feature does not work.
The scenarios tested the layer the author assumed the fix would live in, so nothing ever
exercised the path a user takes.

## Solution

Write every `When`/`Then` at the level a user experiences the behaviour. Then apply the
test: **could this scenario pass while the feature is broken for a user?** If yes, it is
at the wrong altitude — raise it until the answer is no.

"When the pet is validated" is an implementation detail. "When the pet is saved" is the
requirement.

## Why

Issue #14 raised the pet name limit from 30 to 50. Its scenarios said "When the pet is
validated / Then there are no errors on name", its constraints said "change PetValidator
only", and its Out of scope said "the database column width".

`pets.name` is `VARCHAR(30)`. A 50-character name passes validation and then fails to
persist.

The harnessed agent obeyed all three instructions exactly and shipped a validator that
accepts a name the database cannot store — with better tests than the alternative, and
two lexicon entries recorded. The unharnessed agent, which never saw any of those
constraints, widened the schema and shipped something that works.

The harness did not fail. The spec did, and the harness executed it faithfully. Obedience
to a wrong spec is more dangerous than disobedience, because the result is confident,
complete and green.

Note both PRs still missed `db/postgres/schema.sql`. A scenario at the persistence level
would have caught all three schemas at once, because it would have had to run against one.
