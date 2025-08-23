/**
 * Enhanced UI System - Incremental Evolution Approach
 * 
 * This system provides immediate visual improvements while maintaining
 * compatibility with existing codebase architecture.
 */

// ===== DESIGN TOKENS =====
export const tokens = {
  colors: {
    // ACIM-inspired palette
    primary: {
      50: '#F0F7FF',
      100: '#E0EFFF', 
      200: '#B8DCFF',
      300: '#7CC1FF',
      400: '#369BFF',
      500: '#0066CC',  // Main brand
      600: '#0052A3',
      700: '#003D7A',
      800: '#002952',
      900: '#001529'
    },
    sacred: {
      50: '#FEFEF9',
      100: '#FDFDEE',
      200: '#F9F9D6',
      300: '#F1F1B8',
      400: '#E5E593',
      500: '#D4D46B',  // Sacred gold
      600: '#B8B850',
      700: '#9A9A3A',
      800: '#7A7A28',
      900: '#5A5A19'
    },
    peace: {
      50: '#F8FAFC',
      100: '#F1F5F9',
      200: '#E2E8F0',
      300: '#CBD5E1',
      400: '#94A3B8',
      500: '#64748B',  // Peaceful gray
      600: '#475569',
      700: '#334155',
      800: '#1E293B',
      900: '#0F172A'
    }
  },
  
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
    xxxl: 64
  },
  
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
      serif: ['Playfair Display', 'Georgia', 'serif'],
      mono: ['JetBrains Mono', 'monospace']
    },
    fontSize: {
      xs: 12,
      sm: 14,
      base: 16,
      lg: 18,
      xl: 20,
      '2xl': 24,
      '3xl': 30,
      '4xl': 36
    }
  },
  
  animations: {
    duration: {
      fast: 150,
      normal: 300,
      slow: 500
    },
    easing: {
      smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
      bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
    }
  }
};

// ===== ENHANCED COMPONENTS =====

/**
 * Animated Message Bubble with typing effect
 */
export const EnhancedMessageBubble = ({ message, isUser, isTyping = false }) => {
  const bubbleStyle = {
    maxWidth: isUser ? 280 : '100%',
    backgroundColor: isUser ? tokens.colors.primary[500] : 'transparent',
    color: isUser ? 'white' : tokens.colors.peace[800],
    padding: isUser ? `${tokens.spacing.md}px ${tokens.spacing.lg}px` : 0,
    borderRadius: isUser ? '20px' : 0,
    borderBottomRightRadius: isUser ? '6px' : 0,
    boxShadow: isUser ? `0 4px 12px ${tokens.colors.primary[500]}20` : 'none',
    marginLeft: isUser ? 'auto' : 0,
    marginRight: isUser ? 0 : 'auto',
    animation: 'messageSlideIn 0.4s ease-out',
    position: 'relative',
    overflow: 'hidden'
  };

  const typingIndicatorStyle = {
    display: isTyping ? 'flex' : 'none',
    alignItems: 'center',
    gap: '4px',
    padding: '8px 0'
  };

  return `
    <div style="${Object.entries(bubbleStyle).map(([k,v]) => `${k.replace(/([A-Z])/g, '-$1').toLowerCase()}: ${v}`).join('; ')}">
      ${isTyping ? `
        <div style="${Object.entries(typingIndicatorStyle).map(([k,v]) => `${k}: ${v}`).join('; ')}">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      ` : message}
    </div>
    
    <style>
      @keyframes messageSlideIn {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
      
      .typing-dot {
        width: 6px;
        height: 6px;
        background: ${tokens.colors.peace[400]};
        border-radius: 50%;
        animation: typingPulse 1.4s infinite ease-in-out;
      }
      
      .typing-dot:nth-child(1) { animation-delay: -0.32s; }
      .typing-dot:nth-child(2) { animation-delay: -0.16s; }
      
      @keyframes typingPulse {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
      }
    </style>
  `;
};

/**
 * Floating Action Button with spiritual iconography
 */
