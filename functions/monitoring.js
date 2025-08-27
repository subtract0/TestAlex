const functions = require("firebase-functions/v2");
const { onRequest } = require("firebase-functions/v2/https");
const { onSchedule } = require("firebase-functions/v2/scheduler");
const { initializeApp } = require("firebase-admin/app");
const { getFirestore } = require("firebase-admin/firestore");
const { logger } = require("firebase-functions");
const https = require("https");

// Initialize Firebase Admin
const app = initializeApp();
const db = getFirestore(app);

/**
 * Health Check Endpoint for Load Balancers/Uptime Monitoring
 */
exports.healthcheck = onRequest(
  {
    cors: true,
    timeoutSeconds: 30
  },
  async (req, res) => {
    const startTime = Date.now();
    const checks = [];
    
    try {
      // Database connectivity check
      const dbCheck = await db.collection("health").doc("test").get();
      checks.push({
        service: "firestore",
        status: "healthy",
        responseTime: Date.now() - startTime
      });
    } catch (error) {
      checks.push({
        service: "firestore",
        status: "unhealthy",
        error: error.message
      });
    }

    // OpenAI API check
    try {
      const response = await makeHttpRequest("https://api.openai.com/v1/models", {
        headers: {
          "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`,
          "Content-Type": "application/json"
        }
      });
      
      checks.push({
        service: "openai",
        status: response.statusCode === 200 ? "healthy" : "unhealthy",
        responseTime: Date.now() - startTime
      });
    } catch (error) {
      checks.push({
        service: "openai",
        status: "unhealthy",
        error: error.message
      });
    }

    const overallHealth = checks.every(check => check.status === "healthy");
    const responseTime = Date.now() - startTime;
    
    const healthStatus = {
      status: overallHealth ? "healthy" : "unhealthy",
      timestamp: new Date().toISOString(),
      responseTime: `${responseTime}ms`,
      services: checks,
      environment: process.env.NODE_ENV || "production",
      version: process.env.APP_VERSION || "1.0.0"
    };

    // Log health status
    logger.info("Health check completed", {
      status: healthStatus.status,
      responseTime: healthStatus.responseTime,
      services: checks.length
    });

    res.status(overallHealth ? 200 : 503).json(healthStatus);
  }
);

/**
 * Scheduled Health Monitoring (runs every 5 minutes)
 */
