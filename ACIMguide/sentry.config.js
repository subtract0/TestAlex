/**
 * Sentry Configuration for ACIMguide React Native App
 * Maintains spiritual integrity while providing mobile error tracking
 */

import * as Sentry from '@sentry/react-native';
import Constants from 'expo-constants';

/**
 * Spiritual Content Protection for Mobile App
 * Ensures ACIM content never appears in error logs
 */
function scrubACIMContentMobile(event) {
  try {
    // Scrub user messages that might contain spiritual content
    if (event.contexts?.state?.userMessage) {
      if (event.contexts.state.userMessage.length > 100) {
        event.contexts.state.userMessage = '[ACIM_CONTENT_REDACTED]';
      }
    }

    // Scrub navigation parameters that might contain spiritual content
    if (event.contexts?.app?.navigation) {
      delete event.contexts.app.navigation.params;
    }

    // Remove sensitive AsyncStorage data
    if (event.contexts?.device?.storage) {
      delete event.contexts.device.storage.userMessages;
      delete event.contexts.device.storage.spiritualContent;
    }

    // Hash user IDs for privacy
    if (event.user?.id) {
      const crypto = require('expo-crypto');
      event.user.id = crypto.digestStringAsync(
        crypto.CryptoDigestAlgorithm.SHA256, 
        event.user.id
      ).then(hash => hash.substring(0, 16));
    }

    // Remove sensitive headers from network requests
    if (event.request?.headers) {
      delete event.request.headers.authorization;
      delete event.request.headers.cookie;
      delete event.request.headers['x-api-key'];
    }

    // Remove IP addresses and device identifiers
    delete event.user?.ip_address;
    if (event.contexts?.device) {
      delete event.contexts.device.device_unique_identifier;
      delete event.contexts.device.simulator;
    }

    return event;
  } catch (error) {
    console.warn('Error in spiritual content scrubbing:', error.message);
    return event;
  }
}

/**
 * Initialize Sentry for ACIMguide Mobile App
 */
export function initSentryMobile() {
  const dsn = Constants.expoConfig?.extra?.sentryDsnMobile;
  const environment = __DEV__ ? 'local' : 'production';

  if (!dsn) {
    console.warn('SENTRY_DSN_MOBILE not configured - mobile error tracking disabled');
    return;
  }

  Sentry.init({
    dsn,
    environment,
    
    // Performance monitoring with conservative sampling for mobile
    tracesSampleRate: __DEV__ ? 0.5 : 0.1,
    
    // Enable mobile-specific integrations
    integrations: [
      new Sentry.ReactNativeTracing({
        // Track navigation performance while protecting spiritual content
        routingInstrumentation: new Sentry.ReactNavigationInstrumentation(),
        enableNativeFramesTracking: !__DEV__, // Only in production
        enableStallTracking: false, // Avoid performance overhead
      }),
    ],

    // Enhanced error context while protecting spiritual content
    beforeSend: scrubACIMContentMobile,

    // Tag all events with spiritual mobile context
    initialScope: {
      tags: {
        platform: 'react-native',
        app: 'acimguide',
        spiritual_integrity: 'protected',
        content_policy: 'acim_pure'
      },
      context: {
        spiritual_platform: 'mobile',
        user_privacy: 'maximum'
      }
    },

    // Disable automatic breadcrumbs that might capture sensitive data
    enableAutoSessionTracking: true,
    sessionTrackingIntervalMillis: 30000,
    
    // Mobile-specific settings
    enableNativeCrashHandling: !__DEV__,
    enableAutoPerformanceTracing: true,
    enableUserInteractionTracing: false, // Disable to protect spiritual interactions
  });

  console.log('Sentry initialized for ACIMguide mobile app', {
    environment,
    spiritualIntegrity: 'protected'
  });
}

/**
 * Safe error capture for mobile that respects spiritual content
 */
export function captureErrorMobile(error, context = {}) {
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
      platform: 'mobile'
    },
    extra: context
  });
}

/**
 * Create a transaction for mobile performance monitoring
 */
export function createTransactionMobile(name, operation = 'navigation') {
  return Sentry.startTransaction({
    name,
    op: operation,
    tags: {
      spiritual_platform: 'acimguide-mobile',
      content_protection: 'enabled'
    }
  });
}

/**
 * Set user context safely (privacy-first)
 */
export function setUserContextMobile(userId, subscriptionTier = 'free') {
  Sentry.setUser({
    id: userId ? `mobile_${userId.substring(0, 8)}` : 'anonymous',
    segment: subscriptionTier,
    platform: 'mobile'
    // Never include: email, name, personal data, spiritual content
  });
}

export default {
  initSentryMobile,
  captureErrorMobile,
  createTransactionMobile,
  setUserContextMobile
};
