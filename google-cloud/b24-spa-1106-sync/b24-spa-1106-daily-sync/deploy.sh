#!/bin/bash
# Deploy script for B24 SPA 1106 Daily Sync
# Scheduled function that syncs all active Sprawy cudzoziemców daily

set -e

# Load environment variables from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../../../.env"

if [ -f "$ENV_FILE" ]; then
    echo "📦 Loading config from $ENV_FILE"
    source "$ENV_FILE"
else
    echo "❌ Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Function-specific configuration
FUNCTION_NAME="b24-spa-1106-daily-sync"
TOPIC_NAME="b24-spa-1106-sync-events"
SCHEDULER_JOB_NAME="b24-spa-1106-daily-sync-job"
SCHEDULE="0 3 * * *"  # 03:00 every day
TIMEZONE="Europe/Warsaw"

echo ""
echo "🚀 Deploying $FUNCTION_NAME to $GCP_REGION..."
echo "   Project: $PROJECT_ID"
echo ""

# Deploy HTTP triggered function
gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=$GCP_RUNTIME \
  --region=$GCP_REGION \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --memory=256MB \
  --timeout=300s \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,B24_DOMAIN=mojo.bitrix24.pl,ACCESS_TOKEN_SECRET=b24-access-token,TOPIC_NAME=$TOPIC_NAME,SPA_SPRAWY_ID=1106"

# Get function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$GCP_REGION --format='value(serviceConfig.uri)')

echo ""
echo "✅ Function deployed!"
echo "   URL: $FUNCTION_URL"
echo ""

# Create or update Cloud Scheduler job
echo "📅 Setting up Cloud Scheduler job..."

# Check if job exists
if gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location=$GCP_REGION --project=$PROJECT_ID &>/dev/null; then
    echo "   Updating existing scheduler job..."
    gcloud scheduler jobs update http $SCHEDULER_JOB_NAME \
      --location=$GCP_REGION \
      --project=$PROJECT_ID \
      --schedule="$SCHEDULE" \
      --uri="$FUNCTION_URL" \
      --http-method=POST \
      --time-zone="$TIMEZONE" \
      --attempt-deadline=600s
else
    echo "   Creating new scheduler job..."
    gcloud scheduler jobs create http $SCHEDULER_JOB_NAME \
      --location=$GCP_REGION \
      --project=$PROJECT_ID \
      --schedule="$SCHEDULE" \
      --uri="$FUNCTION_URL" \
      --http-method=POST \
      --time-zone="$TIMEZONE" \
      --attempt-deadline=600s
fi

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Configuration:"
echo "   Function: $FUNCTION_NAME"
echo "   URL: $FUNCTION_URL"
echo "   Scheduler: $SCHEDULER_JOB_NAME"
echo "   Schedule: $SCHEDULE ($TIMEZONE)"
echo ""
echo "📊 Architecture:"
echo "   Cloud Scheduler ($SCHEDULE)"
echo "           ↓"
echo "   $FUNCTION_NAME"
echo "           ↓ (publishes N messages)"
echo "   Pub/Sub: $TOPIC_NAME"
echo "           ↓"
echo "   b24-spa-1106-sync-worker (parallel processing)"
echo ""
echo "🧪 To test manually:"
echo "   curl -X POST $FUNCTION_URL"
echo ""
echo "📊 To run scheduler job now:"
echo "   gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$GCP_REGION"
echo ""
