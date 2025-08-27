# Sentry MCP Integration Guide for TestAlex
## Comprehensive Error Tracking & Performance Monitoring for Spiritual AI Platform

### Overview

This guide implements enterprise-grade observability for the TestAlex spiritual AI ecosystem using Sentry MCP (Managed Control Plane). The integration maintains spiritual integrity while providing production-ready monitoring for:

- **ACIMguide Platform** (React Native + Firebase)
- **AI Business Automation** (Python autonomous systems)
- **Advanced RAG Systems** (Vector databases + LLMs)
- **Autonomous CI/CD Pipeline** (GitHub Actions monitoring)
- **Research Frameworks** (ML improvement methodologies)

### 🎯 Core Principles

1. **Spiritual Integrity First**: All error tracking respects ACIM authenticity
2. **PII Protection**: User spiritual content is never exposed in error logs
3. **Production Ready**: Enterprise-grade monitoring with SOC 2 compliance capability
4. **Autonomous Integration**: Self-healing systems with intelligent alerting

## 1. Sentry Organization & Project Structure

### Organization: "TestAlex Spiritual AI"

**Projects Mapping:**
- `acimguide-web` → Web frontend (React)
- `acimguide-mobile` → React Native mobile app
- `firebase-functions` → Cloud Functions backend
- `ai-automation-py` → Business automation systems
- `rag-systems-py` → Advanced RAG frameworks
- `ci-cd-node` → Autonomous CI/CD monitoring

**Environments:** `local`, `staging`, `production`

### Environment Variables Structure

```bash
# Production DSNs (stored in Firebase Config + GitHub Secrets)
SENTRY_DSN_WEB=https://public@sentry.io/project-web
SENTRY_DSN_MOBILE=https://public@sentry.io/project-mobile  
SENTRY_DSN_FUNCTIONS=https://public@sentry.io/project-functions
SENTRY_DSN_AI=https://public@sentry.io/project-ai
SENTRY_DSN_RAG=https://public@sentry.io/project-rag
SENTRY_DSN_CI=https://public@sentry.io/project-ci

# Auth token for releases & CI integration
SENTRY_AUTH_TOKEN=sntrys_your_token_here
```

## 2. Firebase Cloud Functions Integration

### Installation & Configuration

```bash
cd functions
npm install @sentry/serverless @sentry/tracing --save
```

### Enhanced Functions Implementation

The Firebase Functions integration wraps your existing `chatWithAssistant` function with comprehensive error tracking and performance monitoring while maintaining spiritual integrity.

## 3. React Native Mobile App Integration

### Installation

```bash
cd ACIMguide
npm install @sentry/react-native --save
```

### Expo Configuration

Sentry integrates seamlessly with Expo while maintaining the spiritual purity of user interactions.

## 4. Python AI Systems Integration

### Requirements Addition

```python
# Add to ai_automation/requirements.txt and other Python components
sentry-sdk[flask]==1.38.0
sentry-sdk[fastapi]==1.38.0
```

### Autonomous Business Systems

Integration provides visibility into product generation, marketing automation, and cost monitoring without compromising business intelligence.

## 5. Autonomous CI/CD Integration

### Enhanced Failure Detection

The existing `autonomous-ci-debugger.js` system gains Sentry integration for enterprise-grade DevOps observability.

## 6. PII Scrubbing & ACIM Integrity Protection

### Spiritual Content Protection

All integrations implement strict content filtering:

1. **User Messages**: Truncated to prevent spiritual content exposure
2. **OpenAI Responses**: Scrubbed of detailed ACIM guidance
3. **Authentication**: User IDs masked, no email/personal data
4. **Rate Limiting**: Token usage metrics only, no content

### Implementation Pattern

```javascript
function scrubACIMContent(event) {
  if (event.request?.data?.message && event.request.data.message.length > 100) {
    event.request.data.message = '[ACIM_CONTENT_REDACTED]';
  }
  return event;
}
```

## 7. Performance Monitoring Strategy

### Sampling Configuration

- **Error Sampling**: 100% (all errors captured)
- **Performance Tracing**: 20% (statistical sampling)
- **Session Replay**: 1% (minimal privacy impact)
- **Profiling**: 10% (production optimization)

### Critical Metrics

- **CourseGPT Response Time**: Target P95 < 2s
- **Firebase Auth Latency**: Target P95 < 500ms
- **Mobile App Launch**: Target P95 < 3s
- **CI/CD Pipeline Health**: 99.9% success rate

