#!/bin/bash
# Deploy script for B24 SPA 1106 Sync Worker
# Pub/Sub triggered function for Sprawy cudzoziemców (1106) synchronization
# Syncs:
#   - Podstawy pobytu (1042) → Sprawy.ufCrm38_1768737959
#   - Uprawnienia do pracy (1046) → Sprawy.ufCrm38_1768738112
#   - Contact passport fields → Sprawy (nr paszportu, Data ważności)

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
FUNCTION_NAME="b24-spa-1106-sync-worker"
TOPIC_NAME="b24-spa-1106-sync-events"

echo ""
echo "🚀 Deploying $FUNCTION_NAME to $GCP_REGION..."
echo "   Project: $PROJECT_ID"
echo "   Trigger: Pub/Sub topic $TOPIC_NAME"
echo ""

# Create Pub/Sub topic if not exists
gcloud pubsub topics create $TOPIC_NAME --project=$PROJECT_ID 2>/dev/null || echo "Topic $TOPIC_NAME already exists"

# Deploy Pub/Sub triggered function
gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=$GCP_RUNTIME \
  --region=$GCP_REGION \
  --source=. \
  --entry-point=main \
  --trigger-topic=$TOPIC_NAME \
  --memory=512MB \
  --timeout=300s \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,B24_DOMAIN=mojo.bitrix24.pl,ACCESS_TOKEN_SECRET=b24-access-token,SPA_SPRAWY_ID=1106,SPA_PODSTAWY_POBYTU_ID=1042,SPA_PRACA_ID=1046,SPA_PROCESY_ID=1110,FIELD_SPRAWY_PODSTAWY=ufCrm38_1768737959,FIELD_SPRAWY_PRACA=ufCrm38_1768738112,FIELD_SPRAWY_PROCESY=ufCrm38_1768738413,FIELD_SPRAWY_PODSTAWY_DATES=ufCrm38_1768738011252,FIELD_PODSTAWY_DATA_DO_KIEDY=ufCrm10_1763581700754,FIELD_SPRAWY_PRACA_DATES=ufCrm38_1768738327769,FIELD_PRACA_DATA_WAZNOSCI=ufCrm12_1764516949310"

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Architecture:"
echo "   Bitrix24 Webhook → b24-spa-1106-http (HTTP Handler)"
echo "                           ↓"
echo "                    Pub/Sub: $TOPIC_NAME"
echo "                           ↓"
echo "                    $FUNCTION_NAME (Worker)"
echo ""
echo "📊 Supported events:"
echo "   SPA Events:"
echo "   • 1106 (Sprawy cudzoziemców) → Full sync (SPAs + Contact fields)"
echo "   • 1042 (Podstawy pobytu) → Sync to Sprawy.ufCrm38_1768737959"
echo "   • 1046 (Uprawnienia do pracy) → Sync to Sprawy.ufCrm38_1768738112"
echo "   • 1110 (Procesy legalizacyjne) → Sync to Sprawy.ufCrm38_1768738413"
echo ""
echo "   Contact Events:"
echo "   • ONCRMCONTACTADD/UPDATE → Sync passport fields to all linked Sprawy"
echo "   • Numer paszportu: Contact.UF_CRM_1758997725285 → Sprawy.ufCrm38_1764509760429"
echo "   • Data ważności: Contact.UF_CRM_1760984058065 → Sprawy.ufCrm38_1764509780038"
echo ""
