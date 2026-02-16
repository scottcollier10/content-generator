# HubSpot Content Generator - Design Document

**Date:** 2025-02-16
**Status:** Approved

## Overview

A Dockerized Python Flask application that replaces the n8n workflow for generating HubSpot email variations via Slack commands. The application receives a Slack slash command, generates 3 email variations using Claude AI with brand context from Google Drive, and creates draft emails in HubSpot.

## Goals

- Replace n8n workflow with a standalone application
- Keep Slack as the primary interface
- Design for pluggable brand context sources (Google Drive now, others later)
- Enable easy client switching via configuration
- Provide logging for debugging and reference

## Non-Goals

- Production deployment (this is for demo purposes)
- Multi-tenant support
- User authentication beyond Slack

## Project Structure

```
application/
├── app.py                      # Flask app, Slack webhook endpoint
├── config.yaml                 # Client-specific settings
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── services/
│   ├── __init__.py
│   ├── brand_context.py        # Google Drive (pluggable interface)
│   ├── content_generator.py    # Claude API
│   └── hubspot.py              # Clone/read/patch
├── models/
│   ├── __init__.py
│   └── schemas.py              # Data classes
├── utils/
│   ├── __init__.py
│   └── logger.py               # Logging setup
├── credentials/                # Service account JSON (gitignored)
└── logs/                       # Generation logs (gitignored)
```

## Request Flow

```
┌─────────┐     POST /slack-campaign      ┌─────────────┐
│  Slack  │ ──────────────────────────────▶│   Flask     │
└─────────┘                                │   app.py    │
     ▲                                     └──────┬──────┘
     │                                            │
     │  1. Immediate "Processing..." response     │
     │◀───────────────────────────────────────────┤
     │                                            ▼
     │                                   ┌────────────────┐
     │                                   │ brand_context  │
     │                                   │ (Google Drive) │
     │                                   └───────┬────────┘
     │                                           ▼
     │                                   ┌────────────────┐
     │                                   │content_generator│
     │                                   │  (Claude API)  │
     │                                   └───────┬────────┘
     │                                           ▼
     │                                   ┌────────────────┐
     │                                   │    hubspot     │
     │                                   │ (clone/patch)  │
     │                                   └───────┬────────┘
     │                                           │
     │  2. Final response with HubSpot links     │
     └◀──────────────────────────────────────────┘
```

**Steps:**

1. Slack POSTs to `/slack-campaign` with topic, audience, goal, optional template_id
2. App returns 200 OK immediately, posts "Processing..." to response_url
3. App fetches brand context from Google Drive (service account auth)
4. App generates 3 email variations via Claude API
5. App clones HubSpot template 3x, patches each with generated content
6. App posts final Slack message with HubSpot edit links
7. Full request logged to `logs/generations/`

## Service Interfaces

### brand_context.py

```python
# Abstract interface for future pluggability
class BrandContextProvider:
    def get_brand_context(self) -> BrandContext

# Google Drive implementation
class GoogleDriveBrandContext(BrandContextProvider):
    # Uses service account JSON key
    # Lists files in configured folder
    # Downloads and extracts text from docs
    # Categorizes by filename (voice, positioning, audience, examples)
```

### content_generator.py

```python
class ContentGenerator:
    def generate_variations(
        self,
        topic: str,
        audience: str,
        goal: str,
        brand_context: BrandContext
    ) -> list[EmailVariation]
    # Returns 3 variations: benefit-focused, story-driven, urgency-based
    # Each has: approach, subject, preview, body_html, cta_text
```

### hubspot.py

```python
class HubSpotClient:
    def clone_template(self, template_id: str, name: str) -> str  # returns clone ID
    def get_email_content(self, email_id: str) -> dict  # widget structure
    def patch_email(self, email_id: str, subject: str, body_html: str) -> str  # returns draft URL
```

## Configuration

### .env (secrets, gitignored)

```bash
ANTHROPIC_API_KEY=sk-ant-...
HUBSPOT_API_KEY=pat-na1-...
GOOGLE_SERVICE_ACCOUNT_JSON=/app/credentials/service-account.json
```

### config.yaml (client-specific, committed)

```yaml
hubspot:
  portal_id: "243444428"
  default_template_id: "314854693604"

google_drive:
  brand_folder_id: "1Pg4I6weH13KGviqYclJ4SK7WxmdKEffD"

slack:
  # No secrets here - Slack sends response_url with each request

logging:
  level: INFO
  output_dir: logs/
```

## Error Handling

| Stage | Error | Behavior |
|-------|-------|----------|
| Brand context | Drive API fails | Log error, continue with empty context (graceful degradation) |
| Content generation | Claude API fails | Post error message to Slack, log full error |
| HubSpot clone | API fails | Post error message to Slack, log full error |
| HubSpot patch | Partial failure | Report successful clones, note failures |

## Logging

```
logs/
├── app.log                           # General app logs (rotating)
└── generations/
    └── 2024-02-16_14-32-05_summer-sale.json   # Per-request log
```

**Per-request log contains:**

```json
{
  "timestamp": "2024-02-16T14:32:05Z",
  "slack_user": "scott.collier",
  "request": { "topic": "summer sale", "audience": "customers", "goal": "conversions" },
  "brand_context_files": ["voice_tone.docx", "positioning.pdf"],
  "variations": [ /* 3 generated variations */ ],
  "hubspot_drafts": [
    { "approach": "benefit-focused", "id": "12345", "url": "..." }
  ],
  "duration_seconds": 12.4
}
```

## Docker Setup

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### docker-compose.yml

```yaml
version: "3.8"
services:
  app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./.env:/app/.env
      - ./config.yaml:/app/config.yaml
      - ./credentials/:/app/credentials/
      - ./logs/:/app/logs/
    environment:
      - FLASK_ENV=development
```

### Running Locally

```bash
# Start the app
docker-compose up --build

# In another terminal, expose to Slack via ngrok
ngrok http 5000

# Configure Slack slash command to: https://<ngrok-url>/slack-campaign
```

## Dependencies

```
flask>=3.0
anthropic>=0.18
google-api-python-client>=2.0
google-auth>=2.0
requests>=2.31
pyyaml>=6.0
python-dotenv>=1.0
```

## Future Considerations

- **Pluggable brand sources:** S3, Notion, local files, etc.
- **Multiple clients:** Per-client config files or database
- **Production deployment:** Vercel, Railway, or similar
- **Additional channels:** Web UI, API endpoints beyond Slack
