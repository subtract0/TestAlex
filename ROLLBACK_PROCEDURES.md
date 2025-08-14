# 🚨 ACIM Guide - Rollback Procedures & Incident Response Plan

> *"In my defenselessness my safety lies."* - ACIM  
> Comprehensive deployment rollback and incident management procedures

## 🔄 Quick Rollback Reference

### **EMERGENCY ROLLBACK** (Use if system is down)

```bash
# 1. Rollback hosting immediately
firebase hosting:rollback --project acim-guide-production

# 2. Rollback functions to last known good version
firebase deploy --only functions --project acim-guide-production

# 3. Check health
curl -s https://acim-guide-production.web.app
```

---

## 📋 Incident Classification

### **Severity Levels**

#### 🚨 **CRITICAL (P0) - Immediate Action Required**
- **Definition**: Complete service outage, data loss, security breach
- **Response Time**: < 5 minutes
- **Escalation**: Immediate rollback + team notification

**Examples:**
- Website completely inaccessible
- Firebase functions returning 500 errors
- Authentication system failure
- Data corruption in Firestore
- Security vulnerability exposed

**Immediate Actions:**
1. Execute emergency rollback (see above)
2. Document issue in incident log
3. Notify team via Slack/PagerDuty
4. Begin root cause analysis

#### ⚠️ **HIGH (P1) - Urgent Response**
- **Definition**: Significant functionality impaired, user experience degraded
- **Response Time**: < 15 minutes
- **Escalation**: Assessment + potential rollback

**Examples:**
- Slow response times (>5 seconds)
- Specific functions failing intermittently
- AI responses not generating
- UI elements not loading properly

**Actions:**
1. Assess impact and user experience
2. Determine if rollback is necessary
3. Monitor error rates and performance
4. Document and investigate

#### ⚠️ **MEDIUM (P2) - Standard Response**
- **Definition**: Minor issues, workarounds available
- **Response Time**: < 1 hour
- **Escalation**: Monitor and fix forward

**Examples:**
- Minor UI styling issues
- Non-critical feature limitations
- Performance slightly degraded
- Cosmetic problems

#### ℹ️ **LOW (P3) - Scheduled Response**
- **Definition**: Enhancement requests, minor improvements
- **Response Time**: Next deployment cycle
- **Escalation**: Include in next release

---

## 🔄 Detailed Rollback Procedures

### **1. Firebase Hosting Rollback**

```bash
# List recent deployments
firebase hosting:channel:list --project acim-guide-production

# Rollback to previous version
firebase hosting:rollback --project acim-guide-production

# Verify rollback success
curl -I https://acim-guide-production.web.app
```

**When to use:**
- Frontend issues, broken UI, JavaScript errors
- Static content problems
- Routing issues

**Verification steps:**
1. Check homepage loads: `curl -s https://acim-guide-production.web.app`
2. Verify authentication works
3. Test core user flows
4. Check console for errors

### **2. Cloud Functions Rollback**

```bash
# Check current functions
firebase functions:list --project acim-guide-production

# Option A: Redeploy from previous git tag
git checkout <previous-stable-tag>
firebase deploy --only functions --project acim-guide-production

# Option B: Deploy specific function version
# (requires manual backup of functions/index.js)
cp functions/index-backup.js functions/index.js
firebase deploy --only functions --project acim-guide-production

# Verify functions health
curl -X POST \
  "https://us-central1-acim-guide-production.cloudfunctions.net/healthCheck" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**When to use:**
- Function errors, timeouts, or crashes
- API integration failures
- Database connection issues
- Performance degradation

**Verification steps:**
1. Test healthCheck function
2. Test chatWithAssistant function
3. Test clearThread function
4. Monitor function logs: `firebase functions:log --project acim-guide-production`

### **3. Firestore Rules Rollback**

```bash
# Deploy previous firestore rules
git checkout <previous-stable-tag> -- firestore.rules
firebase deploy --only firestore:rules --project acim-guide-production

# Verify rules deployment
curl -s https://console.firebase.google.com/project/acim-guide-production/firestore/rules
```

**When to use:**
- Permission errors
- Security rule conflicts
- Data access issues

### **4. Complete System Rollback**

For critical incidents requiring full rollback:

```bash
#!/bin/bash
# full-rollback.sh

echo "🚨 ACIM Guide - Emergency Full Rollback"
echo "======================================"

# Store current state for potential recovery
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p rollback_backup_$TIMESTAMP

# Backup current state
cp -r functions/ rollback_backup_$TIMESTAMP/
cp -r public/ rollback_backup_$TIMESTAMP/
cp firestore.rules rollback_backup_$TIMESTAMP/

