# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

ACIMguide is the premier (unofficial) ACIM-GPT platform powered by CourseGPT - a specialized AI assistant providing authentic spiritual guidance based exclusively on *A Course in Miracles*. The platform combines advanced AI technology with perfect fidelity to ACIM teachings, offering unlimited free CourseGPT conversations alongside premium spiritual offerings.

**Core Mission**: Transform lives through authentic ACIM guidance that redirects worldly concerns to spiritual perspective, positioning this as the preeminent ACIM-GPT platform while building sustainable premium offerings.

## Common Development Commands

### Build & Development
```bash
# Build the platform
npm run build                    # Full build with linting
npm run build:staging           # Staging environment build  
npm run build:production        # Production-ready build

# Development tools
npm run lint                    # ESLint code checking
npm run lint:fix               # Auto-fix linting issues
npm run health-check           # Platform health validation
```

### Testing Suite
```bash
# Unit Testing (Jest)
npm test                       # Run all unit tests
npm run test:watch            # Watch mode for development
npm run test:coverage         # Generate coverage report
npm run test:verbose          # Detailed test output

# End-to-End Testing (Playwright)
npm run test:e2e              # Run e2e test suite
npm run test:e2e:ui           # Interactive test runner
npm run test:e2e:headed       # Visual browser testing
npm run install:playwright    # Install browser dependencies

# Mutation Testing
npm run test:mutant           # Advanced code quality testing
npm run test:mutant:results   # View mutation test results
```

### Firebase Deployment
```bash
# Environment Management
firebase use acim-guide-test        # Switch to staging
firebase use acim-guide-production  # Switch to production

# Deployment Commands  
npm run deploy:staging              # Deploy to staging
npm run deploy:production          # Deploy to production

# Direct Firebase Commands
firebase deploy                     # Deploy all components
firebase deploy --only functions   # Functions only
firebase deploy --only firestore:rules,firestore:indexes  # Database rules
firebase emulators:start           # Local development server
```

### Assistant Management (Python)
```bash
# CourseGPT Assistant Setup (First Time)
python manage_assistant.py create --name "CourseGPT" --model gpt-5-chat-latest

# Assistant Updates
python manage_assistant.py update --prompt /data/CourseGPT.md  # Update system prompt
python manage_assistant.py sync-files                         # Sync ACIM knowledge base

# Testing & Interaction
python main.py "What is forgiveness according to ACIM?"       # Test assistant locally
python main.py                                               # Interactive chat mode
```

### Autonomous Agent Pipeline
```bash
# Run autonomous improvement system
python start_autonomous_pipeline.py                          # Full agent pipeline

# Individual Agent Testing
python -m agents.specialized.acim_scholar                   # Spiritual guardian
python -m agents.specialized.product_manager               # Strategy & growth
python -m agents.specialized.backend_engineer              # API development

# Agent Integration
python -m orchestration.agent_integration_system           # Validate agent coordination
```

## Architecture & Core Systems

### High-Level Architecture

**Core Flow**: User Question → CourseGPT (OpenAI + ACIM Vector Store) → Firebase Functions → Real-time UI Updates

```
Frontend (React Web + React Native Mobile)
    ↕ 
Firebase Functions (Node.js)
    ↕
CourseGPT Assistant (OpenAI GPT-5-chat-latest)
    ↕
ACIM Vector Store (Pure ACIM Content)
    ↕
Firebase Backend (Firestore + Auth + Stripe)
```

### Key Components

1. **CourseGPT System**
   - OpenAI Assistant trained exclusively on ACIM materials
   - Vector database: `/data/A_Course_In_Miracles_Urtext.pdf`
   - Kenneth Wapnick Q&A: `/data/final_training_data_*.py`
   - System prompt: `/data/CourseGPT.md`
   - **No external sources** - completely self-contained

2. **Firebase Backend**
   - **Functions**: `/functions/index.js` - Main API endpoints
   - **Firestore**: User data, conversation history, rate limiting
   - **Authentication**: Firebase Auth with user-specific data access
   - **Stripe Extension**: Premium course payments (€7 guided courses)

3. **Frontend Platforms**
   - **Web**: React-based interface with real-time chat
   - **Mobile**: React Native (Android + iOS development ready)
   - **Real-time UI**: Firebase listeners for immediate response updates

4. **Autonomous Agent Framework**
   - **Location**: `/agents/` directory
   - **Core Agents**: ACIM Scholar (spiritual integrity), Product Manager, Backend Engineer
   - **Specialized**: Blogger, DevOps, UI/UX Designer, QA Tester
   - **Purpose**: Maintains ACIM spiritual integrity while delivering technical excellence

### Data Flow Architecture

1. **User Request** → Frontend captures spiritual question
2. **Authentication** → Firebase Auth validates user
3. **Rate Limiting** → Firestore enforces 10 RPM per user
4. **CourseGPT Processing** → OpenAI Assistant with ACIM knowledge
5. **Real-time Response** → Firestore listeners update UI immediately  
6. **Token Management** → Daily caps (2000 tokens) tracked per user

## Business Model & Strategic Context

### Spiritual Integrity First
- **Sacred Rule**: All guidance must align with authentic ACIM teachings
- **Data Sources**: Exclusively public domain ACIM materials
- **No External Data**: No internet, no image recognition, no worldly citations
- **Spiritual Focus**: Redirect all worldly questions to spiritual perspective

### Revenue Tiers
1. **Free Core (100% Forever)**
   - Unlimited CourseGPT conversations
   - Full ACIM guidance and multilingual support
   - No ads, no limitations on spiritual functionality

