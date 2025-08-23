# GitHub Secrets Setup for ACIM Guide CI/CD

## Overview

This guide walks you through setting up the required GitHub secrets for the ACIM Guide deployment pipeline.

## Current Status

❌ **Missing Required Secrets** - The deployment pipeline requires authentication credentials to deploy to Firebase.

## Required Secrets

### Option 1: Firebase Token (Recommended)

1. **Install Firebase CLI** (if not already installed):
```bash
npm install -g firebase-tools
```

2. **Login to Firebase**:
```bash
firebase login
```

3. **Generate CI Token**:
```bash
firebase login:ci
```

4. **Add to GitHub Secrets**:
   - Go to your repository on GitHub
   - Navigate to `Settings` → `Secrets and variables` → `Actions`
   - Click `New repository secret`
   - Name: `FIREBASE_TOKEN`
   - Value: The token generated in step 3

### Option 2: Google Cloud Service Account (Alternative)

1. **Create Service Account**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to `IAM & Admin` → `Service Accounts`
   - Click `Create Service Account`
   - Give it a name like "GitHub Actions Deploy"

2. **Assign Roles**:
   - Firebase Admin
   - Cloud Functions Admin
   - Cloud Storage Admin
   - Hosting Admin

3. **Generate Key**:
   - Click on the service account
   - Go to `Keys` tab
   - Click `Add Key` → `Create new key`
   - Choose JSON format

4. **Add to GitHub Secrets**:
   - Base64 encode the JSON key: `base64 -i key.json`
   - Add as GitHub secret:
     - Name: `GCP_SA_KEY`
     - Value: The base64-encoded JSON

## Firebase Project Setup

### Create Projects (if not exists)

```bash
# Create staging project
firebase projects:create acim-guide-test --display-name "ACIM Guide (Test)"

# Create production project
firebase projects:create acim-guide-production --display-name "ACIM Guide (Production)"
```

### Enable Required Services

For both projects, enable:
- Firestore Database
- Cloud Functions
- Firebase Hosting
- Firebase Authentication

### Configure Local Firebase

```bash
# Add projects to local Firebase config
firebase use --add acim-guide-test
firebase use --add acim-guide-production

# Set default project
firebase use acim-guide-test
```

## Verification

Once secrets are configured, you can test the deployment pipeline:

1. **Manual Staging Deploy**:
   - Go to `Actions` tab in GitHub
   - Select "Enhanced CD Pipeline"
   - Click "Run workflow"
   - Choose "staging" environment
   - Click "Run workflow"

2. **Check Logs**:
   - Monitor the deployment logs for authentication success
   - Verify the staging URL is accessible

## Troubleshooting

### Common Issues

#### 1. Token Expired
**Error**: `Invalid authentication credentials`
**Solution**: Regenerate Firebase token with `firebase login:ci`

#### 2. Insufficient Permissions
**Error**: `Permission denied`
**Solution**: Ensure service account has all required roles

#### 3. Project Not Found
**Error**: `Project acim-guide-test does not exist`
**Solution**: Create the Firebase projects or update project IDs in workflow

#### 4. Function Deployment Fails
**Error**: `Cloud Functions deployment failed`
**Solution**: Check functions dependencies and Node.js version compatibility

### Testing Authentication

```bash
# Test Firebase authentication locally
firebase list

# Test project access
firebase use acim-guide-test
firebase deploy --only hosting --dry-run
```

## Security Best Practices

1. **Least Privilege**: Only grant necessary permissions to service accounts
2. **Rotate Regularly**: Update tokens/keys periodically
3. **Monitor Usage**: Review deployment logs for unauthorized access
4. **Separate Environments**: Use different credentials for staging/production

## Next Steps

After configuring secrets:

1. ✅ Test staging deployment
2. ✅ Verify health checks pass
3. ✅ Configure production approval process
4. ✅ Set up monitoring and alerts

---

**Need Help?** Check the [DEPLOYMENT.md](./DEPLOYMENT.md) for comprehensive deployment documentation.
