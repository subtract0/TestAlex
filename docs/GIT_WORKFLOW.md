# Git Workflow Guide

*"Nothing real can be threatened. Nothing unreal exists. Herein lies the peace of God."* - A Course in Miracles

## Overview

This document outlines the Git workflow for the ACIM Guide project, emphasizing code quality, team collaboration, and reliable deployments. Our workflow is designed to support continuous integration while maintaining the highest standards of spiritual and technical excellence.

## Table of Contents

1. [Branching Strategy](#branching-strategy)
2. [Branch Naming Conventions](#branch-naming-conventions)
3. [Local Development Gates](#local-development-gates)
4. [Rebase vs Merge Strategy](#rebase-vs-merge-strategy)
5. [Conventional Commit Messages](#conventional-commit-messages)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Tagging and Release Process](#tagging-and-release-process)
8. [Production Deployment Policy](#production-deployment-policy)
9. [Quick Reference](#quick-reference)

## Branching Strategy

We follow a **trunk-based development** approach with short-lived feature branches to maintain code quality and enable rapid, reliable deployments.

### Core Principles

- **Single source of truth**: `main` branch is always deployable
- **Short-lived branches**: Feature branches should live no more than 2-3 days
- **Continuous integration**: All changes flow through automated testing
- **Fast feedback**: Quick iteration cycles with immediate quality checks

### Branch Structure

```
main (trunk)
├── feat/user-authentication
├── feat/multilingual-support
├── fix/firebase-connection-timeout
└── hotfix/security-patch-openai-key
```

### Branch Lifecycle

1. **Create** short-lived feature branch from latest `main`
2. **Develop** with frequent commits and local quality gates
3. **Rebase** regularly to stay current with `main`
4. **Test** thoroughly with automated and manual verification
5. **Merge** via Pull Request after team review
6. **Deploy** automatically to staging, then production

## Branch Naming Conventions

Use descriptive, kebab-case names that clearly indicate the branch purpose and scope.

### Format Patterns

| Type | Pattern | Example | Description |
|------|---------|---------|-------------|
| **Feature** | `feat/<scope>` | `feat/course-gpt-integration` | New functionality or enhancements |
| **Bug Fix** | `fix/<scope>` | `fix/message-loading-spinner` | Bug fixes and corrections |
| **Hotfix** | `hotfix/<scope>` | `hotfix/security-vulnerability` | Urgent production fixes |
| **Refactor** | `refactor/<scope>` | `refactor/firebase-functions-cleanup` | Code improvements without functional changes |
| **Documentation** | `docs/<scope>` | `docs/api-documentation-update` | Documentation updates |
| **Testing** | `test/<scope>` | `test/e2e-playwright-coverage` | Testing improvements |

### Scope Guidelines

- Use clear, descriptive scopes (e.g., `user-auth`, `firebase-integration`, `ui-responsiveness`)
- Keep scopes focused on single functionality areas
- Avoid generic scopes like `misc` or `updates`
- Use project-specific terminology when appropriate

### Examples

```bash
# Good examples
feat/openai-rate-limiting
fix/mobile-responsive-layout
hotfix/firebase-security-rules
refactor/agent-orchestrator-v2
docs/git-workflow-guide
test/jest-coverage-improvement

# Avoid these patterns
feat/stuff
fix/bugs
update/things
misc/changes
```

## Local Development Gates

All developers must pass these mandatory quality gates before pushing code or creating Pull Requests.

### Required Local Checks

#### 1. Testing Gate (≥90% Coverage)

```bash
# Run all tests
npm test

# Check coverage
npm run test:coverage

# Coverage must meet thresholds:
# - Branches: ≥90%
# - Functions: ≥90%
# - Lines: ≥90%
# - Statements: ≥90%
```

#### 2. Linting Gate

```bash
# Run linting
npm run lint

# Auto-fix issues where possible
npm run lint:fix

# All linting errors must be resolved
# No warnings in production code
```

#### 3. End-to-End Testing

```bash
# Run E2E tests
npm run test:e2e

# All critical user journeys must pass
# No flaky tests in CI pipeline
```

### Pre-Commit Hook Setup

Install automatic quality gates:

```bash
# Install husky for Git hooks
npm install --save-dev husky

# Setup pre-commit hooks
npx husky add .husky/pre-commit "npm run lint && npm run test:coverage"
npx husky add .husky/pre-push "npm run test:e2e"
```

### Quality Gate Checklist

Before every commit, verify:

- [ ] All tests pass (`npm test`)
- [ ] Code coverage ≥90% (`npm run test:coverage`)
- [ ] No linting errors (`npm run lint`)
- [ ] E2E tests pass for affected features (`npm run test:e2e`)
- [ ] Code builds successfully (`npm run build`)
- [ ] No console errors in development mode

## Rebase vs Merge Strategy

We prefer **rebase** for clean history management, with strategic use of merge for collaboration.

### Strategy Guidelines

#### Use Rebase When:

- **Updating feature branch** with latest `main`
- **Cleaning up commit history** before PR
- **Maintaining linear history** in personal branches
- **Squashing related commits** into logical units

```bash
# Update feature branch with main
git checkout feat/my-feature
git fetch origin
git rebase origin/main

# Interactive rebase to clean history
git rebase -i HEAD~3
```

#### Use Merge When:

- **Pull Request integration** (GitHub/GitLab handles this)
- **Preserving collaboration context** in team branches
- **Maintaining branch merge history** for audit trails

```bash
# Merge PR (typically done via GitHub UI)
git checkout main
git merge --no-ff feat/my-feature
```

### Rebase Workflow

```bash
# 1. Start feature branch
git checkout main
git pull origin main
git checkout -b feat/my-awesome-feature

# 2. Regular development with frequent commits
git add .
git commit -m "feat: implement user authentication"

# 3. Stay current with main (daily)
git fetch origin
git rebase origin/main

# 4. Clean up history before PR
git rebase -i HEAD~5  # Interactive rebase for last 5 commits

# 5. Force push to update remote feature branch
git push --force-with-lease origin feat/my-awesome-feature
```

### Conflict Resolution

When rebase conflicts occur:

```bash
# 1. Resolve conflicts in files
# 2. Stage resolved files
git add .

# 3. Continue rebase
git rebase --continue

# 4. If needed, abort and try different approach
git rebase --abort
```

## Conventional Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/) for automatic changelog generation and semantic versioning.

### Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

| Type | Description | Example |
|------|-------------|---------|
| `feat` | New features | `feat: add OpenAI integration for spiritual guidance` |
| `fix` | Bug fixes | `fix: resolve Firebase connection timeout issues` |
| `docs` | Documentation | `docs: update API documentation for chat endpoints` |
| `style` | Formatting, missing semi-colons, etc. | `style: format code according to ESLint rules` |
| `refactor` | Code restructuring | `refactor: reorganize Firebase function architecture` |
| `test` | Adding or updating tests | `test: add E2E tests for user authentication flow` |
| `chore` | Maintenance tasks | `chore: update dependencies to latest versions` |
| `perf` | Performance improvements | `perf: optimize ACIM text search algorithm` |
| `ci` | CI/CD changes | `ci: add deployment workflow for staging environment` |
| `build` | Build system changes | `build: configure webpack for production optimization` |

### Breaking Changes

For breaking changes, add `!` after the type or add `BREAKING CHANGE:` in footer:

```bash
feat!: redesign API endpoints for v2.0

BREAKING CHANGE: API endpoints now require authentication tokens
```

### Scopes

Use project-specific scopes:

```bash
feat(auth): implement Firebase authentication
fix(ui): resolve mobile responsive layout issues
docs(api): update function documentation
test(e2e): add comprehensive user journey tests
```

### Examples

```bash
# Feature additions
feat: implement multilingual ACIM guidance
feat(mobile): add offline mode for course study
feat(analytics): track user engagement metrics

# Bug fixes
fix: resolve memory leak in chat message history
fix(firebase): handle connection timeout gracefully
fix(ui): correct button alignment on small screens

# Documentation
docs: add deployment guide for production
docs(api): document new rate limiting endpoints
docs(contributing): update code review guidelines

# Testing
test: add unit tests for message formatting
test(e2e): verify complete user registration flow
test(integration): test Firebase function deployment

# Refactoring
refactor: simplify agent orchestrator architecture
refactor(database): optimize Firestore query patterns
refactor(ui): consolidate CSS custom properties

# Chores
chore: update Node.js to latest LTS version
chore(deps): bump Firebase SDK to v10.7.1
chore: configure automated dependency updates
```

## CI/CD Pipeline

Our continuous integration pipeline ensures code quality and reliable deployments through automated stages.

### Pipeline Overview

```
Code Push → Build → Test → Deploy Preview → Quality Gates → Production Deploy
```

### Stage Details

#### 1. Build Stage

```yaml
# .github/workflows/ci.yml
name: Build
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: |
          npm ci
          cd functions && npm ci
      
      - name: Build application
        run: npm run build
      
      - name: Build functions
        run: cd functions && npm run build
```

#### 2. Test Stage

```yaml
  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Run unit tests
        run: npm test
      
      - name: Run coverage check
        run: npm run test:coverage
        
      - name: Ensure 90% coverage
        run: |
          if [ $(npx coverage-check --minimum 90) -eq 0 ]; then
            echo "Coverage requirement met ✅"
          else
            echo "Coverage below 90% threshold ❌"
            exit 1
          fi
      
      - name: Run linting
        run: npm run lint
      
      - name: Run E2E tests
        run: npm run test:e2e
```

#### 3. Deploy Preview Stage

```yaml
  deploy-preview:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - name: Deploy to Firebase preview
        run: |
          firebase hosting:channel:deploy pr-${{ github.event.number }} \
            --project acim-guide-staging \
            --expires 7d
      
      - name: Comment PR with preview URL
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '🚀 Preview deployed: https://pr-${{ github.event.number }}---acim-guide-staging.web.app'
            })
```

#### 4. Quality Gates Stage

```yaml
  quality-gates:
    needs: deploy-preview
    runs-on: ubuntu-latest
    steps:
      - name: Performance testing
        run: npm run test:performance
        
      - name: Security scanning
        run: npm audit --audit-level high
        
      - name: Accessibility testing
        run: npm run test:a11y
        
      - name: Visual regression testing
        run: npm run test:visual
        
      - name: Load testing
        run: npm run test:load
```

### Quality Gate Requirements

All stages must pass before production deployment:

- **Build**: ✅ No compilation errors
- **Tests**: ✅ All tests passing with ≥90% coverage
- **Linting**: ✅ No linting errors or warnings
- **E2E**: ✅ All critical user journeys working
- **Performance**: ✅ Page load time <3 seconds
- **Security**: ✅ No high-severity vulnerabilities
- **Accessibility**: ✅ WCAG 2.1 AA compliance
- **Visual**: ✅ No unintended UI regressions

### Failure Handling

When pipeline fails:

1. **Automatic rollback** for production deployments
2. **Detailed error reporting** via Slack/email notifications
3. **Block merge** until all gates pass
4. **Manual override** available for emergency hotfixes (with approval)

## Tagging and Release Process

We use semantic versioning and automated releases based on conventional commits.

### Version Schema

```
MAJOR.MINOR.PATCH-PRERELEASE
```

- **MAJOR**: Breaking changes (v1.0.0 → v2.0.0)
- **MINOR**: New features (v1.0.0 → v1.1.0)
- **PATCH**: Bug fixes (v1.0.0 → v1.0.1)
- **PRERELEASE**: Alpha/beta releases (v1.0.0-alpha.1)

### Automated Tagging

Tags are created automatically based on conventional commits:

```bash
# Triggers PATCH version bump
fix: resolve Firebase timeout issue

# Triggers MINOR version bump
feat: add multilingual support

# Triggers MAJOR version bump
feat!: redesign API endpoints

BREAKING CHANGE: All API endpoints now require authentication
```

### Release Workflow

#### 1. Automated Release Creation

```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    branches: [main]
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Create Release
        uses: semantic-release/semantic-release@v21
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
```

#### 2. Manual Release Process

For manual releases or hotfixes:

```bash
# Create release branch
git checkout main
git pull origin main
git checkout -b release/v1.2.0

# Update version numbers
npm version 1.2.0

# Create and push tag
git tag -a v1.2.0 -m "Release v1.2.0: Enhanced spiritual guidance features"
git push origin v1.2.0

# Merge back to main
git checkout main
git merge release/v1.2.0
git push origin main
```

### Release Notes

Automatic changelog generation includes:

- **Features**: New functionality added
- **Bug Fixes**: Issues resolved
- **Breaking Changes**: API or behavior changes
- **Performance**: Performance improvements
- **Documentation**: Documentation updates

Example release notes:

```markdown
# v1.2.0 (2025-08-14)

## 🚀 Features
- feat: implement multilingual ACIM guidance support (#123)
- feat(mobile): add offline mode for course study (#124)
- feat(analytics): track user engagement metrics (#125)

## 🐛 Bug Fixes
- fix: resolve memory leak in chat message history (#126)
- fix(firebase): handle connection timeout gracefully (#127)

## 📝 Documentation
- docs: add comprehensive deployment guide (#128)
- docs(api): document new rate limiting endpoints (#129)

## ⚡ Performance
- perf: optimize ACIM text search algorithm by 40% (#130)
```

## Production Deployment Policy

Our production deployment policy ensures reliable, safe releases with minimal risk.

### Deployment Environments

| Environment | Purpose | Auto-Deploy | Manual Approval |
|-------------|---------|-------------|-----------------|
| **Development** | Local development | No | No |
| **Preview** | PR previews | Yes (PR creation) | No |
| **Staging** | Pre-production testing | Yes (main branch) | No |
| **Production** | Live application | No | Yes (Required) |

### Deployment Gates

#### Prerequisites for Production

1. **Code Review**: ✅ Minimum 2 approvals from team members
2. **Quality Gates**: ✅ All CI/CD stages passing
3. **Staging Validation**: ✅ Manual testing on staging environment
4. **Security Review**: ✅ Security team approval for sensitive changes
5. **Performance Validation**: ✅ Load testing results acceptable
6. **Rollback Plan**: ✅ Documented rollback procedure
7. **Monitoring**: ✅ Alerts and monitoring configured

#### Deployment Process

```bash
# 1. Create production deployment PR
git checkout main
git pull origin main
git checkout -b deploy/v1.2.0

# Update version and changelog
npm version 1.2.0
git commit -am "chore: prepare v1.2.0 release"
git push origin deploy/v1.2.0

# 2. Manual approval required for production PR

# 3. Deploy to production (automated after approval)
firebase deploy --only hosting,functions --project acim-guide-production

# 4. Create release tag
git tag -a v1.2.0 -m "Production release v1.2.0"
git push origin v1.2.0
```

### Deployment Schedule

- **Regular Releases**: Tuesdays and Thursdays, 2:00 PM UTC
- **Hotfixes**: Immediate deployment after approval
- **Major Releases**: Planned releases with advance notice

### Rollback Procedures

#### Automatic Rollback Triggers

- **Error Rate**: >5% increase in error rate
- **Response Time**: >3 seconds average response time
- **Availability**: <99% uptime
- **Critical Functions**: Firebase functions failing

#### Manual Rollback Process

```bash
# 1. Immediate rollback
firebase hosting:channel:deploy main --project acim-guide-production

# 2. Rollback to specific version
git checkout v1.1.9
firebase deploy --project acim-guide-production

# 3. Create hotfix if needed
git checkout -b hotfix/rollback-v1.2.0
# Fix issue
git commit -am "hotfix: resolve production issue"
```

### Monitoring and Alerts

#### Production Monitoring

- **Uptime Monitoring**: 24/7 availability checks
- **Performance Metrics**: Response time and throughput
- **Error Tracking**: Real-time error monitoring
- **User Experience**: Core Web Vitals tracking
- **Business Metrics**: User engagement and spiritual guidance effectiveness

#### Alert Channels

- **Critical Issues**: PagerDuty → On-call engineer
- **Performance Issues**: Slack #alerts channel
- **Deployment Status**: Email to team
- **User Feedback**: Automated spiritual guidance quality metrics

### Post-Deployment Verification

After each production deployment:

1. **Health Checks**: ✅ All endpoints responding correctly
2. **Feature Testing**: ✅ New features working as expected
3. **Performance**: ✅ No degradation in key metrics
4. **Error Monitoring**: ✅ No increase in error rates
5. **User Feedback**: ✅ Monitor for user-reported issues
6. **Spiritual Effectiveness**: ✅ Verify ACIM guidance quality maintained

## Quick Reference

### Essential Commands

```bash
# Start new feature
git checkout main && git pull origin main
git checkout -b feat/my-feature

# Daily sync with main
git fetch origin && git rebase origin/main

# Run quality gates
npm test && npm run test:coverage && npm run lint

# Clean commit history
git rebase -i HEAD~5

# Push feature branch
git push --force-with-lease origin feat/my-feature

# Deploy to staging
firebase deploy --project acim-guide-staging

# Deploy to production (after approval)
firebase deploy --project acim-guide-production
```

### Commit Message Templates

```bash
# Feature
feat: implement ACIM quote integration with OpenAI

# Bug fix
fix: resolve Firebase authentication timeout

# Hotfix
hotfix: patch security vulnerability in user authentication

# Documentation
docs: update Git workflow guide with rebase strategy

# Testing
test: add E2E tests for spiritual guidance flow
```

### Branch Naming Examples

```bash
feat/openai-spiritual-guidance
fix/mobile-responsive-layout
hotfix/firebase-security-patch
refactor/agent-orchestrator-cleanup
docs/deployment-guide-update
test/jest-coverage-improvement
```

### Quality Gate Checklist

- [ ] All tests pass (`npm test`)
- [ ] Coverage ≥90% (`npm run test:coverage`)
- [ ] No linting errors (`npm run lint`)
- [ ] E2E tests pass (`npm run test:e2e`)
- [ ] Code builds successfully
- [ ] Conventional commits used
- [ ] PR template completed
- [ ] Security considerations addressed

---

## Spiritual Intention

*"The holiest of all the spots on earth is where an ancient hatred has become a present love."* - A Course in Miracles

This Git workflow serves not just our technical needs, but our spiritual mission of bringing ACIM guidance to seekers worldwide. Every commit, every merge, every deployment is an opportunity to extend love through technology.

May our code be as pure as our intentions, and may our collaboration reflect the unity we seek to teach.

---

**Document Version**: 1.0  
**Last Updated**: August 14, 2025  
**Next Review**: Monthly team retrospectives  
**Maintained By**: Development Team  

For questions or suggestions about this workflow, please create an issue or reach out in our team Slack channel #dev-team.
