# HubSpot Content Generator

A Dockerized Flask application that generates HubSpot email variations via Slack commands.

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This application:
1. Receives Slack slash commands with topic, audience, and goal
2. Fetches brand context from Google Drive
3. Generates 3 email variations using Claude AI
4. Creates draft emails in HubSpot
5. Returns links to the drafts via Slack

## Prerequisites

- Docker and Docker Compose
- Google Cloud service account with Drive API access
- Anthropic API key
- HubSpot API key (with Marketing Email scope)
- Slack app with slash command configured

## Setup

### 1. Clone and configure

```bash
cd application
cp .env.example .env
```

### 2. Edit `.env` with your credentials

```bash
ANTHROPIC_API_KEY=sk-ant-...
HUBSPOT_API_KEY=pat-na1-...
GOOGLE_SERVICE_ACCOUNT_JSON=/app/credentials/service-account.json
```

### 3. Add Google service account

Place your service account JSON key in `credentials/service-account.json`

### 4. Update `config.yaml`

Set your client-specific values:
- `hubspot.portal_id`
- `hubspot.default_template_id`
- `google_drive.brand_folder_id`

## Running

### Start the application

```bash
docker-compose up --build
```

### Expose to Slack (development)

```bash
ngrok http 5001
```

Configure your Slack slash command to: `https://<ngrok-url>/slack-campaign`

## Slack Command Usage

```
/campaign topic="Summer Sale" audience="Existing customers" goal="Drive conversions"
```

Optional: Add `template_id="12345"` to use a specific HubSpot template.

## Architecture

```
Slack → Flask → Google Drive (brand context)
                    ↓
              Claude AI (generation)
                    ↓
              HubSpot (create drafts)
                    ↓
              Slack (return links)
```

## Logs

Generation logs are saved to `logs/generations/` with full request/response details.
