---
id: base64-encode-service-account-keys-in-env-vars
title: Base64-encode service account keys in env vars
type: fact
cortex: infra
description: Raw private keys in env vars lose their newlines and break auth only
  in production.
tags:
- env
- secrets
- deploy
confidence: 0.9
created: '2026-10-27'
last_validated: '2026-10-27'
status: active
links:
- to: deploy-procedure-for-the-docs-site
  rel: applies-to
- to: firestore-region-europe-west1-for-eu-prospect-data
  rel: same-stack
---

> For the next agent: if auth fails only in production with a vague key error, check whether the key was pasted raw. Store it base64-encoded and decode it at startup.

## Why
Private keys contain newlines that env var UIs and shells mangle silently.

## How to apply
Encode once with `base64 -i key.json`, decode in the app's config loader.
