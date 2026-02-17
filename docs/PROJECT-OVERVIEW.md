# HubSpot Content Generator - Project Overview

**Created:** 2025-02-16
**Purpose:** Convert n8n workflow to standalone Python application

---

## What We Built

A Dockerized Python Flask application that generates HubSpot marketing email variations via Slack commands. This replaces an n8n workflow with a standalone, maintainable codebase.

### The Flow

```
User types Slack command
        ↓
/campaign product-launch enterprise awareness 315102898877
        ↓
┌─────────────────────────────────────────────────────────┐
│                    Flask App (Docker)                    │
├─────────────────────────────────────────────────────────┤
│  1. Parse Slack command (topic, audience, goal, template)│
│  2. Return 200 OK immediately (Slack requires < 3 sec)   │
│  3. Spawn background thread for processing               │
└─────────────────────────────────────────────────────────┘
        ↓ (background thread)
┌─────────────────────────────────────────────────────────┐
│  Google Drive Service                                    │
│  - Fetch brand documents from configured folder          │
│  - Categorize by filename (voice, positioning, etc.)     │
│  - Extract text content                                  │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│  Claude AI Service (Anthropic API)                       │
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
│  - Clone template 3 times (one per variation)            │
│  - Patch each clone with generated content               │
│  - Return draft URLs                                     │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│  Slack Response                                          │
│  - Post message to response_url with draft links         │
│  - Log full request/response to logs/generations/        │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
application/
├── app.py                      # Flask app, Slack webhook endpoint
├── config.yaml                 # Client-specific settings (portal IDs, folder IDs)
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Local development setup
├── .env                        # Secrets (API keys) - gitignored
├── .env.example                # Template for .env
├── README.md                   # Setup instructions
│
├── models/
│   ├── __init__.py
│   └── schemas.py              # Data classes (SlackCommand, BrandContext, etc.)
│
├── services/
│   ├── __init__.py
│   ├── brand_context.py        # Google Drive integration (pluggable)
│   ├── content_generator.py    # Claude API integration
│   └── hubspot.py              # HubSpot API (clone/patch emails)
│
├── utils/
│   ├── __init__.py
│   └── logger.py               # Generation logging
│
├── tests/                      # Unit tests for each component
│   ├── test_app.py
│   ├── test_brand_context.py
│   ├── test_content_generator.py
│   ├── test_hubspot.py
│   ├── test_integration.py
│   └── test_logger.py
│
├── credentials/                # Service account JSON (gitignored)
│   └── README.md
│
└── logs/                       # Generation logs (gitignored)
    └── generations/
```

---

## Key Design Decisions

### 1. Slack Integration Pattern

Slack requires webhook responses within 3 seconds. We handle this by:
- Returning `200 OK` immediately
- Processing in a background thread
- Posting results to Slack's `response_url` when done

```python
@app.route("/slack-campaign", methods=["POST"])
def slack_campaign():
    command = SlackCommand.from_slack_body(request.form.to_dict())
    thread = threading.Thread(target=process_campaign, args=(command,))
    thread.start()
    return "", 200  # Immediate response
```

### 2. Pluggable Brand Context

Brand documents could come from anywhere. We designed an abstract interface:

```python
class BrandContextProvider(ABC):
    @abstractmethod
    def get_brand_context(self) -> BrandContext:
        pass

class GoogleDriveBrandContext(BrandContextProvider):
    # Current implementation
    pass

# Future: NotionBrandContext, S3BrandContext, etc.
```

### 3. Graceful Degradation

If brand context fails to load, the app continues with empty context rather than crashing. Claude will still generate emails, just without brand-specific guidance.

### 4. Docker + Volume Mounts

Configuration and secrets are mounted as volumes, not baked into the image:

```yaml
volumes:
  - ./.env:/app/.env              # Secrets
  - ./config.yaml:/app/config.yaml # Client settings
  - ./credentials/:/app/credentials/ # Service account
  - ./logs/:/app/logs/            # Persistent logs
```

This means you can:
- Update config without rebuilding
- Switch clients by swapping config files
- Keep logs between container restarts

### 5. Port 5001 (macOS Compatibility)

Port 5000 is used by macOS AirPlay Receiver. We map container port 5000 to host port 5001:

```yaml
ports:
  - "5001:5000"
```

---

## Configuration

### Secrets (.env)

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
HUBSPOT_API_KEY=pat-na1-...
GOOGLE_SERVICE_ACCOUNT_JSON=/app/credentials/service-account.json
```

### Client Settings (config.yaml)

```yaml
hubspot:
  portal_id: "243444428"
  default_template_id: "314854693604"

google_drive:
  brand_folder_id: "1Pg4I6weH13KGviqYclJ4SK7WxmdKEffD"

logging:
  level: INFO
  output_dir: logs/
```

---

## Running the Application

### Prerequisites

- Docker Desktop
- ngrok account (free tier works)
- API keys: Anthropic, HubSpot, Google Cloud service account

### Setup

```bash
cd application

# 1. Create .env with your API keys
cp .env.example .env
# Edit .env with real values

# 2. Add Google service account JSON
# Place in credentials/service-account.json

# 3. Update config.yaml with your IDs
# Edit hubspot.portal_id, hubspot.default_template_id, google_drive.brand_folder_id

# 4. Start the app
docker-compose up --build

# 5. Expose to internet (separate terminal)
ngrok http 5001

