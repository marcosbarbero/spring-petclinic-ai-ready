---
key: pet-name-length-boundary
title: Pet name max length: one constant, but a VARCHAR(30) behind it
tags: [owner, validation, boundary, schema]
---

## Problem

Raising PetValidator.MAX_NAME_LENGTH broke the existing test validateWithLongPetName, which hard-coded "A".repeat(31) as a stand-in for 'max + 1'. A brief that says 'do not modify existing tests' collides with any boundary change of this kind.

## Solution

Express boundary inputs relative to the constant (MAX_NAME_LENGTH, MAX_NAME_LENGTH + 1) rather than as bare literals, so a future limit change moves one number. Note also that pets.name is VARCHAR_IGNORECASE(30) in src/main/resources/db/h2/schema.sql: the validator now accepts names the schema cannot store, so a length change is really two changes.

## Why

A hard-coded 'just over the limit' literal is invisible until the limit moves, and the validator limit and the column width are set in two files that nothing keeps in sync.
