#!/bin/bash
# Deploy script for B24 SPA 1106 Webhook Handler
# Fast HTTP handler that publishes to Pub/Sub

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
FUNCTION_NAME="b24-spa-1106-http"
TOPIC_NAME="b24-spa-1106-sync-events"

echo ""
echo "🚀 Deploying $FUNCTION_NAME to $GCP_REGION..."
echo "   Project: $PROJECT_ID"
echo ""

# Create Pub/Sub topic if not exists
gcloud pubsub topics create $TOPIC_NAME --project=$PROJECT_ID 2>/dev/null || echo "Topic $TOPIC_NAME already exists"

# Deploy HTTP function
gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=$GCP_RUNTIME \
  --region=$GCP_REGION \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated \
  --memory=256MB \
  --timeout=30s \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,TOPIC_NAME=$TOPIC_NAME"

echo ""
echo "✅ Deployment completed!"
echo ""

# Get function URL
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$GCP_REGION --format='value(serviceConfig.uri)')
echo "🔗 Function URL: $FUNCTION_URL"
echo ""
echo "📋 Bitrix24 Webhook URLs (use in Automation Rules):"
echo ""
echo "   Create/Update Sprawy cudzoziemców (SPA 1106):"
echo "   $FUNCTION_URL?event=sprawy_updated&id={=Document:ID}&contact_id={=Document:CONTACT_ID}&entity_type_id=1106"
echo ""
echo "   Create/Update Podstawy pobytu (SPA 1042):"
echo "   $FUNCTION_URL?event=podstawy_updated&id={=Document:ID}&contact_id={=Document:CONTACT_ID}&entity_type_id=1042"
echo ""
echo "   Create/Update Uprawnienia do pracy (SPA 1046):"
echo "   $FUNCTION_URL?event=praca_updated&id={=Document:ID}&contact_id={=Document:CONTACT_ID}&entity_type_id=1046"
echo ""
echo "   Create/Update Procesy legalizacyjne (SPA 1110):"
echo "   $FUNCTION_URL?event=procesy_updated&id={=Document:ID}&contact_id={=Document:CONTACT_ID}&entity_type_id=1110"
echo ""
echo "   Full sync for contact:"
echo "   $FUNCTION_URL?event=sync_all&contact_id={=Document:CONTACT_ID}"
echo ""
