---
key: lexicon-add-overwrites-silently
title: lexicon.py add on an existing key overwrites it, dropping fields you did not re-pass
tags: [lexicon, tooling, harness, knowledge-loss]
seen_in: [#1, PR #6]
---

## Problem

A session learned something new about a topic the lexicon already covered and ran 'lexicon.py add --key <existing-key>' to record it. The command succeeded with no warning, but it did not merge: it rewrote the file from only the flags given on that invocation. Because --example and --seen-in were not re-passed, the worked code example and the 'seen_in: [#1, PR #2]' provenance from the earlier entry were silently deleted. The loss is invisible in the tool output and only shows up as a modified (not added) file in git status.

## Solution

Before recording, check whether the key already exists: 'lexicon.py get <key>'. If it does, EDIT the markdown file under docs/lexicon/entries/ directly and merge the new insight into the existing Problem/Solution/Why, keeping the example and seen_in. Reserve 'add' for genuinely new keys. When reviewing a work branch, treat a MODIFIED file in docs/lexicon/entries/ as a signal to diff it - an entry that shrank probably lost knowledge.

## Why

add() ends in an unconditional path.write_text(...) with no existence check and no --force guard, so overwrite is the default and there is no prompt. The whole value of the lexicon is that it accumulates; an append-only-looking command that silently truncates converts a knowledge base into a last-writer-wins cache. Also note the frontmatter title is unquoted, so a title containing a colon is invalid YAML - quote it if the parser is ever tightened.