exports.scheduledHealthCheck = onSchedule(
  {
    schedule: "every 5 minutes",
    timeZone: "UTC",
    retryConfig: {
      retryCount: 3,
      maxRetryDuration: "60s"
    }
  },
  async (event) => {
    logger.info("Starting scheduled health check");
    
    try {
      const healthData = await performHealthCheck();
      
      // Store health metrics
      await db.collection("monitoring").doc("health").collection("checks")
        .doc(new Date().toISOString()).set({
          ...healthData,
          timestamp: new Date(),
          type: "scheduled"
        });

      // Check if we need to send alerts
      if (healthData.status === "unhealthy") {
        await sendHealthAlert(healthData);
      }

      logger.info("Scheduled health check completed", {
        status: healthData.status,
        services: healthData.services.length
      });

    } catch (error) {
      logger.error("Scheduled health check failed", error);
      
      // Send critical alert
      await sendCriticalAlert({
        message: "Health check system failure",
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
);

/**
 * API Usage and Cost Monitoring
 */
exports.monitorApiUsage = onRequest(
  {
    cors: true,
    timeoutSeconds: 30
  },
  async (req, res) => {
    try {
      const today = new Date();
      const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      
      // Get usage data from Firestore
      const usageSnapshot = await db.collection("usage")
        .where("timestamp", ">=", startOfMonth)
        .orderBy("timestamp", "desc")
        .get();

      let totalTokens = 0;
      let totalCost = 0;
      let requestCount = 0;

      usageSnapshot.forEach(doc => {
        const data = doc.data();
        totalTokens += data.tokens || 0;
        totalCost += data.cost || 0;
        requestCount += 1;
      });

      const budgetLimit = parseFloat(process.env.MONTHLY_BUDGET_EUR || 500);
      const utilizationPercent = (totalCost / budgetLimit) * 100;

      const usage = {
        period: {
          start: startOfMonth.toISOString(),
          end: today.toISOString()
        },
        metrics: {
          totalRequests: requestCount,
          totalTokens,
          totalCost: totalCost.toFixed(2),
          budgetLimit: budgetLimit.toFixed(2),
          utilizationPercent: utilizationPercent.toFixed(1),
          averageCostPerRequest: requestCount > 0 ? (totalCost / requestCount).toFixed(4) : 0
        },
        alerts: {
          budgetWarning: utilizationPercent > 70,
          budgetCritical: utilizationPercent > 90,
          highUsage: requestCount > 1000
        }
      };

      // Log usage metrics
      logger.info("API usage monitored", {
        totalCost,
        utilizationPercent: utilizationPercent.toFixed(1),
        requests: requestCount
      });

      res.json(usage);

    } catch (error) {
      logger.error("API usage monitoring failed", error);
      res.status(500).json({
        error: "Failed to retrieve usage metrics",
        message: error.message
      });
    }
  }
);

/**
 * Performance Metrics Collection
 */
exports.collectMetrics = onRequest(
  {
    cors: true,
    timeoutSeconds: 15
  },
  async (req, res) => {
    try {
      const metrics = {
        timestamp: new Date().toISOString(),
        memory: process.memoryUsage(),
        uptime: process.uptime(),
        platform: process.platform,
        nodeVersion: process.version,
        cpuUsage: process.cpuUsage()
      };

      // Store metrics in Firestore
      await db.collection("monitoring").doc("metrics").collection("performance")
        .add(metrics);

      logger.info("Performance metrics collected", {
        memoryMB: Math.round(metrics.memory.heapUsed / 1024 / 1024),
        uptimeHours: Math.round(metrics.uptime / 3600)
      });

      res.json({
        status: "success",
        metrics: {
          memoryUsageMB: Math.round(metrics.memory.heapUsed / 1024 / 1024),
          uptimeHours: Math.round(metrics.uptime / 3600),
          timestamp: metrics.timestamp
        }
      });

    } catch (error) {
      logger.error("Metrics collection failed", error);
      res.status(500).json({
        error: "Failed to collect metrics",
        message: error.message
      });
    }
  }
);

// Helper Functions
async function performHealthCheck() {
  const checks = [];
  
  // Check Firestore
  try {
    await db.collection("health").doc("test").get();
    checks.push({ service: "firestore", status: "healthy" });
  } catch (error) {
    checks.push({ service: "firestore", status: "unhealthy", error: error.message });
  }

  // Check OpenAI
  try {
    const response = await makeHttpRequest("https://api.openai.com/v1/models");
    checks.push({ 
      service: "openai", 
      status: response.statusCode === 200 ? "healthy" : "unhealthy" 
    });
  } catch (error) {
    checks.push({ service: "openai", status: "unhealthy", error: error.message });
  }

  return {
    status: checks.every(check => check.status === "healthy") ? "healthy" : "unhealthy",
    services: checks,
    timestamp: new Date().toISOString()
  };
}

async function sendHealthAlert(healthData) {
  // Implementation depends on your preferred notification channel
  // This could be email, Slack, Discord, etc.
  logger.warn("Health alert triggered", healthData);
  
  // Store alert in database
  await db.collection("alerts").add({
    type: "health",
    severity: "warning",
    data: healthData,
    timestamp: new Date()
  });
}

async function sendCriticalAlert(alertData) {
  logger.error("Critical alert triggered", alertData);
  
  await db.collection("alerts").add({
    type: "critical",
    severity: "critical",
    data: alertData,
    timestamp: new Date()
  });
}

function makeHttpRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const request = https.request(url, options, (response) => {
      let data = "";
      response.on("data", chunk => data += chunk);
      response.on("end", () => resolve({
        statusCode: response.statusCode,
        data
      }));
    });
    
    request.on("error", reject);
    request.setTimeout(10000, () => {
      request.destroy();
      reject(new Error("Request timeout"));
    });
    
    request.end();
  });
}