## 8. Alert Configuration

### Production Alerts
- **Error Rate > 0.1%** in 5 minutes
- **P95 Response Time > 2s** for critical functions
- **Daily Token Usage > 80%** of quota
- **CI Pipeline Failures** (immediate)

### Routing Strategy
- **Production Issues** → `#acim-ops` Slack channel
- **Staging Issues** → `#acim-dev` Slack channel  
- **Critical Errors** → Email + SMS escalation

## 9. Dashboard & Reporting

### Key Dashboards

1. **Spiritual Platform Health**
   - CourseGPT response times
   - User engagement metrics
   - Authentication success rates

2. **Business Automation Insights**
   - Product generation success
   - Marketing campaign performance
   - Cost monitoring alerts

3. **Technical Infrastructure**
   - CI/CD pipeline health
   - Database performance
   - API endpoint monitoring

## 10. Compliance & Security

### SOC 2 Readiness
- **Audit Logging**: All administrative actions tracked
- **Access Control**: Role-based permissions enforced
- **Data Encryption**: All data encrypted in transit and at rest
- **Incident Response**: Automated alerting with escalation procedures

### GDPR Compliance
- **Data Minimization**: Only essential error context captured
- **User Consent**: Error tracking disclosed in privacy policy
- **Right to Deletion**: User data purging on account deletion
- **Data Processing**: Legitimate interest basis documented

## 11. Release Management

### Source Maps & Debugging

Automated source map uploads enable detailed stack traces while protecting intellectual property:

```yaml
# .github/workflows/ci-improved.yml enhancement
- name: Upload Sentry Release
  run: |
    sentry-cli releases new $GITHUB_SHA
    sentry-cli releases files $GITHUB_SHA upload-sourcemaps ./build
    sentry-cli releases finalize $GITHUB_SHA
```

### Deployment Integration

Each deployment creates a Sentry release with:
- **Git SHA**: Full traceability
- **Deployment Environment**: Staging vs production
- **Source Maps**: Full debugging capability
- **Performance Baseline**: Before/after comparison

## 12. Advanced Features

### Custom Instrumentation

Beyond automatic error capture, custom spans track business-critical operations:

```javascript
// Example: Track ACIM guidance generation performance
const transaction = Sentry.startTransaction({ name: 'acim-guidance-generation' });
const span = transaction.startChild({ op: 'openai-request' });
// ... CourseGPT interaction
span.finish();
transaction.finish();
```

### User Context (Privacy-Safe)

```javascript
Sentry.setUser({
  id: hashUserId(user.uid), // One-way hash for privacy
  segment: user.subscriptionTier, // Business intelligence
  // Never include: email, name, personal data
});
```

## 13. Maintenance & Evolution

### Health Check Integration

Enhanced health check script validates Sentry connectivity:

```javascript
// Enhanced scripts/health-check-ci.js
async function checkSentryHealth() {
  const response = await fetch(`${SENTRY_API_URL}/organizations/${ORG}/projects/`, {
    headers: { 'Authorization': `Bearer ${SENTRY_AUTH_TOKEN}` }
  });
  return response.ok;
}
```

### Continuous Improvement

Monthly review process:
1. **Error Trend Analysis**: Identify recurring patterns
2. **Performance Regression Detection**: Monitor key metrics
3. **Alert Tuning**: Reduce noise, improve signal
4. **Spiritual Integrity Audit**: Ensure ACIM purity maintained

---

## Implementation Checklist

- [ ] Create Sentry organization "TestAlex Spiritual AI"
- [ ] Configure 6 projects with staging/production environments
- [ ] Install SDKs in all components
- [ ] Implement PII scrubbing and ACIM content protection
- [ ] Configure performance monitoring with appropriate sampling
- [ ] Set up alert rules and Slack integration
- [ ] Create dashboards for spiritual platform, business automation, and technical infrastructure
- [ ] Enhance CI/CD workflows with source map uploads
- [ ] Update health check scripts
- [ ] Validate end-to-end in staging environment
- [ ] Roll out to production with monitoring

This integration transforms your spiritual AI platform with enterprise-grade observability while maintaining the sacred integrity of ACIM guidance. Every error captured, every metric tracked, and every alert sent serves the higher purpose of delivering authentic spiritual transformation to seekers worldwide.
