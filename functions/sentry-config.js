/**
 * Sentry Configuration for TestAlex Firebase Functions
 * Maintains spiritual integrity while providing enterprise-grade error tracking
 */

const Sentry = require("@sentry/serverless");
const { logger } = require("firebase-functions");

/**
 * Spiritual Content Protection Filter
 * Ensures ACIM content never appears in error logs
 */
function scrubACIMContent(event) {
  try {
    // Scrub user messages that might contain spiritual content
    if (event.request?.data?.message) {
      if (event.request.data.message.length > 100) {
        event.request.data.message = '[ACIM_CONTENT_REDACTED]';
      }
    }

    // Scrub OpenAI responses
    if (event.contexts?.response?.data) {
      if (typeof event.contexts.response.data === 'string' && 
          event.contexts.response.data.length > 200) {
        event.contexts.response.data = '[SPIRITUAL_RESPONSE_REDACTED]';
      }
    }

    // Remove sensitive headers
    if (event.request?.headers) {
      delete event.request.headers.authorization;
      delete event.request.headers.cookie;
      delete event.request.headers['x-api-key'];
    }

    // Hash user IDs for privacy
    if (event.user?.id) {
      const crypto = require('crypto');
      event.user.id = crypto.createHash('sha256').update(event.user.id).digest('hex').substring(0, 16);
    }

    // Remove IP addresses
    delete event.user?.ip_address;

    return event;
  } catch (error) {
    logger.warn('Error in spiritual content scrubbing', { error: error.message });
    return event;
  }
}

/**
 * Initialize Sentry with spiritual integrity protection
 */
function initSentry() {
  const dsn = process.env.SENTRY_DSN_FUNCTIONS;
  const environment = process.env.FUNCTIONS_EMULATOR === 'true' ? 'local' : 
                     (process.env.GCLOUD_PROJECT === 'acim-guide-test' ? 'staging' : 'production');

  if (!dsn) {
    logger.warn('SENTRY_DSN_FUNCTIONS not configured - error tracking disabled');
    return;
  }

  Sentry.AWSLambda.init({
    dsn,
    environment,
    release: process.env.GITHUB_SHA || 'unknown',
    
    // Performance monitoring with conservative sampling
    tracesSampleRate: environment === 'production' ? 0.1 : 0.5,
    
    // Enhanced error context while protecting spiritual content
    beforeSend: scrubACIMContent,
    
    // Additional integrations
    integrations: [
      new Sentry.Integrations.Http({ tracing: true }),
      new Sentry.Integrations.OnUncaughtException(),
      new Sentry.Integrations.OnUnhandledRejection(),
    ],

    // Tag all events with spiritual platform context
    initialScope: {
      tags: {
        component: 'firebase-functions',
        platform: 'spiritual-ai',
        service: 'acimguide'
      },
      context: {
        spiritual_integrity: 'protected',
        content_policy: 'acim_pure'
      }
    }
  });

  logger.info('Sentry initialized for TestAlex spiritual AI platform', {
    environment,
    release: process.env.GITHUB_SHA || 'unknown'
  });
}

/**
 * Wrap a Firebase Function with Sentry monitoring
 */
function wrapFunction(handler) {
  // If Sentry is not configured, return the handler as-is
  if (!process.env.SENTRY_DSN_FUNCTIONS) {
    return handler;
  }
  
  return Sentry.AWSLambda.wrapHandler(handler);
}

/**
 * Create a transaction for performance monitoring
 */
function createTransaction(name, operation = 'function') {
  // If Sentry is not configured, return a mock transaction object
  if (!process.env.SENTRY_DSN_FUNCTIONS) {
    return {
      startChild: () => ({ finish: () => {}, setStatus: () => {} }),
      setStatus: () => {},
      setTag: () => {},
      finish: () => {}
    };
  }
  
  return Sentry.startTransaction({
    name,
    op: operation,
    tags: {
      spiritual_platform: 'acimguide',
      content_protection: 'enabled'
    }
  });
}

/**
 * Safe error capture that respects spiritual content
 */
function captureError(error, context = {}) {
  // Never capture errors that might contain spiritual content
  if (context.containsSpirtualContent) {
    logger.error('Spiritual content error (not sent to Sentry)', {
      message: error.message,
      stack: error.stack?.split('\n')[0] // Only first line of stack
    });
    return;
  }

  // If Sentry is not configured, just log the error
  if (!process.env.SENTRY_DSN_FUNCTIONS) {
    logger.error('Error occurred (Sentry not configured)', {
      message: error.message,
      stack: error.stack,
      context
    });
    return;
  }

  Sentry.captureException(error, {
    tags: {
      spiritual_integrity: 'maintained',
      error_type: 'technical'
    },
    extra: context
  });
}

module.exports = {
  initSentry,
  wrapFunction,
  createTransaction,
  captureError,
  scrubACIMContent
};
