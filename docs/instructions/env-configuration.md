# Environment Configuration (.env)

## Overview

The `.env` file contains all configuration variables for the Mojo Agency Bitrix24 integration project. This file is structured into logical sections for easy maintenance.

## File Structure

### 1. Google Cloud Platform Configuration

```bash
PROJECT_ID="mojo-478621"
GCP_REGION="europe-central2"
GCP_RUNTIME="python312"
```

**Purpose**: Core GCP settings used across all Cloud Functions and services.

- `PROJECT_ID`: GCP project identifier (standard variable name)
- `GCP_REGION`: Default region for deployments (europe-central2 = Warsaw)
- `GCP_RUNTIME`: Python runtime version for Cloud Functions

### 2. Bitrix24 Configuration

```bash
# Domain
B24_DOMAIN="mojo.bitrix24.pl"
BITRIX_HOST="https://mojo.bitrix24.pl"

# Webhooks (Legacy - for scripts)
BITRIX_WEBHOOK_GET="https://mojo.bitrix24.pl/rest/8/1fd4f6kwp9aenqb0/"
BITRIX_WEBHOOK_POST="https://mojo.bitrix24.pl/rest/8/tq8x3k9m1vzk2jzm/"
```

**Purpose**: Bitrix24 instance configuration.

- `B24_DOMAIN`: Domain without protocol (used in Cloud Functions)
- `BITRIX_HOST`: Full URL with protocol (used in scripts)
- `BITRIX_WEBHOOK_*`: Legacy webhooks for utility scripts

### 3. OAuth 2.0 Credentials

```bash
BITRIX_CLIENT_ID="local.696cd1f600d861.37534656"
BITRIX_CLIENT_SECRET="EPno5S9gNaz8CEKzjf7haTxB5XGndYV2TfpYbq0cvIkaXj5Ck1"
BITRIX_REFRESH_TOKEN="8c629469007fe7eb007cb77b00000008e0e307b55c8ab9f81cdaecf43ac892c7a85528"
```

**Purpose**: OAuth credentials for API authentication.

**Important**: These are also stored in Google Secret Manager:
- `b24-client-id`
- `b24-client-secret`
- `b24-refresh-token`
- `b24-access-token` (auto-refreshed every 45 minutes)

### 4. SPA 1106 Sync Configuration

#### Entity Type IDs

```bash
SPA_SPRAWY_ID="1106"              # Sprawy cudzoziemców
SPA_PODSTAWY_POBYTU_ID="1042"     # Podstawy pobytu
SPA_PRACA_ID="1046"               # Uprawnienia do pracy
SPA_PROCESY_ID="1110"             # Procesy legalizacyjne
```

#### Field IDs - Sprawy (1106)

```bash
FIELD_SPRAWY_PODSTAWY="ufCrm38_1768737959"           # Aktualne podstawy pobytu (links)
FIELD_SPRAWY_PODSTAWY_DATES="ufCrm38_1768738011252" # Data ważności podstawy pobytu (dates)
FIELD_SPRAWY_PRACA="ufCrm38_1768738112"             # Aktualne uprawnienia do pracy (links)
FIELD_SPRAWY_PRACA_DATES="ufCrm38_1768738327769"    # Data ważności uprawnienia do pracy (dates)
FIELD_SPRAWY_PROCESY="ufCrm38_1768738413"           # Aktualne procesy legalizacyjne (links)
```

#### Field IDs - Related SPAs

```bash
FIELD_PODSTAWY_DATA_DO_KIEDY="ufCrm10_1763581700754"  # Podstawy: Data do kiedy
FIELD_PRACA_DATA_WAZNOSCI="ufCrm12_1764516949310"     # Praca: Data ważności
```

## Usage in Services

### Cloud Functions

All Cloud Functions automatically load these variables during deployment via `deploy.sh` scripts:

```bash
source "$ENV_FILE"

gcloud functions deploy my-function \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,B24_DOMAIN=$B24_DOMAIN,..."
```

### Python Scripts

Scripts can load the `.env` file using `python-dotenv`:

```python
from dotenv import load_dotenv
import os

load_dotenv()

project_id = os.getenv("PROJECT_ID")
b24_domain = os.getenv("B24_DOMAIN")
```

### Deployment Scripts

The `deploy.sh` scripts source the `.env` file:

```bash
source "$SCRIPT_DIR/../../../.env"
echo "Deploying to project: $PROJECT_ID"
```

## Deployed Services

The following services use these configuration variables:

### 1. b24-token-refresh
- **Schedule**: Every 45 minutes
- **Purpose**: Auto-refresh OAuth access tokens
- **Variables**: `PROJECT_ID`, `BITRIX_CLIENT_ID`, `BITRIX_CLIENT_SECRET`

### 2. b24-spa-1106-http
- **Trigger**: HTTP webhook from Bitrix24
- **Purpose**: Receive events and publish to Pub/Sub
- **Variables**: All SPA and field IDs

### 3. b24-spa-1106-sync-worker
- **Trigger**: Pub/Sub messages
- **Purpose**: Process sync events
- **Variables**: All SPA and field IDs, domain, secrets

### 4. b24-spa-1106-daily-sync
- **Schedule**: Daily at 03:00 Warsaw time
- **Purpose**: Full sync of all active Sprawy
- **Variables**: `PROJECT_ID`, `B24_DOMAIN`, `SPA_SPRAWY_ID`

## Security Notes

### Sensitive Data

The following variables contain sensitive data:
- `BITRIX_CLIENT_SECRET`
- `BITRIX_REFRESH_TOKEN`
- `BITRIX_WEBHOOK_*`

**Important**:
- ✅ `.env` is in `.gitignore` (never committed)
- ✅ Secrets are stored in Google Secret Manager
- ✅ Cloud Functions access secrets at runtime
- ❌ Never hardcode secrets in code

### Secret Manager Storage

Secrets stored in Google Secret Manager:

```bash
# View secrets
gcloud secrets list --project=mojo-478621

# Access a secret
gcloud secrets versions access latest \
  --secret=b24-access-token \
  --project=mojo-478621
```

## Maintenance

### Adding New Variables

1. Add to `.env` file in appropriate section
2. Update this documentation
3. Update relevant `deploy.sh` scripts
4. Redeploy affected services

### Updating Field IDs

If Bitrix24 field IDs change:

1. Update field IDs in `.env`
2. Redeploy all sync services:
   ```bash
   cd google-cloud/b24-spa-1106-sync/b24-spa-1106-sync-worker
   ./deploy.sh
   ```

### Rotating Secrets

To rotate OAuth credentials:

1. Generate new credentials in Bitrix24
2. Update `.env` file
3. Update Secret Manager:
   ```bash
   echo -n "new_secret" | gcloud secrets versions add b24-client-secret --data-file=-
   ```
4. Redeploy token refresh function

## Backup

A backup of the old `.env` is saved as `.env.backup`:

```bash
# View backup
cat .env.backup

# Restore if needed
cp .env.backup .env
```

## Related Documentation

- [OAuth Setup Guide](./b24-oauth-setup.md)
- [Logging Guide](./logging-guide.md)
- [Environment Setup](./env-setup.md)
