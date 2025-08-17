# Firebase + Cloud Run Deployment Guide

This guide explains how to deploy the Teamwork Challenge Platform using Firebase Firestore and Google Cloud Run.

## Architecture

- **Database**: Firebase Firestore (NoSQL document database)
- **Backend API**: Python FastAPI running on Google Cloud Run
- **Authentication**: API key-based authentication stored in Firestore
- **File Storage**: Google Cloud Storage (if needed)

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Node.js** (for Firebase CLI)
3. **Python 3.11+**
4. **Docker** (for containerization)

### Required Tools

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Install Google Cloud SDK
# Follow instructions at: https://cloud.google.com/sdk/docs/install

# Verify installations
firebase --version
gcloud --version
docker --version
```

## Local Development

### 1. Set Up Local Environment

```bash
# Clone the repository
git clone <repository-url>
cd teamwork-challenge/platform

# Make scripts executable
chmod +x dev.sh deploy.sh

# Start local development environment
./dev.sh
```

The development script will:
- Start Firebase emulators (Firestore + UI)
- Install Python dependencies
- Run all Firebase service tests
- Start the API server with hot reload

**Local Services:**
- API Server: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Firebase UI: http://localhost:4000
- Firestore Emulator: localhost:8080

### 2. Running Tests

```bash
cd back
python -m pytest test_firebase*.py -v
```

## Production Deployment

### 1. Google Cloud Setup

```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create teamwork-platform-prod
gcloud config set project teamwork-platform-prod

# Enable billing for the project
# Go to: https://console.cloud.google.com/billing
```

### 2. Firebase Setup

```bash
# Login to Firebase
firebase login

# Initialize Firebase in project directory
firebase init firestore --project teamwork-platform-prod
```

### 3. Deploy to Production

```bash
# Set environment variables (optional)
export PROJECT_ID="teamwork-platform-prod"
export REGION="us-central1"

# Run deployment script
./deploy.sh
```

The deployment script will:
1. Verify prerequisites and authentication
2. Enable required Google Cloud APIs
3. Deploy Firestore rules and indexes
4. Build and deploy the container to Cloud Run
5. Provide service URLs and console links

### 4. Manual Deployment Steps

If you prefer manual deployment:

```bash
# 1. Enable required APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    firestore.googleapis.com

# 2. Deploy Firestore configuration
firebase deploy --only firestore --project $PROJECT_ID

# 3. Build and deploy container
cd back
gcloud builds submit --config=cloudbuild.yaml ..

# 4. Verify deployment
gcloud run services list --region=us-central1
```

## Environment Variables

The application uses the following environment variables:

### Production
- `STAGE=prod` - Enables production mode with Firestore
- `GOOGLE_CLOUD_PROJECT` - Your Google Cloud project ID
- `PORT=8080` - Port for Cloud Run (automatically set)

### Development
- `STAGE=dev` - Enables development mode
- `FIRESTORE_EMULATOR_HOST=127.0.0.1:8080` - Firestore emulator
- `GOOGLE_CLOUD_PROJECT=test-project` - Test project ID

## Database Schema

The Firebase implementation uses the following structure:

```
challenges/{challenge_id}/
├── title, description
├── teams/
│   └── {team_id}/
│       └── name, members, captain_contact
└── rounds/
    └── {round_id}/
        ├── title, description, published, start, end
        ├── task_types/
        │   └── {type_code}/
        │       └── generator_url, secret, score, etc.
        ├── tasks/
        │   └── {task_id}/
        │       └── team_id, status, statement, input, etc.
        └── submissions/
            └── {submission_id}/
                └── team_id, task_id, status, answer, score

keys/{api_key}/
└── challenge_id, role, team_id
```

## Security

### Current Security Model
- **Open Access**: All documents are readable/writable (for backend access)
- **API Key Authentication**: Teams and admins use API keys stored in Firestore
- **No Client Access**: Only the backend service accesses Firestore

### Production Security Considerations
1. **Firestore Rules**: Current rules allow all access - implement proper rules for production
2. **API Keys**: Stored in plain text as specified in requirements
3. **Network Security**: Cloud Run service can be configured with authentication
4. **Secrets Management**: Use Google Secret Manager for generator secrets

## Monitoring and Logging

### Available Dashboards
- **Firebase Console**: https://console.firebase.google.com/project/{PROJECT_ID}
- **Cloud Run Console**: https://console.cloud.google.com/run
- **Cloud Build History**: https://console.cloud.google.com/cloud-build/builds

### Logs
```bash
# View Cloud Run logs
gcloud logs read --project=$PROJECT_ID --service=teamwork-platform-api

# View build logs
gcloud builds log {BUILD_ID}
```

## Costs

### Firebase Firestore
- **Free tier**: 1GB storage, 50K reads, 20K writes per day
- **Paid usage**: $0.18 per 100K reads, $0.18 per 100K writes

### Cloud Run
- **Free tier**: 2M requests, 400K GB-seconds per month
- **Paid usage**: $0.40 per million requests + compute time

### Container Registry
- **Free tier**: None
- **Paid usage**: $0.10 per GB per month storage

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   gcloud auth login
   firebase login
   gcloud config set project $PROJECT_ID
   ```

2. **Firestore Emulator Issues**
   ```bash
   firebase emulators:kill
   firebase emulators:start --only firestore --port 8080
   ```

3. **Container Build Failures**
   - Check Cloud Build logs in console
   - Verify Dockerfile syntax
   - Ensure all dependencies are listed in requirements.txt

4. **Service Not Starting**
   - Check Cloud Run logs for errors
   - Verify environment variables
   - Test container locally with Docker

### Getting Help

1. Check logs in Google Cloud Console
2. Test locally with emulators first
3. Verify all environment variables are set correctly
4. Ensure proper authentication to Google Cloud and Firebase

## Next Steps

After successful deployment:

1. **Set up monitoring** with Cloud Monitoring
2. **Configure custom domains** if needed
3. **Implement proper security rules** for Firestore
4. **Set up CI/CD pipeline** with Cloud Build triggers
5. **Configure backup strategy** for Firestore data