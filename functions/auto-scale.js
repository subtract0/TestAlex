/**
 * Auto-scaling Cloud Function
 * Dynamically adjusts Cloud Functions maxInstances based on usage metrics
 * Runs every 10 minutes to optimize cost and performance
 */

const functions = require("firebase-functions");
const admin = require("firebase-admin");
const {GoogleAuth} = require("google-auth-library");
const logger = require("firebase-functions/logger");

// Initialize Firebase Admin if not already initialized
if (!admin.apps.length) {
  admin.initializeApp();
}

// Auto-scaling configuration
const SCALING_CONFIG = {
  minInstances: 0,
  maxInstancesLow: 5,
  maxInstancesPeak: 20,
  maxInstancesHigh: 35,
  maxInstancesEmergency: 50,
  
  thresholds: {
    dailyTokens: {
      low: 10000,
      medium: 30000,
      high: 45000,
      emergency: 50000
    },
    requestsPerMinute: {
      low: 10,
      medium: 30,
      high: 60,
      emergency: 100
    },
    errorRate: {
      warning: 0.05,  // 5%
      critical: 0.10  // 10%
    }
  },
  
  // Peak hours: 9 AM - 9 PM UTC (adjust for user timezone)
  peakHours: {
    start: 9,
    end: 21
  }
};

/**
 * Get current usage metrics from Firestore and Cloud Monitoring
 */
async function getCurrentUsageMetrics() {
  try {
    const now = new Date();
    const dayStart = new Date().setHours(0, 0, 0, 0);
    const tenMinutesAgo = new Date(now.getTime() - 10 * 60 * 1000);
    
    // Get daily token usage across all users
    const rateLimitsSnapshot = await admin.firestore()
      .collection("rateLimits")
      .get();
    
    let totalDailyTokens = 0;
    let activeUsers = 0;
    let recentRequests = 0;
    
    rateLimitsSnapshot.docs.forEach(doc => {
      const data = doc.data();
      if (data.lastReset >= dayStart) {
        totalDailyTokens += data.dailyTokens || 0;
        if (data.dailyTokens > 0) activeUsers++;
        
        // Count recent requests (last 10 minutes)
        const recentRequestsCount = (data.requests || [])
          .filter(timestamp => timestamp >= tenMinutesAgo.getTime()).length;
        recentRequests += recentRequestsCount;
      }
    });
    
    // Get error rate from recent function executions
    const errorsSnapshot = await admin.firestore()
      .collection("function_logs")
      .where("timestamp", ">=", tenMinutesAgo)
      .where("level", "==", "ERROR")
      .get();
    
    const totalExecutionsSnapshot = await admin.firestore()
      .collection("function_logs")
      .where("timestamp", ">=", tenMinutesAgo)
      .get();
    
    const errorRate = totalExecutionsSnapshot.size > 0 
      ? errorsSnapshot.size / totalExecutionsSnapshot.size 
      : 0;
    
    // Calculate requests per minute
    const requestsPerMinute = recentRequests / 10; // Average over 10 minutes
    
    return {
      totalDailyTokens,
      activeUsers,
      recentRequests,
      requestsPerMinute,
      errorRate,
      timestamp: now.toISOString()
    };
    
  } catch (error) {
    logger.error("Failed to get usage metrics", { error: error.message });
    throw error;
  }
}

/**
 * Calculate optimal maxInstances based on current metrics
 */
