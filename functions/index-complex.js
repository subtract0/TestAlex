/**
 * ACIMguide Cloud Functions
 * Chat endpoint for CourseGPT Assistant with enhanced token management
 */

/* eslint-disable max-len */

require("dotenv").config();
const {onCall} = require("firebase-functions/https");
const logger = require("firebase-functions/logger");
const admin = require("firebase-admin");
const OpenAI = require("openai");

// Initialize Firebase Admin
if (!admin.apps.length) {
  admin.initializeApp();
}

// Get configuration from Firebase functions.config() (legacy format)
const functions = require("firebase-functions");
const config = functions.config();

// Initialize OpenAI client - try both new and legacy config formats
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || (config.openai && config.openai.key);
const openai = new OpenAI({
  apiKey: OPENAI_API_KEY,
});

// Configuration constants - try both new and legacy config formats
const ASSISTANT_ID = process.env.ASSISTANT_ID || (config.assistant && config.assistant.id);
const VECTOR_STORE_ID = process.env.VECTOR_STORE_ID || (config.vector && config.vector.store_id);
const DAILY_OUT_TOKENS_CAP = parseInt(process.env.DAILY_OUT_TOKENS_CAP || (config.tokens && config.tokens.daily_cap)) || 10000;
const RATE_LIMIT_RPM = 10; // Requests per minute per user

// Auto-scaling configuration based on usage metrics
// Dynamic maxInstances based on daily usage patterns and cost control
const AUTO_SCALE_CONFIG = {
  // Base configuration
  minInstances: 0,
  maxInstancesLow: 5,    // Off-peak hours
  maxInstancesPeak: 20,  // Peak hours (9 AM - 9 PM)
  maxInstancesHigh: 35,  // High usage periods
  
  // Usage thresholds for scaling decisions
  thresholds: {
    dailyTokensLow: 10000,    // < 10K tokens/day = low usage
    dailyTokensMedium: 30000, // 10K-30K tokens/day = medium usage  
    dailyTokensHigh: 45000,   // > 30K tokens/day = high usage
    requestsPerMinute: {
      low: 10,
      medium: 30,
      high: 60
    }
  }
};

/**
 * Determine optimal maxInstances based on current usage metrics
 * @return {Promise<number>} Optimal maxInstances value
 */
async function calculateOptimalMaxInstances() {
  try {
    const now = new Date();
    const hour = now.getHours();
    const dayStart = new Date().setHours(0, 0, 0, 0);
    
    // Get current daily token usage across all users
    const rateLimitsSnapshot = await admin.firestore().collection('rateLimits').get();
    let totalDailyTokens = 0;
    let activeUsers = 0;
    
    rateLimitsSnapshot.docs.forEach(doc => {
      const data = doc.data();
      if (data.lastReset >= dayStart) {
        totalDailyTokens += data.dailyTokens || 0;
        if (data.dailyTokens > 0) activeUsers++;
      }
    });
    
    // Get recent request rate (last 10 minutes)
    const recentMetricsSnapshot = await admin.firestore()
      .collection('metrics')
      .doc('requests')
      .get();
    
    const recentData = recentMetricsSnapshot.exists ? recentMetricsSnapshot.data() : {};
    const recentRequests = recentData.last10Minutes || 0;
    
    // Determine time-based scaling
    let timeBasedMax;
    if (hour >= 9 && hour <= 21) {
      // Peak hours: 9 AM - 9 PM
      timeBasedMax = AUTO_SCALE_CONFIG.maxInstancesPeak;
    } else {
      // Off-peak hours
      timeBasedMax = AUTO_SCALE_CONFIG.maxInstancesLow;
    }
    
    // Determine usage-based scaling
    let usageBasedMax;
    if (totalDailyTokens >= AUTO_SCALE_CONFIG.thresholds.dailyTokensHigh) {
      usageBasedMax = AUTO_SCALE_CONFIG.maxInstancesHigh;
    } else if (totalDailyTokens >= AUTO_SCALE_CONFIG.thresholds.dailyTokensMedium) {
      usageBasedMax = AUTO_SCALE_CONFIG.maxInstancesPeak;
    } else {
      usageBasedMax = AUTO_SCALE_CONFIG.maxInstancesLow;
    }
    
    // Take the minimum of time-based and usage-based scaling for cost control
    const optimalMax = Math.min(timeBasedMax, usageBasedMax);
    
    // Log scaling decision for monitoring
    logger.info('Auto-scaling calculation', {
      hour,
      totalDailyTokens,
      activeUsers,
      recentRequests,
      timeBasedMax,
      usageBasedMax,
      optimalMax,
      currentBudgetUtilization: totalDailyTokens / DAILY_OUT_TOKENS_CAP
    });
    
    return Math.max(1, optimalMax); // Always allow at least 1 instance
    
  } catch (error) {
    logger.warn('Auto-scaling calculation failed, using default', {
      error: error.message,
      defaultMax: AUTO_SCALE_CONFIG.maxInstancesLow
    });
    return AUTO_SCALE_CONFIG.maxInstancesLow;
  }
}

