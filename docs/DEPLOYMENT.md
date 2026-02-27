# Deployment Guide

## Local Development

### Start the app
```bash
docker-compose up --build
```

### Expose to internet (for Slack)
```bash
ngrok http 5001
```

Set your Slack slash command Request URL to:
```
https://<ngrok-subdomain>.ngrok.io/slack-campaign
```

### Config changes
Config is volume-mounted — no rebuild required:
```bash
docker-compose restart
```

### Log inspection
```bash
# Container logs
docker-compose logs -f

# Generation audit logs (JSON)
ls logs/
cat logs/2026-02-17_00-35-58_product-launch.json | python3 -m json.tool
```

---

## Running Tests

```bash
python -m pytest tests/ -v

# Single file
python -m pytest tests/test_hubspot.py -v
```

---

## Production Deployment Checklist

- [ ] Replace Flask dev server with Gunicorn: `CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]`
- [ ] Set `debug=False` in `app.py`
- [ ] Add Slack signature verification (HMAC via `X-Slack-Signature`)
- [ ] Add Redis + Celery for job queuing (replace threading)
- [ ] Set up centralized logging (CloudWatch / Datadog)
- [ ] Use secrets manager instead of `.env` file
- [ ] Add health check monitoring
- [ ] Configure HTTPS (not just ngrok tunnel)

---

## Troubleshooting

**Port 5000 already in use**  
macOS AirPlay uses port 5000. We map to 5001: check `docker-compose.yml` shows `"5001:5000"`.

**"Could not resolve authentication method"**  
Missing or invalid API key in `.env`. Run `cat .env` to verify.

**Google Drive errors**  
Check the service account JSON exists at `credentials/service-account.json`, the service account email has been shared on the Drive folder, and `config.yaml` has the correct `brand_folder_id`.

**HubSpot clone fails**  
Verify the `HUBSPOT_API_KEY` has Marketing Email permissions and the template ID exists in your portal. Check `docker-compose logs -f` for the full error.

**ngrok session expired**  
Free ngrok sessions expire. Restart ngrok and update the Slack Request URL with the new subdomain.
