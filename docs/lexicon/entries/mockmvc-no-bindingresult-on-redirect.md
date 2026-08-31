---
key: mockmvc-no-bindingresult-on-redirect
title: model().attributeHasNoErrors() fails on a successful redirect
tags: [testing, mockmvc, webmvctest, validation]
---

## Problem

A @WebMvcTest asserting a valid form submission with .andExpect(model().attributeHasNoErrors("pet")) fails with 'No BindingResult for attribute: pet', even though the POST succeeds and redirects. It looks like the assertion found errors; it did not.

## Solution

On the success path the controller redirects and no BindingResult is placed in the model, so attributeHasNoErrors has nothing to inspect and throws. Assert the outcome instead: status().is3xxRedirection() and view().name("redirect:/owners/{ownerId}"). Reserve attributeHasFieldErrorCode/attributeHasNoErrors for the re-rendered-form (error) path, which is where a BindingResult actually exists.

## Why

The failure message reads like an assertion failure about errors, so the instinct is to debug the validator. The real cause is that the assertion is only meaningful on the error path.