// Note: Global options not available in Functions v1
// Function-specific options are set individually in each export

/**
 * Validate environment variables on startup
 */
if (!OPENAI_API_KEY) {
  throw new Error("OPENAI_API_KEY environment variable is required");
}
if (!ASSISTANT_ID) {
  throw new Error("ASSISTANT_ID environment variable is required");
}

logger.info("Cloud Functions initialized", {
  assistantId: ASSISTANT_ID,
  vectorStoreId: VECTOR_STORE_ID,
  dailyTokenCap: DAILY_OUT_TOKENS_CAP,
  rateLimitRpm: RATE_LIMIT_RPM,
});

/**
 * Check rate limit for user
 * @param {string} userId - The user ID to check rate limits for
 * @return {Promise<number>} Current daily token usage
 */
async function checkRateLimit(userId) {
  const now = Date.now();
  const windowStart = now - (60 * 1000); // 1 minute window

  const rateLimitDoc = admin.firestore().collection("rateLimits").doc(userId);

  return admin.firestore().runTransaction(async (transaction) => {
    const doc = await transaction.get(rateLimitDoc);
    const data = doc.exists ? doc.data() :
      {requests: [], dailyTokens: 0, lastReset: now};

    // Reset daily tokens if it's a new day
    const dayStart = new Date().setHours(0, 0, 0, 0);
    if (data.lastReset < dayStart) {
      data.dailyTokens = 0;
      data.lastReset = now;
    }

    // Filter requests within the current window
    data.requests = (data.requests || []).filter((time) => time > windowStart);

    // Check rate limit
    if (data.requests.length >= RATE_LIMIT_RPM) {
      throw new Error(
          `Rate limit exceeded. Maximum ${RATE_LIMIT_RPM} requests per minute.`,
      );
    }

    // Check daily token limit
    if (data.dailyTokens >= DAILY_OUT_TOKENS_CAP) {
      throw new Error(
          `Daily token limit reached. Limit: ${DAILY_OUT_TOKENS_CAP} tokens.`,
      );
    }

    // Add current request
    data.requests.push(now);
    transaction.set(rateLimitDoc, data);

    return data.dailyTokens;
  });
}

/**
 * Update token usage for user
 * @param {string} userId - The user ID
 * @param {number} tokenIn - Input tokens used
 * @param {number} tokenOut - Output tokens used
 * @return {Promise<void>}
 */
async function updateTokenUsage(userId, tokenIn, tokenOut) {
  const rateLimitDoc = admin.firestore().collection("rateLimits").doc(userId);

  await admin.firestore().runTransaction(async (transaction) => {
    const doc = await transaction.get(rateLimitDoc);
    const data = doc.exists ? doc.data() : {dailyTokens: 0};

    data.dailyTokens = (data.dailyTokens || 0) + tokenOut;
    transaction.set(rateLimitDoc, data, {merge: true});
  });
}

/**
 * Extract citations from assistant response
 * @param {Object} message - The assistant message object
 * @return {Array} Array of citation objects
 */
function extractCitations(message) {
  const citations = [];

  // Look for file citations in the message annotations
  if (message.content[0] && message.content[0].text && message.content[0].text.annotations) {
    message.content[0].text.annotations.forEach((annotation) => {
      if (annotation.type === "file_citation") {
        citations.push({
          type: "file",
          fileId: annotation.file_citation.file_id,
          text: annotation.text,
        });
      }
    });
  }

  return citations;
}