export const SacredFloatingButton = ({ action, icon = '🕊️', position = 'bottom-right' }) => {
  const positions = {
    'bottom-right': { bottom: '24px', right: '24px' },
    'bottom-left': { bottom: '24px', left: '24px' },
    'top-right': { top: '24px', right: '24px' }
  };

  const style = {
    position: 'fixed',
    ...positions[position],
    width: '56px',
    height: '56px',
    backgroundColor: tokens.colors.sacred[500],
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '24px',
    boxShadow: `0 8px 24px ${tokens.colors.sacred[500]}40`,
    cursor: 'pointer',
    transition: `all ${tokens.animations.duration.normal}ms ${tokens.animations.easing.smooth}`,
    border: `2px solid ${tokens.colors.sacred[300]}`,
    zIndex: 1000
  };

  return `
    <button onclick="${action}" style="${Object.entries(style).map(([k,v]) => `${k.replace(/([A-Z])/g, '-$1').toLowerCase()}: ${v}`).join('; ')}" 
            onmouseover="this.style.transform='scale(1.1) rotate(5deg)'" 
            onmouseout="this.style.transform='scale(1) rotate(0deg)'">
      ${icon}
    </button>
  `;
};

/**
 * Guided Onboarding Overlay
 */
export const SpiritualOnboarding = () => {
  const steps = [
    {
      target: '.message-input',
      title: 'Welcome to Your ACIM Journey',
      content: 'Ask me anything about A Course in Miracles. I\'m here to guide you with love and understanding.',
      position: 'top'
    },
    {
      target: '.quick-actions',
      title: 'Quick Spiritual Practices',
      content: 'Use these shortcuts to dive into core ACIM teachings and daily practices.',
      position: 'top'
    },
    {
      target: '.chat-container',
      title: 'Your Sacred Space',
      content: 'This is your personal sanctuary for learning and growth. All conversations are private.',
      position: 'center'
    }
  ];

  return `
    <div id="onboarding-overlay" class="onboarding-overlay">
      <div class="onboarding-backdrop"></div>
      <div class="onboarding-content">
        <div class="onboarding-step active" data-step="0">
          <div class="step-indicator">
            <span class="step-number">1</span>
            <span class="step-total"> of ${steps.length}</span>
          </div>
          <h3 class="step-title">${steps[0].title}</h3>
          <p class="step-content">${steps[0].content}</p>
          <div class="step-actions">
            <button class="skip-button" onclick="skipOnboarding()">Skip Tour</button>
            <button class="next-button" onclick="nextOnboardingStep()">Next</button>
          </div>
        </div>
      </div>
    </div>
    
    <style>
      .onboarding-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .onboarding-backdrop {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(4px);
      }
      
      .onboarding-content {
        position: relative;
        background: white;
        padding: ${tokens.spacing.xl}px;
        border-radius: 16px;
        max-width: 400px;
        margin: ${tokens.spacing.md}px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
        animation: onboardingSlideIn 0.5s ease-out;
      }
      
      @keyframes onboardingSlideIn {
        from {
          opacity: 0;
          transform: scale(0.9) translateY(20px);
        }
        to {
          opacity: 1;
          transform: scale(1) translateY(0);
        }
      }
      
      .step-indicator {
        color: ${tokens.colors.peace[500]};
        font-size: ${tokens.typography.fontSize.sm}px;
        margin-bottom: ${tokens.spacing.md}px;
      }
      
      .step-title {
        font-size: ${tokens.typography.fontSize.xl}px;
        font-weight: 600;
        color: ${tokens.colors.peace[800]};
        margin-bottom: ${tokens.spacing.md}px;
        font-family: ${tokens.typography.fontFamily.serif[0]};
      }
      
      .step-content {
        color: ${tokens.colors.peace[600]};
        line-height: 1.6;
        margin-bottom: ${tokens.spacing.lg}px;
      }
      
      .step-actions {
        display: flex;
        gap: ${tokens.spacing.md}px;
        justify-content: flex-end;
      }
      
      .skip-button, .next-button {
        padding: ${tokens.spacing.sm}px ${tokens.spacing.md}px;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: all ${tokens.animations.duration.normal}ms;
      }
      
      .skip-button {
        background: transparent;
        color: ${tokens.colors.peace[500]};
      }
      
      .next-button {
        background: ${tokens.colors.primary[500]};
        color: white;
      }
      
      .next-button:hover {
        background: ${tokens.colors.primary[600]};
        transform: translateY(-1px);
      }
    </style>
  `;
};

/**
 * Progress Meditation Ring (inspired by Apple Watch)
 */
