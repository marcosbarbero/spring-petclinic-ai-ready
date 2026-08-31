---
key: pit-needs-1-19-on-jdk-21
title: PIT crashes on JDK 21 below version 1.19
tags: [build, mutation-testing, jdk]
---

## Problem

./mvnw -Pmutation verify dies with 'Coverage generator Minion exited abnormally due to UNKNOWN_ERROR'.

## Solution

Use pitest-maven 1.19.6 with pitest-junit5-plugin 1.2.3.

## Why

PIT 1.17 predates proper JDK 21 support. The toolchain here reports java.version 17 but actually runs Adoptium 21, so the mismatch is easy to miss.