# Checkout last known good state
echo "📋 Rolling back to last stable version..."
LAST_STABLE=$(git tag --sort=-version:refname | head -1)
git checkout $LAST_STABLE

# Deploy all services
echo "🔄 Deploying hosting..."
firebase deploy --only hosting --project acim-guide-production

echo "⚡ Deploying functions..."
firebase deploy --only functions --project acim-guide-production

echo "🔒 Deploying firestore rules..."
firebase deploy --only firestore:rules --project acim-guide-production

echo "✅ Full rollback complete"
echo "Backup stored in: rollback_backup_$TIMESTAMP/"

# Run health checks
echo "🏥 Running post-rollback health checks..."
node health-check-test.js
```

---

## 📊 Health Check Procedures

### **Automated Health Check**

```bash
# Run comprehensive health check
node health-check-test.js

# Check specific services
node basic-monitoring-check.js

# Manual verification URLs
echo "Manual check URLs:"
echo "• Homepage: https://acim-guide-production.web.app"
echo "• Firebase Console: https://console.firebase.google.com/project/acim-guide-production"
echo "• Function Logs: https://console.cloud.google.com/logs/viewer?project=acim-guide-production"
```

### **Health Check Criteria**

✅ **System Healthy** - All checks pass
- Authentication: ✅ Working
- Health Check Function: ✅ Responding
- Firestore Read/Write: ✅ Working
- Homepage: ✅ Accessible
- Chat Function: ✅ Available

⚠️ **System Degraded** - 80%+ checks pass
- Minor issues acceptable
- Monitor closely
- Plan fix forward

❌ **System Critical** - <80% checks pass
- **Immediate rollback required**
- Escalate to team
- Begin incident response

---

## 🛠️ Incident Response Workflow

### **Phase 1: Detection & Assessment** (0-5 minutes)

1. **Identify Issue**
   - Monitoring alerts
   - User reports
   - Health check failures

2. **Initial Assessment**
   ```bash
   # Quick system check
   curl -I https://acim-guide-production.web.app
   node health-check-test.js
   firebase functions:list --project acim-guide-production
   ```

3. **Classify Severity**
   - P0: Immediate rollback required
   - P1: Assessment needed
   - P2: Monitor and fix forward
   - P3: Schedule for next release

### **Phase 2: Response & Mitigation** (5-15 minutes)

1. **P0 Response**: Execute immediate rollback
2. **P1 Response**: Detailed assessment
3. **Document Issue**
   ```bash
   # Create incident log
   echo "$(date): [P0/P1/P2/P3] Issue description" >> incident_log.md
   ```

### **Phase 3: Recovery & Verification** (15-30 minutes)

1. **Execute Chosen Solution**
   - Rollback procedures (if required)
   - Fix forward (if safe)
   - Monitoring increase

2. **Verify Recovery**
   ```bash
   # Run full health check
   node health-check-test.js
   
   # Monitor for 10 minutes
   watch -n 30 'curl -s -o /dev/null -w "%{http_code}\n" https://acim-guide-production.web.app'
   ```

### **Phase 4: Documentation & Learning** (30+ minutes)

1. **Complete Incident Report**
2. **Root Cause Analysis**
3. **Preventive Measures**
4. **Process Improvements**

---

## 📚 Git-Based Rollback Strategy

### **Tagging Strategy**

```bash
# Tag stable releases
git tag -a v1.0.0-stable -m "Stable production release"
git push origin v1.0.0-stable

# Tag deployment checkpoints
git tag -a deploy-$(date +%Y%m%d_%H%M) -m "Pre-deployment checkpoint"
git push origin deploy-$(date +%Y%m%d_%H%M)
```

### **Branch Strategy for Rollbacks**

```bash
# Create rollback branch
git checkout -b rollback-$(date +%Y%m%d_%H%M)

# Rollback to specific commit
git reset --hard <last-known-good-commit>

# Deploy from rollback branch
firebase deploy --project acim-guide-production
```

---

## 📞 Emergency Contacts & Escalation

### **Escalation Matrix**

1. **Level 1**: Automated systems (monitoring, alerts)
2. **Level 2**: On-call developer (primary responder)
3. **Level 3**: Development team lead
4. **Level 4**: Project manager / CTO
5. **Level 5**: Executive leadership

### **Communication Channels**

- **Slack**: `#acim-guide-incidents` channel
- **PagerDuty**: Critical alert notifications
- **Email**: team-acim-guide@company.com
- **Status Page**: status.acimguide.com (future)

---

## 🔍 Common Issue Troubleshooting

### **Issue: "Authentication Failed"**

**Symptoms**: Users cannot log in, auth errors in console
**Solution**:
```bash
# Check Firebase auth status
curl -s https://acim-guide-production.web.app | grep -i "auth"

# Redeploy hosting with auth config
firebase deploy --only hosting --project acim-guide-production
```