export const MeditationProgressRing = ({ progress = 0.3, size = 80 }) => {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress * circumference);

  return `
    <div class="meditation-ring-container" style="width: ${size}px; height: ${size}px;">
      <svg width="${size}" height="${size}" class="meditation-ring">
        <!-- Background ring -->
        <circle
          cx="${size / 2}"
          cy="${size / 2}"
          r="${radius}"
          stroke="${tokens.colors.peace[200]}"
          stroke-width="6"
          fill="transparent"
        />
        <!-- Progress ring -->
        <circle
          cx="${size / 2}"
          cy="${size / 2}"
          r="${radius}"
          stroke="url(#meditationGradient)"
          stroke-width="6"
          fill="transparent"
          stroke-dasharray="${circumference}"
          stroke-dashoffset="${offset}"
          stroke-linecap="round"
          class="progress-circle"
        />
        <!-- Sacred center dot -->
        <circle
          cx="${size / 2}"
          cy="${size / 2}"
          r="3"
          fill="${tokens.colors.sacred[500]}"
        />
        <defs>
          <linearGradient id="meditationGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="${tokens.colors.primary[400]}" />
            <stop offset="100%" stop-color="${tokens.colors.sacred[500]}" />
          </linearGradient>
        </defs>
      </svg>
    </div>
    
    <style>
      .meditation-ring-container {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .progress-circle {
        transition: stroke-dashoffset ${tokens.animations.duration.slow}ms ${tokens.animations.easing.smooth};
        transform: rotate(-90deg);
        transform-origin: center;
      }
      
      .meditation-ring:hover .progress-circle {
        stroke-width: 8;
      }
    </style>
  `;
};

/**
 * Breathing Animation Component (for meditation guidance)
 */
export const BreathingGuide = ({ isActive = false }) => {
  return `
    <div class="breathing-guide ${isActive ? 'active' : ''}" 
         onclick="toggleBreathing()">
      <div class="breath-circle">
        <div class="breath-inner">
          <span class="breath-text">🧘</span>
        </div>
      </div>
      <div class="breath-instructions">
        <span class="breath-instruction">Breathe with the circle</span>
      </div>
    </div>
    
    <style>
      .breathing-guide {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: ${tokens.spacing.md}px;
        padding: ${tokens.spacing.lg}px;
        cursor: pointer;
        user-select: none;
      }
      
      .breath-circle {
        width: 120px;
        height: 120px;
        border: 2px solid ${tokens.colors.primary[300]};
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        transition: all ${tokens.animations.duration.normal}ms;
      }
      
      .breath-inner {
        width: 80px;
        height: 80px;
        background: linear-gradient(135deg, ${tokens.colors.primary[100]}, ${tokens.colors.sacred[100]});
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        transition: all ${tokens.animations.duration.slow}ms;
      }
      
      .breathing-guide.active .breath-inner {
        animation: breatheAnimation 8s infinite ease-in-out;
      }
      
      .breathing-guide.active .breath-circle {
        border-color: ${tokens.colors.primary[500]};
        box-shadow: 0 0 20px ${tokens.colors.primary[300]}40;
      }
      
      @keyframes breatheAnimation {
        0%, 100% { 
          transform: scale(1);
          background: linear-gradient(135deg, ${tokens.colors.primary[100]}, ${tokens.colors.sacred[100]});
        }
        50% { 
          transform: scale(1.2);
          background: linear-gradient(135deg, ${tokens.colors.primary[200]}, ${tokens.colors.sacred[200]});
        }
      }
      
      .breath-instructions {
        color: ${tokens.colors.peace[600]};
        font-size: ${tokens.typography.fontSize.sm}px;
        text-align: center;
      }
    </style>
  `;
};

// ===== ENHANCED INTERACTIVE ELEMENTS =====

/**
 * Sacred Quote Card with parallax effect
 */
