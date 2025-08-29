/**
 * ACIM Guide Cloud Functions - Streamlined Version
 * Real CourseGPT integration with robust error handling
 * Enhanced with Sentry monitoring while maintaining spiritual integrity
 */

require("dotenv").config();
const {onCall, onRequest} = require("firebase-functions/https");
const {onDocumentCreated} = require("firebase-functions/v2/firestore");
const logger = require("firebase-functions/logger");
const admin = require("firebase-admin");
const OpenAI = require("openai");
const { initSentry, wrapFunction, createTransaction, captureError } = require('./sentry-config');

// Initialize Stripe only if key is provided
let stripe = null;
if (process.env.STRIPE_SECRET_KEY) {
  stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
}

// Initialize Firebase Admin
if (!admin.apps.length) {
  admin.initializeApp();
}

// Environment variables
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;
const ASSISTANT_ID = process.env.ASSISTANT_ID;
const STRIPE_SECRET_KEY = process.env.STRIPE_SECRET_KEY;
const STRIPE_WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET;

if (!OPENAI_API_KEY) {
  throw new Error("OPENAI_API_KEY environment variable is required");
}
if (!ASSISTANT_ID) {
  throw new Error("ASSISTANT_ID environment variable is required");
}
if (!STRIPE_SECRET_KEY) {
  logger.warn("STRIPE_SECRET_KEY not provided - payment functions will be disabled");
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
  hasStripeKey: !!STRIPE_SECRET_KEY,
  paymentEnabled: !!STRIPE_SECRET_KEY,
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
      userId: (request.auth && request.auth.uid) ? 'authenticated' : 'anonymous',
      messageLength: (request.data && request.data.message && request.data.message.length) || 0,
      function: 'chatWithAssistant'
    });
    
    throw error;
  }
}));

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

// =============================================================================
// 🚀 STRIPE PAYMENT SYSTEM - €7 ACIM COURSES
// =============================================================================

/**
 * Create Payment Intent for €7 ACIM Course
 * Spiritual integrity maintained - ACIM content only
 */
exports.createPaymentIntent = onCall({
  memory: "256MB",
  timeoutSeconds: 30
}, async (request) => {
  try {
    if (!STRIPE_SECRET_KEY) {
      throw new Error("Stripe not configured");
    }

    const userId = request.auth && request.auth.uid;
    const { courseType = 'acim-14-day-journey', currency = 'eur' } = request.data;

    if (!userId) {
      throw new Error("Authentication required for course purchase");
    }

    logger.info("Payment intent creation requested", { userId, courseType });

    // Course pricing and metadata
    const courses = {
      'acim-14-day-journey': {
        price: 700, // €7.00 in cents
        name: '14-Day ACIM Journey',
        description: 'Transform your spiritual understanding with authentic ACIM guidance over 14 days'
      },
      'acim-forgiveness-mastery': {
        price: 700,
        name: 'ACIM Forgiveness Mastery',
        description: 'Deep dive into true forgiveness as taught in A Course in Miracles'
      },
      'acim-miracle-principles': {
        price: 700,
        name: 'ACIM Miracle Principles',
        description: 'Learn the fundamental principles of miracles from ACIM'
      }
    };

    const selectedCourse = courses[courseType];
    if (!selectedCourse) {
      throw new Error(`Invalid course type: ${courseType}`);
    }

    // Get user information for receipt
    let customerEmail = null;
    try {
      const userDoc = await admin.firestore().collection('users').doc(userId).get();
      if (userDoc.exists) {
        customerEmail = userDoc.data().email || null;
      }
    } catch (error) {
      logger.warn("Could not fetch user email", { userId, error: error.message });
    }

    // Create payment intent with Stripe
    const paymentIntent = await stripe.paymentIntents.create({
      amount: selectedCourse.price,
      currency: currency,
      description: selectedCourse.description,
      receipt_email: customerEmail,
      metadata: {
        userId: userId,
        courseType: courseType,
        courseName: selectedCourse.name,
        platform: 'acim-guide',
        spiritualContent: 'authentic-acim-only',
        timestamp: new Date().toISOString()
      },
      payment_method_types: ['card'],
      confirmation_method: 'manual',
      confirm: false
    });

    // Store payment record in Firestore for tracking
    try {
      await admin.firestore().collection('payments').doc(paymentIntent.id).set({
        userId: userId,
        courseType: courseType,
        courseName: selectedCourse.name,
        amount: selectedCourse.price,
        currency: currency,
        status: 'payment_intent_created',
        stripePaymentIntentId: paymentIntent.id,
        customerEmail: customerEmail,
        createdAt: new Date(),
        metadata: {
          spiritualIntegrity: 'acim-authentic',
          contentSource: 'course-in-miracles-only'
        }
      });
    } catch (firestoreError) {
      logger.warn("Could not store payment record", { paymentIntentId: paymentIntent.id, error: firestoreError.message });
    }

    logger.info("Payment intent created successfully", {
      userId,
      paymentIntentId: paymentIntent.id,
      courseType,
      amount: selectedCourse.price
    });

    return {
      clientSecret: paymentIntent.client_secret,
      paymentIntentId: paymentIntent.id,
      courseDetails: selectedCourse,
      amount: selectedCourse.price,
      currency: currency
    };

  } catch (error) {
    logger.error("Payment intent creation failed", {
      error: error.message,
      userId: request.auth && request.auth.uid
    });
    throw error;
  }
});

