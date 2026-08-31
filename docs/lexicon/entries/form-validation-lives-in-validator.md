---
key: form-validation-lives-in-validator
title: Form validation goes in a Validator, not on the entity
tags: [validation, owner, architecture]
seen_in: [#1]
---

## Problem

Adding a rule to a form and reaching for a jakarta.validation annotation on the entity.

## Solution

Put form rules in the slice's Validator (e.g. PetValidator). Leave the entity's annotations alone.

## Why

Entities are shared with non-form paths (imports, fixtures, integration tests). An annotation added for a form rejects data on every path, including ones that legitimately carry historical values.

## Example

```java
PetValidator.validate(...) -> errors.rejectValue(field, code, message)
```
