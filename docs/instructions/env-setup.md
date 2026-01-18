# Environment Configuration Guide (.env)

> **Comprehensive guide for setting up and managing environment variables**
>
> Version: 1.0 | Last Updated: 2026-01-04

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [File Location](#file-location)
3. [Security Best Practices](#security-best-practices)
4. [Required Variables](#required-variables)
5. [Optional Variables](#optional-variables)
6. [Setup Instructions](#setup-instructions)
7. [Validation](#validation)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The `.env` file contains **environment-specific configuration** for the Bergermann project. This file is:

- ✅ **Excluded from Git** (via `.gitignore`)
- ✅ **Required for deployment** (Cloud Functions, local development)
- ✅ **Shared across all services** (single source of truth)
- ⚠️ **Contains sensitive data** (API keys, secrets)

**Purpose:**
- Centralized configuration management
- Separation of code and configuration
- Easy environment switching (dev/staging/prod)
- Secure credential storage

---

## 📂 File Location

```
/Users/Dev/bergermann/.env
```

**Structure:**
```
bergermann/
├── .env                    # ← Main configuration file
├── .env.example            # ← Template (safe to commit)
├── .gitignore              # ← Must include .env
└── google-cloud/
    └── */deploy.sh         # ← Scripts that source .env
```

---

## 🔒 Security Best Practices

### ✅ DO

1. **Keep `.env` out of version control**
   ```bash
   # .gitignore
   .env
   .env.local
   .env.*.local
   ```

2. **Use environment-specific files**
   ```
   .env              # Production
   .env.development  # Development
   .env.staging      # Staging
   ```

3. **Restrict file permissions**
   ```bash
   chmod 600 .env
   ```

4. **Use Secret Manager for production**
   - Store sensitive values in Google Secret Manager
   - Reference secrets in Cloud Functions
   - Never hardcode secrets in code

5. **Document all variables**
   - Create `.env.example` with descriptions
   - Keep this guide updated

6. **Rotate credentials regularly**
   - API keys every 90 days
   - OAuth secrets every 180 days
   - Access tokens as needed

### ❌ DON'T

1. ❌ Commit `.env` to Git
2. ❌ Share `.env` via email/Slack
3. ❌ Include `.env` in Docker images
4. ❌ Log environment variables
5. ❌ Use production credentials locally
6. ❌ Store `.env` in cloud storage without encryption

---

## 📝 Required Variables

### 1. Google Cloud Platform

```bash
# Project Configuration
PROJECT_NUMBER="612210466256"           # GCP Project Number (numeric ID)
PROJECT_ID="bergermann"                 # GCP Project ID (string identifier)
GCP_REGION="europe-central2"            # Primary deployment region
GCP_RUNTIME="python314"                 # Cloud Functions runtime version
```

**How to get:**
```bash
# Project ID
gcloud config get-value project

# Project Number
gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)"

# Available regions
gcloud functions regions list

# Available runtimes
gcloud functions runtimes list
```

**Notes:**
- `PROJECT_NUMBER`: Used for service accounts, IAM
- `PROJECT_ID`: Used for resource naming, API calls
- `GCP_REGION`: Choose closest to users (europe-central2 = Warsaw)
- `GCP_RUNTIME`: Must match requirements.txt Python version

---

### 2. Bitrix24 Configuration

```bash
# OAuth Application Credentials
B24_CLIENT_ID="local.694ff4e64627d8.70225405"
B24_CLIENT_SECRET="ToRUabZ1bpUravPh79oVzqbP9gDX6Nj2XXZZq1j31493kbHZgN"

# Instance Configuration
B24_DOMAIN="bergermann.bitrix24.pl"
```

**How to get:**
1. Go to Bitrix24: **Settings → Developer Resources → OAuth Applications**
2. Create new application:
   - **Name:** Bergermann Integration
   - **Redirect URI:** `https://oauth.pstmn.io/v1/callback`
   - **Permissions:** Full access (for development)
3. Copy `Client ID` and `Client Secret`

**Security:**
- ⚠️ `B24_CLIENT_SECRET` is highly sensitive
- Store in Secret Manager for production
- Rotate every 6 months

**Documentation:**
- [OAuth Setup Guide](./oauth-setup.md)
- [Bitrix24 OAuth Docs](https://dev.1c-bitrix.ru/rest_help/oauth/)

---

### 3. AI Services

```bash
# Google Gemini API
GEMINI_API_KEY="AIzaSyBQNfYc21TmvC33j8wicYdEluTqkqdjHV8"
```

**How to get:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API key
3. Enable Gemini API in your project

**Usage:**
- Document parsing (OCR → structured data)
- File categorization
- Text extraction and analysis

**Limits:**
- Free tier: 60 requests/minute
- Check quota: [Google Cloud Console](https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas)

---

### 4. Document AI (OCR)

```bash
# Document AI Processor
OCR_PROCESSOR_ID="49bc90a852a7babf"
OCR_LOCATION="eu"
```

**How to get:**
1. Go to [Document AI Console](https://console.cloud.google.com/ai/document-ai/processors)
2. Create processor:
   - **Type:** Document OCR
   - **Location:** EU (GDPR compliance)
3. Copy Processor ID from URL or details page

**Locations:**
- `us`: United States
- `eu`: European Union (GDPR compliant)
- `asia`: Asia Pacific

**Cost:**
- First 1,000 pages/month: Free
- After: $1.50 per 1,000 pages
- [Pricing Details](https://cloud.google.com/document-ai/pricing)

---

## 🔧 Optional Variables

### Development & Testing

```bash
# Local Development
DEBUG="true"                            # Enable debug logging
LOG_LEVEL="INFO"                        # DEBUG, INFO, WARNING, ERROR
ENVIRONMENT="development"               # development, staging, production

# Testing
TEST_MODE="false"                       # Skip external API calls
MOCK_BITRIX="false"                     # Use mock Bitrix24 responses
```

### Webhook Configuration

```bash
# Bitrix24 Webhooks (Alternative to OAuth)
BITRIX_WEBHOOK_GET="https://bergermann.bitrix24.pl/rest/1/xxxxx/"
BITRIX_WEBHOOK_POST="https://bergermann.bitrix24.pl/rest/1/xxxxx/"
```

**When to use:**
- Quick testing without OAuth
- Read-only operations
- Automation scripts

**Limitations:**
- ⚠️ Less secure than OAuth
- ⚠️ No user context
- ⚠️ Limited to specific user permissions

### Performance Tuning

```bash
# Request Timeouts
BITRIX_REQUEST_TIMEOUT="10"             # Seconds
DOCUMENT_AI_TIMEOUT="60"                # Seconds for OCR
GEMINI_TIMEOUT="30"                     # Seconds for AI parsing

# Retry Configuration
MAX_RETRIES="3"                         # Number of retry attempts
RETRY_DELAY="2"                         # Seconds between retries
```

### Feature Flags

```bash
# Enable/Disable Features
ENABLE_OCR="true"                       # OCR processing
ENABLE_CATEGORIZATION="true"            # File categorization
ENABLE_TIMELINE_POSTS="true"            # Bitrix24 timeline updates
ENABLE_DAILY_SYNC="true"                # Daily synchronization jobs
```

---

## 🚀 Setup Instructions

### Step 1: Create .env file

```bash
cd /Users/Dev/bergermann
touch .env
chmod 600 .env
```

### Step 2: Copy template

```bash
# Copy from example (if exists)
cp .env.example .env

# Or create from scratch
cat > .env << 'EOF'
# Google Cloud Platform
PROJECT_NUMBER=""
PROJECT_ID=""
GCP_REGION="europe-central2"
GCP_RUNTIME="python314"

# Bitrix24
B24_CLIENT_ID=""
B24_CLIENT_SECRET=""
B24_DOMAIN=""

# AI Services
GEMINI_API_KEY=""

# Document AI
OCR_PROCESSOR_ID=""
OCR_LOCATION="eu"
EOF
```

### Step 3: Fill in values

1. **Get GCP values:**
   ```bash
   gcloud config get-value project
   gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)"
   ```

2. **Get Bitrix24 credentials:**
   - Follow [OAuth Setup Guide](./oauth-setup.md)
   - Or use webhook URLs for testing

3. **Get API keys:**
   - Gemini: [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Document AI: [Console](https://console.cloud.google.com/ai/document-ai/processors)

### Step 4: Validate

```bash
# Check file exists and is readable
test -f .env && echo "✅ .env exists" || echo "❌ .env missing"

# Check permissions (should be 600 or 400)
ls -l .env | grep -q "rw-------" && echo "✅ Permissions OK" || echo "⚠️ Check permissions"

# Validate required variables
source .env
for var in PROJECT_ID GCP_REGION B24_DOMAIN; do
    [ -z "${!var}" ] && echo "❌ Missing: $var" || echo "✅ $var set"
done
```

### Step 5: Test configuration

```bash
# Test GCP connection
gcloud config set project $PROJECT_ID
gcloud projects describe $PROJECT_ID

# Test Bitrix24 connection
curl "https://$B24_DOMAIN/rest/crm.contact.list.json?auth=YOUR_TOKEN" | jq .
```

---

## ✅ Validation

### Automated Validation Script

Create `scripts/validate-env.sh`:

```bash
#!/bin/bash
# Validate .env configuration

set -e

ENV_FILE=".env"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Validating .env configuration..."
echo ""

# Check file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Check permissions
PERMS=$(stat -f %A "$ENV_FILE" 2>/dev/null || stat -c %a "$ENV_FILE" 2>/dev/null)
if [ "$PERMS" != "600" ] && [ "$PERMS" != "400" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env permissions are $PERMS (should be 600)${NC}"
fi

# Load environment
source "$ENV_FILE"

# Required variables
REQUIRED_VARS=(
    "PROJECT_ID"
    "GCP_REGION"
    "B24_DOMAIN"
)

# Check required variables
MISSING=0
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Missing required variable: $var${NC}"
        MISSING=1
    else
        echo -e "${GREEN}✅ $var: ${!var}${NC}"
    fi
done

# Optional but recommended
OPTIONAL_VARS=(
    "GEMINI_API_KEY"
    "OCR_PROCESSOR_ID"
    "B24_CLIENT_ID"
    "B24_CLIENT_SECRET"
)

echo ""
echo "📋 Optional variables:"
for var in "${OPTIONAL_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${YELLOW}⚠️  $var: not set${NC}"
    else
        # Show first 10 chars only
        VALUE="${!var:0:10}..."
        echo -e "${GREEN}✅ $var: $VALUE${NC}"
    fi
done

echo ""
if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}✅ All required variables are set${NC}"
    exit 0
else
    echo -e "${RED}❌ Some required variables are missing${NC}"
    exit 1
fi
```

**Usage:**
```bash
chmod +x scripts/validate-env.sh
./scripts/validate-env.sh
```

---

## 🐛 Troubleshooting

### Issue: Variables not loaded in deploy scripts

**Symptoms:**
```
❌ ERROR: Configure BITRIX_WEBHOOK_GET or BITRIX_HOST in .env.
```

**Solution:**
```bash
# Check if .env is sourced in deploy script
grep "source.*\.env" google-cloud/*/deploy.sh

# Verify path is correct
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../../../.env"
echo "Looking for .env at: $ENV_FILE"
test -f "$ENV_FILE" && echo "Found" || echo "Not found"
```

### Issue: Permission denied

**Symptoms:**
```
bash: .env: Permission denied
```

**Solution:**
```bash
# Fix permissions
chmod 600 .env

# Check ownership
ls -l .env
# Should show your user as owner
```

### Issue: Variables with quotes

**Problem:**
```bash
PROJECT_ID="bergermann"  # Wrong in some contexts
```

**Solution:**
```bash
# In .env file, quotes are optional but recommended
PROJECT_ID="bergermann"   # OK
PROJECT_ID=bergermann     # Also OK

# When sourcing, both work:
source .env
echo $PROJECT_ID  # Outputs: bergermann (no quotes)
```

### Issue: Multiline values

**Problem:**
```bash
# This breaks:
PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...
-----END PRIVATE KEY-----"
```

**Solution:**
```bash
# Option 1: Escape newlines
PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...\n-----END PRIVATE KEY-----"

# Option 2: Use Secret Manager (recommended)
# Store in Secret Manager, reference by name
PRIVATE_KEY_SECRET="projects/bergermann/secrets/private-key/versions/latest"
```

### Issue: Special characters in values

**Problem:**
```bash
PASSWORD=P@ssw0rd!  # @ and ! may cause issues
```

**Solution:**
```bash
# Always quote values with special characters
PASSWORD="P@ssw0rd!"

# Or escape special characters
PASSWORD=P\@ssw0rd\!
```

---

## 📚 Related Documentation

- [OAuth Setup Guide](./oauth-setup.md) - Bitrix24 OAuth configuration
- [Logging Guide](./logging-guide.md) - Logging best practices
- [Deployment Guide](../README.md) - Cloud Functions deployment

---

## 🔄 Version History

### 2026-01-04 (v1.0)
- ✅ Initial version
- ✅ Complete variable documentation
- ✅ Security best practices
- ✅ Validation script
- ✅ Troubleshooting guide

---

## 📞 Support

**Issues with .env configuration?**

1. Check this guide first
2. Run validation script: `./scripts/validate-env.sh`
3. Check related documentation
4. Contact: info@keyframelab.com

---

**Author:** KeyFrame Lab  
**Version:** 1.0  
**Last Updated:** 2026-01-04