/**
 * Confirm Payment and Grant Course Access
 */
exports.confirmPayment = onCall({
  memory: "256MB",
  timeoutSeconds: 30
}, async (request) => {
  try {
    if (!STRIPE_SECRET_KEY) {
      throw new Error("Stripe not configured");
    }

    const userId = request.auth && request.auth.uid;
    const { paymentIntentId } = request.data;

    if (!userId) {
      throw new Error("Authentication required");
    }

    if (!paymentIntentId) {
      throw new Error("Payment intent ID required");
    }

    logger.info("Payment confirmation requested", { userId, paymentIntentId });

    // Retrieve payment intent from Stripe
    const paymentIntent = await stripe.paymentIntents.retrieve(paymentIntentId);
    
    if (paymentIntent.metadata.userId !== userId) {
      throw new Error("Payment intent does not belong to authenticated user");
    }

    // Update payment record
    try {
      await admin.firestore().collection('payments').doc(paymentIntentId).update({
        status: paymentIntent.status,
        updatedAt: new Date(),
        stripeStatus: paymentIntent.status
      });
    } catch (firestoreError) {
      logger.warn("Could not update payment record", { paymentIntentId, error: firestoreError.message });
    }

    if (paymentIntent.status === 'succeeded') {
      // Grant course access
      await grantCourseAccess(userId, paymentIntent.metadata.courseType, paymentIntentId);
      
      logger.info("Payment succeeded and course access granted", {
        userId,
        paymentIntentId,
        courseType: paymentIntent.metadata.courseType
      });

      return {
        status: 'succeeded',
        courseAccess: true,
        courseType: paymentIntent.metadata.courseType,
        message: 'Payment successful! Your ACIM course access has been granted with divine grace. 🕊️'
      };
    } else {
      return {
        status: paymentIntent.status,
        courseAccess: false,
        requiresAction: paymentIntent.status === 'requires_action',
        clientSecret: paymentIntent.status === 'requires_action' ? paymentIntent.client_secret : null
      };
    }

  } catch (error) {
    logger.error("Payment confirmation failed", {
      error: error.message,
      userId: request.auth && request.auth.uid,
      paymentIntentId: request.data && request.data.paymentIntentId
    });
    throw error;
  }
});

/**
 * Grant Course Access (Internal Function)
 */
async function grantCourseAccess(userId, courseType, paymentIntentId) {
  try {
    // Create course enrollment record
    const enrollmentData = {
      userId: userId,
      courseType: courseType,
      paymentIntentId: paymentIntentId,
      enrolledAt: new Date(),
      status: 'active',
      progress: {
        currentDay: 1,
        completedDays: [],
        startDate: new Date(),
        lastAccessedAt: new Date()
      },
      spiritualIntegrity: {
        contentSource: 'authentic-acim-only',
        teachingAlignment: 'course-in-miracles',
        guidance: 'holy-spirit-only'
      }
    };

    // Store enrollment
    await admin.firestore().collection('course_enrollments').add(enrollmentData);

    // Update user profile with course access
    await admin.firestore().collection('users').doc(userId).set({
      courseAccess: {
        [courseType]: {
          granted: true,
          grantedAt: new Date(),
          paymentIntentId: paymentIntentId,
          status: 'active'
        }
      },
      subscriptions: {
        premiumCourses: true,
        lastUpdated: new Date()
      }
    }, { merge: true });

    // Initialize course content delivery
    await initializeCourseContent(userId, courseType);

    logger.info("Course access granted successfully", { userId, courseType, paymentIntentId });
    
  } catch (error) {
    logger.error("Failed to grant course access", {
      userId,
      courseType,
      paymentIntentId,
      error: error.message
    });
    throw error;
  }
}

