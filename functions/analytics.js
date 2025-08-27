const functions = require("firebase-functions/v2");
const { onCall, onRequest } = require("firebase-functions/v2/https");
const { onSchedule } = require("firebase-functions/v2/scheduler");
const { initializeApp } = require("firebase-admin/app");
const { getFirestore, FieldValue } = require("firebase-admin/firestore");
const { logger } = require("firebase-functions");

// Initialize Firebase Admin
const app = initializeApp();
const db = getFirestore(app);

/**
 * User Behavior Analytics
 */
exports.trackUserInteraction = onCall(
  {
    cors: true,
    timeoutSeconds: 15
  },
  async (request) => {
    const { data, auth } = request;
    
    if (!auth) {
      throw new functions.https.HttpsError("unauthenticated", "User must be authenticated");
    }

    const { 
      action, 
      category, 
      label = "", 
      value = 1,
      metadata = {} 
    } = data;

    const interaction = {
      userId: auth.uid,
      action,
      category,
      label,
      value,
      metadata: {
        ...metadata,
        timestamp: new Date(),
        sessionId: metadata.sessionId || generateSessionId(),
        userAgent: (request.headers && request.headers["user-agent"]) || "unknown",
        platform: metadata.platform || "unknown"
      }
    };

    try {
      // Store individual interaction
      await db.collection("analytics").doc("interactions").collection("events").add(interaction);
      
      // Update aggregated stats
      await updateUserStats(auth.uid, action, category, value);
      
      logger.info("User interaction tracked", {
        userId: auth.uid,
        action,
        category
      });

      return { success: true, timestamp: interaction.metadata.timestamp };
      
    } catch (error) {
      logger.error("Failed to track interaction", error);
      throw new functions.https.HttpsError("internal", "Failed to track interaction");
    }
  }
);

/**
 * Advanced User Journey Analysis
 */
exports.analyzeUserJourney = onCall(
  {
    cors: true,
    timeoutSeconds: 30
  },
  async (request) => {
    const { data, auth } = request;
    
    if (!auth) {
      throw new functions.https.HttpsError("unauthenticated", "User must be authenticated");
    }

    const { timeframe = "30d", includePatterns = true } = data;

    try {
      const endDate = new Date();
      const startDate = new Date();
      
      // Calculate start date based on timeframe
      switch (timeframe) {
      case "7d":
        startDate.setDate(endDate.getDate() - 7);
        break;
      case "30d":
        startDate.setDate(endDate.getDate() - 30);
        break;
      case "90d":
        startDate.setDate(endDate.getDate() - 90);
        break;
      default:
        startDate.setDate(endDate.getDate() - 30);
      }

      // Get user interactions
      const interactionsSnapshot = await db
        .collection("analytics")
        .doc("interactions")
        .collection("events")
        .where("userId", "==", auth.uid)
        .where("metadata.timestamp", ">=", startDate)
        .where("metadata.timestamp", "<=", endDate)
        .orderBy("metadata.timestamp", "asc")
        .get();

      const interactions = interactionsSnapshot.docs.map(doc => doc.data());

      // Analyze patterns
      const analysis = {
        totalInteractions: interactions.length,
        uniqueSessions: new Set(interactions.map(i => i.metadata.sessionId)).size,
        categories: analyzeCategories(interactions),
        timePatterns: analyzeTimePatterns(interactions),
        journey: buildUserJourney(interactions),
        insights: generateInsights(interactions)
      };

      if (includePatterns) {
        analysis.behaviorPatterns = identifyBehaviorPatterns(interactions);
        analysis.recommendations = generateRecommendations(analysis);
      }

      logger.info("User journey analyzed", {
        userId: auth.uid,
        timeframe,
        totalInteractions: analysis.totalInteractions
      });

      return analysis;

    } catch (error) {
      logger.error("Failed to analyze user journey", error);
      throw new functions.https.HttpsError("internal", "Analysis failed");
    }
  }
);

/**
 * Content Effectiveness Analytics
 */
exports.getContentAnalytics = onCall(
  {
    cors: true,
    timeoutSeconds: 20
  },
  async (request) => {
    const { auth } = request;
    
    if (!auth) {
      throw new functions.https.HttpsError("unauthenticated", "User must be authenticated");
    }

    try {
      // Get user's content interactions
      const contentSnapshot = await db
        .collection("analytics")
        .doc("content")
        .collection("effectiveness")
        .where("userId", "==", auth.uid)
        .get();

      const contentData = contentSnapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));

      const analytics = {
        mostEngagingTopics: findTopTopics(contentData, "engagement"),
        mostHelpfulResponses: findTopResponses(contentData, "helpfulness"),
        contentPreferences: analyzeContentPreferences(contentData),
        improvementAreas: identifyImprovementAreas(contentData),
        personalizedRecommendations: generatePersonalizedContent(auth.uid, contentData)
      };

      return analytics;

    } catch (error) {
      logger.error("Failed to get content analytics", error);
      throw new functions.https.HttpsError("internal", "Content analytics failed");
    }
  }
);

