#!/bin/bash

# Development script for local Firebase development
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting local development environment${NC}"

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo -e "${RED}❌ Firebase CLI is not installed.${NC}"
    echo -e "${YELLOW}Install it with: npm install -g firebase-tools${NC}"
    exit 1
fi

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python is not installed.${NC}"
    exit 1
fi

# Start Firebase emulator in background
echo -e "${YELLOW}🔥 Starting Firebase emulators...${NC}"
firebase emulators:start --only firestore &
FIREBASE_PID=$!

# Wait for Firebase emulator to be ready
echo -e "${YELLOW}⏳ Waiting for Firebase emulator to start...${NC}"
sleep 5

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
    if [ ! -z "$FIREBASE_PID" ]; then
        kill $FIREBASE_PID 2>/dev/null || true
    fi
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Set environment variables for local development
export FIRESTORE_EMULATOR_HOST="127.0.0.1:8080"
export GOOGLE_CLOUD_PROJECT="test-project"
export STAGE="dev"

echo -e "${GREEN}✅ Firebase emulator started at http://localhost:4000${NC}"
echo -e "${GREEN}✅ Firestore emulator started at localhost:8080${NC}"

# Install Python dependencies if not already done
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
cd back
pip install -r requirements-dev.txt

# Run tests to make sure everything works
echo -e "${YELLOW}🧪 Running Firebase tests...${NC}"
python -m pytest test_firebase*.py -v
cd ..

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed. Please check the output above.${NC}"
    exit 1
fi

# Start the API server
echo -e "${YELLOW}🌐 Starting API server...${NC}"
python -m uvicorn back.main:app --host 127.0.0.1 --port 8000 --reload &
API_PID=$!

echo ""
echo -e "${GREEN}🎉 Development environment ready!${NC}"
echo -e "${GREEN}📡 API Server: http://localhost:8000${NC}"
echo -e "${GREEN}📊 API Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}🔥 Firebase UI: http://localhost:4000${NC}"
echo -e "${GREEN}🔥 Firestore: localhost:8080${NC}"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Wait for interrupt
while true; do
    sleep 1
done