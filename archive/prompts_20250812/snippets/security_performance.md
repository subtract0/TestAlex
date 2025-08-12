# Security & Performance Guidelines

## Secrets Handling

### Environment Variables
- **NEVER** hardcode secrets in source code, configuration files, or version control
- Use environment variables for all sensitive data: API keys, database URLs, auth tokens
- Implement tiered environment management: `dev`, `staging`, `prod`
- Use dotenv files locally with `.env` in `.gitignore`
- Validate required environment variables at application startup

```javascript
// Good: Environment variable usage
const apiKey = process.env.FIREBASE_API_KEY;
if (!apiKey) {
  throw new Error('FIREBASE_API_KEY environment variable is required');
}

// Bad: Hardcoded secret
const apiKey = 'AIzaSyDGx7B4Kf9L2mN3oP4qR5s6T7u8V9w0X1y';
```

### Firebase Configuration
- Store Firebase config as environment variables, not in client-side code
- Use Firebase Security Rules for client-side access control
- Implement Firebase App Check for production apps
- Rotate Firebase service account keys regularly
- Use Firebase Emulator Suite for local development

```javascript
// Secure Firebase initialization
const firebaseConfig = {
  apiKey: process.env.FIREBASE_API_KEY,
  authDomain: process.env.FIREBASE_AUTH_DOMAIN,
  projectId: process.env.FIREBASE_PROJECT_ID,
  // ... other config from env vars
};
```

### Secret Management Best Practices
- Use cloud secret managers (AWS Secrets Manager, Google Secret Manager)
- Implement secret rotation policies (90 days max)
- Use least-privilege access principles
- Audit secret access regularly
- Never log sensitive data

## Rate Limiting & Token Cost Management

### Rate Limit Awareness
- Implement exponential backoff with jitter for API retries
- Cache responses when possible to reduce API calls
- Use request queuing to avoid burst rate limit violations
- Monitor rate limit headers: `X-RateLimit-Remaining`, `Retry-After`

```javascript
// Rate limit aware API client
class RateLimitedClient {
  async makeRequest(url, options = {}) {
    const maxRetries = 3;
    let retryCount = 0;
    
    while (retryCount < maxRetries) {
      try {
        const response = await fetch(url, options);
        
        if (response.status === 429) {
          const retryAfter = response.headers.get('Retry-After') || Math.pow(2, retryCount);
          await this.sleep(retryAfter * 1000 + Math.random() * 1000); // Add jitter
          retryCount++;
          continue;
        }
        
        return response;
      } catch (error) {
        retryCount++;
        await this.sleep(Math.pow(2, retryCount) * 1000);
      }
    }
    throw new Error('Max retries exceeded');
  }
}
```

### Token Cost Estimation Formulas

#### OpenAI/LLM Costs
```
Total Cost = (Input Tokens × Input Rate) + (Output Tokens × Output Rate)

Where:
- Input Tokens ≈ Characters / 4 (rough estimate)
- Output Tokens = Generated response length / 4
- Rates vary by model (e.g., GPT-4: $0.03/1K input, $0.06/1K output)

Monthly Budget = Daily Requests × Avg Tokens per Request × Token Rate × 30
```

#### Firebase Costs
```
Firestore Reads = Document Reads + Query Executions
Firestore Writes = Document Writes + Index Updates
Storage Cost = (Storage Used in GB) × $0.18/month
Function Invocations = Request Count × ($0.40/1M requests)
Function Compute = (Memory × Duration) × $0.0000025/100ms
```

### Cost Optimization Strategies
- Implement request deduplication
- Use caching layers (Redis, in-memory)
- Batch API requests when possible
- Set spending alerts and circuit breakers
- Monitor token usage per user/session

## OWASP Best Practices

### OWASP Mobile Top 10 Compliance

#### M1: Improper Platform Usage
- Follow platform security guidelines (iOS Keychain, Android Keystore)
- Implement proper permission models
- Use secure inter-app communication

#### M2: Insecure Data Storage
- Encrypt sensitive data at rest
- Use secure storage APIs (Keychain, EncryptedSharedPreferences)
- Avoid storing sensitive data in logs, temp files

#### M3: Insecure Communication
- Use TLS 1.2+ for all network communication
- Implement certificate pinning
- Validate all server certificates

```kotlin
// Android secure storage example
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val sharedPreferences = EncryptedSharedPreferences.create(
    context,
    "secret_shared_prefs",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)
```

#### M4: Insecure Authentication
- Implement multi-factor authentication
- Use OAuth 2.0/OIDC for third-party auth
- Implement proper session management
- Use biometric authentication when available

#### M5: Insufficient Cryptography
- Use established cryptographic libraries
- Never implement custom crypto
- Use proper key derivation (PBKDF2, Argon2)
- Implement secure random number generation

### OWASP Cloud Function Security

#### Function Authentication & Authorization
- Implement proper IAM roles and policies
- Use function-level authentication
- Validate all inputs and sanitize outputs
- Implement request signing for sensitive operations

