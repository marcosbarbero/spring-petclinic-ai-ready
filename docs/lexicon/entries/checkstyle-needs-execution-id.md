---
key: checkstyle-needs-execution-id
title: Bare checkstyle:check runs the DEFAULT ruleset
tags: [build, checkstyle]
---

## Problem

Running ./mvnw checkstyle:check reports hundreds of violations that the normal build never mentions.

## Solution

Invoke the project's execution by id: ./mvnw checkstyle:check@nohttp-checkstyle-validation (or @quality-checkstyle-validation).

## Why

A CLI invocation uses default-cli configuration, not the <execution> config in the pom. It falls back to Sun conventions — 413 violations here, none of them real.