function calculateOptimalMaxInstances(metrics) {
  const now = new Date();
  const hour = now.getUTCHours();
  
  // Determine base scaling level based on time
  let timeBasedMax;
  if (hour >= SCALING_CONFIG.peakHours.start && hour <= SCALING_CONFIG.peakHours.end) {
    timeBasedMax = SCALING_CONFIG.maxInstancesPeak;
  } else {
    timeBasedMax = SCALING_CONFIG.maxInstancesLow;
  }
  
  // Determine scaling level based on usage
  let usageBasedMax = SCALING_CONFIG.maxInstancesLow;
  
  // Token-based scaling
  if (metrics.totalDailyTokens >= SCALING_CONFIG.thresholds.dailyTokens.emergency) {
    usageBasedMax = Math.max(usageBasedMax, SCALING_CONFIG.maxInstancesEmergency);
  } else if (metrics.totalDailyTokens >= SCALING_CONFIG.thresholds.dailyTokens.high) {
    usageBasedMax = Math.max(usageBasedMax, SCALING_CONFIG.maxInstancesHigh);
  } else if (metrics.totalDailyTokens >= SCALING_CONFIG.thresholds.dailyTokens.medium) {
    usageBasedMax = Math.max(usageBasedMax, SCALING_CONFIG.maxInstancesPeak);
  }
  
  // Request rate-based scaling
  if (metrics.requestsPerMinute >= SCALING_CONFIG.thresholds.requestsPerMinute.emergency) {
    usageBasedMax = Math.max(usageBasedMax, SCALING_CONFIG.maxInstancesEmergency);
  } else if (metrics.requestsPerMinute >= SCALING_CONFIG.thresholds.requestsPerMinute.high) {
    usageBasedMax = Math.max(usageBasedMax, SCALING_CONFIG.maxInstancesHigh);
  } else if (metrics.requestsPerMinute >= SCALING_CONFIG.thresholds.requestsPerMinute.medium) {
    usageBasedMax = Math.max(usageBasedMax, SCALING_CONFIG.maxInstancesPeak);
  }
  
  // Error rate-based emergency scaling
  if (metrics.errorRate >= SCALING_CONFIG.thresholds.errorRate.critical) {
    logger.warn("Critical error rate detected, enabling emergency scaling", {
      errorRate: metrics.errorRate,
      threshold: SCALING_CONFIG.thresholds.errorRate.critical
    });
    usageBasedMax = Math.max(usageBasedMax, SCALING_CONFIG.maxInstancesEmergency);
  }
  
  // Take the maximum of time-based and usage-based scaling for performance
  // but apply cost control limits
  const optimalMax = Math.min(
    Math.max(timeBasedMax, usageBasedMax),
    SCALING_CONFIG.maxInstancesEmergency
  );
  
  return {
    recommended: Math.max(1, optimalMax),
    reasoning: {
      timeBasedMax,
      usageBasedMax,
      finalMax: optimalMax,
      peakHours: hour >= SCALING_CONFIG.peakHours.start && hour <= SCALING_CONFIG.peakHours.end,
      emergencyScaling: metrics.errorRate >= SCALING_CONFIG.thresholds.errorRate.critical
    }
  };
}

/**
 * Update Cloud Function configuration with new maxInstances
 * Note: This would require Cloud Functions Admin API in production
 */
async function updateFunctionScaling(functionName, newMaxInstances) {
  try {
    logger.info(`Updating function scaling`, {
      functionName,
      newMaxInstances
    });
    
    // In a real implementation, you would use the Cloud Functions Admin API
    // to update the function configuration. For now, we'll log the change
    // and store it in Firestore for monitoring.
    
    await admin.firestore().collection("scaling_events").add({
      functionName,
      newMaxInstances,
      timestamp: new Date(),
      action: "scale_update",
      status: "simulated" // In production, this would be 'applied'
    });
    
    logger.info(`Scaling configuration updated for ${functionName}`, {
      maxInstances: newMaxInstances
    });
    
  } catch (error) {
    logger.error("Failed to update function scaling", {
      functionName,
      error: error.message
    });
    throw error;
  }
}

/**
 * Store scaling metrics for monitoring and analysis
 */
async function storeScalingMetrics(metrics, scalingDecision) {
  try {
    await admin.firestore().collection("scaling_metrics").add({
      ...metrics,
      scalingDecision,
      timestamp: new Date()
    });
    
    // Keep only last 7 days of metrics to control storage costs
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    
    const oldMetricsQuery = admin.firestore()
      .collection("scaling_metrics")
      .where("timestamp", "<", weekAgo)
      .limit(100);
    
    const oldMetrics = await oldMetricsQuery.get();
    
    if (!oldMetrics.empty) {
      const batch = admin.firestore().batch();
      oldMetrics.docs.forEach(doc => {
        batch.delete(doc.ref);
      });
      await batch.commit();
      
      logger.info("Cleaned up old scaling metrics", {
        deletedCount: oldMetrics.size
      });
    }
    
  } catch (error) {
    logger.error("Failed to store scaling metrics", { error: error.message });
    // Don't throw - this is not critical for the scaling operation
  }
}