# 6. Configure Slack slash command
# Set Request URL to: https://<ngrok-url>/slack-campaign
```

### Slack Command Format

```
/campaign <topic> <audience> <goal> [template_id]
```

Examples:
```
/campaign product-launch enterprise awareness
/campaign summer-sale customers conversions 315102898877
/campaign newsletter subscribers engagement
```

---

## Scalability & Future Considerations

### Current Limitations (Demo Scope)

1. **Single-threaded background processing** - One request at a time
2. **No request queue** - Heavy load could overwhelm the app
3. **Local logs only** - No centralized logging
4. **No Slack signature verification** - Anyone with URL can trigger
5. **Debug mode enabled** - Not production-safe

### Scaling for Production

#### Level 1: Simple Improvements

```python
# Add Slack signature verification
import hmac
import hashlib

def verify_slack_signature(request):
    timestamp = request.headers.get('X-Slack-Request-Timestamp')
    signature = request.headers.get('X-Slack-Signature')
    # Verify using SLACK_SIGNING_SECRET
```

```python
# Disable debug mode
app.run(host="0.0.0.0", port=port, debug=False)
```

#### Level 2: Production Deployment

- **Gunicorn/uWSGI** instead of Flask dev server
- **Redis queue** (Celery/RQ) for background jobs
- **Cloud deployment** (Vercel, Railway, AWS ECS)
- **Centralized logging** (CloudWatch, Datadog)

#### Level 3: Multi-Tenant / Multi-Client

```yaml
# Per-client config structure
clients/
  ├── acme-corp/
  │   ├── config.yaml
  │   └── credentials/
  ├── globex/
  │   ├── config.yaml
  │   └── credentials/
```

```python
# Route by Slack workspace ID
@app.route("/slack-campaign", methods=["POST"])
def slack_campaign():
    team_id = request.form.get("team_id")
    client_config = load_client_config(team_id)
    # Use client-specific settings
```

#### Level 4: Enterprise Features

- **OAuth instead of API keys** for HubSpot/Google
- **User authentication** via Slack SSO
- **Usage tracking & billing**
- **A/B testing** of generated content
- **Approval workflows** before publishing

### Alternative Brand Context Sources

The pluggable interface makes it easy to add:

```python
class NotionBrandContext(BrandContextProvider):
    def get_brand_context(self) -> BrandContext:
        # Fetch from Notion API
        pass

class S3BrandContext(BrandContextProvider):
    def get_brand_context(self) -> BrandContext:
        # Fetch from S3 bucket
        pass

class LocalFileBrandContext(BrandContextProvider):
    def get_brand_context(self) -> BrandContext:
        # Read from local directory
        pass
```

---

## Development Workflow

### Running Tests

```bash
# All tests
cd application
python3 -m pytest tests/ -v

# Specific test file
python3 -m pytest tests/test_app.py -v
```

### Viewing Logs

```bash
# Docker container logs
docker-compose logs -f

# Generation logs (JSON files)
ls application/logs/generations/
cat application/logs/generations/2025-02-16_*.json | python3 -m json.tool
```

### Making Changes

```bash
# Rebuild after code changes
docker-compose down
docker-compose up --build

# Config changes don't require rebuild (volume mounted)
# Just restart:
docker-compose restart
```

---

## Original n8n Workflow

This application replaces the `HubSpot_Content_Generator_v1.0_PRODUCTION.json` n8n workflow which:

1. Received Slack webhooks
2. Parsed command parameters
3. Fetched brand context from Google Drive
4. Called Claude API for content generation
5. Cloned/patched HubSpot emails
6. Responded to Slack

The Python application provides:
- **Better maintainability** - Real code vs. visual workflow
- **Version control** - Git history for all changes
- **Testing** - Unit tests for each component
- **Debugging** - Proper logging and error handling
- **Flexibility** - Easy to extend and modify

---

## Files Reference

| File | Purpose |
|------|---------|
| `app.py` | Main Flask application, routes, orchestration |
| `models/schemas.py` | Data classes for type safety |
| `services/brand_context.py` | Google Drive integration |
| `services/content_generator.py` | Claude API integration |
| `services/hubspot.py` | HubSpot API integration |
| `utils/logger.py` | Generation logging |
| `config.yaml` | Client-specific settings |
| `.env` | API keys and secrets |
| `Dockerfile` | Container definition |
| `docker-compose.yml` | Development environment |

---

## Troubleshooting

### "Port 5000 already in use"

macOS AirPlay uses port 5000. We use 5001 instead. If you see this error, check `docker-compose.yml` has `"5001:5000"`.

### "Could not resolve authentication method"

Missing or invalid API key in `.env`. Check:
```bash
cat application/.env
# Verify ANTHROPIC_API_KEY is set correctly
```

### "ngrok not running"

Start ngrok in a separate terminal:
```bash
ngrok http 5001
```

### Google Drive errors

1. Check service account JSON exists at `credentials/service-account.json`
2. Verify service account has access to the Drive folder
3. Check `config.yaml` has correct `brand_folder_id`

### HubSpot clone fails

1. Verify `HUBSPOT_API_KEY` has Marketing Email permissions
2. Check template ID exists and is accessible
3. Review logs: `docker-compose logs -f`

---

## Summary

This project demonstrates how to convert a visual workflow (n8n) into a maintainable Python application while:

- Keeping the same user interface (Slack)
- Preserving all functionality
- Adding proper error handling and logging
- Designing for future extensibility
- Following software engineering best practices

The codebase is ready for demo use and provides a solid foundation for production deployment with the scaling considerations outlined above.
