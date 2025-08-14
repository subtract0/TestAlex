# ACIM Guide Style Guide

## Design Philosophy
The ACIM Guide interface embodies peace, simplicity, and spiritual clarity. Every design decision should reflect the Course's principles of love, forgiveness, and inner peace.

## Visual Hierarchy

### Typography
- **Primary Font**: Inter or system font stack for UI elements
- **ACIM Quote Font**: Georgia or serif for Course quotes (vintage typewriter feel)
- **Font Sizes**:
  - H1: 32px (rare use, page titles)
  - H2: 24px (section headers)
  - Body: 16px (comfortable reading)
  - Small: 14px (metadata, timestamps)
- **Line Height**: 1.6 for body text, 1.4 for headers
- **Font Weight**: Regular (400) for body, Medium (500) for emphasis, Bold (600) for headings

### Color Palette
- **Primary Blue**: #1e3a8a (trust, depth, spiritual wisdom)
- **Light Blue**: #3b82f6 (accents, hover states)
- **White**: #ffffff (purity, space, clarity)
- **Light Gray**: #f8fafc (subtle backgrounds)
- **Medium Gray**: #64748b (secondary text)
- **Dark Gray**: #1e293b (primary text)
- **Success Green**: #10b981 (confirmations)
- **Warning Orange**: #f59e0b (alerts)

### Spacing System
- **Base Unit**: 8px
- **Micro**: 4px (fine adjustments)
- **Small**: 8px (tight spacing)
- **Medium**: 16px (comfortable spacing)
- **Large**: 24px (section separation)
- **XL**: 32px (major sections)
- **XXL**: 48px (page sections)

## Component Standards

### Chat Interface
- **Full viewport height**: Utilize 100vh properly
- **Message bubbles**: 
  - AI messages: Full-width with subtle background
  - User messages: Right-aligned, max-width 70%
- **Spacing**: 16px between messages, 12px internal padding
- **Animations**: Smooth 0.3s ease-in-out transitions

### Navigation & Headers
- **Header height**: 64px maximum
- **Logo**: Clean SVG, max 40px height
- **Navigation**: Minimal, essential items only
- **Search/Input**: Full-width with subtle shadows

### Buttons & Interactions
- **Primary Button**: Dark blue background, white text, 8px border-radius
- **Secondary Button**: White background, blue border and text
- **Hover States**: Subtle scale (1.02) or opacity (0.9) changes
- **Focus States**: Clear outline for accessibility

### Cards & Containers
- **Border Radius**: 8px for cards, 12px for major containers
- **Shadows**: Subtle box-shadows (0 1px 3px rgba(0,0,0,0.1))
- **Borders**: Use sparingly, prefer shadows for separation

## Layout Principles

### Grid System
- **Container**: Max-width 1200px, centered
- **Breakpoints**: 
  - Mobile: <768px
  - Tablet: 768px-1024px
  - Desktop: >1024px
- **Gutters**: 16px on mobile, 24px on desktop

### White Space
- **Generous margins**: Never cramped feeling
- **Breathing room**: 24px+ between major sections
- **Content density**: Prefer fewer elements with more space

### Responsive Design
- **Mobile-first**: Design for mobile, enhance for desktop
- **Touch targets**: Minimum 44px for interactive elements
- **Text scaling**: Readable at all screen sizes

## Accessibility Requirements
- **Color contrast**: WCAG AA compliant (4.5:1 ratio minimum)
- **Focus indicators**: Visible for keyboard navigation
- **Alt text**: All images and icons properly labeled
- **Semantic HTML**: Proper heading hierarchy and ARIA labels

## Animation & Transitions
- **Duration**: 0.2s for micro-interactions, 0.3s for transitions
- **Easing**: ease-in-out for natural movement
- **Purpose**: Enhance understanding, never distract
- **Reduce motion**: Respect user preferences

## Logo & Branding
- **Logo placement**: Top-left, consistent sizing
- **Brand colors**: Consistent application of primary blue
- **Voice**: Compassionate, wise, never preachy
- **Tone**: Peaceful, supportive, authentic ACIM wisdom
