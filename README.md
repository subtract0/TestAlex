# ACIMguide - Authentic ACIM Spiritual Guidance Platform

**The premier (unofficial) ACIM-GPT platform powered by CourseGPT**

ACIMguide provides authentic spiritual guidance based exclusively on *A Course in Miracles*, helping people remember their unshakable wellbeing through genuine spiritual transformation. Our platform combines advanced AI technology with perfect fidelity to ACIM teachings.

---

## 🎯 Mission & Vision

**Core Mission**: Transform lives through authentic ACIM guidance that redirects worldly concerns to spiritual perspective, offering exact quotations and gentle wisdom that supports genuine inner peace.

**Strategic Vision**: Become the trusted ACIM-GPT platform where spiritual seekers find reliable, authentic guidance while building a sustainable business model through honest premium offerings.

📖 **[Complete Strategic Vision →](./STRATEGIC_VISION.md)**

## 🚀 Platform Status

**FULLY FUNCTIONAL** - Complete frontend/backend integration with real-time CourseGPT responses.

### **✅ Core Experience (WORKING)**
- **CourseGPT Integration**: ✅ Authentic ACIM guidance with multilingual support
- **Real-time UI**: ✅ Immediate response display with citation support
- **Free Forever**: ✅ Unlimited spiritual conversations, no limitations
- **Data Sources**: Exclusive ACIM content (no external sources)
  - `/data/CourseGPT.md` - Core system prompt
  - `/data/ACIM_CE.pdf` - Complete Edition text
  - `/data/final_training_data_*.py` - Kenneth Wapnick Q&A database

### **✅ Technical Foundation (STABLE)**
- **Frontend**: ✅ React-style UI with Firebase real-time listeners
- **Backend**: ✅ Firebase Cloud Functions with OpenAI GPT-4o integration
- **Database**: ✅ Firestore with optimized indexes and security rules
- **Features**: ✅ Rate limiting, token management, spiritual guidance optimization
- **Security**: ✅ Production-ready authentication and user privacy protection
- **Monitoring**: ✅ Comprehensive logging and error handling

### **Recent Technical Updates (2025-08-12)**
- **Frontend/Backend Integration**: Fixed message field mismatch (`assistantResponse` vs `text`)
- **Real-time Listeners**: Replaced invalid `:contains()` selector with safe DOM scanning
- **Environment Variables**: Added compatibility for both `process.env` and `functions.config()`
- **Firestore Indexes**: Updated to use `timestamp` field for optimal query performance
- **Emulator Support**: Fixed Firebase Admin SDK compatibility for local development
- **Citation Display**: Enhanced UI to show ACIM citations with assistant responses

### **Business Model**
- **Free Core**: 100% free unlimited CourseGPT conversations
- **Premium Tiers**: €7 guided courses, advanced AI, personal coaching
- **Growth Engine**: SEO blog content driving organic traffic

🗺️ **[Implementation Roadmap →](./IMPLEMENTATION_ROADMAP.md)**

## 🏗️ Architecture Overview

### **Platform Structure**
- **ACIMguide.com**: Main product with free CourseGPT + premium features
- **ACIMcoach.com**: Personal brand blog driving traffic and conversions
- **Mobile Apps**: React Native cross-platform (iOS/Android)

### **Agent System**
Our autonomous development is powered by specialized AI agents:

📁 **[Agent Documentation →](./agents/README.md)**
- **Core Agents**: ACIM Scholar, Product Manager, Backend Engineer
- **Specialized Agents**: Blogger, DevOps, UI/UX Designer, QA Tester
- **Templates**: Standardized agent creation and integration

### **Development Phases**
1. **Foundation**: CourseGPT integration, documentation overhaul
2. **Core Features**: Premium courses, blog automation, payment processing  
3. **Growth**: Advanced AI, personal coaching, mobile development
4. **Scale**: Community features, international expansion

🗺️ **[Complete Implementation Roadmap →](./IMPLEMENTATION_ROADMAP.md)**

---

## 🚀 Quick Start Guide

### **For Users**
1. **Visit ACIMguide.com** for free unlimited CourseGPT conversations
2. **Ask spiritual questions** and receive authentic ACIM guidance
3. **Explore premium courses** for deeper spiritual transformation

### **For Developers**
```bash
# Clone and setup
git clone https://github.com/subtract0/TestAlex.git
cd TestAlex
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your OPENAI_API_KEY

# Deploy to Firebase
firebase deploy

# Test locally
python main.py "What is forgiveness according to ACIM?"
```

📚 **[Complete Setup Guide →](./DEPLOYMENT.md)**

## 🛠️ Development Status

### ✅ **Foundation Complete**
- **CourseGPT System**: Authentic ACIM guidance with multilingual support
- **Agent Framework**: Consolidated autonomous development system
- **Firebase Backend**: Production-ready with security and monitoring
- **Documentation**: Comprehensive cross-referenced guides

### ✅ **Production Infrastructure**
- **Cloud Functions**: Enhanced API with rate limiting and token management
- **Firestore**: Optimized with security rules and indexes
- **Authentication**: User-specific data access and privacy protection
- **Monitoring**: Real-time logging and spiritual content validation

### 🎯 **Next Phase: Core Features**
- **Premium Courses**: €7 14-day guided spiritual journeys
- **Blog Automation**: SEO content engine for organic growth
- **Mobile Development**: React Native cross-platform apps

## 🔧 API Reference

