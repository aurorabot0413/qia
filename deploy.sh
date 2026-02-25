#!/bin/bash
# QiA Deploy Script

set -e

PROJECT_ID="core-trees-487719-n8"
REGION="us-central1"

echo "🚀 Deploying QiA to Google Cloud..."

# 1. Create Cloud Storage bucket (if not exists)
echo "📦 Creating Cloud Storage bucket..."
gsutil mb -p $PROJECT_ID -l $REGION gs://qia-artifacts-bucket 2>/dev/null || echo "Bucket already exists"

# 2. Create Pub/Sub topic
echo "📡 Creating Pub/Sub topic..."
gcloud pubsub topics create qia-webhooks 2>/dev/null || echo "Topic already exists"

# 3. Build and push Orchestrator
echo "🏗️ Building Orchestrator..."
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions=_PROJECT_ID=$PROJECT_ID \
  .

# 4. Get Cloud Run URL
echo "🌐 Getting Cloud Run URL..."
SERVICE_URL=$(gcloud run services describe qia-orchestrator \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)')

echo "✅ Orchestrator deployed at: $SERVICE_URL"

# 5. Create Pub/Sub subscription
echo "🔗 Creating Pub/Sub subscription..."
gcloud pubsub subscriptions create qia-webhooks-sub \
  --topic=qia-webhooks \
  --push-endpoint=$SERVICE_URL/webhook/github \
  2>/dev/null || echo "Subscription already exists"

# 6. Build QA Worker
echo "🏗️ Building QA Worker..."
gcloud builds submit \
  --config cloudbuild-worker.yaml \
  --substitutions=_PROJECT_ID=$PROJECT_ID \
  .

echo "✅ QiA deployed successfully!"
echo ""
echo "📊 Service URL: $SERVICE_URL"
echo "📡 Pub/Sub Topic: qia-webhooks"
echo "🪣 Storage Bucket: gs://qia-artifacts-bucket"
echo ""
echo "🧪 Test with:"
echo "  curl $SERVICE_URL/"
