# ACIM Guide UX Rules

## Core UX Principles

### 1. Spiritual Clarity Over Complexity
- **Rule**: Every interface element should serve the user's spiritual journey
- **Application**: Remove any feature that doesn't directly support ACIM study or practice
- **Test**: Ask "Does this help someone understand forgiveness better?"

### 2. Peaceful Interaction Design
- **Rule**: No jarring transitions, aggressive colors, or stressful UI patterns
- **Application**: Gentle animations, soft color transitions, calming feedback
- **Test**: Does the interaction feel peaceful and supportive?

### 3. Immediate Value Recognition
- **Rule**: Users should understand the value within 3 seconds of page load
- **Application**: Clear headlines, obvious primary action, visible benefits
- **Test**: Can a new user explain what this does in 10 words or less?

## Layout & Navigation Rules

### Viewport Utilization
- **Must fit**: All core functionality visible on 1366x768 (common laptop size)
- **Header height**: Maximum 64px, preferably 56px
- **Chat area**: Minimum 60% of viewport height for conversation
- **Input area**: Fixed bottom position, never more than 80px tall

### Information Hierarchy
- **Most important**: User's current conversation and input field
- **Secondary**: Navigation to past conversations and settings
- **Tertiary**: Branding, help, profile information
- **Hidden until needed**: Advanced features, detailed settings

### Responsive Breakpoints
- **Mobile (320-767px)**: Single column, full-width messages, hidden sidebar
- **Tablet (768-1023px)**: Condensed layout, collapsible sidebar
- **Desktop (1024px+)**: Full layout with persistent sidebar and proper whitespace

## Authentication & User Management

### Login Flow
- **Anonymous first**: Users can try the system immediately
- **Progressive registration**: Ask for account creation after value is demonstrated
- **Social login**: Google, Apple preferred for ease
- **Email backup**: Traditional email/password as fallback

### Conversation History
- **Persistent storage**: All conversations saved automatically
- **Easy access**: Sidebar with chronological list of past conversations
- **Search capability**: Find specific topics or quotes
- **Privacy controls**: Clear data deletion options

### User States
- **Anonymous**: Basic chat functionality, no history persistence
- **Registered**: Full features, conversation history, personalization
- **Returning**: Quick access to recent conversations and bookmarks

## Chat Interface Rules

### Message Flow
- **Chronological order**: Newest messages at bottom
- **Auto-scroll**: Always show latest message when new content arrives
- **Typing indicators**: Show when AI is generating response
- **Message status**: Clear indication of sent/delivered/read states

### Message Formatting
- **AI messages**: Full-width, subtle background, authoritative but gentle
- **User messages**: Right-aligned bubbles, personal and conversational
- **ACIM quotes**: Distinct styling with serif font and left border
- **System messages**: Minimal, center-aligned, different color

### Input Experience
- **Auto-focus**: Input ready immediately on page load
- **Multi-line support**: Shift+Enter for line breaks, Enter to send
- **Character limit**: Visible counter when approaching limits
- **Quick actions**: Suggested prompts for new users

## Accessibility Standards

### Keyboard Navigation
- **Tab order**: Logical flow through all interactive elements
- **Skip links**: Quick navigation to main content
- **Escape key**: Close modals and return to previous state
- **Arrow keys**: Navigate through conversation history

### Screen Reader Support
- **ARIA labels**: All interactive elements properly labeled
- **Live regions**: Chat messages announced as they arrive
- **Heading structure**: Proper H1-H6 hierarchy for navigation
- **Alt text**: Descriptive text for all images and icons

### Visual Accessibility
- **Color contrast**: 4.5:1 minimum ratio for all text
- **Focus indicators**: Clear outlines for keyboard users
- **Text scaling**: Readable up to 200% zoom
- **Motion preferences**: Respect reduced-motion settings

## Performance Standards

### Loading Times
- **Initial page load**: Under 2 seconds on 3G connection
- **Time to interactive**: Under 3 seconds
- **Response generation**: Loading state shown within 100ms
- **Image loading**: Progressive enhancement, never blocking

### Offline Capability
- **Basic functionality**: Core chat works offline with cache
- **Graceful degradation**: Clear messaging when features unavailable
- **Background sync**: Queue messages for sending when online
- **Local storage**: Preserve conversation state during network issues

## Error Handling

### User-Friendly Messages
- **No technical jargon**: Plain language error explanations
- **Actionable guidance**: Clear next steps for resolution
- **Spiritual framing**: Errors as opportunities for patience and peace
- **Retry mechanisms**: Easy ways to attempt failed actions again

### Failure States
- **Network errors**: "Let's try that again" with retry button
- **Authentication**: Gentle prompts to sign in or register
- **Rate limits**: Encouraging messages about patience
- **Service unavailable**: Temporary notification with expected resolution

## Content Guidelines

### AI Response Quality
- **ACIM authenticity**: All responses aligned with Course principles
- **Compassionate tone**: Never judgmental or preachy
- **Practical application**: Connect concepts to daily life
- **Quote integration**: Use actual Course text when relevant

### User Guidance
- **Onboarding**: Progressive disclosure of features
- **Help text**: Contextual assistance without cluttering
- **Examples**: Show don't tell for complex features
- **Encouragement**: Positive reinforcement for engagement

## Measurement Criteria

### User Experience Metrics
- **Task completion rate**: >90% for core chat functionality
- **Time to first value**: <30 seconds for new users
- **Session duration**: Quality engagement, not just time spent
- **Return rate**: Users coming back for continued learning

### Satisfaction Indicators
- **Perceived usefulness**: Does this help with ACIM practice?
- **Emotional response**: Do users feel peaceful and supported?
- **Trust level**: Confidence in AI responses and platform
- **Recommendation likelihood**: Would users share this with others?

## Scoring Rubric for UI Evaluation

### Layout & Visual Design (3 points)
- **3**: Perfect spacing, typography, and visual hierarchy
- **2**: Minor spacing or typography issues
- **1**: Major layout problems or poor visual hierarchy
- **0**: Completely broken layout

### Functionality & Usability (3 points)
- **3**: All features work intuitively without explanation
- **2**: Minor usability friction but functional
- **1**: Significant usability issues or confusing interface
- **0**: Core functionality broken or inaccessible

### Responsiveness & Accessibility (2 points)
- **2**: Perfect responsive behavior and accessibility features
- **1**: Minor responsive issues or accessibility gaps
- **0**: Poor mobile experience or major accessibility problems

### Brand & Spiritual Alignment (2 points)
- **2**: Perfectly embodies ACIM principles and peaceful design
- **1**: Generally aligned but some elements feel off-brand
- **0**: Contradicts spiritual mission or feels commercial/aggressive

**Total Score: /10**
- **8-10**: Excellent, aligned with spiritual mission and high usability
- **6-7**: Good, minor improvements needed
- **4-5**: Needs significant improvement
- **0-3**: Major redesign required