### **Issue: "Functions Not Responding"**

**Symptoms**: Function timeouts, 500 errors
**Solution**:
```bash
# Check function logs
firebase functions:log --limit 50 --project acim-guide-production

# Redeploy functions
firebase deploy --only functions --project acim-guide-production
```

### **Issue: "Firestore Permission Denied"**

**Symptoms**: Database read/write errors
**Solution**:
```bash
# Check firestore rules
firebase firestore:rules --project acim-guide-production

# Redeploy rules if needed
firebase deploy --only firestore:rules --project acim-guide-production
```

### **Issue: "High Costs / Usage Spike"**

**Symptoms**: Unexpected Firebase billing alerts
**Solution**:
1. Check Firebase console usage metrics
2. Review function invocation patterns
3. Implement rate limiting if needed
4. Consider temporary service restrictions

---

## 📈 Post-Incident Activities

### **Immediate (Within 1 hour)**
- [ ] Verify system stability
- [ ] Document incident timeline
- [ ] Notify stakeholders of resolution
- [ ] Remove any temporary restrictions

### **Short-term (Within 24 hours)**
- [ ] Complete incident report
- [ ] Root cause analysis
- [ ] Identify preventive measures
- [ ] Update monitoring/alerting

### **Long-term (Within 1 week)**
- [ ] Implement process improvements
- [ ] Update documentation
- [ ] Team retrospective
- [ ] Enhanced monitoring/testing

---

## 🛡️ Prevention Strategies

### **Deployment Safety Measures**
1. **Staged deployments**: Test → Staging → Production
2. **Feature flags**: Gradual feature rollouts
3. **Automated testing**: Pre-deployment validation
4. **Monitoring**: Real-time health checks

### **System Resilience**
1. **Graceful degradation**: Fallback mechanisms
2. **Circuit breakers**: Prevent cascade failures
3. **Timeout configurations**: Prevent hanging requests
4. **Error boundaries**: Isolate failures

### **Operational Excellence**
1. **Regular drills**: Practice rollback procedures
2. **Documentation**: Keep procedures updated
3. **Team training**: Incident response skills
4. **Automation**: Reduce manual errors

---

## 🙏 Spiritual Approach to Incident Management

Following ACIM principles in crisis management:

### **"Nothing real can be threatened"**
- Focus on what truly matters: user experience and spiritual service
- Don't let technical issues disturb inner peace
- Remember the deeper purpose beyond the technology

### **"Miracles are natural"**
- Expect smooth operations as the natural state
- View incidents as opportunities to strengthen the system
- Trust that solutions will emerge naturally

### **"In my defenselessness my safety lies"**
- Embrace vulnerability through chaos engineering
- Learn from failures without defensiveness
- Practice transparent communication

---

## 🔧 Tools & Scripts Reference

### **Emergency Rollback Script**
```bash
chmod +x emergency-rollback.sh
./emergency-rollback.sh
```

### **Health Check Scripts**
```bash
node health-check-test.js          # Comprehensive health check
node basic-monitoring-check.js     # Basic monitoring verification
```

### **Useful Commands**
```bash
# Check deployment status
firebase projects:list
firebase use acim-guide-production

# View recent deployments  
firebase hosting:channel:list --project acim-guide-production

# Monitor function logs in real-time
firebase functions:log --follow --project acim-guide-production

# Check Firebase service status
curl -s https://status.firebase.google.com/
```

---

## 📄 Incident Log Template

```markdown
## Incident Report: [INCIDENT-ID]

**Date**: [YYYY-MM-DD]
**Time**: [HH:MM UTC]
**Severity**: [P0/P1/P2/P3]
**Duration**: [X minutes/hours]
**Affected Services**: [List services]

### Summary
Brief description of the incident.

### Timeline
- [Time]: Issue detected
- [Time]: Initial response
- [Time]: Rollback initiated (if applicable)
- [Time]: Service restored
- [Time]: Incident closed

### Root Cause
Technical explanation of what caused the issue.

### Resolution
What was done to resolve the issue.

### Impact
- Users affected: [Number/percentage]
- Financial impact: [Cost estimate]
- Reputation impact: [Assessment]

### Lessons Learned
- What went well?
- What could be improved?
- Action items for prevention

### Action Items
- [ ] Fix root cause
- [ ] Update monitoring
- [ ] Improve documentation
- [ ] Team training

**Prepared by**: [Name]
**Reviewed by**: [Name]
**Date**: [YYYY-MM-DD]
```

---

**May this rollback plan serve as a safety net that's never needed, but always ready to protect the spiritual service we provide to ACIM students worldwide.** 🕊️

*"The truth needs no defense; it merely is."* - ACIM