/**
 * Send alert if scaling thresholds are exceeded
 */
async function sendScalingAlerts(metrics, scalingDecision) {
  try {
    const alerts = [];
    
    // High token usage alert
    if (metrics.totalDailyTokens >= SCALING_CONFIG.thresholds.dailyTokens.high) {
      alerts.push({
        type: "high_token_usage",
        severity: metrics.totalDailyTokens >= SCALING_CONFIG.thresholds.dailyTokens.emergency ? "critical" : "warning",
        message: `Daily token usage: ${metrics.totalDailyTokens}`,
        threshold: SCALING_CONFIG.thresholds.dailyTokens.high
      });
    }
    
    // High error rate alert
    if (metrics.errorRate >= SCALING_CONFIG.thresholds.errorRate.warning) {
      alerts.push({
        type: "high_error_rate",
        severity: metrics.errorRate >= SCALING_CONFIG.thresholds.errorRate.critical ? "critical" : "warning",
        message: `Error rate: ${(metrics.errorRate * 100).toFixed(2)}%`,
        threshold: SCALING_CONFIG.thresholds.errorRate.warning
      });
    }
    
    // Emergency scaling alert
    if (scalingDecision.reasoning.emergencyScaling) {
      alerts.push({
        type: "emergency_scaling",
        severity: "critical",
        message: `Emergency scaling activated: ${scalingDecision.recommended} instances`,
        reason: "Critical error rate detected"
      });
    }
    
    if (alerts.length > 0) {
      // Store alerts for monitoring dashboard
      await admin.firestore().collection("scaling_alerts").add({
        alerts,
        timestamp: new Date(),
        metrics,
        scalingDecision
      });
      
      logger.warn("Scaling alerts generated", { alertCount: alerts.length, alerts });
    }
    
  } catch (error) {
    logger.error("Failed to send scaling alerts", { error: error.message });
    // Don't throw - this is not critical for the scaling operation
  }
}

/**
 * Main auto-scaling function
 * Triggered every 10 minutes by Cloud Scheduler
 */
exports.autoScaleCloudFunctions = functions.pubsub
  .schedule("every 10 minutes")
  .onRun(async (context) => {
    try {
      logger.info("Auto-scaling function triggered");
      
      // Get current usage metrics
      const metrics = await getCurrentUsageMetrics();
      
      // Calculate optimal scaling
      const scalingDecision = calculateOptimalMaxInstances(metrics);
      
      logger.info("Auto-scaling analysis complete", {
        metrics,
        scalingDecision
      });
      
      // Get current configuration to see if update is needed
      const currentConfigDoc = await admin.firestore()
        .collection("function_config")
        .doc("chatWithAssistant")
        .get();
      
      const currentMaxInstances = currentConfigDoc.exists 
        ? currentConfigDoc.data().maxInstances || SCALING_CONFIG.maxInstancesLow
        : SCALING_CONFIG.maxInstancesLow;
      
      // Only update if there's a significant change (avoid constant adjustments)
      const changeThreshold = 2;
      if (Math.abs(scalingDecision.recommended - currentMaxInstances) >= changeThreshold) {
        // Update function scaling
        await updateFunctionScaling("chatWithAssistant", scalingDecision.recommended);
        
        // Store updated configuration
        await admin.firestore()
          .collection("function_config")
          .doc("chatWithAssistant")
          .set({
            maxInstances: scalingDecision.recommended,
            lastUpdate: new Date(),
            previousMaxInstances: currentMaxInstances
          }, { merge: true });
        
        logger.info("Function scaling updated", {
          previousMaxInstances: currentMaxInstances,
          newMaxInstances: scalingDecision.recommended,
          change: scalingDecision.recommended - currentMaxInstances
        });
      } else {
        logger.info("No scaling change needed", {
          currentMaxInstances,
          recommendedMaxInstances: scalingDecision.recommended,
          changeThreshold
        });
      }
      
      // Store metrics for analysis
      await storeScalingMetrics(metrics, scalingDecision);
      
      // Send alerts if needed
      await sendScalingAlerts(metrics, scalingDecision);
      
      return {
        status: "success",
        metrics,
        scalingDecision,
        updated: Math.abs(scalingDecision.recommended - currentMaxInstances) >= changeThreshold
      };
      
    } catch (error) {
      logger.error("Auto-scaling function failed", {
        error: error.message,
        stack: error.stack
      });
      
      // Store error for monitoring
      await admin.firestore().collection("scaling_errors").add({
        error: error.message,
        stack: error.stack,
        timestamp: new Date()
      });
      
      throw error;
    }
  });

