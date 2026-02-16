# Credentials Folder

Place your Google Cloud service account JSON key file here.

## Setup

1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Save it as `service-account.json` in this folder
4. Update `.env` with: `GOOGLE_SERVICE_ACCOUNT_JSON=/app/credentials/service-account.json`

This folder is gitignored for security.
