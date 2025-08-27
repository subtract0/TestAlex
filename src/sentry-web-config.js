/**
 * Sentry Configuration for ACIMguide Web Frontend
 * Maintains spiritual integrity while providing web error tracking
 */

import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';

/**
 * Spiritual Content Protection for Web Frontend
 * Ensures ACIM content never appears in error logs
 */
function scrubACIMContentWeb(event) {
  try {
    // Scrub user input that might contain spiritual content
    if (event.contexts?.state?.userInput) {
      if (event.contexts.state.userInput.length > 100) {
        event.contexts.state.userInput = '[ACIM_CONTENT_REDACTED]';
      }
    }

    // Scrub form data that might contain spiritual questions
    if (event.request?.data) {
      Object.keys(event.request.data).forEach(key => {
        if (key.includes('message') || key.includes('question') || key.includes('spiritual')) {
          if (typeof event.request.data[key] === 'string' && event.request.data[key].length > 100) {
            event.request.data[key] = '[ACIM_CONTENT_REDACTED]';
          }
        }
      });
    }

    // Scrub localStorage/sessionStorage that might contain spiritual content
    if (event.contexts?.storage) {
      delete event.contexts.storage.chatHistory;
      delete event.contexts.storage.spiritualContent;
      delete event.contexts.storage.acimGuidance;
    }

    // Remove sensitive headers
    if (event.request?.headers) {
      delete event.request.headers.authorization;
      delete event.request.headers.cookie;
      delete event.request.headers['x-api-key'];
    }

    // Hash user IDs for privacy
    if (event.user?.id) {
      const encoder = new TextEncoder();
      const data = encoder.encode(event.user.id);
      crypto.subtle.digest('SHA-256', data).then(hash => {
        const hashArray = Array.from(new Uint8Array(hash));
        event.user.id = hashArray.map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 16);
      });
    }

    // Remove IP addresses and sensitive browser info
    delete event.user?.ip_address;
    if (event.contexts?.browser) {
      delete event.contexts.browser.cookies;
      delete event.contexts.browser.localStorage;
    }

    return event;
  } catch (error) {
    console.warn('Error in spiritual content scrubbing:', error.message);
    return event;
  }
}

/**
 * Initialize Sentry for ACIMguide Web Frontend
 */
export function initSentryWeb() {
  const dsn = process.env.REACT_APP_SENTRY_DSN;
  const environment = process.env.NODE_ENV || 'development';
  const version = process.env.REACT_APP_VERSION || '1.0.0';

  if (!dsn) {
    console.warn('REACT_APP_SENTRY_DSN not configured - web error tracking disabled');
    return;
  }

  Sentry.init({
    dsn,
    environment,
    release: `acimguide-web@${version}`,
    
    // Performance monitoring with conservative sampling for web
    tracesSampleRate: environment === 'production' ? 0.1 : 0.5,
    
    // Enable web-specific integrations
    integrations: [
      new BrowserTracing({
        // Track navigation performance while protecting spiritual content
        routingInstrumentation: Sentry.reactRouterV6Instrumentation(
          React.useEffect,
          useLocation,
          useNavigationType,
          createRoutesFromChildren,
          matchRoutes
        ),
        enableLongTask: false, // Avoid performance overhead
        enableInp: true, // Core Web Vitals
      }),
    ],

    // Enhanced error context while protecting spiritual content
    beforeSend: scrubACIMContentWeb,

    // Tag all events with spiritual web context
    initialScope: {
      tags: {
        platform: 'react-web',
        app: 'acimguide',
        spiritual_integrity: 'protected',
        content_policy: 'acim_pure'
      },
      context: {
        spiritual_platform: 'web',
        user_privacy: 'maximum'
      }
    },

    // Web-specific settings
    enableAutoSessionTracking: true,
    sessionTrackingIntervalMillis: 30000,
    
    // Disable automatic breadcrumbs that might capture sensitive data
    defaultIntegrations: [
      // Filter out integrations that might capture spiritual content
      ...Sentry.defaultIntegrations.filter(integration => 
        integration.name !== 'Breadcrumbs' || 
        integration.name !== 'GlobalHandlers'
      )
    ],
  });

  // Set up custom error boundary for spiritual content
  const SpiritualErrorBoundary = Sentry.withErrorBoundary;
  
  console.log('Sentry initialized for ACIMguide web frontend', {
    environment,
    version,
    spiritualIntegrity: 'protected'
  });

  return { SpiritualErrorBoundary };
}

/**
 * Safe error capture for web that respects spiritual content
 */
export function captureErrorWeb(error, context = {}) {
  // Never capture errors that might contain spiritual content
  if (context.containsSpirtualContent) {
    console.error('Spiritual content error (not sent to Sentry):', {
      message: error.message,
      location: context.location
    });
    return;
  }

  Sentry.captureException(error, {
    tags: {
      spiritual_integrity: 'maintained',
      error_type: 'technical',
      platform: 'web'
    },
    extra: context
  });
}

/**
 * Create a transaction for web performance monitoring
 */
export function createTransactionWeb(name, operation = 'pageload') {
  return Sentry.startTransaction({
    name,
    op: operation,
    tags: {
      spiritual_platform: 'acimguide-web',
      content_protection: 'enabled'
    }
  });
}

/**
 * Set user context safely (privacy-first)
 */
export function setUserContextWeb(userId, subscriptionTier = 'free') {
  Sentry.setUser({
    id: userId ? `web_${userId.substring(0, 8)}` : 'anonymous',
    segment: subscriptionTier,
    platform: 'web'
    // Never include: email, name, personal data, spiritual content
  });
}

/**
 * React Hook for spiritual content protection
 */
export function useSpiritualErrorBoundary() {
  React.useEffect(() => {
    const handleUnhandledRejection = (event) => {
      // Check if error might contain spiritual content
      if (event.reason?.message?.toLowerCase().includes('acim') ||
          event.reason?.message?.toLowerCase().includes('spiritual') ||
          event.reason?.message?.toLowerCase().includes('course')) {
        console.error('Spiritual content error detected, not sending to Sentry');
        return;
      }
      
      Sentry.captureException(event.reason);
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    return () => window.removeEventListener('unhandledrejection', handleUnhandledRejection);
  }, []);
}

export default {
  initSentryWeb,
  captureErrorWeb,
  createTransactionWeb,
  setUserContextWeb,
  useSpiritualErrorBoundary
};