/**
 * Detect language of user message for multilingual CourseGPT response
 * @param {string} message - User message to analyze
 * @return {string} Detected language code (e.g., 'en', 'de', 'es', 'fr')
 */
function detectLanguage(message) {
  try {
    if (!message || typeof message !== 'string' || message.trim().length === 0) {
      return 'en'; // Default to English for empty/invalid messages
    }

    const text = message.toLowerCase().trim();
    
    // Language detection patterns based on common words, phrases, and character patterns
    const languagePatterns = {
      'es': {
        // Spanish indicators
        words: ['el', 'la', 'de', 'que', 'y', 'es', 'en', 'un', 'una', 'con', 'no', 'se', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'como', 'para', 'del', 'está', 'todo', 'pero', 'más', 'hacer', 'muy', 'puede', 'dios', 'amor', 'vida', 'curso', 'milagros'],
        patterns: [/¿.*?\?/, /¡.*?!/, /ñ/, /á|é|í|ó|ú/, /ción$/, /dad$/, /mente$/],
        greeting: ['hola', 'buenos días', 'buenas tardes', 'buenas noches']
      },
      'fr': {
        // French indicators
        words: ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus', 'par', 'grand', 'il', 'me', 'même', 'faire', 'elle', 'dieu', 'amour', 'vie', 'cours', 'miracles'],
        patterns: [/ç/, /à|é|è|ê|î|ô|ù|û/, /tion$/, /ment$/, /ique$/],
        greeting: ['bonjour', 'bonsoir', 'salut']
      },
      'de': {
        // German indicators  
        words: ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als', 'auch', 'es', 'an', 'werden', 'aus', 'er', 'hat', 'daß', 'sie', 'nach', 'wird', 'bei', 'gott', 'liebe', 'leben', 'kurs', 'wunder'],
        patterns: [/ä|ö|ü|ß/, /ung$/, /keit$/, /lich$/],
        greeting: ['hallo', 'guten tag', 'guten morgen', 'guten abend']
      },
      'pt': {
        // Portuguese indicators
        words: ['o', 'de', 'e', 'do', 'a', 'em', 'um', 'para', 'é', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'foi', 'ao', 'ele', 'das', 'tem', 'à', 'seu', 'sua', 'ou', 'ser', 'quando', 'muito', 'há', 'nos', 'já', 'está', 'eu', 'também', 'deus', 'amor', 'vida', 'curso', 'milagres'],
        patterns: [/ã|õ|ç/, /ção$/, /dade$/, /mente$/],
        greeting: ['olá', 'oi', 'bom dia', 'boa tarde', 'boa noite']
      },
      'it': {
        // Italian indicators
        words: ['il', 'di', 'che', 'e', 'la', 'per', 'un', 'in', 'con', 'del', 'da', 'a', 'al', 'le', 'si', 'dei', 'come', 'lo', 'se', 'gli', 'alla', 'più', 'nel', 'dalla', 'sua', 'suo', 'ci', 'anche', 'tutto', 'ancora', 'fatto', 'dopo', 'vita', 'tempo', 'anni', 'stato', 'dio', 'amore', 'corso', 'miracoli'],
        patterns: [/à|è|é|ì|í|î|ò|ó|ù|ú/, /zione$/, /mente$/, /ario$/],
        greeting: ['ciao', 'salve', 'buongiorno', 'buonasera']
      }
    };

    const scores = {};
    
    // Initialize scores for each language
    Object.keys(languagePatterns).forEach(lang => {
      scores[lang] = 0;
    });

    // Check for language-specific words
    const words = text.split(/\s+/);
    Object.entries(languagePatterns).forEach(([lang, patterns]) => {
      // Word matching (higher weight)
      patterns.words.forEach(word => {
        const regex = new RegExp(`\\b${word}\\b`, 'gi');
        const matches = (text.match(regex) || []).length;
        scores[lang] += matches * 3;
      });
      
      // Pattern matching (medium weight)
      patterns.patterns.forEach(pattern => {
        const matches = (text.match(pattern) || []).length;
        scores[lang] += matches * 2;
      });
      
      // Greeting detection (high weight)
      patterns.greeting.forEach(greeting => {
        if (text.includes(greeting)) {
          scores[lang] += 5;
        }
      });
    });

    // Find the language with highest score
    let detectedLang = 'en'; // Default to English
    let maxScore = 0;
    
    Object.entries(scores).forEach(([lang, score]) => {
      if (score > maxScore) {
        maxScore = score;
        detectedLang = lang;
      }
    });

    // If no strong signal detected, check message length and character patterns
    if (maxScore === 0 && text.length > 10) {
      // Check for non-English character patterns
      if (/[àáâãäèéêëìíîïòóôõöùúûüç]/i.test(text)) {
        // Romance language indicators - default to Spanish for ACIM context
        detectedLang = 'es';
      } else if (/[äöüß]/i.test(text)) {
        detectedLang = 'de';
      }
    }

    // Log detection for monitoring (only in non-production)
    if (process.env.NODE_ENV !== 'production') {
      logger.info('Language detection', {
        message: text.substring(0, 50) + '...',
        detected: detectedLang,
        scores: scores,
        messageLength: text.length
      });
    }

    return detectedLang;
    
  } catch (error) {
    logger.warn('Language detection error, defaulting to English', {
      error: error.message,
      message: message ? message.substring(0, 50) + '...' : 'undefined'
    });
    return 'en'; // Safe fallback to English
  }
}

