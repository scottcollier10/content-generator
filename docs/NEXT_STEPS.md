# Roadmap & Next Steps

## Current Status

- [x] Universal HubSpot template support
- [x] Brand-aware AI generation (Google Drive → Claude)
- [x] 3 strategic variations per command (benefit-focused, story-driven, urgency-based)
- [x] Slack integration (command + rich response with links)
- [x] Docker deployment
- [x] Audit logging (JSON per generation)
- [x] Unit tests

---

## Phase 2: Content Library Integration

**Effort:** 3–4 hours  
Connect a Supabase vector store with past campaigns, case studies, and statistics. Claude references relevant examples from the library automatically.

```python
# Rough interface
class SupabaseContentLibrary:
    def find_relevant(self, topic: str, limit: int = 5) -> list[ContentItem]:
        # Vector similarity search
        ...
```

## Phase 3: Approval Workflows

**Effort:** 2–3 hours  
Add Slack interactive buttons (Approve / Edit / Reject) before drafts are created in HubSpot. Prevents low-quality output from ever touching the CRM.

## Phase 4: Campaign Association

**Effort:** Requires HubSpot Pro  
Auto-associate generated emails with HubSpot campaigns for A/B test tracking and performance reporting by variation type.

## Phase 5: Multi-Channel Output

**Effort:** 4–5 hours  
Same campaign topic → email + LinkedIn post + blog intro. One Slack command, multiple channel-appropriate outputs.

---

## Production Hardening

- Slack signature verification (HMAC)
- Gunicorn instead of Flask dev server
- Redis + Celery for job queue
- Per-client config structure for multi-tenant use
- OAuth flows for HubSpot and Google (instead of service account)
