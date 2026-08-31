---
key: inclusive-date-boundary
title: "Not in the future" means today is valid
tags: [validation, boundary, mutation-testing]
seen_in: [#1]
---

## Problem

A date rule says "must not be in the future" and the boundary is ambiguous: is today allowed?

## Solution

Default to inclusive — today valid, tomorrow invalid — and use isAfter(LocalDate.now()). Say so explicitly in the ticket.

## Why

isAfter gives the inclusive boundary directly. isBefore/isEqual chains get this wrong under mutation testing: a survivor on the conditional means the test only checked 'some past date' and 'some future date', never the boundary itself.

## Example

```java
if (pet.getBirthDate().isAfter(LocalDate.now())) { errors.rejectValue(...); }
```