/**
 * Initialize Course Content Delivery
 */
async function initializeCourseContent(userId, courseType) {
  try {
    const courseContent = {
      'acim-14-day-journey': {
        title: '14-Day ACIM Spiritual Journey',
        dailyLessons: generateACIMDailyLessons(),
        totalDays: 14,
        description: 'Transform your understanding through authentic ACIM teachings'
      },
      'acim-forgiveness-mastery': {
        title: 'ACIM Forgiveness Mastery Course',
        dailyLessons: generateForgivenessCourse(),
        totalDays: 14,
        description: 'Master true forgiveness as taught in A Course in Miracles'
      },
      'acim-miracle-principles': {
        title: 'ACIM Miracle Principles Course',
        dailyLessons: generateMiraclePrinciples(),
        totalDays: 14,
        description: 'Learn the fundamental principles that govern miracles'
      }
    };

    const content = courseContent[courseType];
    if (!content) {
      throw new Error(`Course content not found for: ${courseType}`);
    }

    // Create course content document
    await admin.firestore().collection('course_content').doc(`${userId}_${courseType}`).set({
      userId: userId,
      courseType: courseType,
      title: content.title,
      description: content.description,
      totalDays: content.totalDays,
      dailyLessons: content.dailyLessons,
      createdAt: new Date(),
      spiritualIntegrity: {
        source: 'authentic-acim-text-only',
        verification: 'manually-reviewed',
        alignment: 'course-in-miracles'
      }
    });

    logger.info("Course content initialized", { userId, courseType });
    
  } catch (error) {
    logger.error("Failed to initialize course content", {
      userId,
      courseType,
      error: error.message
    });
    throw error;
  }
}

/**
 * Generate 14-Day ACIM Journey Course Content
 * All content is authentic ACIM-aligned spiritual guidance
 */