### **Core Endpoints**

#### `chatWithAssistant`
**Purpose**: CourseGPT spiritual guidance conversations

```javascript
// Request
{
  "message": "What does ACIM say about forgiveness?",
  "tone": "gentle" // optional: "direct" | "gentle"
}

// Response
{
  "messageId": "msg_abc123",
  "tokenIn": 45,
  "tokenOut": 156,
  "limitRemaining": 1844
}
```

#### `clearThread`
**Purpose**: Reset user conversation history

```javascript
// Response
{
  "threadId": "thread_xyz789",
  "message": "Thread cleared and reset successfully"
}
```

📚 **[Complete API Documentation →](./DEPLOYMENT.md#api-reference)**

## 🛠️ Development Workflow

### **Assistant Management**
```bash
# Create CourseGPT assistant (first time)
python manage_assistant.py create --name "CourseGPT" --model gpt-4o

# Update system prompt with CourseGPT
python manage_assistant.py update --prompt /data/CourseGPT.md

# Sync ACIM knowledge base
python manage_assistant.py sync-files

# Test locally
python main.py "Help me understand ACIM Lesson 1"
```

### **Firebase Development**
```bash
# Local development
firebase emulators:start --only functions

# Deploy to production
firebase deploy --only functions

# Monitor production
firebase functions:log --only chatWithAssistant
```

### **Agent System**
```bash
# Run autonomous improvement pipeline
python start_autonomous_pipeline.py

# Test specific agent
python -m agents.specialized.acim_scholar

# Validate agent integration
python -m orchestration.agent_integration_system
```

## ⚙️ Configuration

### **Environment Variables**
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
ASSISTANT_ID=asst_coursegpt_id  # Auto-generated

# Optional
VECTOR_STORE_ID=vs_acim_knowledge  # Auto-generated
DAILY_OUT_TOKENS_CAP=2000  # Per-user daily limit
LOG_LEVEL=INFO  # Logging verbosity
```

### **Firebase Configuration**
```bash
# Project setup
firebase use acim-guide-test
firebase deploy --only functions,firestore:rules,firestore:indexes

# Environment variables
firebase functions:config:set openai.api_key="your_key_here"
firebase functions:config:set assistant.id="asst_coursegpt_id"
```

## 📊 Analytics & Monitoring

### **Key Events**
- `coursegpt_conversation_start` - User begins spiritual guidance session
- `premium_course_purchase` - €7 course conversion
- `spiritual_insight_shared` - User reports transformation
- `acim_quote_requested` - Specific ACIM text lookup
- `multilingual_response` - Non-English guidance provided

### **Success Metrics**
- **Spiritual Impact**: User transformation testimonials
- **Engagement**: Average session depth and return rates
- **Conversion**: Free-to-premium upgrade rates
- **Content Quality**: ACIM quotation accuracy
- **Platform Health**: Response times and uptime

---

## 🤖 Autonomous Agent System

Our development is powered by specialized AI agents that maintain ACIM spiritual integrity while delivering technical excellence.

### **Agent Architecture**
```
/agents/
├── core/
│   ├── master_system_prompt.md      # Universal ACIM principles
│   ├── orchestration_protocol.md    # Agent coordination
│   └── coursegpt_integration.md     # Core system prompt
├── specialized/
│   ├── acim_scholar.md              # Spiritual guardian
│   ├── product_manager.md           # Strategy & growth
│   ├── backend_engineer.md          # API development
│   ├── blogger.md                   # SEO content creation
│   └── [other specialized agents]
└── templates/
    └── agent_template.md            # Standard format
```

### **Agent Capabilities**
- **ACIM Scholar**: Validates all content for spiritual authenticity
- **Product Manager**: Drives strategy and user experience optimization  
- **Backend Engineer**: Develops robust APIs and database architecture
- **Blogger**: Creates SEO-optimized ACIM content for organic growth
- **DevOps Engineer**: Ensures scalable, reliable infrastructure

📁 **[Complete Agent Documentation →](./agents/README.md)**

### Validation and CI

The prompt system includes automated validation:

```yaml
# .github/workflows/validate-prompts.yml
name: Validate Prompts
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r scripts/requirements.txt
      - name: Validate prompt integrity
        run: python scripts/render_prompt.py --validate-all
```

### Design Principles

1. **Hierarchical Inheritance**: Role prompts inherit from master prompt
2. **Modular Composition**: Snippets can be mixed for specific contexts
3. **ACIM Fidelity**: All prompts maintain spiritual integrity of the project
4. **Technical Excellence**: Enforces best practices and quality standards
5. **Agent Coordination**: Clear handoff protocols between different roles
6. **Validation**: Automated checking for prompt completeness and integrity

### Extending the System

To add a new role:

1. Create `prompts/new_role_engineer.md`
2. Include the standard inheritance line: `*Inherits all principles, rules, and architecture from [Master System Prompt](./master_system_prompt.md)*`
3. Define role-specific scope, responsibilities, and success criteria
4. Add handoff protocols to/from other roles
5. Update `scripts/render_prompt.py` to recognize the new role
6. Add validation tests

To add a new snippet:

1. Create `prompts/snippets/new_snippet.md`
2. Focus on a specific, reusable concern (security, performance, etc.)
3. Use clear headings and actionable guidelines
4. Update the renderer to include the snippet in appropriate contexts

---

That's it. Ship the smallest valuable thing, then iterate.
