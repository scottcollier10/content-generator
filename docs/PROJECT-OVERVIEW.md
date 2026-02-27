# HubSpot Content Generator — Project Overview

**Created:** February 2026  
**Purpose:** AI-powered marketing email generation via Slack → HubSpot

---

## What We Built

A Dockerized Python Flask application that generates HubSpot marketing email variations from a single Slack command. Loads brand context from Google Drive, generates three strategic variations via Claude, and creates editable drafts directly in HubSpot — all in under 20 seconds.

### The Flow

```
User types Slack command
        ↓
/campaign product-launch enterprise awareness 315102898877
        ↓
┌─────────────────────────────────────────────────────────┐
│                Flask App (Docker)                    │
├─────────────────────────────────────────────────────────┤
│  1. Parse Slack command (topic, audience, goal, template)│
│  2. Return 200 OK immediately (Slack requires < 3 sec)   │
│  3. Spawn background thread for processing               │
└─────────────────────────────────────────────────────────┘
        ↓ (background thread)
┌─────────────────────────────────────────────────────────┐
│  Google Drive Service                                    │
│  - List files in brand folder                            │
│  - Download each file                                    │
│  - Categorize by filename into BrandContext fields       │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│  Claude AI (Anthropic API)                               │
│  - Build prompt with brand context + request             │
│  - Generate 3 email variations:                          │
│    • Benefit-focused                                     │
│    • Story-driven                                        │
│    • Urgency-based                                       │
│  - Parse JSON response into EmailVariation objects       │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│  HubSpot Service                                         │
│  - Clone template ×3 (one per variation)                 │
│  - Patch each clone with generated content               │
│  - Return draft edit URLs                                │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│  Slack Response                                          │
│  - Post rich message to response_url                     │
│  - Clickable "Edit in HubSpot" buttons for each draft    │
└─────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Slack Integration Pattern

Slack requires webhook responses within 3 seconds. We handle this by returning `200 OK` immediately and processing in a background thread, posting results to `response_url` when done.

### 2. Pluggable Brand Context

Brand documents could come from anywhere. We designed an abstract interface (`BrandContextProvider`) so the source can be swapped without changing the rest of the system.

### 3. Graceful Degradation

If brand context fails to load, the app continues with empty context rather than failing. Claude will still generate emails — just without brand-specific guidance.

### 4. Clone → Read → Patch Pattern

HubSpot's API doesn't expose a native clone endpoint. We simulate it by fetching the source template structure and POSTing a new email from it. This preserves the client's template layout, footer, and unsubscribe links without requiring any template redesign.

### 5. Dynamic Widget Discovery

Different HubSpot templates use different widget IDs for the body content (`hs_email_body` in classic templates vs. module IDs in DnD templates). The service auto-discovers the correct target widget so the same code works with any template.

### 6. Docker Volume Mounts for Secrets

Secrets and config are mounted as Docker volumes rather than baked into the image. This means you can update config or rotate keys without rebuilding the container.

---

## Performance

| Step | Time |
|---|---|
| Brand file loading | 2–3s |
| Claude generation | 8–10s |
| HubSpot clone + patch | 3–4s |
| **Total** | **~15 seconds** |

---

## Production Considerations

The current implementation is demo-grade. For production:

- Replace Flask dev server with **Gunicorn or uWSGI**
- Set `debug=False`
- Add **Slack signature verification** (HMAC via `X-Slack-Signature` header)
- Add a **job queue** (Redis + Celery/RQ) for concurrent requests
- Add **centralized logging** (CloudWatch, Datadog, etc.)
- Use **environment-specific configs** (dev/staging/prod)
