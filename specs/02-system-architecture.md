# 02. System Architecture

*"Everything is connected to everything else." — ACIM*

## Architecture Overview

The ACIMguide system is designed as a distributed, cloud-native architecture that prioritizes spiritual authenticity, scalability, and reliability. The system follows microservices patterns with clear separation of concerns while maintaining the simplicity that aligns with ACIM principles.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Mobile App    │◄──►│ Firebase Cloud  │◄──►│ OpenAI Platform │
│  (React Native) │    │   Functions     │    │   (CourseGPT)   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│ Firebase Auth   │    │   Firestore     │    │  Vector Store   │
│                 │    │   Database      │    │   (ACIM Data)   │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components Architecture (C4 Model)

### Level 1: System Context

```
┌────────────────────────────────────────────────────────────┐
│                        ACIMguide System                    │
│                                                            │
│  Provides spiritual guidance through AI-powered           │
│  conversations based exclusively on ACIM teachings        │
│                                                            │
└────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │                      │
                    │    ACIM Student      │
                    │                      │
                    │ Uses mobile app for  │
                    │ spiritual guidance   │
                    │                      │
                    └──────────────────────┘
```

### Level 2: Container Diagram

```
External Systems           ACIMguide System                    External APIs
                          
┌──────────────┐         ┌──────────────────┐              ┌──────────────┐
│              │         │                  │              │              │
│  App Store   │◄────────│   Mobile App     │─────────────►│   OpenAI     │
│              │         │ (React Native)   │              │   Platform   │
└──────────────┘         └──────────────────┘              └──────────────┘
                                   │
                                   │ HTTPS/WSS
                                   │
                          ┌──────────────────┐              ┌──────────────┐
                          │                  │              │              │
                          │ Firebase Cloud   │─────────────►│  Firebase    │
                          │   Functions      │              │   Services   │
                          │                  │              │              │
                          └──────────────────┘              └──────────────┘
                                   │
                                   │
                          ┌──────────────────┐
                          │                  │
                          │    Firestore     │
                          │    Database      │
                          │                  │
                          └──────────────────┘
```

### Level 3: Component Diagram - Mobile App

```
┌────────────────────────────────────────────────────────────┐
│                    Mobile Application                       │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │             │  │             │  │                     │ │
│  │    Chat     │  │   Settings  │  │   Authentication    │ │
│  │   Screen    │  │   Screen    │  │      Manager        │ │
│  │             │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │             │  │             │  │                     │ │
│  │  Message    │  │  Firebase   │  │   Local Storage     │ │
│  │ Components  │  │  Client     │  │     Manager         │ │
│  │             │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │             │  │             │  │                     │ │
│  │ Navigation  │  │  UI Design  │  │    Error Handler    │ │
│  │   System    │  │   System    │  │                     │ │
│  │             │  │             │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Level 4: Code Structure - React Native App

```
src/
├── components/
│   ├── chat/
│   │   ├── MessageBubble.tsx
│   │   ├── ChatInput.tsx
│   │   ├── QuickActions.tsx
│   │   └── TypingIndicator.tsx
│   ├── common/
│   │   ├── Button.tsx
│   │   ├── Loading.tsx
│   │   └── ErrorBoundary.tsx
│   └── ui/
│       ├── Theme.tsx
│       └── DesignSystem.tsx
├── screens/
│   ├── ChatScreen.tsx
│   ├── SettingsScreen.tsx
│   └── OnboardingScreen.tsx
├── services/
│   ├── firebase/
│   │   ├── auth.ts
│   │   ├── firestore.ts
│   │   └── functions.ts
│   ├── api/
│   │   └── coursegpt.ts
│   └── storage/
│       └── localStorage.ts
├── hooks/
│   ├── useAuth.ts
│   ├── useChat.ts
│   └── useSettings.ts
├── utils/
│   ├── constants.ts
│   ├── helpers.ts
│   └── validation.ts
└── types/
    ├── chat.ts
    ├── user.ts
    └── api.ts
```

## Data Flow Architecture

### Primary Chat Flow

```
User Input
    │
    ▼
┌─────────────────┐
│   Chat Screen   │ ──┐
└─────────────────┘   │
                      │ 1. User types message
                      ▼
┌─────────────────────────────────────┐
│        Firebase Functions           │
│     chatWithAssistant()            │
│                                    │
│ 2. Validate & authenticate        │
│ 3. Create/get OpenAI thread       │ ──┐
│ 4. Send to CourseGPT               │   │
└─────────────────────────────────────┘   │
                                          │
                                          ▼
                               ┌─────────────────┐
                               │ OpenAI Platform │
                               │                 │
                               │ 5. Process with │ ──┐
                               │    CourseGPT    │   │
                               └─────────────────┘   │
                                                     │
                                                     ▼
                               ┌─────────────────────────────┐
                               │      Vector Store           │
                               │                             │
                               │ 6. Reference ACIM content   │ ──┐
                               │    for accurate citations   │   │
                               └─────────────────────────────┘   │
                                                                 │
                                                                 ▼
                               ┌─────────────────────────────────────┐
                               │         Response Flow               │
                               │                                     │
                               │ 7. Generate ACIM-aligned response   │ ──┐
                               │ 8. Extract citations                │   │
                               │ 9. Return structured response       │   │
                               └─────────────────────────────────────┘   │
                                                                         │
                                                                         ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                           Storage & Response                              │
