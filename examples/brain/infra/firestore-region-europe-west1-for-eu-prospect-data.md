---
id: firestore-region-europe-west1-for-eu-prospect-data
title: Firestore region europe-west1 for EU prospect data
type: decision
cortex: infra
description: EU prospect data stays in the EU; the region of a Firestore database
  cannot change after creation.
tags:
- firestore
- region
- gdpr
confidence: 0.95
created: '2026-10-27'
last_validated: '2026-10-27'
status: active
links:
- to: firestore-region-us-central1
  rel: supersedes
- to: base64-encode-service-account-keys-in-env-vars
  rel: same-stack
---

> For the next agent: create every new Firestore database in eur3 or europe-west1. Moving later means a migration.

## Why
The data belongs to European prospects, and the region is fixed at creation.
