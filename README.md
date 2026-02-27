# HubSpot Content Generator

> AI-powered email content generation via Slack. Type one command, get three brand-aware email drafts in HubSpot in under 20 seconds.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?logo=flask)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Sonnet_4-orange)
![HubSpot](https://img.shields.io/badge/HubSpot-Marketing_API-FF7A59?logo=hubspot)

---

## What It Does

A single Slack command triggers a fully automated pipeline:

```
/campaign webinar CFOs engagement
```

**~15 seconds later, in Slack:**

```
✅ 3 Email Variations Ready!

1. BENEFIT-FOCUSED  — Subject: "Your CFO peers are already ahead..."
   [Edit in HubSpot]

2. STORY-DRIVEN  — Subject: "The quarter-end scramble nobody talks about"
   [Edit in HubSpot]

3. URGENCY-BASED  — Subject: "Last chance: CFO webinar seats filling fast"
   [Edit in HubSpot]
```

Every draft:
- Uses **your existing HubSpot template** (header, footer, brand colors all preserved)
- Is written in **your brand voice** (loaded from Google Drive brand docs)
- Is immediately editable and sendable in HubSpot

---

## Architecture

```
Slack Slash Command
        ↓
    Flask App (Docker)
    ├─ Return 200 OK immediately (Slack requires < 3s)
    └─ Spawn background thread
            ↓
    Google Drive
    └─ Fetch brand markdown files (voice, positioning, audience, examples)
            ↓
    Claude API (Anthropic)
    └─ Generate 3 variations with brand context injected into prompt
    └─ Returns: benefit-focused | story-driven | urgency-based
            ↓
    HubSpot Marketing API
    └─ Clone template ×3 (preserves layout)
    └─ Patch each clone with AI-generated content
    └─ Return editable draft URLs
            ↓
    Slack Response
    └─ Post rich message with clickable HubSpot links
```

---

## Project Structure

```
content-generator/
├── app.py                    # Flask app, Slack endpoint, orchestration
├── config.yaml               # Client-specific IDs (portal, templates, Drive folder)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example              # Template for your .env secrets
├── models/
│   └── schemas.py             # Data classes: SlackCommand, BrandContext, EmailVariation...
├── services/
│   ├── brand_context.py       # Google Drive integration (pluggable abstract interface)
│   ├── content_generator.py   # Claude API integration + prompt builder
│   └── hubspot.py             # HubSpot clone → patch email workflow
├── utils/
│   └── logger.py              # App logger + JSON generation audit log
├── tests/
│   ├── test_app.py
│   └── test_hubspot.py
├── credentials/              # gitignored — place service-account.json here
├── logs/                     # gitignored — JSON audit log per generation
└── docs/                     # Architecture, lessons learned, deployment notes
```

---

## Quick Start

### Prerequisites

- Docker Desktop
- [ngrok](https://ngrok.com) (free tier)
- API keys: Anthropic, HubSpot (Private App token), Google Cloud service account

### 1. Clone and configure

```bash
git clone https://github.com/scottcollier10/content-generator.git
cd content-generator

# Copy the env template and fill in your keys
cp .env.example .env
```

Edit `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
HUBSPOT_API_KEY=pat-na1-...
GOOGLE_SERVICE_ACCOUNT_JSON=/app/credentials/service-account.json
```

Edit `config.yaml`:
```yaml
hubspot:
  portal_id: "YOUR_PORTAL_ID"
  default_template_id: "YOUR_TEMPLATE_ID"

google_drive:
  brand_folder_id: "YOUR_DRIVE_FOLDER_ID"
```

### 2. Add Google credentials

Place your service account JSON at:
```
credentials/service-account.json
```

See `credentials/README.md` for setup instructions.

### 3. Run

```bash
docker-compose up --build
```

### 4. Expose via ngrok

```bash
# In a separate terminal
ngrok http 5001
```

### 5. Configure Slack

In your Slack app settings, set the slash command Request URL to:
```
https://<your-ngrok-url>/slack-campaign
```

---

## Slack Command Reference

```
/campaign <topic> <audience> <goal> [template_id]
```

| Parameter | Required | Description |
|---|---|---|
| `topic` | Yes | Campaign subject (e.g. `webinar`, `product-launch`) |
| `audience` | Yes | Target audience (e.g. `CFOs`, `enterprise`, `partners`) |
| `goal` | Yes | Campaign objective (e.g. `engagement`, `conversions`, `awareness`) |
| `template_id` | No | HubSpot email template ID. Omit to use config default. |

**Examples:**
```bash
/campaign webinar CFOs engagement
/campaign product-launch enterprise awareness 315102898877
/campaign newsletter subscribers retention
```

---

## Brand Context

The system loads brand documents from a Google Drive folder and categorizes them by filename:

| Filename contains | Feeds into |
|---|---|
| `voice`, `tone` | Brand voice & tone section |
| `position`, `messaging`, `value_prop` | Positioning section |
| `audience`, `persona`, `icp`, `segment` | Target audience section |
| `copy`, `example`, `case`, `campaign`, `landing` | Example copy section |

All four sections are injected into the Claude prompt. The more brand docs you provide, the more consistent the output.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## How the HubSpot Integration Works

HubSpot's API doesn't have a `/clone` endpoint, so we implement the pattern manually:

1. **GET** the source template to retrieve its full structure
2. **POST** a new email using that structure (preserves layout, footer, unsubscribe)
3. **GET** the clone to read its exact widget IDs
4. **PATCH** the clone to inject AI content into the body widget

Widget discovery is dynamic — works with both classic templates (`hs_email_body`) and drag-and-drop templates (auto-detected by widget path).

---

## Extending the Brand Context Source

The brand context provider is an abstract interface. Swap out Google Drive for any source:

```python
class NotionBrandContext(BrandContextProvider):
    def get_brand_context(self) -> BrandContext:
        # Fetch from Notion API
        ...

class S3BrandContext(BrandContextProvider):
    def get_brand_context(self) -> BrandContext:
        # Fetch from S3 bucket
        ...
```

---

## Docs

- [`docs/PROJECT-OVERVIEW.md`](docs/PROJECT-OVERVIEW.md) — Full architecture and design decisions
- [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md) — Debugging notes, n8n patterns, multi-model strategy
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — Production deployment guide
- [`docs/NEXT_STEPS.md`](docs/NEXT_STEPS.md) — Roadmap and phase 2 features

---

## Tech Stack

| Layer | Technology |
|---|---|
| App framework | Flask 3 + Python 3.12 |
| AI generation | Anthropic Claude Sonnet 4 |
| Email platform | HubSpot Marketing Hub API |
| Brand context | Google Drive API + service account |
| Trigger | Slack slash commands |
| Infrastructure | Docker + docker-compose |
| Tunnel (dev) | ngrok |

---

## License

MIT
