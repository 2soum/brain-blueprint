---
id: deploy-procedure-for-the-portfolio
title: Deploy procedure for the portfolio
type: procedure
cortex: engineering
description: Push to main deploys to production in under a minute.
tags:
- deploy
- vercel
confidence: 0.8
created: '2026-10-27'
last_validated: '2026-10-27'
status: active
links:
- to: base64-encode-service-account-keys-in-env-vars
  rel: applies-to
---

> For the next agent: there is no staging. Run the build locally before pushing.

1. `pnpm build`
2. `git push origin main`
3. Poll the production URL until the new copy appears.
