# 🧪 ACIMguide Testing Infrastructure

This document outlines the comprehensive testing strategy and infrastructure for the ACIMguide platform, focusing on ensuring the highest quality for spiritual seekers accessing A Course in Miracles content.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Test Types](#test-types)
3. [Coverage Requirements](#coverage-requirements)
4. [Playwright E2E Testing](#playwright-e2e-testing)
5. [Mutation Testing](#mutation-testing)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Local Development](#local-development)
8. [Test Data & Fixtures](#test-data--fixtures)
9. [Performance Testing](#performance-testing)
10. [Accessibility Testing](#accessibility-testing)
11. [Security Testing](#security-testing)
12. [Troubleshooting](#troubleshooting)

## 🎯 Overview

Our testing strategy ensures that every aspect of the ACIMguide platform maintains the highest quality standards while preserving the spiritual integrity of ACIM content.

### Testing Pyramid

```
    🔺 E2E Tests (Playwright)
      - Chat functionality
      - Course purchase flow  
      - Blog CTA interactions
      - Cross-browser compatibility
      - Mobile responsiveness

  🔺🔺 Integration Tests
    - API endpoint testing
    - Database interactions
    - Firebase integration
    - Payment processing

🔺🔺🔺 Unit Tests
  - Python backend logic
  - JavaScript/TypeScript components
  - Utility functions
  - ACIM content validation
```

### Quality Gates

- **90% Code Coverage Minimum**: Both Python and JavaScript/TypeScript
- **90% Accessibility Score**: WCAG compliance
- **80+ Performance Score**: Lighthouse audits
- **70%+ Mutation Test Score**: Code quality validation
- **Cross-browser Compatibility**: Chrome, Firefox, Safari, Edge
- **Mobile-first Design**: Responsive across all devices

## 🧪 Test Types

### 1. Unit Tests

**Python Tests** (`tests/`)
- Orchestration system logic
- Agent task execution
- Firebase integrations
- Utility functions

```bash
# Run Python unit tests
pytest tests/ --cov=orchestration --cov-fail-under=90
```

**JavaScript/TypeScript Tests** (`*.test.js`, `*.spec.ts`)
- React component testing
- Frontend utility functions
- State management
- API client logic

```bash
# Run JavaScript unit tests
npm run test:coverage
```

### 2. Integration Tests

- API endpoint testing
- Database operations
- Firebase authentication & storage
- Payment provider integration

### 3. End-to-End Tests (Playwright)

**Critical User Journeys:**

1. **Chat Functionality** (`e2e/tests/chat.spec.ts`)
   - ACIM content validation
   - Message sending/receiving
   - Quick actions
   - Error handling
   - Mobile responsiveness

2. **Course Purchase Flow** (`e2e/tests/purchase.spec.ts`)
   - Pricing display
   - Payment processing
   - Form validation
   - Security features
   - Mobile checkout

3. **Blog CTA Testing** (`e2e/tests/blog-cta.spec.ts`)
   - Call-to-action visibility
   - Click-through tracking
   - Newsletter signup
   - Social media links
   - Conversion funnel

**Cross-Browser Testing:**
- Chromium (Chrome/Edge)
- Firefox
- WebKit (Safari)
- Mobile browsers (iOS/Android)

### 4. Performance Tests

- Lighthouse CI audits
- Core Web Vitals monitoring
- API response time testing
- Memory usage profiling

### 5. Accessibility Tests

- WCAG 2.1 AA compliance
- Screen reader compatibility
- Keyboard navigation
- Color contrast validation

### 6. Security Tests

- Dependency vulnerability scanning
- Code security analysis
- XSS prevention
- CSRF protection

## 📊 Coverage Requirements

### Minimum Coverage Thresholds

| Test Type | Threshold | Tool | Enforcement |
|-----------|-----------|------|-------------|
| Python Unit | 90% | pytest-cov | CI Pipeline |
| JavaScript Unit | 90% | Jest | CI Pipeline |
| E2E Coverage | Comprehensive | Playwright | Manual Review |
| Mutation Testing | 70% | mutmut | CI Pipeline |
| Performance | 80+ | Lighthouse | CI Pipeline |
| Accessibility | 90+ | Lighthouse | CI Pipeline |

### Coverage Reports

```bash
# Python coverage HTML report
pytest --cov=orchestration --cov-report=html:htmlcov

# JavaScript coverage report  
npm run test:coverage

# View reports
open htmlcov/index.html
open coverage/lcov-report/index.html
```

## 🎭 Playwright E2E Testing

### Test Structure

```
e2e/
├── tests/                 # Test specifications
│   ├── chat.spec.ts      # Chat functionality tests
│   ├── purchase.spec.ts  # Purchase flow tests
│   └── blog-cta.spec.ts  # Blog CTA tests
├── utils/                # Page Object Models & Utilities
│   ├── chat-page.ts      # Chat page interactions
│   ├── purchase-page.ts  # Purchase flow interactions
│   ├── blog-cta-page.ts  # Blog CTA interactions
│   └── test-helpers.ts   # Common utilities
└── fixtures/             # Test data
    └── test-data.ts      # Mock data & configurations
```

### Page Object Model

We use the Page Object Model (POM) pattern for maintainable and reusable test code:

```typescript
// Example: ChatPage class
class ChatPage {
  constructor(private page: Page) {}
  
  async sendMessage(message: string): Promise<void> {
    await this.messageInput.fill(message);
    await this.sendButton.click();
  }
  
  async waitForAIResponse(): Promise<string> {
    // Wait for response logic
  }
  
  async testACIMConversation(): Promise<void> {
    // ACIM-specific test scenarios
  }
}
```

### Running E2E Tests

```bash
# Install Playwright browsers
npm run install:playwright

# Run all E2E tests
npm run test:e2e

# Run tests in headed mode (with browser UI)
npm run test:e2e:headed

# Run tests with UI mode
npm run test:e2e:ui

# Run specific test file
npx playwright test e2e/tests/chat.spec.ts

# Run tests on specific browser
npx playwright test --project=firefox
```

### ACIM Content Validation

Our E2E tests include specialized validation for ACIM content authenticity:

```typescript
async validateACIMContent(text: string): Promise<boolean> {
  const acimKeywords = ['Course in Miracles', 'Holy Spirit', 'forgiveness', 'miracle'];
  const hasACIMKeywords = acimKeywords.some(keyword => 
    text.toLowerCase().includes(keyword.toLowerCase())
  );
  
  const hasLessonStructure = /lesson \d+/i.test(text);
  return hasACIMKeywords || hasLessonStructure;
}
```

## 🧬 Mutation Testing

Mutation testing with `mutmut` ensures our test suite catches potential bugs by introducing small changes to the code.

### Configuration (`setup.cfg`)

```ini
[mutmut]
paths_to_mutate=orchestration/,scripts/
paths_to_exclude=tests/,__pycache__/,.git/
test_command=pytest tests/ -x --tb=short
timeout_factor=2.0
test_time_limit=300
```

### Running Mutation Tests

```bash
# Run mutation testing
mutmut run

# Show results
mutmut results

# Show specific mutant
mutmut show 5

# Run mutation testing with timeout
timeout 1800 mutmut run
```

### Interpreting Results

- **Killed**: Test caught the mutation ✅
- **Survived**: Mutation not caught by tests ⚠️
- **Timeout**: Test took too long ⚠️
- **Error**: Test error occurred ❌

Target: **70%+ mutation score** (killed / total mutations)

## 🔄 CI/CD Pipeline

### Workflow Overview (`.github/workflows/ci.yml`)

```yaml
name: Comprehensive CI/CD Pipeline with Testing

on:
  push: [main, develop]
  pull_request: [main, develop]
  schedule: '0 2 * * *'  # Nightly E2E tests
  workflow_dispatch: # Manual triggers

jobs:
  setup: # Repository validation
  python-tests: # Unit tests + coverage
  mutation-testing: # Code quality validation  
  node-setup: # JavaScript tests + linting
  e2e-tests: # Cross-browser E2E testing
  performance-tests: # Lighthouse audits
  security-tests: # Vulnerability scanning
  coverage-report: # Aggregate coverage
  notify-results: # Test summary
  nightly-report: # Scheduled test reports
```

### Quality Gates

The pipeline enforces these quality gates:

1. **Python tests must pass with 90%+ coverage**
2. **JavaScript tests must pass with 90%+ coverage**  
3. **E2E tests must pass across all browsers**
4. **Performance scores must meet thresholds**
5. **Security scans must pass**
6. **Mutation testing should achieve 70%+ score**

### Nightly E2E Testing

Every night at 2 AM UTC, comprehensive E2E tests run against the staging environment:

- Full browser compatibility testing
- Performance regression detection
- Accessibility compliance verification
- ACIM content validation
- Purchase flow testing
- Blog CTA conversion tracking

## 🛠 Local Development

### Quick Start

```bash
# Install dependencies
npm ci
pip install -r requirements.txt

# Run all tests
./scripts/run-tests.sh --all

# Run specific test types
./scripts/run-tests.sh --python      # Python only
./scripts/run-tests.sh --e2e        # E2E only
./scripts/run-tests.sh --mutation   # Mutation only
```

### Test Runner Options

```bash
# Test runner help
./scripts/run-tests.sh --help

# Custom coverage threshold
./scripts/run-tests.sh --all --coverage 85

# Verbose output
./scripts/run-tests.sh --python --verbose
```

### Environment Configuration

Create `.env.test` with test-specific configuration:

```env
NODE_ENV=test
PLAYWRIGHT_BASE_URL=http://localhost:3000
COVERAGE_THRESHOLD_PYTHON=90
COVERAGE_THRESHOLD_JAVASCRIPT=90
```

### Pre-commit Hooks

Set up pre-commit hooks to run tests automatically:

```bash
# Install pre-commit
pip install pre-commit

# Set up hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## 📊 Test Data & Fixtures

### Structured Test Data (`e2e/fixtures/test-data.ts`)

```typescript
export const TestUsers = {
  validUser: { email: 'test@acimguide.com', password: 'test123' },
  premiumUser: { email: 'premium@acimguide.com', password: 'premium123' }
};

export const TestMessages = {
  acimQuestions: [
    "What is lesson 1 of ACIM?",
    "Tell me about forgiveness",
    // ... more ACIM-specific queries
  ]
};

export const PaymentTestData = {
  validCard: { number: '4242424242424242', expiry: '12/25', cvc: '123' },
  declinedCard: { number: '4000000000000002', expiry: '12/25', cvc: '123' }
};
```

### Mock Data Strategy

- **Deterministic**: Same input always produces same output
- **Realistic**: Reflects real-world usage patterns
- **Comprehensive**: Covers edge cases and error scenarios
- **ACIM-Authentic**: Maintains spiritual content integrity

## ⚡ Performance Testing

### Lighthouse CI Integration

```javascript
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['/', '/chat', '/blog', '/purchase'],
      numberOfRuns: 3
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', {minScore: 0.8}],
        'categories:accessibility': ['error', {minScore: 0.9}]
      }
    }
  }
};
```

### Core Web Vitals Monitoring

- **LCP (Largest Contentful Paint)**: < 2.5s
- **FID (First Input Delay)**: < 100ms  
- **CLS (Cumulative Layout Shift)**: < 0.1

### Performance Test Scenarios

1. **Page Load Performance**
   - Cold cache loading
   - Warm cache loading
   - Slow network conditions

2. **Runtime Performance**
   - Chat message processing
   - Blog content rendering
   - Purchase flow interactions

3. **Memory Usage**
   - Memory leak detection
   - Garbage collection monitoring

## ♿ Accessibility Testing

### WCAG 2.1 AA Compliance

Our accessibility testing ensures the platform is usable by all spiritual seekers:

1. **Keyboard Navigation**
   - Tab order validation
   - Focus management
   - Skip links

2. **Screen Reader Support**
   - ARIA labels
   - Semantic markup
   - Alternative text

3. **Visual Accessibility**
   - Color contrast ratios
   - Text scaling
   - High contrast mode

### Accessibility Test Implementation

```typescript
async checkBasicAccessibility(): Promise<void> {
  // Check for alt text on images
  const images = await this.page.locator('img').all();
  for (const image of images) {
    const alt = await image.getAttribute('alt');
    expect(alt).toBeTruthy();
  }

  // Check heading hierarchy
  const h1s = await this.page.locator('h1').count();
  expect(h1s).toBe(1); // Should have exactly one h1 per page
}
```

## 🔒 Security Testing

### Vulnerability Scanning

1. **Dependency Scanning** (Trivy)
   - NPM package vulnerabilities
   - Python package vulnerabilities
   - Docker image scanning

2. **Static Code Analysis** (Bandit)
   - Security anti-patterns
   - Hardcoded secrets detection
   - SQL injection prevention

3. **Dynamic Security Testing**
   - XSS prevention
   - CSRF protection
   - Input validation

### Security Test Implementation

```bash
# Run security scans
npm audit --audit-level moderate
safety check --json
bandit -r orchestration/ -f json
trivy fs .
```

## 🐛 Troubleshooting

### Common Issues

1. **Playwright Browser Not Found**
   ```bash
   npx playwright install
   ```

2. **Python Coverage Below Threshold**
   ```bash
   pytest --cov=orchestration --cov-report=html
   open htmlcov/index.html  # Review uncovered code
   ```

3. **E2E Tests Timing Out**
   ```bash
   # Increase timeout in playwright.config.ts
   timeout: 60000  // 60 seconds
   ```

4. **Mutation Testing Taking Too Long**
   ```bash
   # Use timeout with mutmut
   timeout 1800 mutmut run
   ```

### Debug Mode

```bash
# Run E2E tests with debug
DEBUG=pw:* npm run test:e2e

# Run Playwright in headed mode
npm run test:e2e:headed

# Python tests with verbose output
pytest -v -s tests/

# JavaScript tests in watch mode
npm run test:watch
```

### CI/CD Debugging

1. **Check GitHub Actions logs**
2. **Download test artifacts**
3. **Review coverage reports**
4. **Examine Playwright traces**

### Getting Help

- **Internal Documentation**: `/docs/`
- **Test Artifacts**: Check CI/CD pipeline artifacts
- **Debug Logs**: Enable verbose logging
- **Community**: ACIM development community

---

## 📝 Summary

This comprehensive testing infrastructure ensures that the ACIMguide platform maintains the highest quality standards while preserving the sacred nature of ACIM content. Every component is thoroughly tested across multiple dimensions:

- **Functionality**: Unit and integration tests
- **User Experience**: E2E testing across browsers and devices  
- **Performance**: Speed and efficiency monitoring
- **Accessibility**: Universal access compliance
- **Security**: Vulnerability prevention
- **Code Quality**: Mutation testing and coverage analysis

The 90% coverage threshold and nightly E2E testing provide confidence that spiritual seekers will have a reliable, secure, and accessible experience when engaging with A Course in Miracles content through our platform.

---

*"Nothing real can be threatened. Nothing unreal exists. Herein lies the peace of God."* - A Course in Miracles

Our testing practices honor this truth by ensuring only what is genuine and helpful reaches those seeking spiritual guidance.