/**
 * Real-time Usage Dashboard
 */
exports.getDashboardData = onRequest(
  {
    cors: true,
    timeoutSeconds: 25
  },
  async (req, res) => {
    try {
      const timeframe = req.query.timeframe || "24h";
      const endDate = new Date();
      const startDate = new Date();
      
      switch (timeframe) {
      case "1h":
        startDate.setHours(endDate.getHours() - 1);
        break;
      case "24h":
        startDate.setDate(endDate.getDate() - 1);
        break;
      case "7d":
        startDate.setDate(endDate.getDate() - 7);
        break;
      default:
        startDate.setDate(endDate.getDate() - 1);
      }

      // Get aggregated metrics
      const [
        activeUsers,
        totalInteractions,
        averageSessionDuration,
        topCategories,
        systemHealth
      ] = await Promise.all([
        getActiveUsers(startDate, endDate),
        getTotalInteractions(startDate, endDate),
        getAverageSessionDuration(startDate, endDate),
        getTopCategories(startDate, endDate),
        getSystemHealthMetrics()
      ]);

      const dashboard = {
        timeframe,
        period: {
          start: startDate.toISOString(),
          end: endDate.toISOString()
        },
        metrics: {
          activeUsers,
          totalInteractions,
          averageSessionDuration,
          topCategories
        },
        systemHealth,
        lastUpdated: new Date().toISOString()
      };

      res.json(dashboard);

    } catch (error) {
      logger.error("Dashboard data retrieval failed", error);
      res.status(500).json({
        error: "Failed to retrieve dashboard data",
        message: error.message
      });
    }
  }
);

/**
 * Scheduled Analytics Processing (runs daily)
 */
exports.processAnalytics = onSchedule(
  {
    schedule: "0 2 * * *", // Daily at 2 AM
    timeZone: "UTC"
  },
  async () => {
    logger.info("Starting daily analytics processing");

    try {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      yesterday.setHours(0, 0, 0, 0);

      const today = new Date(yesterday);
      today.setDate(today.getDate() + 1);

      // Process analytics for yesterday
      await Promise.all([
        aggregateDailyStats(yesterday, today),
        updateUserSegments(),
        generateInsightReports(yesterday),
        cleanupOldData()
      ]);

      logger.info("Daily analytics processing completed");

    } catch (error) {
      logger.error("Analytics processing failed", error);
    }
  }
);

// Helper Functions
async function updateUserStats(userId, action, category, value) {
  const statsRef = db.collection("userStats").doc(userId);
  
  await statsRef.set({
    [`actions.${action}`]: FieldValue.increment(value),
    [`categories.${category}`]: FieldValue.increment(value),
    totalInteractions: FieldValue.increment(value),
    lastActivity: new Date(),
    updatedAt: new Date()
  }, { merge: true });
}

function analyzeCategories(interactions) {
  const categories = {};
  interactions.forEach(interaction => {
    categories[interaction.category] = (categories[interaction.category] || 0) + 1;
  });
  
  return Object.entries(categories)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 10)
    .map(([category, count]) => ({ category, count }));
}

function analyzeTimePatterns(interactions) {
  const hourly = new Array(24).fill(0);
  const daily = {};
  
  interactions.forEach(interaction => {
    const date = new Date(interaction.metadata.timestamp);
    const hour = date.getHours();
    const day = date.getDay();
    
    hourly[hour]++;
    daily[day] = (daily[day] || 0) + 1;
  });
  
  return {
    hourlyDistribution: hourly,
    dailyDistribution: daily,
    peakHour: hourly.indexOf(Math.max(...hourly)),
    peakDay: Object.keys(daily).reduce((a, b) => daily[a] > daily[b] ? a : b)
  };
}

function buildUserJourney(interactions) {
  const sessions = {};
  
  // Group by session
  interactions.forEach(interaction => {
    const sessionId = interaction.metadata.sessionId;
    if (!sessions[sessionId]) {
      sessions[sessionId] = [];
    }
    sessions[sessionId].push(interaction);
  });
  
  // Analyze journey patterns
  const journeySteps = [];
  Object.values(sessions).forEach(session => {
    const steps = session.map(i => ({
      action: i.action,
      category: i.category,
      timestamp: i.metadata.timestamp
    }));
    journeySteps.push(steps);
  });
  
  return {
    totalSessions: Object.keys(sessions).length,
    averageStepsPerSession: journeySteps.reduce((sum, steps) => sum + steps.length, 0) / journeySteps.length,
    commonPaths: identifyCommonPaths(journeySteps)
  };
}