/**
 * Chat with CourseGPT Assistant - Enhanced with multilingual support and budget control
 * Responds in the user's detected language for authentic ACIM guidance
 */
exports.chatWithAssistant = onCall({
  memory: '512MB',
  timeoutSeconds: 60,
  maxInstances: 10
}, async (request) => {
  const startTime = Date.now();
  let tokenIn = 0;
  let tokenOut = 0;
  let budgetAllowed = true;
  let serviceLevel = 'normal';
  let maxTokens = 500;

  try {
    const {message, tone = "gentle", userTier = "free"} = request.data;
    const userId = request.auth && request.auth.uid;

    if (!userId) {
      throw new Error("Authentication required");
    }

    if (!message || typeof message !== "string") {
      throw new Error("Message is required and must be a string");
    }

    if (message.length > 4000) {
      throw new Error("Message too long. Maximum 4000 characters.");
    }

    // Check budget allowance before processing
    try {
      const budgetCheck = await admin.firestore().runTransaction(async (transaction) => {
        // Simulate budget check (in production, this would call the budget microservice)
        const budgetDoc = await transaction.get(
          admin.firestore().collection('budget_status').doc('current')
        );
        
        const budgetData = budgetDoc.exists ? budgetDoc.data() : { utilization: 0.5 };
        
        // Determine service parameters based on budget
        if (budgetData.utilization >= 1.0) {
          return { allowed: false, serviceLevel: 'shutoff', maxTokens: 0, reason: 'Monthly budget exhausted' };
        } else if (budgetData.utilization >= 0.95) {
          return { 
            allowed: userTier !== 'free', 
            serviceLevel: 'emergency', 
            maxTokens: 150,
            reason: userTier === 'free' ? 'Budget constraints: Free tier temporarily limited' : null
          };
        } else if (budgetData.utilization >= 0.85) {
          return { allowed: true, serviceLevel: 'slowdown', maxTokens: 300 };
        } else if (budgetData.utilization >= 0.7) {
          return { 
            allowed: true, 
            serviceLevel: 'warning', 
            maxTokens: userTier === 'free' ? 300 : 500 
          };
        } else {
          return { allowed: true, serviceLevel: 'normal', maxTokens: 500 };
        }
      });
      
      budgetAllowed = budgetCheck.allowed;
      serviceLevel = budgetCheck.serviceLevel;
      maxTokens = budgetCheck.maxTokens;
      
      if (!budgetAllowed) {
        throw new Error(budgetCheck.reason || 'Service temporarily unavailable due to budget constraints');
      }
      
    } catch (budgetError) {
      logger.warn('Budget check failed, proceeding with caution', {
        error: budgetError.message,
        userId
      });
      // Continue with reduced service in case of budget check failure
      maxTokens = 300;
      serviceLevel = 'warning';
    }

    // Detect user's language for multilingual response
    const detectedLanguage = detectLanguage(message);

    logger.info("Chat request received", {
      userId,
      messageLength: message.length,
      tone,
      detectedLanguage,
      timestamp: startTime,
    });

    // Check rate limits and daily token usage
    const currentDailyTokens = await checkRateLimit(userId);

    // Get or create thread for user
    let userThreadId = await getOrCreateThread(userId);
    
    if (!userThreadId) {
      throw new Error("Failed to create or retrieve thread ID");
    }

    logger.info("Thread ID confirmed", {userId, threadId: userThreadId});

    // Create message document in Firestore first (for streaming)
    const messageDoc = {
      userId,
      threadId: userThreadId,
      userMessage: message,
      assistantResponse: "", // Will be updated as we stream
      tone,
      detectedLanguage,
      status: "processing",
      timestamp: new Date(),
      tokenIn: 0,
      tokenOut: 0,
      citations: [],
      startTime: startTime,
    };

    const messageRef = await admin.firestore().collection("messages").add(messageDoc);
    logger.info("Message document created", {messageId: messageRef.id});

    // Add user message to OpenAI thread
    await openai.beta.threads.messages.create(userThreadId, {
      role: "user",
      content: message,
    });

    // Create and run the assistant
    const run = await openai.beta.threads.runs.create(userThreadId, {
      assistant_id: ASSISTANT_ID,
    });

    logger.info("Assistant run started", {runId: run.id, threadId: userThreadId});

    // Poll for completion with detailed status tracking
    let runStatus = run;
    let pollCount = 0;
    const maxPolls = 120; // 2 minutes timeout

    while (["queued", "in_progress"].includes(runStatus.status) && pollCount < maxPolls) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      // Store parameters in local variables to prevent scoping issues
      const currentThreadId = userThreadId;
      const currentRunId = run.id;
      
      // Ensure parameters are still valid before making API call
      if (!currentThreadId) {
        throw new Error("Thread ID became undefined during polling");
      }
      if (!currentRunId) {
        throw new Error("Run ID became undefined during polling");
      }
      
      logger.info("Polling run status", {threadId: currentThreadId, runId: currentRunId, pollCount});
      
      // Debug log to verify parameters before API call
      logger.info("API call parameters", {
        param1_threadId: currentThreadId,
        param2_runId: currentRunId,
        threadIdType: typeof currentThreadId,
        runIdType: typeof currentRunId
      });
      
      // Fix: Use correct OpenAI v4 SDK syntax with object parameters
      runStatus = await openai.beta.threads.runs.retrieve(currentThreadId, currentRunId);
      pollCount++;

      if (pollCount % 10 === 0) {
        logger.info("Run status update", {
          runId: run.id,
          threadId: userThreadId,
          status: runStatus.status,
          pollCount,
        });
      }
    }

    if (runStatus.status === "completed") {
      // Get the assistant's response
      const messages = await openai.beta.threads.messages.list(userThreadId);
      const assistantMessage = messages.data.find((msg) =>
        msg.role === "assistant" && msg.run_id === run.id,
      );

      if (assistantMessage) {
        const response = (assistantMessage.content[0] && assistantMessage.content[0].text && assistantMessage.content[0].text.value) || "No response generated";
        const citations = extractCitations(assistantMessage);

        // Estimate token usage (rough approximation: 1 token ≈ 4 characters)
        tokenIn = Math.ceil(message.length / 4);
        tokenOut = Math.ceil(response.length / 4);

        // Update token usage
        await updateTokenUsage(userId, tokenIn, tokenOut);

        // Update message document with final response
        await messageRef.update({
          assistantResponse: response,
          text: response, // compatibility field for frontend listeners expecting `text`
          status: "completed",
          tokenIn: tokenIn,
          tokenOut: tokenOut,
          citations: citations,
          completedAt: new Date(),
          latency: Date.now() - startTime,
          runId: run.id,
        });

        // Calculate remaining daily tokens
        const limitRemaining = Math.max(0, DAILY_OUT_TOKENS_CAP - (currentDailyTokens + tokenOut));

        logger.info("Chat completed successfully", {
          userId,
          messageId: messageRef.id,
          tokenIn,
          tokenOut,
          limitRemaining,
          latency: Date.now() - startTime,
          citationsCount: citations.length,
        });

        // Return response with actual CourseGPT content for immediate display
        return {
          messageId: messageRef.id,
          response: response,
          tokenIn,
          tokenOut,
          limitRemaining,
          citations: citations,
        };
      }
    }

    // Handle failed runs
    await messageRef.update({
      status: "failed",
      error: `Assistant run failed with status: ${runStatus.status}`,
      failedAt: new Date(),
    });

    logger.error("Assistant run failed", {
      runId: run.id,
      status: runStatus.status,
      lastError: runStatus.last_error,
    });

    throw new Error(`Assistant run failed with status: ${runStatus.status}`);
  } catch (error) {
    logger.error("Chat function error", {
      userId: request.auth && request.auth.uid,
      error: error.message,
      stack: error.stack,
      latency: Date.now() - startTime,
    });
    throw error;
  }
});

