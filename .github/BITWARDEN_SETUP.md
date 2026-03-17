# Bitwarden Secrets Manager – GitHub Actions Setup

All environment variables must come from Bitwarden. No defaults are used anywhere.

## Overview

- **BW_ACCESS_TOKEN**: Stored in GitHub Secrets (Bitwarden machine account token)
- **BW_SECRET_ID_CONFIG**: Stored in GitHub Secrets (UUID of the pulsestream-config secret)
- **pulsestream-config**: Single Bitwarden secret containing a JSON object with all env vars

Used by **CI** (tests) and **CD** (deploy). For CD, use production values (e.g. `ENVIRONMENT=production`, prod DB password). CD overrides `POSTGRES_HOST` and `REDIS_HOST` to `postgres`/`redis` for Docker networking.

## Step 1: Create the Config Secret in Bitwarden

1. Go to [Bitwarden Secrets Manager](https://bitwarden.com/products/secrets-manager/)
2. Create a **Project** (e.g. `pulsestream`)
3. Create a **Secret** named `pulsestream-config`
4. Set the secret value to a JSON object with all required keys:

```json
{
  "APP_NAME": "Pulsestream",
  "APP_VERSION": "0.1.0",
  "BASE_URL": "http://localhost:8000",
  "SUPPORT_EMAIL": "your-email@example.com",
  "ENVIRONMENT": "development",
  "DEBUG": "true",
  "LOG_LEVEL": "INFO",
  "HOST": "0.0.0.0",
  "PORT": "8000",
  "WORKERS": "4",
  "POSTGRES_HOST": "localhost",
  "POSTGRES_PORT": "5432",
  "POSTGRES_USER": "pulsestream",
  "POSTGRES_PASSWORD": "your-secure-password",
  "POSTGRES_DB": "pulsestream_db",
  "POSTGRES_POOL_SIZE": "20",
  "POSTGRES_MAX_OVERFLOW": "10",
  "REDIS_HOST": "localhost",
  "REDIS_PORT": "6379",
  "REDIS_PASSWORD": "",
  "REDIS_DB": "0",
  "REDIS_POOL_SIZE": "10",
  "REDIS_STREAM_USER_EVENTS": "events:user",
  "REDIS_STREAM_ACTIVITY_EVENTS": "events:activity",
  "REDIS_STREAM_TRANSACTION_EVENTS": "events:transaction",
  "REDIS_STREAM_SYSTEM_EVENTS": "events:system",
  "REDIS_CONSUMER_GROUP": "event-processors",
  "REDIS_STREAM_MAXLEN": "100000",
  "REDIS_BATCH_SIZE": "100",
  "EVENT_BATCH_SIZE": "500",
  "PROCESSING_TIMEOUT": "30",
  "MAX_RETRIES": "3",
  "RAW_EVENTS_RETENTION_DAYS": "90",
  "MINUTE_AGG_RETENTION_DAYS": "7",
  "HOURLY_AGG_RETENTION_DAYS": "90",
  "DAILY_AGG_RETENTION_DAYS": "730",
  "ADMIN_API_KEY": "your-admin-api-key",
  "USER_API_KEY": "your-user-api-key",
  "ENABLE_RATE_LIMITING": "true",
  "DEFAULT_RATE_LIMIT": "100/minute"
}
```

5. Copy the **Secret ID** (UUID) shown in Bitwarden

## Step 2: GitHub Repository Secrets

1. In your repo: **Settings → Secrets and variables → Actions**
2. Add:

   | Name                 | Value                              |
   |----------------------|------------------------------------|
   | `BW_ACCESS_TOKEN`    | Bitwarden machine account token    |
   | `BW_SECRET_ID_CONFIG`| UUID of pulsestream-config secret  |

## Step 3: Local Development

For local runs (including `docker-compose`), populate `.env` from Bitwarden. Example using Bitwarden CLI:

```bash
bw get secret <pulsestream-config-secret-id> | jq -r 'to_entries | .[] | "\(.key)=\(.value)"' > .env
```

Or manually copy the JSON values into a `.env` file (one `KEY=value` per line).

## CI-Specific Overrides

For CI, `POSTGRES_HOST` and `REDIS_HOST` must be `localhost` (tests run on the runner). The JSON above uses `localhost`; when running in Docker, override in your `.env` with `postgres` and `redis` for the app/worker services.

## Self-Hosted Bitwarden

Add to the Bitwarden step in the workflow:

```yaml
with:
  access_token: ${{ secrets.BW_ACCESS_TOKEN }}
  base_url: https://your-bitwarden-domain.com
```

## EU Region

For `vault.bitwarden.eu`:

```yaml
with:
  access_token: ${{ secrets.BW_ACCESS_TOKEN }}
  cloud_region: eu
```