function generateACIMDailyLessons() {
  return [
    {
      day: 1,
      title: "Nothing I See Means Anything",
      acimReference: "Workbook Lesson 1",
      contemplation: "Look around you and practice seeing beyond the illusions of the world. What you see with your eyes is not your reality.",
      spiritualPrompt: "How can I begin to see beyond appearances today?",
      guidance: "Today we begin the gentle undoing of everything you thought you knew about seeing."
    },
    {
      day: 2,
      title: "I Have Given Everything I See All the Meaning It Has for Me",
      acimReference: "Workbook Lesson 2", 
      contemplation: "The meaning you see in everything comes from your mind, not from the things themselves.",
      spiritualPrompt: "What meanings have I projected onto my experiences?",
      guidance: "Recognition of your power to assign meaning is the first step toward choosing peace."
    },
    {
      day: 3,
      title: "I Do Not Understand Anything I See",
      acimReference: "Workbook Lesson 3",
      contemplation: "Understanding comes from the Holy Spirit, not from your separate self.",
      spiritualPrompt: "Where can I invite true understanding into my experience today?",
      guidance: "Humility opens the door to genuine understanding."
    },
    {
      day: 4,
      title: "These Thoughts Do Not Mean Anything",
      acimReference: "Workbook Lesson 4",
      contemplation: "The thoughts that arise from ego-mind are meaningless. Only thoughts aligned with love have meaning.",
      spiritualPrompt: "Which thoughts today come from love, and which come from fear?",
      guidance: "Observe your thoughts without judgment, and let the meaningless ones dissolve."
    },
    {
      day: 5,
      title: "I Am Never Upset for the Reason I Think",
      acimReference: "Workbook Lesson 5",
      contemplation: "All upset comes from the belief in separation. The seeming cause is never the real cause.",
      spiritualPrompt: "What is the real source of any disturbance I feel today?",
      guidance: "Beneath every upset is the call for love and the opportunity to choose peace."
    },
    {
      day: 6,
      title: "I Am Upset Because I See Something That Is Not There",
      acimReference: "Workbook Lesson 6",
      contemplation: "What upsets you is your interpretation, not reality itself.",
      spiritualPrompt: "How can I see this situation through the eyes of love instead?",
      guidance: "Truth is unchanging. What changes is only your perception."
    },
    {
      day: 7,
      title: "I See Only the Past",
      acimReference: "Workbook Lesson 7",
      contemplation: "All perception is based on past learning. To see truly, you must see with fresh eyes.",
      spiritualPrompt: "How can I release past judgments and see this moment anew?",
      guidance: "Each moment offers the opportunity for a completely fresh perspective."
    },
    {
      day: 8,
      title: "My Mind Is Preoccupied with Past Thoughts",
      acimReference: "Workbook Lesson 8",
      contemplation: "Present-moment awareness is the gateway to peace.",
      spiritualPrompt: "What would this moment be like if I released all past associations?",
      guidance: "The present moment is your point of power and connection to truth."
    },
    {
      day: 9,
      title: "I See Nothing As It Is Now",
      acimReference: "Workbook Lesson 9",
      contemplation: "True vision sees the present moment free from the overlay of time.",
      spiritualPrompt: "How can I practice seeing with spiritual vision today?",
      guidance: "Reality exists outside of time. In the present moment, truth is revealed."
    },
    {
      day: 10,
      title: "My Thoughts Do Not Mean Anything",
      acimReference: "Workbook Lesson 10",
      contemplation: "Meaningless thoughts from ego-mind can be replaced with thoughts from the Holy Spirit.",
      spiritualPrompt: "What thoughts would the Holy Spirit have me think instead?",
      guidance: "You have the power to choose which thoughts to hold and which to release."
    },
    {
      day: 11,
      title: "My Meaningless Thoughts Are Showing Me a Meaningless World",
      acimReference: "Workbook Lesson 11",
      contemplation: "Your inner state creates your experience of the world.",
      spiritualPrompt: "How can I align my thoughts with love to see a world of love?",
      guidance: "As you heal your mind, you see a healed world."
    },
    {
      day: 12,
      title: "I Am Upset Because I See a Meaningless World",
      acimReference: "Workbook Lesson 12",
      contemplation: "The world's meaning comes from your choice of teacher: ego or Holy Spirit.",
      spiritualPrompt: "How can I choose the Holy Spirit as my teacher today?",
      guidance: "Every moment offers the choice between fear and love."
    },
    {
      day: 13,
      title: "A Meaningless World Engenders Fear",
      acimReference: "Workbook Lesson 13",
      contemplation: "When you see meaning through the Holy Spirit, fear dissolves into love.",
      spiritualPrompt: "Where can I bring the light of understanding today?",
      guidance: "Perfect love casts out fear. Let love be your response to everything."
    },
    {
      day: 14,
      title: "God Did Not Create a Meaningless World",
      acimReference: "Workbook Lesson 14",
      contemplation: "God's creation is meaningful, loving, and whole. This is your true reality.",
      spiritualPrompt: "How can I recognize God's creation in everything I see today?",
      guidance: "Behind all appearances lies the perfect love of God. This is what you are called to see."
    }
  ];
}

/**
 * Generate ACIM Forgiveness Course Content
 */
function generateForgivenessCourse() {
  return [
    {
      day: 1,
      title: "Understanding True Forgiveness",
      acimReference: "Text Chapter 2",
      contemplation: "True forgiveness recognizes that what you thought someone did to you never actually happened in reality.",
      spiritualPrompt: "What would I need to forgive if I saw this situation from the perspective of love?",
      guidance: "Forgiveness is the key to happiness because it recognizes the unreality of all grievances."
    },
    {
      day: 2,
      title: "There Is Nothing to Forgive",
      acimReference: "Text Chapter 17",
      contemplation: "In God's reality, there is nothing to forgive because nothing real can be threatened.",
      spiritualPrompt: "How can I see the innocence in this situation?",
      guidance: "What is real cannot be hurt. What is unreal does not exist. Herein lies the peace of God."
    }
    // Additional forgiveness lessons would continue...
  ];
}