2. **Premium Offerings**
   - **€7 14-Day Courses**: Personalized spiritual guidance journeys
   - **Advanced AI Integration**: EmptyMirrorGPT for deeper inquiry
   - **Personal Coaching**: 6-month cohorts with weekly Q&A calls

### Success Metrics
- **Spiritual Impact**: User transformation testimonials
- **Engagement**: Session depth and authentic spiritual connection  
- **Business Growth**: €7 course conversions, premium client acquisition
- **Platform Health**: 99.9% uptime, <2s response times

## Development Workflows

### Local Development Setup
1. **Environment Configuration**
   ```bash
   cd TestAlex
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Configure .env file
   cp .env.template .env
   # Add: OPENAI_API_KEY, ASSISTANT_ID, VECTOR_STORE_ID
   ```

2. **Firebase Setup**
   ```bash
   cd functions && npm install && cd ..
   firebase login
   firebase use acim-guide-test  # or acim-guide-production
   ```

3. **Assistant Creation** (First time only)
   ```bash
   python manage_assistant.py create --name "CourseGPT" --model gpt-5-chat-latest
   # This populates ASSISTANT_ID and VECTOR_STORE_ID automatically
   ```

### Testing Workflows
1. **Unit Testing**: `npm test` for Jest-based component testing
2. **E2E Testing**: `npm run test:e2e` for full user journey validation
3. **Mutation Testing**: `npm run test:mutant` for advanced code quality
4. **Local Assistant Testing**: `python main.py "test question"` for CourseGPT validation

### Deployment Pipeline
1. **Staging**: `npm run deploy:staging` → `acim-guide-test.web.app`
2. **Production**: `npm run deploy:production` → production domain
3. **Monitoring**: `firebase functions:log --only chatWithAssistant`
4. **Health Checks**: `npm run health-check` validates all systems

## Repository Structure

```
TestAlex/
├── functions/              # Firebase Cloud Functions (Node.js API)
│   ├── index.js           # Main API endpoints (chatWithAssistant, clearThread)
│   └── package.json       # Backend dependencies
├── agents/                # Autonomous agent framework
│   ├── core/              # Master system prompts
│   ├── specialized/       # Role-specific agents (ACIM Scholar, etc.)
│   └── templates/         # Agent creation templates
├── data/                  # ACIM knowledge base
│   ├── CourseGPT.md      # Master system prompt
│   ├── A_Course_In_Miracles_Urtext.pdf  # Complete ACIM text
│   └── final_training_data_*.py  # Kenneth Wapnick Q&A
├── e2e/                   # Playwright end-to-end tests
├── tests/                 # Jest unit tests  
├── public/                # Static web assets
├── android/               # React Native Android development
├── specs/                 # Comprehensive product specifications
├── orchestration/         # Agent coordination system
└── monitoring/            # Platform health & observability
```

### Critical Dependencies
- **OpenAI Assistant**: Requires `ASSISTANT_ID` and `VECTOR_STORE_ID`
- **Firebase Project**: Must be configured for `acim-guide-test` or production
- **ACIM Knowledge Base**: Vector store must contain authentic ACIM materials only
- **Stripe Integration**: For premium course payments (€7 impulse buy tier)

## Quality Assurance & Testing

### Test Coverage Strategy
- **Unit Tests**: Jest for components and utility functions
- **E2E Tests**: Playwright for complete user journeys across browsers
- **Mutation Testing**: Advanced code quality validation
- **Manual Testing**: Spiritual guidance accuracy and ACIM fidelity

### Testing Commands
```bash
npm run test:coverage     # Generate detailed coverage report
npm run test:e2e:headed   # Visual e2e testing for debugging
npm run test:mutant       # Mutation testing for robust code
npm run health-check      # Platform-wide health validation
```

### Spiritual Quality Assurance
- **ACIM Scholar Agent**: Validates all content for spiritual authenticity
- **Manual Review**: All CourseGPT responses checked for ACIM alignment
- **User Feedback**: Transformation testimonials validate spiritual impact

## Key Integrations & APIs

### CourseGPT API Endpoints
```javascript
// Primary chat endpoint
POST /chatWithAssistant
{
  "message": "What is forgiveness according to ACIM?",
  "tone": "gentle"  // or "direct"
}

// Thread management
POST /clearThread  // Reset conversation history
```

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_key
ASSISTANT_ID=asst_coursegpt_id
VECTOR_STORE_ID=vs_acim_knowledge

# Optional Configuration
DAILY_OUT_TOKENS_CAP=2000
LOG_LEVEL=INFO
```

## Monitoring & Observability

### Key Metrics
- **Spiritual Engagement**: Average session depth, return user rates
- **Technical Performance**: Response times, uptime, error rates  
- **Business Growth**: Course conversion rates, premium upgrades
- **Platform Health**: Token usage, rate limiting effectiveness

### Monitoring Commands
```bash
firebase functions:log                              # All function logs
firebase functions:log --only chatWithAssistant   # Chat-specific logs
firebase functions:log --filter="severity>=ERROR" # Error tracking
```

---

## References & Further Documentation

- **[Complete Strategic Vision →](./STRATEGIC_VISION.md)**: Business model, spiritual mission, premium offerings
- **[Product Specifications →](./specs.md)**: Technical requirements, user experience, quality standards
- **[Deployment Guide →](./DEPLOYMENT.md)**: Environment setup, CI/CD, production configuration
- **[Agent Framework →](./agents/README.md)**: Autonomous development system, agent coordination

**Remember**: This is a spiritual platform with commercial implications. ACIM authenticity and spiritual integrity are non-negotiable. When in doubt about content or guidance changes, prioritize spiritual alignment over technical optimization.
