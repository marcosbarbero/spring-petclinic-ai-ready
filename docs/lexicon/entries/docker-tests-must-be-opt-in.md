---
key: docker-tests-must-be-opt-in
title: Container-backed tests must be opt-in, not default
tags: [build, testing, docker]
---

## Problem

./mvnw verify fails on a fresh clone with 'docker compose up' errors, on a machine where Docker is fine.

## Solution

Exclude *IntegrationTests from the default surefire run; restore them with -Pcontainers, which CI uses.

## Why

Compose cannot bind a port another container already holds — an unrelated postgres on 5432 breaks the build. A takeaway repo must go green without Docker, or the first thing a new clone does is fail for reasons unrelated to the change.