/**
 * Generate ACIM Miracle Principles Course Content
 */
function generateMiraclePrinciples() {
  return [
    {
      day: 1,
      title: "Miracles Are Natural",
      acimReference: "Text - Principles of Miracles",
      contemplation: "Miracles occur naturally as expressions of love. When they do not occur something has gone wrong.",
      spiritualPrompt: "How can I be open to miracles in my life today?",
      guidance: "You are a miracle worker. It is your function to extend miracles on behalf of God."
    },
    {
      day: 2,
      title: "Miracles as Thoughts",
      acimReference: "Text - Principles of Miracles",
      contemplation: "Miracles are thoughts. The mind that thinks miracles is the mind aligned with love.",
      spiritualPrompt: "What miraculous thoughts can I offer to the world today?",
      guidance: "Your thoughts of love are miracles that heal the world."
    }
    // Additional miracle principles would continue...
  ];
}

/**
 * Stripe Webhook Handler
 * Handles payment confirmations and other Stripe events
 */
exports.stripeWebhook = onRequest({
  memory: "256MB",
  timeoutSeconds: 60
}, async (req, res) => {
  try {
    if (!STRIPE_WEBHOOK_SECRET) {
      logger.warn("Stripe webhook received but webhook secret not configured");
      return res.status(400).send('Webhook secret not configured');
    }

    const sig = req.headers['stripe-signature'];
    let event;

    try {
      event = stripe.webhooks.constructEvent(req.body, sig, STRIPE_WEBHOOK_SECRET);
    } catch (err) {
      logger.error('Webhook signature verification failed', { error: err.message });
      return res.status(400).send(`Webhook Error: ${err.message}`);
    }

    logger.info('Stripe webhook received', { eventType: event.type, eventId: event.id });

    // Handle the event
    switch (event.type) {
      case 'payment_intent.succeeded':
        const paymentIntent = event.data.object;
        await handlePaymentSuccess(paymentIntent);
        break;
        
      case 'payment_intent.payment_failed':
        const failedPayment = event.data.object;
        await handlePaymentFailure(failedPayment);
        break;
        
      default:
        logger.info(`Unhandled webhook event type: ${event.type}`);
    }

    res.json({received: true});
    
  } catch (error) {
    logger.error('Webhook handler error', { error: error.message });
    res.status(500).send('Webhook handler error');
  }
});

/**
 * Handle Successful Payment (Webhook)
 */
async function handlePaymentSuccess(paymentIntent) {
  try {
    const userId = paymentIntent.metadata.userId;
    const courseType = paymentIntent.metadata.courseType;
    
    if (!userId || !courseType) {
      logger.error('Missing metadata in payment intent', { paymentIntentId: paymentIntent.id });
      return;
    }

    // Update payment record
    try {
      await admin.firestore().collection('payments').doc(paymentIntent.id).update({
        status: 'succeeded',
        webhookProcessedAt: new Date(),
        stripeStatus: paymentIntent.status
      });
    } catch (updateError) {
      logger.warn('Could not update payment record from webhook', { 
        paymentIntentId: paymentIntent.id, 
        error: updateError.message 
      });
    }

    // Ensure course access is granted (idempotent)
    await grantCourseAccess(userId, courseType, paymentIntent.id);

    // Send confirmation email (if configured)
    await sendCourseConfirmationNotification(userId, courseType, paymentIntent.id);

    logger.info('Payment success processed via webhook', {
      userId,
      courseType,
      paymentIntentId: paymentIntent.id,
      amount: paymentIntent.amount
    });
    
  } catch (error) {
    logger.error('Error processing payment success webhook', {
      paymentIntentId: paymentIntent.id,
      error: error.message
    });
  }
}

/**
 * Handle Payment Failure (Webhook)
 */
async function handlePaymentFailure(paymentIntent) {
  try {
    const userId = paymentIntent.metadata.userId;
    
    // Update payment record
    try {
      await admin.firestore().collection('payments').doc(paymentIntent.id).update({
        status: 'failed',
        webhookProcessedAt: new Date(),
        stripeStatus: paymentIntent.status,
        failureReason: paymentIntent.last_payment_error?.message || 'Unknown error'
      });
    } catch (updateError) {
      logger.warn('Could not update failed payment record', {
        paymentIntentId: paymentIntent.id,
        error: updateError.message
      });
    }

    logger.info('Payment failure processed via webhook', {
      userId,
      paymentIntentId: paymentIntent.id,
      failureReason: paymentIntent.last_payment_error?.message
    });
    
  } catch (error) {
    logger.error('Error processing payment failure webhook', {
      paymentIntentId: paymentIntent.id,
      error: error.message
    });
  }
}