/**
 * Get existing thread for user or create a new one
 * @param {string} userId - The user ID
 * @return {Promise<string>} Thread ID
 */
async function getOrCreateThread(userId) {
  try {
    if (!userId) {
      throw new Error("User ID is required for thread management");
    }

    // Check if user has existing thread
    const userDoc = await admin.firestore().collection("users").doc(userId).get();

    if (userDoc.exists && userDoc.data().threadId) {
      const existingThreadId = userDoc.data().threadId;
      logger.info("Using existing thread", {userId, threadId: existingThreadId});
      return existingThreadId;
    }

    // Create new thread
    const thread = await openai.beta.threads.create();
    
    if (!thread || !thread.id) {
      throw new Error("Failed to create OpenAI thread - no thread ID returned");
    }

    // Store thread ID in user document
    const firestore = admin.firestore();
    await firestore.collection("users").doc(userId).set({
      threadId: thread.id,
      createdAt: new Date(),
    }, {merge: true});

    logger.info("New thread created for user", {userId, threadId: thread.id});
    return thread.id;
  } catch (error) {
    logger.error("Error managing thread", {userId, error: error.message, stack: error.stack});
    throw new Error(`Thread management failed: ${error.message}`);
  }
}

/**
 * Clear thread for user (delete and recreate)
 * Callable HTTPS Function as specified in specs.md
 */
