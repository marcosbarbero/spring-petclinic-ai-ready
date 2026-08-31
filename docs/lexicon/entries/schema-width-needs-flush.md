---
key: schema-width-needs-flush
title: A column-width change is only proven by a test that flushes
tags: [jpa, testing, schema, h2]
---

## Problem

In a @DataJpaTest, saving an entity with an over-long value and reading it back via the repository passes even when the column is too narrow: the read is served by the Hibernate first-level cache and the INSERT is never sent. A widening of pets.name from VARCHAR(30) to VARCHAR(50) would therefore look covered by a test that cannot fail.

## Solution

After the save, call entityManager.flush() then entityManager.clear() before re-reading. Inject the EntityManager with @PersistenceContext. With the flush, h2 raises JdbcSQLDataException 'Value too long for column NAME VARCHAR_IGNORECASE(30)' and the test is genuinely red before the schema change.

## Why

DDL here comes from src/main/resources/db/<vendor>/schema.sql, not from JPA annotations (NamedEntity.name is a bare @Column with no length), so nothing at the Java level enforces or reveals the width. Only a real round-trip through the database does.
