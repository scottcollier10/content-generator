# credentials/

This directory holds sensitive service account credentials and is **gitignored**.

## Setup

1. Create a Google Cloud service account with **Google Drive API** read access.
2. Download the JSON key file.
3. Rename it to `service-account.json` and place it here.
4. Share your Google Drive brand folder with the service account email address.

## File expected

```
credentials/
└── service-account.json   ← gitignored, never commit this
```

## Environment variable

The path is configured via `.env`:

```env
GOOGLE_SERVICE_ACCOUNT_JSON=/app/credentials/service-account.json
```

> **Never commit `service-account.json` to version control.**
