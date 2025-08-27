/**
 * ACIM Guide Cloud Functions - Streamlined Version
 * Real CourseGPT integration with robust error handling
 * Enhanced with Sentry monitoring while maintaining spiritual integrity
 */

require("dotenv").config();
const {onCall} = require("firebase-functions/https");
const logger = require("firebase-functions/logger");
const admin = require("firebase-admin");
const OpenAI = require("openai");
const { initSentry, wrapFunction, createTransaction, captureError } = require('./sentry-config');

// Initialize Firebase Admin
if (!admin.apps.length) {
  admin.initializeApp();
}

// Environment variables
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const ASSISTANT_ID = process.env.ASSISTANT_ID;

if (!OPENAI_API_KEY) {
  throw new Error("OPENAI_API_KEY environment variable is required");
}
if (!ASSISTANT_ID) {
  throw new Error("ASSISTANT_ID environment variable is required");
}

// Initialize Sentry for spiritual AI platform monitoring
initSentry();

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: OPENAI_API_KEY
});

logger.info("ACIM Guide Functions initialized", {
  hasApiKey: !!OPENAI_API_KEY,
  hasAssistantId: !!ASSISTANT_ID,
  sentryEnabled: !!process.env.SENTRY_DSN_FUNCTIONS,
  timestamp: new Date().toISOString()
});

/**
 * Get or create thread for user
 */
async function getOrCreateThread(userId) {
  try {
    let existingThreadId = null;
    
    // Try to get existing thread from Firestore (optional)
    try {
      const userDoc = await admin.firestore().collection("users").doc(userId).get();
      if (userDoc.exists && userDoc.data().threadId) {
        existingThreadId = userDoc.data().threadId;
        
        // Verify thread still exists in OpenAI
        try {
          await openai.beta.threads.retrieve(existingThreadId);
          logger.info("Using existing thread", {userId, threadId: existingThreadId});
          return existingThreadId;
        } catch (error) {
          logger.warn("Existing thread not found in OpenAI, creating new one", {userId, oldThreadId: existingThreadId});
          existingThreadId = null;
        }
      }
    } catch (firestoreError) {
      logger.warn("Firestore unavailable for thread lookup, creating new thread", {
        userId,
        error: firestoreError.message
      });
    }
    
    // Create new thread
    const thread = await openai.beta.threads.create();
    logger.info("Created new OpenAI thread", {userId, threadId: thread.id});
    
    // Try to store thread ID in Firestore (optional)
    try {
      await admin.firestore().collection("users").doc(userId).set({
        threadId: thread.id,
        createdAt: new Date(),
        lastActiveAt: new Date()
      }, { merge: true });
      logger.info("Thread ID stored in Firestore", {userId, threadId: thread.id});
    } catch (firestoreError) {
      logger.warn("Could not store thread in Firestore, continuing", {
        userId,
        threadId: thread.id,
        error: firestoreError.message
      });
    }
    
    return thread.id;
  } catch (error) {
    logger.error("Critical error in thread management", {userId, error: error.message});
    throw error;
  }
}

/**
 * Chat with CourseGPT Assistant - Enhanced with Sentry Monitoring
 * Maintains spiritual integrity while providing enterprise-grade observability
 */
