---
id: base64-encode-service-account-keys
title: Base64-encode service account keys in env vars
type: fact            # fact | decision | preference | procedure | episode | insight
cortex: infra         # one theme per cortex; reuse before creating
description: Raw private keys in env vars lose their newlines and break auth in production.
tags: [env, secrets, deploy]
confidence: 0.9       # 0..1, how sure the writer was
created: 2026-10-27
last_validated: 2026-10-27
status: active        # active | superseded
links:
  - to: vercel-env-vars-are-per-environment
    rel: related
---

> For the next agent: if auth fails only in production with a vague key error,
> check whether the service account key was pasted raw. Store it base64-encoded
> and decode it at startup.

## Why
Private keys contain `\n`. Most env var UIs and shells mangle them silently.

## How to apply
`FIREBASE_SERVICE_ACCOUNT_B64=$(base64 -i key.json)`, then decode in code.
