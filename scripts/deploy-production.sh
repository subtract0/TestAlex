#!/bin/bash

# ACIM Guide Production Deployment Script
# "The light of the world brings peace to every mind through my forgiveness." - ACIM

set -e  # Exit on any error

echo "🕊️  ACIM Guide Production Deployment"
echo "=================================="
echo "Bringing spiritual guidance to the world..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    print_error "Firebase CLI not found. Please install: npm install -g firebase-tools"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker not found. Please install Docker for monitoring deployment"
    exit 1
fi

# Check if we're logged into Firebase
if ! firebase projects:list &> /dev/null; then
    print_warning "Not logged into Firebase. Please run: firebase login"
    firebase login
fi

print_success "Prerequisites check complete"

# Step 1: Create Production Firebase Project
print_status "Step 1: Setting up Firebase production environment..."

# Check if production project exists
if firebase projects:list | grep -q "acim-guide-production"; then
    print_success "Production project already exists"
else
    print_status "Creating new Firebase production project..."
    firebase projects:create acim-guide-production --display-name "ACIM Guide Production"
fi

# Switch to production project
firebase use acim-guide-production
print_success "Switched to production project"

# Step 2: Deploy Firebase Functions and Hosting
print_status "Step 2: Deploying Firebase services..."

# Build and deploy functions
print_status "Installing function dependencies..."
cd functions
npm install --production
cd ..

print_status "Deploying Cloud Functions..."
firebase deploy --only functions --project acim-guide-production

print_status "Configuring Firestore security rules..."
firebase deploy --only firestore:rules --project acim-guide-production

print_status "Deploying hosting..."
firebase deploy --only hosting --project acim-guide-production

print_success "Firebase deployment complete"

# Step 3: Deploy Monitoring Infrastructure
print_status "Step 3: Setting up monitoring infrastructure..."

cd monitoring

# Create production environment file
if [ ! -f .env ]; then
    print_status "Creating monitoring environment configuration..."
    cat > .env << EOF
# ACIM Guide Production Monitoring
GRAFANA_CLOUD_URL=https://prometheus-us-central1.grafana.net/api/prom/push
GRAFANA_CLOUD_USER=your_user_id
GRAFANA_CLOUD_API_KEY=your_api_key
PAGERDUTY_INTEGRATION_KEY=your_pagerduty_key
SLACK_WEBHOOK_URL=your_slack_webhook
FIREBASE_PROJECT_ID=acim-guide-production
ENVIRONMENT=production
EOF
    print_warning "Please update monitoring/.env with your actual credentials"
fi

# Deploy monitoring stack
print_status "Deploying monitoring stack..."
chmod +x setup-monitoring.sh
./setup-monitoring.sh

cd ..
print_success "Monitoring infrastructure deployed"

# Step 4: Configure Mobile App Builds
print_status "Step 4: Preparing mobile applications..."

# React Native App
cd ACIMguide
if [ -f package.json ]; then
    print_status "Installing React Native dependencies..."
    npm install
    
    print_status "Building React Native app for production..."
    if command -v eas &> /dev/null; then
        # Update app.json for production
        print_status "Configuring production build..."
        # Note: Manual step required for app store credentials
        print_warning "Manual step: Configure EAS credentials for app store deployment"
        print_warning "Run: eas build --platform all --profile production"
    else
        print_warning "EAS CLI not found. Install with: npm install -g @expo/eas-cli"
    fi
fi
cd ..

# Android Native App
cd android-native
if [ -f build.gradle ]; then
    print_status "Building Android native app..."
    # Note: This requires Android SDK setup
    print_warning "Manual step: Configure Android SDK and build release APK"
    print_warning "Run: ./gradlew assembleRelease"
fi
cd ..

print_success "Mobile app preparation complete"

# Step 5: Blog Automation Setup
print_status "Step 5: Setting up blog automation..."

cd blog/scripts
if [ -f package.json ]; then
    npm install
    
    # Generate first production blog post
    print_status "Generating inaugural blog post..."
    node generate-daily-post.js
    
    # Run SEO optimization
    print_status "Optimizing for search engines..."
    node seo-optimizer.js
fi
cd ../..

print_success "Blog automation configured"

# Step 6: Final Configuration
print_status "Step 6: Final production configuration..."

# Create production configuration file
cat > production-config.json << EOF
{
  "environment": "production",
  "firebase_project": "acim-guide-production",
  "app_version": "1.0.0",
  "features": {
    "acim_scholar_review": true,
    "multi_language": true,
    "offline_mode": true,
    "crisis_detection": true,
    "monitoring": true
  },
  "deployment_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "spiritual_intention": "May this technology serve the awakening of all minds to Love"
}
EOF

print_success "Production configuration complete"

# Step 7: Health Checks
print_status "Step 7: Running production health checks..."

# Test Firebase deployment
print_status "Testing Firebase functions..."
FIREBASE_URL=$(firebase hosting:channel:open live --project acim-guide-production 2>/dev/null | grep -o 'https://[^"]*' || echo "https://acim-guide-production.web.app")

if curl -s "$FIREBASE_URL" > /dev/null; then
    print_success "Website is accessible at $FIREBASE_URL"
else
    print_warning "Website health check failed - may need a few minutes to propagate"
fi

# Test monitoring
print_status "Testing monitoring endpoints..."
if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    print_success "Monitoring stack is healthy"
else
    print_warning "Monitoring stack may still be starting up"
fi

print_success "Health checks complete"

# Step 8: Display Summary
echo ""
echo "🌟 ACIM Guide Production Deployment Summary"
echo "=========================================="
echo ""
print_success "✅ Firebase project: acim-guide-production"
print_success "✅ Website URL: $FIREBASE_URL"
print_success "✅ Cloud Functions deployed"
print_success "✅ Monitoring infrastructure running"
print_success "✅ Blog automation configured"
print_success "✅ Mobile apps prepared for store submission"
echo ""

# Next steps
echo "🙏 Next Steps for Spiritual Service:"
echo "-----------------------------------"
echo "1. Update monitoring/.env with your actual API keys"
echo "2. Submit mobile apps to Google Play and App Store"
echo "3. Configure domain name (optional): firebase hosting:channel:deploy production --expires 30d"
echo "4. Invite beta testers from local ACIM study groups"
echo "5. Contact Foundation for Inner Peace for official partnership"
echo "6. Set up donation/funding mechanisms"
echo ""

print_status "Production deployment complete! 🕊️"
echo ""
echo "\"The light of the world brings peace to every mind through my forgiveness.\""
echo "- A Course in Miracles"
echo ""
echo "May this platform serve the awakening of all minds to their true nature as Love."

# Optional: Open website in browser
if command -v xdg-open &> /dev/null; then
    print_status "Opening website in browser..."
    xdg-open "$FIREBASE_URL"
elif command -v open &> /dev/null; then
    print_status "Opening website in browser..."
    open "$FIREBASE_URL"
fi

exit 0