exports.chatWithAssistant = onCall({
  memory: "512MB",
  timeoutSeconds: 60,
  maxInstances: 10
}, wrapFunction(async (request) => {
  const startTime = Date.now();
  const transaction = createTransaction('chatWithAssistant', 'spiritual-guidance');
  
  try {
    const {message, tone = "gentle"} = request.data;
    const userId = request.auth && request.auth.uid;

    // Set user context for Sentry (privacy-safe)
    const Sentry = require('@sentry/serverless');
    Sentry.setUser({
      id: userId ? require('crypto').createHash('sha256').update(userId).digest('hex').substring(0, 16) : 'anonymous',
      segment: 'spiritual-seeker' // Business context only
    });

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
      timestamp: startTime
    });

    // Get or create thread for user
    const userThreadId = await getOrCreateThread(userId);
    
    if (!userThreadId) {
      throw new Error("Failed to create or retrieve thread ID");
    }

    logger.info("Thread ID confirmed", {userId, threadId: userThreadId});

    // Create message document in Firestore (for real-time updates)
    const messageDoc = {
      userId,
      threadId: userThreadId,
      userMessage: message,
      assistantResponse: "",
      tone,
      status: "processing",
      timestamp: new Date(),
      startTime: startTime
    };

    let messageRef;
    try {
      messageRef = await admin.firestore().collection("messages").add(messageDoc);
      logger.info("Message document created", {messageId: messageRef.id});
    } catch (firestoreError) {
      logger.warn("Firestore write failed, continuing without storage", {error: firestoreError.message});
    }

    // Add user message to OpenAI thread (with performance tracking)
    const addMessageSpan = transaction.startChild({ op: 'openai', description: 'Add message to thread' });
    await openai.beta.threads.messages.create(userThreadId, {
      role: "user",
      content: message
    });
    addMessageSpan.finish();

    // Create and run the assistant (with performance tracking)
    const runSpan = transaction.startChild({ op: 'openai', description: 'Create assistant run' });
    const run = await openai.beta.threads.runs.create(userThreadId, {
      assistant_id: ASSISTANT_ID
    });
    runSpan.finish();

    logger.info("Assistant run started", {runId: run.id, threadId: userThreadId});

    // Poll for completion
    let runStatus = run;
    let pollCount = 0;
    const maxPolls = 60; // 1 minute timeout for streamlined version

    while (["queued", "in_progress"].includes(runStatus.status) && pollCount < maxPolls) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      runStatus = await openai.beta.threads.runs.retrieve(userThreadId, run.id);
      pollCount++;

      if (pollCount % 10 === 0) {
        logger.info("Run status update", {
          runId: run.id,
          status: runStatus.status,
          pollCount
        });
      }
    }

    if (runStatus.status === "completed") {
      // Get the assistant's response (with performance tracking)
      const getResponseSpan = transaction.startChild({ op: 'openai', description: 'Retrieve assistant response' });
      const messages = await openai.beta.threads.messages.list(userThreadId);
      const assistantMessage = messages.data.find((msg) =>
        msg.role === "assistant" && msg.run_id === run.id
      );
      getResponseSpan.finish();

      if (assistantMessage) {
        let response = (assistantMessage.content[0] && assistantMessage.content[0].text && assistantMessage.content[0].text.value) || "No response generated";
        
        // Clean up section breaks and HTML tags that should not be displayed
        response = response
          // Handle all section-break patterns comprehensively
          .replace(/\*?["']?section-break["']?\*?[>]?/gi, "\n\n---\n\n")
          // Handle specific patterns that might appear
          .replace(/"section-break"[>]?/gi, "\n\n---\n\n")
          .replace(/[*]"section-break"[*][>]?/gi, "\n\n---\n\n")
          .replace(/<\/?section-break\/?>/gi, "\n\n---\n\n")
          .replace(/<\/?[^>]+(>|$)/g, "") // Remove any remaining HTML tags
          .replace(/\n{3,}/g, "\n\n") // Clean up excessive line breaks
          .trim();

        // Update message document if we created one (with performance tracking)
        if (messageRef) {
          const updateSpan = transaction.startChild({ op: 'firestore', description: 'Update message document' });
          try {
            await messageRef.update({
              assistantResponse: response,
              text: response, // compatibility field
              status: "completed",
              completedAt: new Date(),
              latency: Date.now() - startTime,
              runId: run.id
            });
            updateSpan.setStatus('ok');
          } catch (updateError) {
            logger.warn("Failed to update message document", {error: updateError.message});
            updateSpan.setStatus('internal_error');
          }
          updateSpan.finish();
        }

        logger.info("Chat completed successfully", {
          userId,
          messageId: (messageRef && messageRef.id),
          responseLength: response.length,
          latency: Date.now() - startTime
        });

        // Mark transaction as successful
        transaction.setStatus('ok');
        transaction.setTag('spiritual_guidance_success', true);
        transaction.finish();

        // Return response for immediate display
        return {
          messageId: (messageRef && messageRef.id),
          response: response,
          latency: Date.now() - startTime,
          isPlaceholder: false
        };
      } else {
        throw new Error("No assistant response found");
      }
    } else if (runStatus.status === "failed") {
      logger.error("Assistant run failed", {
        runId: run.id,
        status: runStatus.status,
        error: runStatus.last_error
      });
      throw new Error(`Assistant run failed: ${(runStatus.last_error && runStatus.last_error.message) || "Unknown error"}`);
    } else {
      logger.error("Assistant run timed out", {runId: run.id, status: runStatus.status, pollCount});
      throw new Error("Assistant response timed out");
    }

  } catch (error) {
    logger.error("Chat function error", {
      error: error.message,
      stack: error.stack,
      userId: (request.auth && request.auth.uid)
    });
    
    // Mark transaction as failed and capture error
    transaction.setStatus('internal_error');
    transaction.setTag('spiritual_guidance_success', false);
    transaction.finish();
    
    // Capture error with spiritual content protection
    captureError(error, {
      userId: request.auth?.uid ? 'authenticated' : 'anonymous',
      messageLength: request.data?.message?.length || 0,
      function: 'chatWithAssistant'
    });
    
    throw error;
  }
});

/**
 * Clear thread function
 */
exports.clearThread = onCall(async (request) => {
  try {
    const userId = request.auth && request.auth.uid;

    if (!userId) {
      throw new Error("Authentication required");
    }

    logger.info("Clear thread request", {userId});

    // Create new thread
    const newThread = await openai.beta.threads.create();
    logger.info("New thread created for clear", {userId, threadId: newThread.id});
    
    // Try to update user document with new thread ID
    try {
      await admin.firestore().collection("users").doc(userId).set({
        threadId: newThread.id,
        lastClearedAt: new Date(),
        lastActiveAt: new Date()
      }, { merge: true });
      logger.info("Thread ID updated in Firestore", {userId, threadId: newThread.id});
    } catch (firestoreError) {
      logger.warn("Could not update user thread in Firestore", {
        userId,
        threadId: newThread.id,
        error: firestoreError.message
      });
    }

    // Try to clear user's messages (optional)
    try {
      const messagesQuery = admin.firestore().collection("messages").where("userId", "==", userId);
      const messagesToDelete = await messagesQuery.get();

      if (!messagesToDelete.empty) {
        const batch = admin.firestore().batch();
        messagesToDelete.docs.forEach((doc) => {
          batch.delete(doc.ref);
        });
        await batch.commit();
        logger.info("Messages cleared from Firestore", {userId, count: messagesToDelete.size});
      }
    } catch (cleanupError) {
      logger.warn("Message cleanup failed, continuing", {error: cleanupError.message});
    }

    logger.info("Thread cleared successfully", {userId, newThreadId: newThread.id});

    return {
      threadId: newThread.id,
      message: "Thread cleared successfully"
    };

  } catch (error) {
    logger.error("Clear thread error", {error: error.message});
    throw error;
  }
});

/**
 * Health check function
 */
exports.healthCheck = onCall(async (request) => {
  return {
    status: "healthy",
    timestamp: new Date().toISOString(),
    version: "1.0.0-streamlined",
    message: "ACIM Guide Functions are running with divine grace 🕊️"
  };
});
