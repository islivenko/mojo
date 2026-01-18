#!/bin/bash
# Deploy script for B24 Token Refresh
# Uses Secret Manager for OAuth tokens with auto-cleanup

set -e

# Load environment variables from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../../.env"

if [ -f "$ENV_FILE" ]; then
    echo "📦 Loading config from $ENV_FILE"
    source "$ENV_FILE"
else
    echo "❌ Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Configuration from .env
FUNCTION_NAME="b24-token-refresh"
TOPIC_NAME="b24-token-refresh-trigger"

echo "🚀 Deploying $FUNCTION_NAME to $PROJECT_ID..."

gcloud config set project $PROJECT_ID

# Grant Secret Manager admin access for the service account
# (needed to create/destroy secret versions)
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
echo "📝 Granting Secret Manager access to $SERVICE_ACCOUNT..."

gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=$GCP_RUNTIME \
  --region=$GCP_REGION \
  --source=. \
  --entry-point=main \
  --trigger-topic=$TOPIC_NAME \
  --memory=256MB \
  --timeout=120s \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,ACCESS_TOKEN_SECRET=b24-access-token,REFRESH_TOKEN_SECRET=b24-refresh-token" \
  --set-secrets="B24_CLIENT_ID=b24-client-id:latest,B24_CLIENT_SECRET=b24-client-secret:latest"

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Set up Cloud Scheduler:"
echo "   gcloud scheduler jobs create pubsub b24-token-refresh-job \\"
echo "     --schedule='*/30 * * * *' \\"
echo "     --topic=$TOPIC_NAME \\"
echo "     --message-body='{}' \\"
echo "     --location=$GCP_REGION"
echo ""
echo "🔑 Secret Manager secrets used:"
echo "   - b24-access-token (read/write)"
echo "   - b24-refresh-token (read/write)"
echo "   - b24-client-id (read)"
echo "   - b24-client-secret (read)"
