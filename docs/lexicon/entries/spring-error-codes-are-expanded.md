---
key: spring-error-codes-are-expanded
title: "Asserting on a Spring validation error code: getCodes() is a list, and getFieldError() hides siblings"
tags: [spring, validation, testing, assertj, mutation-testing]
seen_in: [#1, PR #2]
---

## Problem

A brief asked to prove a validator emits error code 'typeMismatch.birthDate' and does NOT emit it when the field is merely missing. The obvious assertion, assertThat(errors.getFieldError("birthDate").getCode()).isEqualTo(...), is wrong twice over. First, rejectValue(field, code, msg) does not store the code verbatim: DefaultMessageCodesResolver expands it into four codes, most to least specific ('typeMismatch.birthDate.pet.birthDate', '.birthDate', '.java.time.LocalDate', 'typeMismatch.birthDate'), so equality against the raw string is brittle and the bare code is never first. Second, getFieldError() returns only the FIRST error on the field, so a negative assertion ('does not report a future date') passes vacuously if a second, unwanted error was also registered behind the first.

## Solution

Assert against the flattened codes of ALL field errors, then AssertJ contains(...) / doesNotContain(...). contains() tolerates the resolver expansion; using getFieldErrors (plural) makes the negative clause actually load-bearing.

## Why

Both halves fail silently rather than loudly. Raw-code equality fails with a confusing four-element diff that tempts you to weaken the assertion; the getFieldError() singular form fails by PASSING a test that proves nothing, which mutation testing will then punish as a survivor. Reach for getFieldErrors + getCodes + contains whenever a requirement names a specific error code.

## Example

```java
// Brittle - getCode() returns the MOST specific expansion, not your code:
assertThat(errors.getFieldError("birthDate").getCode()).isEqualTo("typeMismatch.birthDate"); // fails

// Correct - flatten every code on every error for the field:
private List<String> errorCodesFor(String field) {
    return errors.getFieldErrors(field).stream()
        .flatMap(e -> Arrays.stream(e.getCodes()))
        .toList();
}

assertThat(errorCodesFor("birthDate")).contains("typeMismatch.birthDate");
assertThat(errorCodesFor("birthDate")).contains("required").doesNotContain("typeMismatch.birthDate");
```