export const SacredQuoteCard = ({ quote, citation, background = 'light' }) => {
  const backgrounds = {
    light: `linear-gradient(135deg, ${tokens.colors.sacred[50]}, ${tokens.colors.primary[50]})`,
    sacred: `linear-gradient(135deg, ${tokens.colors.sacred[100]}, ${tokens.colors.sacred[200]})`,
    peace: `linear-gradient(135deg, ${tokens.colors.peace[50]}, ${tokens.colors.peace[100]})`
  };

  return `
    <div class="sacred-quote-card" data-background="${background}">
      <div class="quote-content">
        <div class="quote-mark">✨</div>
        <blockquote class="quote-text">${quote}</blockquote>
        <cite class="quote-citation">${citation}</cite>
      </div>
      <div class="quote-ornament">🕊️</div>
    </div>
    
    <style>
      .sacred-quote-card {
        background: ${backgrounds[background]};
        border-radius: 16px;
        padding: ${tokens.spacing.lg}px;
        margin: ${tokens.spacing.lg}px 0;
        position: relative;
        overflow: hidden;
        border-left: 4px solid ${tokens.colors.sacred[400]};
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all ${tokens.animations.duration.normal}ms;
      }
      
      .sacred-quote-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
      }
      
      .quote-mark {
        font-size: 24px;
        margin-bottom: ${tokens.spacing.sm}px;
      }
      
      .quote-text {
        font-style: italic;
        font-size: ${tokens.typography.fontSize.lg}px;
        line-height: 1.6;
        color: ${tokens.colors.peace[700]};
        margin: 0 0 ${tokens.spacing.md}px 0;
        font-family: ${tokens.typography.fontFamily.serif[0]};
      }
      
      .quote-citation {
        display: block;
        font-size: ${tokens.typography.fontSize.sm}px;
        color: ${tokens.colors.peace[500]};
        font-style: normal;
        font-weight: 500;
      }
      
      .quote-ornament {
        position: absolute;
        top: ${tokens.spacing.md}px;
        right: ${tokens.spacing.md}px;
        font-size: 20px;
        opacity: 0.3;
      }
    </style>
  `;
};

// ===== JAVASCRIPT INTEGRATION FUNCTIONS =====
export const uiHelpers = {
  // Initialize enhanced UI system
  init() {
    this.addGlobalStyles();
    this.initializeAnimations();
    this.setupInteractiveElements();
  },

  // Add global enhanced styles
  addGlobalStyles() {
    const style = document.createElement('style');
    style.textContent = `
      /* Enhanced smooth scrolling */
      html {
        scroll-behavior: smooth;
      }
      
      /* Better focus indicators */
      *:focus {
        outline: 2px solid ${tokens.colors.primary[400]};
        outline-offset: 2px;
      }
      
      /* Improved button interactions */
      button {
        transition: all ${tokens.animations.duration.normal}ms;
      }
      
      button:hover {
        transform: translateY(-1px);
      }
      
      button:active {
        transform: translateY(0);
      }
    `;
    document.head.appendChild(style);
  },

  // Initialize entrance animations
  initializeAnimations() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.animationPlayState = 'running';
        }
      });
    });

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
      observer.observe(el);
    });
  },

  // Setup interactive elements
  setupInteractiveElements() {
    // Add ripple effect to buttons
    document.querySelectorAll('button').forEach(button => {
      button.addEventListener('click', this.createRipple);
    });
  },

  // Create Material Design ripple effect
  createRipple(event) {
    const button = event.currentTarget;
    const circle = document.createElement('span');
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;

    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${event.clientX - button.offsetLeft - radius}px`;
    circle.style.top = `${event.clientY - button.offsetTop - radius}px`;
    circle.classList.add('ripple');

    const ripple = button.getElementsByClassName('ripple')[0];
    if (ripple) {
      ripple.remove();
    }

    button.appendChild(circle);

    // Add ripple styles
    if (!document.querySelector('#ripple-styles')) {
      const style = document.createElement('style');
      style.id = 'ripple-styles';
      style.textContent = `
        .ripple {
          position: absolute;
          border-radius: 50%;
          transform: scale(0);
          animation: rippleAnimation 600ms linear;
          background-color: rgba(255, 255, 255, 0.6);
        }
        
        @keyframes rippleAnimation {
          to {
            transform: scale(4);
            opacity: 0;
          }
        }
      `;
      document.head.appendChild(style);
    }
  },

  // Show onboarding for new users
  showOnboarding() {
    if (!localStorage.getItem('acim-guide-onboarding-complete')) {
      document.body.insertAdjacentHTML('beforeend', SpiritualOnboarding());
    }
  },

  // Hide onboarding and mark as complete
  completeOnboarding() {
    localStorage.setItem('acim-guide-onboarding-complete', 'true');
    const overlay = document.getElementById('onboarding-overlay');
    if (overlay) {
      overlay.remove();
    }
  }
};

// Global functions for integration
window.skipOnboarding = () => uiHelpers.completeOnboarding();
window.nextOnboardingStep = () => {
  // Implementation for multi-step onboarding
  console.log('Next onboarding step');
};
window.toggleBreathing = () => {
  const guide = document.querySelector('.breathing-guide');
  guide?.classList.toggle('active');
};

export default {
  tokens,
  EnhancedMessageBubble,
  SacredFloatingButton,
  SpiritualOnboarding,
  MeditationProgressRing,
  BreathingGuide,
  SacredQuoteCard,
  uiHelpers
};