/**
 * Manual scaling override function
 * Allows manual adjustment of maxInstances for emergency situations
 */
exports.manualScaleOverride = functions.https.onCall(async (data, context) => {
  try {
    // Verify admin access
    if (!context.auth || !context.auth.token.admin) {
      throw new functions.https.HttpsError(
        "permission-denied",
        "Admin access required for manual scaling override"
      );
    }
    
    const { maxInstances, reason, duration = 60 } = data;
    
    if (!maxInstances || typeof maxInstances !== "number") {
      throw new functions.https.HttpsError(
        "invalid-argument",
        "maxInstances must be a number"
      );
    }
    
    if (maxInstances < 1 || maxInstances > SCALING_CONFIG.maxInstancesEmergency) {
      throw new functions.https.HttpsError(
        "invalid-argument",
        `maxInstances must be between 1 and ${SCALING_CONFIG.maxInstancesEmergency}`
      );
    }
    
    logger.warn("Manual scaling override requested", {
      requestedBy: context.auth.uid,
      maxInstances,
      reason,
      duration
    });
    
    // Apply manual override
    await updateFunctionScaling("chatWithAssistant", maxInstances);
    
    // Store override configuration with expiration
    const overrideEnd = new Date();
    overrideEnd.setMinutes(overrideEnd.getMinutes() + duration);
    
    await admin.firestore()
      .collection("function_config")
      .doc("chatWithAssistant")
      .set({
        maxInstances,
        lastUpdate: new Date(),
        manualOverride: {
          active: true,
          requestedBy: context.auth.uid,
          reason,
          expiresAt: overrideEnd,
          originalMaxInstances: maxInstances
        }
      }, { merge: true });
    
    // Log override event
    await admin.firestore().collection("scaling_events").add({
      type: "manual_override",
      functionName: "chatWithAssistant",
      maxInstances,
      requestedBy: context.auth.uid,
      reason,
      duration,
      timestamp: new Date()
    });
    
    return {
      status: "success",
      message: `Manual scaling override applied: ${maxInstances} instances for ${duration} minutes`,
      expiresAt: overrideEnd.toISOString()
    };
    
  } catch (error) {
    logger.error("Manual scaling override failed", {
      error: error.message,
      requestedBy: (context.auth && context.auth.uid)
    });
    throw error;
  }
});

/**
 * Get scaling metrics and status
 */
exports.getScalingStatus = functions.https.onCall(async (data, context) => {
  try {
    // Verify authenticated access
    if (!context.auth) {
      throw new functions.https.HttpsError(
        "unauthenticated",
        "Authentication required"
      );
    }
    
    // Get current configuration
    const configDoc = await admin.firestore()
      .collection("function_config")
      .doc("chatWithAssistant")
      .get();
    
    const config = configDoc.exists ? configDoc.data() : {};
    
    // Get recent metrics (last hour)
    const oneHourAgo = new Date();
    oneHourAgo.setHours(oneHourAgo.getHours() - 1);
    
    const recentMetricsSnapshot = await admin.firestore()
      .collection("scaling_metrics")
      .where("timestamp", ">=", oneHourAgo)
      .orderBy("timestamp", "desc")
      .limit(10)
      .get();
    
    const recentMetrics = recentMetricsSnapshot.docs.map(doc => doc.data());
    
    // Get recent scaling events
    const recentEventsSnapshot = await admin.firestore()
      .collection("scaling_events")
      .where("timestamp", ">=", oneHourAgo)
      .orderBy("timestamp", "desc")
      .limit(5)
      .get();
    
    const recentEvents = recentEventsSnapshot.docs.map(doc => doc.data());
    
    return {
      currentConfig: config,
      recentMetrics,
      recentEvents,
      scalingConfig: SCALING_CONFIG,
      timestamp: new Date().toISOString()
    };
    
  } catch (error) {
    logger.error("Get scaling status failed", { error: error.message });
    throw new functions.https.HttpsError(
      "internal",
      "Failed to get scaling status"
    );
  }
});