exports.clearThread = onCall({
  memory: '256MB',
  timeoutSeconds: 30,
  maxInstances: 5
}, async (request) => {
  try {
    const userId = request.auth && request.auth.uid;

    if (!userId) {
      throw new Error("Authentication required");
    }

    logger.info("Clear thread request", {userId});

    // Get user's current thread
    const userDoc = await admin.firestore().collection("users").doc(userId).get();

    if (userDoc.exists && userDoc.data().threadId) {
      const oldThreadId = userDoc.data().threadId;

      try {
        // Delete old thread from OpenAI (if possible)
        // Note: OpenAI doesn't have a delete thread endpoint yet, but we prepare for it
        logger.info("Old thread cleared from records", {userId, oldThreadId});
      } catch (error) {
        logger.warn("Could not delete old thread from OpenAI", {error: error.message});
      }
    }

    // Create new thread
    const newThread = await openai.beta.threads.create();

    // Update user document
    await admin.firestore().collection("users").doc(userId).set({
      threadId: newThread.id,
      clearedAt: new Date(),
    }, {merge: true});

    // Clear user's message history in Firestore
    const messagesQuery = admin.firestore().collection("messages").where("userId", "==", userId);
    const messagesToDelete = await messagesQuery.get();

    const batch = admin.firestore().batch();
    messagesToDelete.docs.forEach((doc) => {
      batch.delete(doc.ref);
    });
    await batch.commit();

    logger.info("Thread cleared successfully", {userId, newThreadId: newThread.id});

    return {
      threadId: newThread.id,
      message: "Thread cleared and reset successfully",
    };
  } catch (error) {
    logger.error("Clear thread error", {error: error.message, stack: error.stack});
    throw error;
  }
});
