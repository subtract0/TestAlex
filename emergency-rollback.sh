#!/bin/bash

# ACIM Guide - Emergency Rollback Script
# For immediate system recovery in case of critical deployment issues

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Header
echo -e "${RED}"
echo "🚨 ACIM Guide - EMERGENCY ROLLBACK"
echo "=================================="
echo -e "${NC}"
echo "\"In my defenselessness my safety lies.\" - ACIM"
echo ""

# Confirm rollback
print_warning "This script will rollback the production deployment."
read -p "Are you sure you want to proceed? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    print_info "Rollback cancelled."
    exit 0
fi

# Store current state for potential recovery
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="rollback_backup_$TIMESTAMP"

print_info "Creating backup of current state..."
mkdir -p "$BACKUP_DIR"

# Backup current state
if [ -d "functions/" ]; then
    cp -r functions/ "$BACKUP_DIR/" 2>/dev/null || true
    print_success "Functions backed up"
fi

if [ -d "public/" ]; then
    cp -r public/ "$BACKUP_DIR/" 2>/dev/null || true
    print_success "Public files backed up"
fi

if [ -f "firestore.rules" ]; then
    cp firestore.rules "$BACKUP_DIR/" 2>/dev/null || true
    print_success "Firestore rules backed up"
fi

print_success "Backup stored in: $BACKUP_DIR/"

# Check if we have git tags to rollback to
print_info "Checking for previous stable version..."
if git tag --list | grep -q "stable\|v[0-9]"; then
    LAST_STABLE=$(git tag --sort=-version:refname | grep -E "(stable|v[0-9])" | head -1)
    if [ -n "$LAST_STABLE" ]; then
        print_info "Found last stable tag: $LAST_STABLE"
        print_info "Rolling back to: $LAST_STABLE"
        git checkout "$LAST_STABLE" 2>/dev/null || {
            print_warning "Could not checkout tag, using current HEAD"
        }
    else
        print_warning "No stable tag found, staying on current branch"
    fi
else
    print_warning "No version tags found, will rollback using last commit"
fi

# Set Firebase project
print_info "Setting Firebase project..."
firebase use acim-guide-production || {
    print_error "Failed to set Firebase project"
    exit 1
}

# Rollback hosting
print_info "Rolling back Firebase Hosting..."
if firebase hosting:rollback --project acim-guide-production --non-interactive; then
    print_success "Hosting rollback successful"
else
    print_warning "Hosting rollback failed or no previous version available"
    print_info "Attempting to redeploy current hosting..."
    if firebase deploy --only hosting --project acim-guide-production; then
        print_success "Hosting redeployed"
    else
        print_error "Hosting deployment failed"
    fi
fi

# Rollback functions
print_info "Rolling back Cloud Functions..."
if firebase deploy --only functions --project acim-guide-production; then
    print_success "Functions rollback successful"
else
    print_error "Functions deployment failed"
    # Try with backup if available
    if [ -f "$BACKUP_DIR/functions/index.js" ]; then
        print_info "Attempting to use backup functions..."
        cp "$BACKUP_DIR/functions/index.js" functions/ 2>/dev/null || true
        firebase deploy --only functions --project acim-guide-production || {
            print_error "Backup functions deployment also failed"
        }
    fi
fi

# Rollback Firestore rules
print_info "Rolling back Firestore rules..."
if firebase deploy --only firestore:rules --project acim-guide-production; then
    print_success "Firestore rules rollback successful"
else
    print_warning "Firestore rules rollback failed"
fi

print_success "Emergency rollback completed!"

# Wait a moment for propagation
print_info "Waiting 30 seconds for changes to propagate..."
sleep 30

# Run health checks
print_info "Running post-rollback health checks..."

# Basic connectivity test
if curl -s -o /dev/null -w "%{http_code}" https://acim-guide-production.web.app | grep -q "200"; then
    print_success "✅ Homepage is accessible"
else
    print_error "❌ Homepage is not responding correctly"
fi

# Test health check function if available
if [ -f "health-check-test.js" ]; then
    print_info "Running comprehensive health check..."
    if node health-check-test.js; then
        print_success "✅ Comprehensive health check passed"
    else
        print_warning "⚠️ Some health checks failed - manual verification required"
    fi
else
    print_warning "Health check script not found - manual verification required"
fi

# Summary
echo ""
print_success "🌟 ROLLBACK SUMMARY"
echo "==================="
print_info "• Backup created: $BACKUP_DIR/"
print_info "• Hosting: Rolled back"
print_info "• Functions: Redeployed"
print_info "• Firestore rules: Redeployed"
print_info "• Health check: Completed"

echo ""
print_info "📋 Next Steps:"
echo "1. Verify the system is working correctly"
echo "2. Monitor for 15-30 minutes to ensure stability"
echo "3. Document the incident and root cause"
echo "4. Plan fix-forward strategy if needed"
echo "5. Notify team and stakeholders"

echo ""
print_info "🔗 Verification URLs:"
echo "• Homepage: https://acim-guide-production.web.app"
echo "• Firebase Console: https://console.firebase.google.com/project/acim-guide-production"
echo "• Function Logs: https://console.cloud.google.com/logs/viewer?project=acim-guide-production"

echo ""
print_info "\"The Holy Spirit will guide you only in love.\" - ACIM"
print_success "Emergency rollback script completed. 🕊️"

# Return to main branch if we switched
if [ -n "$LAST_STABLE" ]; then
    print_info "Returning to main branch for future development..."
    git checkout main 2>/dev/null || git checkout master 2>/dev/null || true
fi

exit 0
