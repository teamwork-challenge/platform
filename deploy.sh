#!/bin/bash

# Deployment script for Firebase + Cloud Run deployment
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-"teamwork-platform"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="teamwork-platform-api"

echo -e "${BLUE}🚀 Starting deployment to Firebase + Cloud Run${NC}"
echo -e "${BLUE}Project ID: ${PROJECT_ID}${NC}"
echo -e "${BLUE}Region: ${REGION}${NC}"
echo ""

# Check if required tools are installed
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed. Please install it first.${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
check_tool "gcloud"
check_tool "docker"
check_tool "firebase"

# Check if logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Please login to gcloud first: gcloud auth login${NC}"
    exit 1
fi

# Set project if not already set
if [ "$(gcloud config get-value project)" != "$PROJECT_ID" ]; then
    echo -e "${YELLOW}🔧 Setting project to ${PROJECT_ID}${NC}"
    gcloud config set project $PROJECT_ID
fi

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    firestore.googleapis.com

# Initialize Firebase if not already done
if [ ! -f "firebase.json" ]; then
    echo -e "${YELLOW}🔥 Initializing Firebase...${NC}"
    firebase init firestore --project $PROJECT_ID
else
    echo -e "${GREEN}✅ Firebase already initialized${NC}"
fi

# Deploy Firestore rules and indexes
echo -e "${YELLOW}🔥 Deploying Firestore configuration...${NC}"
firebase deploy --only firestore --project $PROJECT_ID

# Build and deploy the container
echo -e "${YELLOW}🏗️  Building and deploying container...${NC}"
cd back

# Submit build to Cloud Build
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions=_SERVICE_NAME=$SERVICE_NAME \
    ..

cd ..

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format="value(status.url)")

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}📡 Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}🔥 Firebase Console: https://console.firebase.google.com/project/${PROJECT_ID}${NC}"
echo -e "${GREEN}☁️  Cloud Run Console: https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}${NC}"
echo ""
echo -e "${BLUE}🧪 Test your API:${NC}"
echo -e "curl ${SERVICE_URL}/health"