│                                                                           │
│ 10. Store in Firestore                    11. Return to mobile app       │
│     - Message history                          - Response text           │ ──┐
│     - Citations                                - Citations               │   │
│     - Metadata                                 - Metadata                │   │
└───────────────────────────────────────────────────────────────────────────┘   │
                                                                                 │
                                                                                 ▼
                                          ┌─────────────────┐
                                          │   Chat Screen   │
                                          │                 │
                                          │ 12. Display     │
                                          │     response    │
                                          │     with love   │
                                          └─────────────────┘
```

## Technology Stack

### Frontend (React Native Mobile App)
| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Framework** | React Native | 0.79.5 | Cross-platform development, native performance |
| **Navigation** | React Navigation | 7.x | Industry standard, spiritual-friendly transitions |
| **State Management** | React Hooks + Context | Built-in | Simplicity over complexity |
| **UI Library** | Custom Design System | N/A | Spiritual aesthetic, consistent branding |
| **Development Platform** | Expo | ~53.0.20 | Rapid development, easy deployment |
| **Type Safety** | TypeScript | 5.3.0 | Code reliability, better developer experience |

### Backend (Firebase & Cloud Services)
| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **Cloud Functions** | Firebase Functions | 6.4.0 | Serverless, auto-scaling, spiritual simplicity |
| **Database** | Firestore | Latest | NoSQL flexibility, real-time updates |
| **Authentication** | Firebase Auth | 23.0.0 | Secure, social login options |
| **File Storage** | Firebase Storage | Latest | Secure file handling for user data |
| **AI Processing** | OpenAI GPT-4 | 4.x | Most advanced AI for spiritual understanding |
| **Vector Database** | OpenAI Assistants | N/A | Integrated ACIM knowledge base |

### DevOps & Infrastructure
| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| **CI/CD** | GitHub Actions | Latest | Automated, reliable deployment |
| **Mobile Builds** | Expo EAS | Latest | Professional app store deployment |
| **Error Tracking** | Sentry | Latest | Spiritual debugging (gentle error handling) |
| **Analytics** | Firebase Analytics | Latest | Privacy-respecting usage insights |
| **Monitoring** | Firebase Performance | Latest | Ensure spiritual conversations flow smoothly |

## Service Integration Points

### Firebase Cloud Functions APIs

#### 1. Chat Service
```typescript
interface ChatService {
  endpoint: "chatWithAssistant"
  method: "HTTPS Callable"
  authentication: "Firebase Auth Required"
  rateLimiting: "10 requests/minute per user"
  timeout: "60 seconds"
}
```

#### 2. Thread Management
```typescript
interface ThreadService {
  endpoint: "clearThread" 
  method: "HTTPS Callable"
  authentication: "Firebase Auth Required"
  purpose: "Reset conversation history"
}
```

#### 3. Health Monitoring
```typescript
interface HealthService {
  endpoint: "healthCheck"
  method: "HTTPS Callable" 
  authentication: "None"
  purpose: "System status verification"
}
```

### External Service Integration

#### OpenAI Platform
- **Assistant ID**: Configured via environment variables
- **Model**: GPT-4-turbo (optimized for spiritual understanding)
- **Vector Store**: Contains complete ACIM materials
- **Rate Limits**: Managed by Firebase Functions middleware

#### Firebase Services
- **Authentication**: Social providers + email/password
- **Firestore**: Real-time database for messages and user data
- **Storage**: Secure file storage for user-generated content
- **Hosting**: Web interface hosting (future development)

## Scalability Design

### Horizontal Scaling Strategy

1. **Firebase Functions**: Auto-scaling serverless compute
2. **Firestore**: Managed NoSQL with automatic scaling
3. **OpenAI Integration**: Request queuing and retry logic
4. **CDN**: Firebase Hosting for static assets

### Performance Optimizations

1. **Client-Side Caching**: Message history stored locally
2. **Optimistic Updates**: Immediate UI feedback
3. **Connection Pooling**: Efficient Firebase connections
4. **Lazy Loading**: Progressive message history loading

### Load Distribution

```
Traffic Distribution Strategy:

Frontend Load:
- React Native app handles UI state
- Local storage for offline capability
- Optimistic updates for immediate feedback

Backend Load:
- Firebase Functions: Automatic scaling
- Firestore: Distributed queries
- OpenAI: Queued requests with retry logic

Regional Distribution:
- Firebase: Multi-region deployment
- CDN: Global content delivery
- Data: Regional compliance (GDPR, etc.)
```

## Security Architecture

### Authentication Flow
```
1. User opens app
2. Firebase Auth checks existing session
3. If no session: prompt for login
4. Social/email authentication
5. Firebase JWT token generated
6. All API calls include auth token
7. Server validates token on each request
```

### Data Protection
- **In-Transit**: HTTPS/TLS 1.3 encryption
- **At-Rest**: Firebase encryption by default
- **API Keys**: Environment variables only
- **User Data**: Minimal collection, maximum protection

## Monitoring & Observability

### Application Performance Monitoring
- Firebase Performance SDK
- React Native performance metrics
- OpenAI response time tracking
- User experience metrics

### Error Tracking & Logging
- Sentry for React Native error tracking
- Firebase Functions structured logging
- Spiritual error messages (gentle user communication)
- Automated alert system for spiritual harmony disruption

### Health Checks
- Endpoint availability monitoring
- OpenAI API health verification
- Firebase services status tracking
- User experience impact assessment

---

*"The perfect communication of a completely unified thought to universal mind is therefore not only possible, but natural."* — A Course in Miracles

This architecture ensures that our technical foundation serves the spiritual purpose: providing reliable, scalable access to ACIM wisdom while maintaining the simplicity and peace that the Course teaches.