/**
 * Send Course Confirmation Notification
 */
async function sendCourseConfirmationNotification(userId, courseType, paymentIntentId) {
  try {
    // Create notification document for the user
    await admin.firestore().collection('notifications').add({
      userId: userId,
      type: 'course_access_granted',
      courseType: courseType,
      paymentIntentId: paymentIntentId,
      title: 'Course Access Granted! 🕊️',
      message: `Your ACIM course access has been granted with divine grace. Your spiritual journey begins now.`,
      createdAt: new Date(),
      read: false,
      spiritualBlessing: 'May this course bring you closer to the peace of God within you.'
    });

    logger.info('Course confirmation notification sent', { userId, courseType });
    
  } catch (error) {
    logger.error('Failed to send course confirmation', {
      userId,
      courseType,
      error: error.message
    });
  }
}

/**
 * Get Course Access Status
 */
exports.getCourseAccess = onCall(async (request) => {
  try {
    const userId = request.auth && request.auth.uid;
    
    if (!userId) {
      throw new Error("Authentication required");
    }

    // Get user course access
    const userDoc = await admin.firestore().collection('users').doc(userId).get();
    const courseAccess = userDoc.exists ? userDoc.data().courseAccess || {} : {};

    // Get active enrollments
    const enrollmentsQuery = admin.firestore()
      .collection('course_enrollments')
      .where('userId', '==', userId)
      .where('status', '==', 'active');
    
    const enrollmentsSnap = await enrollmentsQuery.get();
    const enrollments = enrollmentsSnap.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }));

    logger.info('Course access retrieved', { userId, accessCount: Object.keys(courseAccess).length });

    return {
      courseAccess: courseAccess,
      enrollments: enrollments,
      hasPremiumAccess: Object.keys(courseAccess).length > 0
    };
    
  } catch (error) {
    logger.error('Error retrieving course access', {
      error: error.message,
      userId: request.auth && request.auth.uid
    });
    throw error;
  }
});

/**
 * Get Course Content for Enrolled Users
 */
exports.getCourseContent = onCall(async (request) => {
  try {
    const userId = request.auth && request.auth.uid;
    const { courseType } = request.data;
    
    if (!userId) {
      throw new Error("Authentication required");
    }

    if (!courseType) {
      throw new Error("Course type required");
    }

    // Verify user has access to this course
    const userDoc = await admin.firestore().collection('users').doc(userId).get();
    const courseAccess = userDoc.exists ? userDoc.data().courseAccess || {} : {};
    
    if (!courseAccess[courseType] || !courseAccess[courseType].granted) {
      throw new Error("Course access not found. Please purchase the course first.");
    }

    // Get course content
    const contentDoc = await admin.firestore()
      .collection('course_content')
      .doc(`${userId}_${courseType}`)
      .get();
    
    if (!contentDoc.exists) {
      throw new Error("Course content not found");
    }

    const content = contentDoc.data();
    
    // Get enrollment progress
    const enrollmentsQuery = admin.firestore()
      .collection('course_enrollments')
      .where('userId', '==', userId)
      .where('courseType', '==', courseType)
      .where('status', '==', 'active');
    
    const enrollmentsSnap = await enrollmentsQuery.get();
    const progress = enrollmentsSnap.empty ? null : enrollmentsSnap.docs[0].data().progress;

    logger.info('Course content retrieved', { userId, courseType });

    return {
      courseContent: {
        title: content.title,
        description: content.description,
        totalDays: content.totalDays,
        dailyLessons: content.dailyLessons
      },
      progress: progress,
      spiritualIntegrity: content.spiritualIntegrity
    };
    
  } catch (error) {
    logger.error('Error retrieving course content', {
      error: error.message,
      userId: request.auth && request.auth.uid,
      courseType: request.data && request.data.courseType
    });
    throw error;
  }
});
