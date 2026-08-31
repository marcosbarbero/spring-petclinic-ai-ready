---
key: spring-error-codes-are-expanded
title: Spring expands rejectValue codes — assert contains, not equals
tags: [spring, validation, testing]
seen_in: [#1, PR #2]
---

## Problem

A test asserts a field error code equals the one passed to errors.rejectValue(...), and fails with a longer, unfamiliar code.

## Solution

Assert that FieldError.getCodes() CONTAINS your code. Do not assert getCode() equals it.

## Why

DefaultMessageCodesResolver expands one code into an array from most to least specific. rejectValue("birthDate", "typeMismatch.birthDate", ...) makes getCode() return "typeMismatch.birthDate.pet.birthDate". The bare code is in getCodes(), never first.

## Example

```java
assertThat(errors.getFieldError("birthDate").getCodes()).contains("typeMismatch.birthDate");
```
