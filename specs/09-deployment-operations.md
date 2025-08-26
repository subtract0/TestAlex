# 09. Deployment & Operations

*"Those who are certain of the outcome can afford to wait, and wait without anxiety." — ACIM*

## DevOps Philosophy

Our deployment and operations strategy balances reliability, speed, and spiritual integrity. We automate everything that can be automated, monitor everything that matters, and keep humans in the loop for spiritual quality and safety.

## Environments & Configuration

### Environment Matrix

| Environment | Purpose | Branch | Firebase Project | OpenAI Assistant |
|-------------|---------|--------|------------------|------------------|
| **Development** | Active feature development | develop | acimguide-dev | assistant_dev_id |
| **Staging** | Pre-release validation | release/* | acimguide-staging | assistant_staging_id |
| **Production** | Live users | main | acimguide | assistant_prod_id |

### Configuration Management

```yaml
# config/environments.yaml
development:
  firebase:
    projectId: acimguide-dev
    region: us-central1
  openai:
    assistantId: ${OPENAI_ASSISTANT_ID_DEV}
    vectorStoreId: ${VECTOR_STORE_ID_DEV}
  logging:
    level: debug
  monitoring:
    samplingRate: 0.1

staging:
  firebase:
    projectId: acimguide-staging
    region: us-central1
  openai:
    assistantId: ${OPENAI_ASSISTANT_ID_STAGING}
    vectorStoreId: ${VECTOR_STORE_ID_STAGING}
  logging:
    level: info
  monitoring:
    samplingRate: 0.5

production:
  firebase:
    projectId: acimguide
    region: us-central1
  openai:
    assistantId: ${OPENAI_ASSISTANT_ID_PROD}
    vectorStoreId: ${VECTOR_STORE_ID_PROD}
  logging:
    level: warn
  monitoring:
    samplingRate: 1.0
```

## CI/CD Pipelines

### GitHub Actions Workflows

```yaml
# .github/workflows/ci.yml
name: CI
on:
  pull_request:
    branches: [ develop, main ]
  push:
    branches: [ develop ]

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - run: npm ci --workspace functions
      - run: npm run lint --workspace functions
      - run: npm test --workspace functions -- --coverage
      - run: npm ci --workspace ACIMguide
      - run: npm run typecheck --workspace ACIMguide || true
      - run: npm run test --workspace ACIMguide -- --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  deploy-staging:
    needs: build-test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/setup-gcloud@v2
        with:
          project_id: acimguide-staging
          export_default_credentials: true
      - name: Firebase deploy (staging)
        run: |
          npm ci --workspace functions
          npx firebase deploy --only functions --project acimguide-staging

  release-builds:
    if: startsWith(github.ref, 'refs/heads/release/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: EAS build
        run: |
          npm ci --workspace ACIMguide
          npx eas build --platform all --non-interactive

  deploy-production:
    needs: release-builds
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/setup-gcloud@v2
        with:
          project_id: acimguide
          export_default_credentials: true
      - name: Firebase deploy (prod)
        run: |
          npm ci --workspace functions
          npx firebase deploy --only functions --project acimguide
```

### Mobile Delivery (Expo EAS)

```json
// ACIMguide/eas.json
{
  "cli": { "version": ">= 13.5.0" },
  "build": {
    "development": { "distribution": "internal", "channel": "development" },
    "staging": { "channel": "staging" },
    "production": { "channel": "production" }
  },
  "submit": {
    "staging": {},
    "production": {}
  }
}
```

## Monitoring & Observability

### SLOs and Alerts

```yaml
# monitoring/slo.yaml
slos:
  - name: Chat P95 Latency
    target: 0.95 <= 1s
    alert: >1s for 5m
  - name: Error Rate
    target: < 1%
    alert: > 5% for 5m
  - name: Uptime
    target: > 99.9%
    alert: incident
```

### Firebase Performance & Logs

- Track: function execution time, cold starts, memory usage
- Correlate: request IDs from client to server logs
- Log fields: userId (hashed), threadId, runId, tokens, status, latency

### App Monitoring

- Crashlytics for crash tracking
- In-app metrics: session length, satisfaction prompts, return rate
- Spiritual indicators: peace score, citation interactions

## Disaster Recovery & Rollbacks

### Rollback Procedures

```bash
# Roll back Firebase Functions
gcloud functions versions list --gen2 --region=us-central1 --service=chatWithAssistant
# Identify last good version
gcloud functions versions delete --gen2 VERSION_ID --region=us-central1 --service=chatWithAssistant

# Roll back EAS channel
npx eas channel:edit production --branch previous-stable
```

### Backup Policies

| Asset | Backup | Retention | Restore Time |
|-------|--------|-----------|--------------|
| Firestore | Point-in-time | 7 years | < 1 hour |
| Secrets | Secret Manager | Current + 2 prev | < 5 minutes |
| Config | Git + S3 snapshot | 1 year | < 15 minutes |
| Mobile Builds | EAS artifacts | 1 year | < 30 minutes |

## Operational Runbooks

### Incident Response

1. Detect alert (latency, error rate, uptime)
2. Acknowledge in incident tool
3. Identify scope and probable cause
4. Mitigate (scale-up, rollback, feature flag)
5. Communicate status (status page, internal)
6. Resolve + verify SLO recovery
7. Postmortem within 48 hours

### Capacity Management

- Weekly review of usage trends
- Adjust Firebase quotas and OpenAI rate limits
- Pre-scale before major content pushes

### Cost Management

- Track OpenAI cost per user session
- Set budget alerts by project and service
- Auto-throttle heavy users if budget exceeded

## Compliance & Privacy Ops

- Data subject requests (export/delete) handled within 30 days
- Audit logs retained for 1 year (access, changes)
- DPIAs (Data Protection Impact Assessments) for major changes

## Operational Metrics Dashboard

```typescript
interface OpsDashboard {
  reliability: {
    uptime: number; // %
    errorRate: number; // %
    p95Latency: number; // ms
  };
  usage: {
    dailyActiveUsers: number;
    messagesPerSecond: number;
    averageSessionLength: number; // seconds
  };
  cost: {
    openAICostPer1000Messages: number;
    firebaseCostPerUser: number;
    infraSpendMonthToDate: number;
  };
  incidents: {
    openIncidents: number;
    mttr: number; // mean time to recovery
    lastIncidentDate: string;
  };
}
```

---

*"Peace is stronger than war because it heals."* — ACIM

These Deployment & Operations specifications ensure that ACIMguide is reliable, observable, and responsibly managed in production, while honoring the sacred nature of the service we provide.
