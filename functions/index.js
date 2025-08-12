/**
 * ACIMguide Cloud Functions
 * Chat endpoint for CourseGPT Assistant with enhanced token management
 */

/* eslint-disable max-len */

require("dotenv").config();
const {setGlobalOptions} = require("firebase-functions");
const {onCall} = require("firebase-functions/v2/https");
const logger = require("firebase-functions/logger");
const admin = require("firebase-admin");
const OpenAI = require("openai");

// Initialize Firebase Admin
if (!admin.apps.length) {
  admin.initializeApp();
}

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Configuration constants
const ASSISTANT_ID = process.env.ASSISTANT_ID;
const VECTOR_STORE_ID = process.env.VECTOR_STORE_ID;
const DAILY_OUT_TOKENS_CAP = parseInt(process.env.DAILY_OUT_TOKENS_CAP) || 2000;
const RATE_LIMIT_RPM = 10; // Requests per minute per user

// For cost control, set maximum containers
setGlobalOptions({maxInstances: 10});

/**
 * Validate environment variables on startup
 */
if (!process.env.OPENAI_API_KEY) {
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
 * Chat with CourseGPT Assistant - Enhanced version with full API contract compliance
 * Callable HTTPS Function as specified in specs.md
 */
exports.chatWithAssistant = onCall(async (request) => {
  const startTime = Date.now();
  let tokenIn = 0;
  let tokenOut = 0;

  try {
    const {message, tone = "gentle"} = request.data;
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

    logger.info("Chat request received", {
      userId,
      messageLength: message.length,
      tone,
      timestamp: startTime,
    });

    // Check rate limits and daily token usage
    const currentDailyTokens = await checkRateLimit(userId);

    // Get or create thread for user
    const threadId = await getOrCreateThread(userId);

    // Create message document in Firestore first (for streaming)
    const messageDoc = {
      userId,
      threadId,
      userMessage: message,
      assistantResponse: "", // Will be updated as we stream
      tone,
      status: "processing",
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      tokenIn: 0,
      tokenOut: 0,
      citations: [],
      startTime: startTime,
    };

    const messageRef = await admin.firestore().collection("messages").add(messageDoc);
    logger.info("Message document created", {messageId: messageRef.id});

    // Add user message to OpenAI thread
    await openai.beta.threads.messages.create(threadId, {
      role: "user",
      content: message,
    });

    // Create and run the assistant
    const run = await openai.beta.threads.runs.create(threadId, {
      assistant_id: ASSISTANT_ID,
    });

    logger.info("Assistant run started", {runId: run.id, threadId});

    // Poll for completion with detailed status tracking
    let runStatus = run;
    let pollCount = 0;
    const maxPolls = 120; // 2 minutes timeout

    while (["queued", "in_progress"].includes(runStatus.status) && pollCount < maxPolls) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      runStatus = await openai.beta.threads.runs.retrieve(threadId, run.id);
      pollCount++;

      if (pollCount % 10 === 0) {
        logger.info("Run status update", {
          runId: run.id,
          status: runStatus.status,
          pollCount,
        });
      }
    }

    if (runStatus.status === "completed") {
      // Get the assistant's response
      const messages = await openai.beta.threads.messages.list(threadId);
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
          status: "completed",
          tokenIn: tokenIn,
          tokenOut: tokenOut,
          citations: citations,
          completedAt: admin.firestore.FieldValue.serverTimestamp(),
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

        // Return response matching API contract from specs.md
        return {
          messageId: messageRef.id,
          tokenIn,
          tokenOut,
          limitRemaining,
        };
      }
    }

    // Handle failed runs
    await messageRef.update({
      status: "failed",
      error: `Assistant run failed with status: ${runStatus.status}`,
      failedAt: admin.firestore.FieldValue.serverTimestamp(),
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
    // Check if user has existing thread
    const userDoc = await admin.firestore().collection("users").doc(userId).get();

    if (userDoc.exists && userDoc.data().threadId) {
      return userDoc.data().threadId;
    }

    // Create new thread
    const thread = await openai.beta.threads.create();

    // Store thread ID in user document
    await admin.firestore().collection("users").doc(userId).set({
      threadId: thread.id,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
    }, {merge: true});

    logger.info("New thread created for user", {userId, threadId: thread.id});
    return thread.id;
  } catch (error) {
    logger.error("Error managing thread", {userId, error: error.message});
    throw error;
  }
}

/**
 * Clear thread for user (delete and recreate)
 * Callable HTTPS Function as specified in specs.md
 */
exports.clearThread = onCall(async (request) => {
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
      clearedAt: admin.firestore.FieldValue.serverTimestamp(),
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
