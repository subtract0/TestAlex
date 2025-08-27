# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**TestAlex** is a comprehensive multi-system spiritual AI platform and research repository combining:

1. **ACIMguide** - Premier ACIM-GPT spiritual guidance platform (React Native + Firebase)
2. **AI Business Automation** - Autonomous business systems for product creation and marketing
3. **Advanced RAG Systems** - State-of-the-art retrieval-augmented generation frameworks
4. **Orchestration Systems** - Sophisticated autonomous agent coordination
5. **Research Frameworks** - Systematic AI/ML improvement methodologies

**Core Mission**: Transform lives through authentic ACIM guidance while pioneering autonomous spiritual business systems and advancing RAG/AI research through systematic methodologies.

**Unique Value**: This repository represents one of the most comprehensive autonomous spiritual AI ecosystems, combining authentic spiritual integrity with cutting-edge AI automation and research frameworks.

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

### React Native Mobile Development (ACIMguide)
```bash
# Mobile App Development
cd ACIMguide
npm install                     # Install dependencies
npm start                       # Start Expo development server
npm run android                 # Run on Android device/emulator
npm run ios                     # Run on iOS simulator
npm run web                     # Run in web browser

# Building & Deployment
npx expo build:android         # Build Android APK
npx expo build:ios             # Build iOS IPA
npx expo publish               # Publish updates via Expo
```

### AI Business Automation System
```bash
# Autonomous Business Operations
cd ai_automation
python autonomous_business.py           # Launch full autonomous system
python cost_monitor.py                  # Real-time cost tracking
python product_generator.py             # AI product creation
python marketing_automation.py          # Social media & ads automation

# Proof of Concept
cd proof_of_concept && python serve.py # View coaching website demo
```

### Advanced RAG Systems
```bash
# Agentic RAG System
cd agentic-rag-system
rag init-db                             # Initialize vector database
rag demo                                # Run complete demo
rag search "machine learning" --limit 5 # Search vector database
rag route "find function process_data"  # Test query routing

# Systematic RAG Improvement
cd systematically-improving-rag
mkdocs serve                            # Serve course documentation
uv install                              # Install with uv package manager
```

### Orchestration & Agent Coordination
```bash
# Orchestration System
cd orchestration
python agent_integration_system.py     # Agent coordination
python live_orchestrator.py            # Live orchestration
python autonomous_monitor.py           # System monitoring
python revenue_analyst.py              # Revenue optimization
```