function generateInsights(interactions) {
  const insights = [];
  
  if (interactions.length > 0) {
    const lastWeek = interactions.filter(i => 
      new Date(i.metadata.timestamp) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    );
    
    if (lastWeek.length > interactions.length * 0.5) {
      insights.push({
        type: "engagement",
        message: "Your engagement has increased significantly this week!",
        confidence: 0.8
      });
    }
    
    // Add more insights based on patterns...
  }
  
  return insights;
}

function identifyBehaviorPatterns() {
  // Implement ML-based pattern recognition
  return {
    sessionLength: "medium", // short, medium, long
    preferredTime: "evening", // morning, afternoon, evening
    interactionStyle: "exploratory", // focused, exploratory, casual
    contentPreference: "spiritual guidance" // spiritual guidance, practical advice, community
  };
}

function generateRecommendations(analysis) {
  const recommendations = [];
  
  // Based on behavior patterns
  if (analysis.behaviorPatterns && analysis.behaviorPatterns.interactionStyle === "exploratory") {
    recommendations.push({
      type: "content",
      message: "Try exploring the guided meditation series",
      priority: "high"
    });
  }
  
  return recommendations;
}

function generateSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).substring(7)}`;
}

// Placeholder functions for dashboard metrics
async function getActiveUsers() {
  return Math.floor(Math.random() * 100) + 50; // Placeholder
}

async function getTotalInteractions() {
  return Math.floor(Math.random() * 1000) + 500; // Placeholder
}

async function getAverageSessionDuration() {
  return Math.floor(Math.random() * 600) + 300; // 5-15 minutes
}

async function getTopCategories() {
  return [
    { category: "spiritual_guidance", count: 245 },
    { category: "meditation", count: 189 },
    { category: "forgiveness", count: 156 }
  ];
}

async function getSystemHealthMetrics() {
  return {
    status: "healthy",
    uptime: "99.9%",
    responseTime: "150ms"
  };
}

// Missing function implementations for ESLint compliance
function findTopTopics(contentData, metric) {
  // Placeholder implementation - analyze content engagement
  return contentData
    .filter(item => item[metric] > 0)
    .sort((a, b) => b[metric] - a[metric])
    .slice(0, 5)
    .map(item => ({ topic: item.topic || "General", score: item[metric] }));
}

function findTopResponses(contentData, metric) {
  // Placeholder implementation - find most helpful responses
  return contentData
    .filter(item => item[metric] > 0.7)
    .sort((a, b) => b[metric] - a[metric])
    .slice(0, 3)
    .map(item => ({ response: item.response || "Helpful guidance", score: item[metric] }));
}

function analyzeContentPreferences() {
  // Placeholder implementation - analyze content preferences
  const preferences = {
    preferredTopics: ["forgiveness", "peace", "love"],
    preferredFormat: "conversational",
    engagementLevel: "high"
  };
  return preferences;
}

function identifyImprovementAreas() {
  // Placeholder implementation - identify areas for improvement
  return [
    { area: "response_time", priority: "medium", suggestion: "Optimize response generation" },
    { area: "content_depth", priority: "low", suggestion: "Provide more detailed explanations" }
  ];
}

function generatePersonalizedContent(userId) {
  // Placeholder implementation - generate personalized recommendations
  logger.info("Generating personalized content for user", { userId });
  return [
    { type: "lesson", title: "Understanding Forgiveness", priority: "high" },
    { type: "meditation", title: "Peace Meditation", priority: "medium" },
    { type: "reading", title: "Daily Reflection", priority: "low" }
  ];
}

async function aggregateDailyStats(startDate, endDate) {
  // Placeholder implementation - aggregate daily statistics
  logger.info("Aggregating daily stats", { startDate, endDate });
  // Would implement actual aggregation logic here
  return true;
}

async function updateUserSegments() {
  // Placeholder implementation - update user segments
  logger.info("Updating user segments");
  // Would implement actual segmentation logic here
  return true;
}

async function generateInsightReports(date) {
  // Placeholder implementation - generate insight reports
  logger.info("Generating insight reports", { date });
  // Would implement actual report generation here
  return true;
}

async function cleanupOldData() {
  // Placeholder implementation - cleanup old data
  logger.info("Cleaning up old data");
  // Would implement actual cleanup logic here
  return true;
}

function identifyCommonPaths() {
  // Placeholder implementation - identify common user journey paths
  return [
    { path: ["question", "guidance", "reflection"], frequency: 0.45 },
    { path: ["meditation", "peace", "gratitude"], frequency: 0.32 }
  ];
}
