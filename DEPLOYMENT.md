# ACIMguide Production Deployment Guide

## Quick Start Deployment

### Prerequisites
- Firebase CLI installed and authenticated
- Node.js 22+ installed
- Python 3.11+ with virtual environment
- OpenAI API key

### 1. Environment Setup

```bash
# Clone and setup
cd TestAlex
source venv/bin/activate
pip install -r requirements.txt

# Install Firebase dependencies
cd functions
npm install
cd ..
```

### 2. Configure Environment Variables

Create `.env` file in project root:
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
ASSISTANT_ID=your_assistant_id_here
VECTOR_STORE_ID=your_vector_store_id_here

# Optional
DAILY_OUT_TOKENS_CAP=2000
LOG_LEVEL=INFO
```

### 3. Create Assistant (First Time Only)

```bash
# Create assistant with knowledge base
python manage_assistant.py create --name "CourseGPT" --model gpt-5-chat-latest

# This will automatically populate ASSISTANT_ID and VECTOR_STORE_ID in .env
```

### 4. Deploy to Firebase

```bash
# Deploy everything
firebase deploy

# Or deploy specific components
firebase deploy --only functions
firebase deploy --only firestore:rules,firestore:indexes
```

### 5. Test Deployment

```bash
# Start local emulators for testing
firebase emulators:start

# Test the deployed functions
firebase functions:log --only chatWithAssistant
```

## Production Configuration

### Firebase Functions Environment

Set production environment variables:
```bash
firebase functions:config:set \
  openai.key="your_openai_api_key" \
  assistant.id="your_assistant_id" \
  vector_store.id="your_vector_store_id" \
  tokens.daily_cap="2000"
```

### Security Checklist

- ✅ Firestore security rules updated (user-specific access)
- ✅ Database indexes configured for performance
- ✅ Rate limiting enabled (10 RPM per user)
- ✅ Token usage caps implemented (2000 daily)
- ✅ Authentication required for all endpoints
- ✅ Comprehensive logging and monitoring

### Monitoring & Observability

```bash
# View function logs
firebase functions:log

# Monitor performance
firebase functions:log --only chatWithAssistant

# Check error rates
firebase functions:log --only chatWithAssistant --filter="severity>=ERROR"
```

## API Endpoints

### Chat Endpoint
```
POST https://us-central1-acim-guide-test.cloudfunctions.net/chatWithAssistant
```

**Request:**
```json
{
  "data": {
    "message": "What is forgiveness according to ACIM?",
    "tone": "gentle"
  }
}
```

**Response:**
```json
{
  "result": {
    "messageId": "message_doc_id",
    "tokenIn": 25,
    "tokenOut": 150,
    "limitRemaining": 1850
  }
}
```

### Clear Thread Endpoint
```
POST https://us-central1-acim-guide-test.cloudfunctions.net/clearThread
```

## Scaling Considerations

### Current Limits
- **Rate Limiting**: 10 requests per minute per user
- **Token Limits**: 2000 output tokens per user per day
- **Function Instances**: Max 10 concurrent instances

### Scaling Up
```bash
# Increase function instances
# Edit functions/index.js:
setGlobalOptions({maxInstances: 50});

# Increase token limits
firebase functions:config:set tokens.daily_cap="5000"
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Ensure Firebase Auth is enabled
   firebase auth:import users.json
   ```

2. **Rate Limit Issues**
   ```bash
   # Check rate limit collection
   firebase firestore:delete --recursive rateLimits/user_id
   ```

3. **Function Timeout**
   ```bash
   # Increase timeout in functions/index.js
   exports.chatWithAssistant = onCall({timeoutSeconds: 540}, async (request) => {
   ```

### Health Checks

```bash
# Test assistant management
python manage_assistant.py sync-files

# Test local chat
python main.py "Test message"

# Test Firebase functions
firebase functions:shell
```

## GitHub Actions CI/CD Pipeline

### Required GitHub Secrets

The following secrets must be configured in your GitHub repository (`Settings > Secrets and variables > Actions`):

#### 1. Firebase Authentication Token
```
FIREBASE_TOKEN
```
**How to obtain:**
```bash
firebase login:ci
```

#### 2. Google Cloud Service Account Key (Alternative)
```
GCP_SA_KEY
```
**How to obtain:**
1. Go to Google Cloud Console
2. Create service account with Firebase Admin, Cloud Functions Admin roles
3. Generate JSON key, base64 encode it
4. Add as GitHub secret

### Pipeline Configuration

#### Automatic Deployments
- **Staging**: Auto-deploy on push to `main` branch
- **Production**: Manual trigger with approval

#### Environment URLs
- **Staging**: https://acim-guide-test.web.app
- **Production**: https://acim-guide-production.web.app

### CI/CD Troubleshooting

#### Authentication Failures
**Error**: Missing credentials configuration
**Solution**: Add `FIREBASE_TOKEN` or `GCP_SA_KEY` secret

#### Build Script Missing
**Solution**: Build scripts added to package.json:
```bash
npm run build          # Standard build
npm run build:staging  # Staging build
npm run deploy:staging # Deploy to staging
```

## Next Steps: Mobile App

### Android Development Setup
1. Create new Android Studio project
2. Package name: `com.acimguide.mvp`
3. Add Firebase SDK dependencies
4. Implement authentication flow
5. Build chat interface

### Key Features to Implement
- Google Sign-In authentication
- Real-time message streaming
- Quick action buttons
- Settings and preferences
- Offline message queuing

## Cost Optimization

### Current Costs (Estimated)
- **Firebase Functions**: ~$0.40 per 1M invocations
- **Firestore**: ~$0.18 per 100K reads
- **OpenAI API**: ~$0.03 per 1K tokens (GPT-4o)

### Optimization Strategies
- Implement response caching for common queries
- Use GPT-4o-mini for simple responses
- Batch Firestore operations
- Implement smart retry logic

---

**Status**: ✅ Production Ready
**Last Updated**: August 2025
**Next Milestone**: Android App Launch