#### Secure Function Development
```javascript
// Secure Cloud Function template
exports.secureFunction = functions
  .runWith({
    memory: '256MB',
    timeoutSeconds: 30
  })
  .https.onCall(async (data, context) => {
    // 1. Authentication check
    if (!context.auth) {
      throw new functions.https.HttpsError('unauthenticated', 'User must be authenticated');
    }
    
    // 2. Input validation
    const { userInput } = data;
    if (!userInput || typeof userInput !== 'string' || userInput.length > 1000) {
      throw new functions.https.HttpsError('invalid-argument', 'Invalid input');
    }
    
    // 3. Authorization check
    const userRole = await getUserRole(context.auth.uid);
    if (!userRole.includes('required-permission')) {
      throw new functions.https.HttpsError('permission-denied', 'Insufficient permissions');
    }
    
    // 4. Rate limiting
    await checkRateLimit(context.auth.uid);
    
    try {
      // 5. Business logic with error handling
      const result = await processSecurely(userInput);
      return { success: true, data: result };
    } catch (error) {
      console.error('Function error:', error.message); // Don't log sensitive data
      throw new functions.https.HttpsError('internal', 'Processing failed');
    }
  });
```

## Performance Budgets

### Cloud Functions Performance Requirements

#### Cold Start Budget: ≤200ms
- Use lightweight runtime (Node.js 18+, Python 3.9+)
- Minimize dependency size and startup code
- Implement connection pooling
- Use global variables for reusable connections

```javascript
// Optimize cold starts
const { initializeApp, getApps } = require('firebase-admin/app');
const { getFirestore } = require('firebase-admin/firestore');

// Global initialization (reused across invocations)
const app = getApps().length === 0 ? initializeApp() : getApps()[0];
const db = getFirestore(app);

exports.optimizedFunction = functions
  .runWith({
    memory: '256MB', // Right-size memory for performance
    timeoutSeconds: 10
  })
  .https.onCall(async (data, context) => {
    // Function logic here
  });
```

#### Function Optimization Strategies
- Use appropriate memory allocation (256MB-1GB based on workload)
- Implement lazy loading for heavy dependencies
- Cache expensive computations
- Use Cloud Function concurrency settings
- Monitor and optimize based on metrics

### Android Performance Requirements

#### First Render Budget: <1 Second
- Target First Contentful Paint (FCP) ≤800ms
- Implement progressive loading strategies
- Optimize initial bundle size
- Use code splitting and lazy loading

```kotlin
// Android performance optimization
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Measure startup time
        val startTime = System.currentTimeMillis()
        
        // Optimize initial loading
        setContentView(R.layout.activity_main)
        
        // Defer non-critical initialization
        lifecycleScope.launch {
            initializeNonCriticalComponents()
        }
        
        // Report startup metrics
        val loadTime = System.currentTimeMillis() - startTime
        FirebasePerformance.startTrace("app_startup")
            .putMetric("startup_time_ms", loadTime)
            .stop()
    }
}
```

#### Mobile Performance Monitoring
- Use Firebase Performance Monitoring
- Track custom metrics: screen load times, API response times
- Monitor memory usage and prevent leaks
- Implement network request caching
- Use image optimization and lazy loading

```kotlin
// Performance monitoring setup
val trace = FirebasePerformance.getInstance().newTrace("network_request")
trace.start()

try {
    val response = apiCall()
    trace.putAttribute("response_code", response.code.toString())
    trace.putMetric("response_time_ms", response.responseTime)
} catch (e: Exception) {
    trace.putAttribute("error", e.message ?: "unknown")
} finally {
    trace.stop()
}
```

### Performance Budget Enforcement
- Set up automated performance testing in CI/CD
- Use Lighthouse CI for web performance
- Implement performance regression detection
- Set up alerts for budget violations
- Regular performance audits and optimization reviews

## Monitoring & Alerting

### Security Monitoring
- Monitor failed authentication attempts
- Track API abuse and unusual usage patterns
- Set up alerts for secret access/rotation
- Log security-relevant events (not sensitive data)

### Performance Monitoring
- Track function execution times and memory usage
- Monitor API response times and error rates
- Set up alerts for performance budget violations
- Use distributed tracing for complex request flows

### Budget Alerts
```javascript
// Example budget monitoring
const PERFORMANCE_BUDGETS = {
  coldStart: 200, // ms
  firstRender: 1000, // ms
  apiResponse: 500, // ms
};

function checkPerformanceBudget(metric, value) {
  if (value > PERFORMANCE_BUDGETS[metric]) {
    console.warn(`Performance budget exceeded: ${metric} took ${value}ms (budget: ${PERFORMANCE_BUDGETS[metric]}ms)`);
    // Send alert to monitoring system
    sendAlert(`Performance budget violation: ${metric}`, { value, budget: PERFORMANCE_BUDGETS[metric] });
  }
}
```

---

*This document should be referenced by backend, cloud functions, and mobile development prompts to ensure consistent security and performance standards across all components.*