### Instructor (Structured Outputs)
```bash
# Structured Output Framework
cd instructor
uv install                              # Install dependencies
mkdocs serve                            # Documentation server
python -m pytest                       # Run test suite
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

### High-Level Multi-System Architecture

**Ecosystem Flow**: Spiritual Platform ↔ Business Automation ↔ Advanced RAG ↔ Research Systems

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          SPIRITUAL INTEGRITY LAYER (ACIM Scholar)              │
└─────────────────────────────────────────────────────────────────────────────────┘
         ↕                    ↕                    ↕                    ↕
┌──────────────────┐  ┌────────────────┐  ┌───────────────────┐  ┌─────────────────┐
│  ACIMguide       │  │ AI Business    │  │ Advanced RAG      │  │ Research        │
│  Platform        │  │ Automation     │  │ Systems           │  │ Frameworks      │
│                  │  │                │  │                   │  │                 │
│ React Web +      │  │ Product Gen +  │  │ Agentic RAG +     │  │ Systematic RAG  │
│ React Native +   │  │ Marketing +    │  │ Vector Search +   │  │ Improvement +   │
│ Firebase +       │  │ Cost Monitor + │  │ Query Routing +   │  │ Instructor +    │
│ CourseGPT        │  │ Sales Auto     │  │ Evaluation        │  │ Documentation   │
└──────────────────┘  └────────────────┘  └───────────────────┘  └─────────────────┘
         ↕                    ↕                    ↕                    ↕
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION & COORDINATION LAYER                      │
│               Agent Integration + Live Orchestrator + Revenue Analyst          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Major System Components

#### 1. **ACIMguide Spiritual Platform**
   - **Web Frontend**: React-based interface with real-time chat
   - **Mobile App**: React Native with Expo (iOS/Android)
   - **Backend**: Firebase Functions + Firestore + Auth
   - **CourseGPT**: OpenAI Assistant with pure ACIM knowledge
   - **Premium Tiers**: €7 courses, coaching, advanced AI

#### 2. **AI Business Automation System**
   - **Autonomous Business**: 24/7 product creation and marketing
   - **Cost Monitoring**: Real-time budget tracking and ROI analysis
   - **Product Generation**: AI-driven digital product creation
   - **Marketing Automation**: Social media, ads, content creation
   - **Proof of Concept**: Working coaching website template

#### 3. **Advanced RAG Framework**
   - **Agentic RAG**: Multi-tool orchestration with vector search
   - **Query Router**: Intelligent query classification and tool selection
   - **Vector Databases**: LanceDB, ChromaDB integration
   - **Structured Outputs**: Pydantic models with type safety
   - **Evaluation Pipeline**: Systematic performance measurement

#### 4. **Research & Education Systems**
   - **Systematic RAG**: Complete course on improving RAG applications
   - **Instructor Framework**: Structured outputs and validation
   - **Documentation**: MkDocs-powered comprehensive guides
   - **Evaluation Tools**: Advanced metrics and benchmarking

#### 5. **Orchestration Infrastructure**
   - **Agent Coordination**: Multi-agent collaboration systems
   - **Live Orchestrator**: Real-time system coordination
   - **Revenue Analyst**: Business intelligence and optimization
   - **Monitoring**: Comprehensive observability and alerting

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
├── functions/                      # Firebase Cloud Functions (Node.js API)
│   ├── index.js                   # Main API endpoints (chatWithAssistant, clearThread)
│   └── package.json               # Backend dependencies
├── ACIMguide/                      # React Native Mobile App (Expo)
│   ├── App.js                     # Main mobile app entry point
│   ├── components/                # Mobile UI components
│   ├── screens/                   # Mobile app screens
│   └── services/                  # Firebase integration services
├── ai_automation/                  # Autonomous Business Systems
│   ├── autonomous_business.py     # Full business automation
│   ├── cost_monitor.py            # Real-time cost tracking
│   ├── product_generator.py       # AI product creation
│   ├── marketing_automation.py    # Social media & ads automation
│   └── proof_of_concept/          # Working website templates
├── agentic-rag-system/             # Advanced RAG with Multi-Tool Support
│   ├── agentic_rag/               # Core RAG framework
│   ├── examples/                  # Usage examples and demos
│   └── tests/                     # RAG system test suite
├── systematically-improving-rag/   # RAG Research & Education
│   ├── docs/                      # Course documentation (MkDocs)
│   ├── latest/                    # Current course materials
│   ├── cohort_1/ & cohort_2/      # Past cohort materials
│   └── mkdocs.yml                 # Documentation configuration
├── instructor/                     # Structured Outputs Framework
│   ├── instructor/                # Core instructor library
│   ├── docs/                      # Documentation and examples
│   └── examples/                  # Usage examples (60+ demos)
├── orchestration/                  # Agent Coordination & Business Intelligence
│   ├── agent_integration_system.py # Multi-agent coordination
│   ├── live_orchestrator.py       # Real-time orchestration
│   ├── revenue_analyst.py         # Business optimization
│   └── autonomous_monitor.py      # System health monitoring
├── agents/                         # Autonomous Agent Framework
│   ├── core/                      # Master system prompts
│   ├── specialized/               # Role-specific agents
│   └── templates/                 # Agent creation templates
├── data/                           # ACIM Knowledge Base
│   ├── CourseGPT.md              # Master system prompt
│   ├── A_Course_In_Miracles_Urtext.pdf  # Complete ACIM text
│   └── final_training_data_*.py  # Kenneth Wapnick Q&A
├── e2e/                           # Playwright End-to-End Tests
│   ├── tests/                     # Test specifications
│   └── fixtures/                  # Test data and utilities
├── tests/ & __tests__/             # Jest Unit Tests
├── monitoring/                     # Platform Health & Observability
│   ├── grafana/                   # Monitoring dashboards
│   └── logs/                      # System logs
├── specs/                          # Product Specifications
├── public/                         # Static Web Assets
├── android/ & android-native/      # Android Development
├── blog/                           # SEO Content System
└── terraform/                      # Infrastructure as Code
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
