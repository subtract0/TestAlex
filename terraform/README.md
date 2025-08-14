# ACIM Guide DevOps Infrastructure

This Terraform configuration sets up a complete DevOps pipeline for ACIM Guide with cost-optimized monitoring, auto-scaling, and budget controls to stay under €500/month until revenue scales.

## 🚀 Features Implemented

### 1. Terraform Module for Firebase Quotas & Alert Policies
- **Budget monitoring** with €500/month limit and multi-threshold alerts (50%, 80%, 95%, 100%)
- **Quota monitoring** for Cloud Functions (2M daily executions) and Firestore (50M daily operations)  
- **Custom dashboards** for real-time usage tracking and cost visualization
- **Alert policies** for error rates, performance issues, and budget overruns

### 2. Enhanced CD Pipeline: Merge → Staging → ACIM Scholar Gate → Production
- **Automatic staging deployment** on main branch merge
- **Preview URLs** for staging environment testing
- **ACIM Scholar approval gate** for theological content validation
- **Health checks** and smoke tests at each stage
- **Rollback mechanisms** for failed deployments
- **Environment-specific configurations**

### 3. Auto-Scaling Cloud Functions via Usage Metrics
- **Dynamic scaling** based on time-of-day (peak hours: 9 AM - 9 PM)
- **Usage-based scaling** considering daily tokens and request rates
- **Cost-optimized scaling** with conservative defaults to control expenses
- **Emergency scaling** for high error rates
- **Manual override** capability for emergency situations

### 4. OpenAI Token Budgeting Micro-service
- **Real-time cost tracking** with €0.03/€0.06 per 1K tokens pricing
- **Smart throttling** with service level degradation at budget thresholds:
  - Normal: Full service
  - Warning (70%): Reduced service for free users
  - Slowdown (85%): Shorter responses, cheaper models
  - Emergency (95%): Premium users only
  - Shutoff (100%): Service disabled
- **User tier management** (free, premium, admin)
- **Daily maintenance** and cleanup automation

## 📋 Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Terraform** >= 1.0 installed
3. **Firebase CLI** installed and authenticated
4. **GitHub repository** for CI/CD

## 🛠 Deployment Instructions

### Step 1: Initialize Terraform

```bash
cd terraform

# Initialize Terraform backend
terraform init

# Create terraform.tfvars file
cat > terraform.tfvars << EOF
project_id      = "your-acimguide-project-id"
billing_account = "your-billing-account-id"
alert_email     = "alerts@yourdomain.com"
github_repo     = "your-org/acimguide-app"
EOF
```

### Step 2: Deploy Infrastructure

```bash
# Plan the deployment
terraform plan

# Apply the configuration
terraform apply
```

### Step 3: Configure GitHub Secrets

Add these secrets to your GitHub repository:

```bash
# Get the service account key from Terraform output
terraform output -raw github_actions_key | base64 -d > gcp-key.json

# Add to GitHub secrets:
# GCP_SA_KEY: (content of gcp-key.json)
# FIREBASE_TOKEN: (get with firebase login:ci)
# OPENAI_API_KEY: (your OpenAI API key)
# ASSISTANT_ID: (your OpenAI Assistant ID)
```

### Step 4: Deploy Cloud Functions

```bash
cd functions

# Install dependencies
npm install

# Add required dependencies for new modules
npm install google-auth-library

# Deploy functions
firebase deploy --only functions
```

### Step 5: Set up Secret Manager

```bash
# Add OpenAI API key
echo "your-openai-api-key" | gcloud secrets versions add openai-api-key --data-file=-

# Add Assistant ID
echo "your-assistant-id" | gcloud secrets versions add openai-assistant-id --data-file=-

# Add Firebase deployment token
firebase login:ci | gcloud secrets versions add firebase-deployment-token --data-file=-
```

## 📊 Monitoring & Dashboards

After deployment, access your monitoring dashboards:

- **Main Dashboard**: `https://console.cloud.google.com/monitoring/dashboards`
- **Budget Alerts**: `https://console.cloud.google.com/billing/budgets`
- **Function Logs**: `https://console.cloud.google.com/functions/list`
- **Scaling Metrics**: Stored in Firestore `scaling_metrics` collection

## 🔧 Configuration Options

### Budget Adjustment

To modify the monthly budget:

```bash
terraform apply -var="monthly_budget_eur=750"
```

### Auto-scaling Parameters

Edit `functions/auto-scale.js` to adjust:
- **Peak hours**: Currently 9 AM - 9 PM UTC
- **Scaling thresholds**: Token limits and request rates
- **Maximum instances**: Conservative limits for cost control

### Budget Control

Edit `functions/token-budget.js` to modify:
- **User tier allocations**: Currently 5% free, 75% premium, 20% admin
- **Service level thresholds**: 70%, 85%, 95%, 100%
- **Model fallback strategy**: GPT-4 → GPT-4 Turbo for cost savings

## 🚦 CI/CD Pipeline Usage

### Staging Deployment
```bash
# Automatic on merge to main
git push origin main
```

### Production Deployment
```bash
# Manual trigger with ACIM Scholar approval
gh workflow run cd-pipeline.yml \
  -f environment=production \
  -f scholar_approved=true
```

### Emergency Deployment
```bash
# Bypass scholar gate (emergency only)
gh workflow run cd-pipeline.yml \
  -f environment=production \
  -f bypass_scholar_gate=true \
  -f force_deploy=true
```

## 📈 Cost Optimization Features

1. **Dynamic Scaling**: Functions scale down during off-peak hours
2. **Budget Throttling**: Service degrades gracefully as budget is consumed
3. **Model Optimization**: Automatic fallback to cheaper models under budget pressure
4. **Response Length Control**: Shorter responses when approaching budget limits
5. **User Tier Management**: Free users limited first when budget is constrained

## 🔍 Troubleshooting

### Budget Service Issues
```bash
# Check budget status
firebase functions:shell
> getBudgetStatus()

# Manual scaling override
> manualScaleOverride({maxInstances: 10, reason: "High traffic", duration: 60})
```

### Auto-scaling Issues
```bash
# Check scaling metrics
> getScalingStatus()

# View recent scaling decisions
gcloud firestore export gs://your-bucket/backup --collection-ids=scaling_metrics
```

### CI/CD Pipeline Issues
- Check GitHub Actions logs for deployment failures
- Verify service account permissions
- Ensure Firebase token is valid

## 📝 Maintenance

### Daily Tasks
- Monitor budget utilization dashboard
- Review error rates and scaling alerts
- Check staging environment health

### Weekly Tasks
- Review cost analysis reports in Cloud Storage
- Update OpenAI pricing if changed
- Analyze usage patterns for optimization opportunities

### Monthly Tasks
- Review and adjust budget allocations
- Update user tier percentages based on revenue
- Optimize auto-scaling parameters based on usage patterns

## 🔐 Security Considerations

- All secrets managed through Google Secret Manager
- Service accounts follow principle of least privilege
- Budget controls prevent runaway costs
- Scholar approval gate ensures content quality
- Comprehensive logging for audit trails

## 📞 Support

For issues or questions:
1. Check the monitoring dashboard for alerts
2. Review Cloud Functions logs
3. Examine Firestore collections for detailed metrics
4. Consult the budget status endpoint for cost analysis

This setup provides a robust, cost-controlled DevOps pipeline that scales with your needs while maintaining strict budget discipline until revenue growth justifies increased spending.
