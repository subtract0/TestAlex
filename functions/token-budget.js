/**
 * OpenAI Token Budgeting Micro-service
 * Manages OpenAI API usage to stay under €500/month until revenue scales
 * Implements smart throttling, budget tracking, and cost optimization
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');
const logger = require('firebase-functions/logger');

// Initialize Firebase Admin if not already initialized
if (!admin.apps.length) {
  admin.initializeApp();
}

// Budget configuration
const BUDGET_CONFIG = {
  // Monthly budget in EUR
  monthlyBudgetEUR: 500,
  
  // OpenAI pricing (as of 2024 - adjust as needed)
  pricing: {
    gpt4: {
      inputTokens: 0.03 / 1000,   // €0.03 per 1K input tokens
      outputTokens: 0.06 / 1000   // €0.06 per 1K output tokens
    },
    gpt4_turbo: {
      inputTokens: 0.01 / 1000,   // €0.01 per 1K input tokens  
      outputTokens: 0.03 / 1000   // €0.03 per 1K output tokens
    }
  },
  
  // Budget allocation strategy
  allocation: {
    dailyPercentage: 0.8 / 30,    // 80% of monthly budget over 30 days
    emergencyReserve: 0.15,       // 15% emergency reserve
    userTiers: {
      free: 0.05,     // 5% for free users
      premium: 0.75,  // 75% for premium users  
      admin: 0.20     // 20% for admin/testing
    }
  },
  
  // Throttling thresholds
  throttling: {
    warningThreshold: 0.7,    // 70% of budget
    slowdownThreshold: 0.85,  // 85% of budget - reduce service quality
    emergencyThreshold: 0.95, // 95% of budget - emergency mode
    shutoffThreshold: 1.0     // 100% of budget - stop service
  },
  
  // Cost optimization strategies
  optimization: {
    // Reduce response length when approaching budget limits
    responseLength: {
      normal: 500,      // Normal max tokens
      reduced: 300,     // Reduced when > 70% budget used
      minimal: 150      // Minimal when > 85% budget used
    },
    // Switch to cheaper models when budget is constrained
    modelFallback: {
      normal: 'gpt-5-chat-latest',
      budgetConstrained: 'gpt-4o',
      emergency: 'gpt-4-turbo'
    }
  }
};

/**
 * Get current monthly budget utilization
 */
async function getCurrentBudgetUtilization() {
  try {
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const monthEnd = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    // Get all token usage for current month
    const usageSnapshot = await admin.firestore()
      .collection('token_usage')
      .where('timestamp', '>=', monthStart)
      .where('timestamp', '<=', monthEnd)
      .get();
    
    let totalCostEUR = 0;
    let totalTokensIn = 0;
    let totalTokensOut = 0;
    let requestCount = 0;
    
    usageSnapshot.docs.forEach(doc => {
      const data = doc.data();
      totalCostEUR += data.costEUR || 0;
      totalTokensIn += data.tokensIn || 0;
      totalTokensOut += data.tokensOut || 0;
      requestCount++;
    });
    
    const budgetUtilization = totalCostEUR / BUDGET_CONFIG.monthlyBudgetEUR;
    const remainingBudgetEUR = BUDGET_CONFIG.monthlyBudgetEUR - totalCostEUR;
    
    // Calculate daily burn rate
    const daysInMonth = monthEnd.getDate();
    const currentDay = now.getDate();
    const dailyBurnRate = totalCostEUR / currentDay;
    const projectedMonthlySpend = dailyBurnRate * daysInMonth;
    
    return {
      monthStart: monthStart.toISOString(),
      monthEnd: monthEnd.toISOString(),
      totalCostEUR,
      totalTokensIn,
      totalTokensOut,
      requestCount,
      budgetUtilization,
      remainingBudgetEUR,
      dailyBurnRate,
      projectedMonthlySpend,
      daysInMonth,
      currentDay,
      timestamp: now.toISOString()
    };
    
  } catch (error) {
    logger.error('Failed to get budget utilization', { error: error.message });
    throw error;
  }
}

/**
 * Calculate cost for OpenAI API usage
 */
function calculateOpenAICost(tokensIn, tokensOut, model = 'gpt-5-chat-latest') {
  const pricing = BUDGET_CONFIG.pricing[model] || BUDGET_CONFIG.pricing.gpt4;
  
  const inputCost = (tokensIn / 1000) * pricing.inputTokens;
  const outputCost = (tokensOut / 1000) * pricing.outputTokens;
  const totalCost = inputCost + outputCost;
  
  return {
    inputCostEUR: inputCost,
    outputCostEUR: outputCost,
    totalCostEUR: totalCost,
    model,
    tokensIn,
    tokensOut
  };
}

/**
 * Record token usage and cost
 */
async function recordTokenUsage(userId, tokensIn, tokensOut, model = 'gpt-5-chat-latest', userTier = 'free') {
  try {
    const cost = calculateOpenAICost(tokensIn, tokensOut, model);
    
    const usageRecord = {
      userId,
      tokensIn,
      tokensOut,
      model,
      userTier,
      ...cost,
      timestamp: new Date(),
      month: new Date().getMonth() + 1,
      year: new Date().getFullYear()
    };
    
    // Store in token usage collection
    await admin.firestore().collection('token_usage').add(usageRecord);
    
    // Update user's monthly usage summary
    const userMonthlyRef = admin.firestore()
      .collection('user_monthly_usage')
      .doc(`${userId}_${usageRecord.year}_${usageRecord.month}`);
    
    await admin.firestore().runTransaction(async (transaction) => {
      const doc = await transaction.get(userMonthlyRef);
      const existing = doc.exists ? doc.data() : {
        userId,
        year: usageRecord.year,
        month: usageRecord.month,
        totalCostEUR: 0,
        totalTokensIn: 0,
        totalTokensOut: 0,
        requestCount: 0
      };
      
      existing.totalCostEUR += cost.totalCostEUR;
      existing.totalTokensIn += tokensIn;
      existing.totalTokensOut += tokensOut;
      existing.requestCount += 1;
      existing.lastUpdate = new Date();
      
      transaction.set(userMonthlyRef, existing);
    });
    
    logger.info('Token usage recorded', {
      userId,
      tokensIn,
      tokensOut,
      costEUR: cost.totalCostEUR,
      model
    });
    
    return cost;
    
  } catch (error) {
    logger.error('Failed to record token usage', {
      userId,
      error: error.message
    });
    throw error;
  }
}

/**
 * Determine service level based on budget utilization
 */
function determineServiceLevel(budgetUtilization) {
  if (budgetUtilization >= BUDGET_CONFIG.throttling.shutoffThreshold) {
    return 'shutoff';
  } else if (budgetUtilization >= BUDGET_CONFIG.throttling.emergencyThreshold) {
    return 'emergency';
  } else if (budgetUtilization >= BUDGET_CONFIG.throttling.slowdownThreshold) {
    return 'slowdown';
  } else if (budgetUtilization >= BUDGET_CONFIG.throttling.warningThreshold) {
    return 'warning';
  } else {
    return 'normal';
  }
}

/**
 * Get optimized parameters based on current budget status
 */
function getOptimizedParameters(budgetUtilization, userTier = 'free') {
  const serviceLevel = determineServiceLevel(budgetUtilization);
  
  let maxTokens = BUDGET_CONFIG.optimization.responseLength.normal;
  let model = BUDGET_CONFIG.optimization.modelFallback.normal;
  let enabled = true;
  
  switch (serviceLevel) {
    case 'shutoff':
      enabled = false;
      break;
      
    case 'emergency':
      maxTokens = BUDGET_CONFIG.optimization.responseLength.minimal;
      model = BUDGET_CONFIG.optimization.modelFallback.emergency;
      break;
      
    case 'slowdown':
      maxTokens = BUDGET_CONFIG.optimization.responseLength.reduced;
      model = BUDGET_CONFIG.optimization.modelFallback.budgetConstrained;
      break;
      
    case 'warning':
      if (userTier === 'free') {
        maxTokens = BUDGET_CONFIG.optimization.responseLength.reduced;
        model = BUDGET_CONFIG.optimization.modelFallback.budgetConstrained;
      }
      break;
      
    default: // normal
      // Use default values
      break;
  }
  
  return {
    serviceLevel,
    enabled,
    maxTokens,
    model,
    budgetUtilization,
    userTier
  };
}

/**
 * Check if user can make API request based on budget
 */
exports.checkBudgetAllowance = functions.https.onCall(async (data, context) => {
  try {
    if (!context.auth) {
      throw new functions.https.HttpsError(
        'unauthenticated',
        'Authentication required'
      );
    }
    
    const userId = context.auth.uid;
    const userTier = data.userTier || 'free';
    
    // Get current budget utilization
    const budgetStatus = await getCurrentBudgetUtilization();
    
    // Get optimized parameters
    const parameters = getOptimizedParameters(budgetStatus.budgetUtilization, userTier);
    
    // Check user's monthly usage
    const now = new Date();
    const userMonthlyRef = admin.firestore()
      .collection('user_monthly_usage')
      .doc(`${userId}_${now.getFullYear()}_${now.getMonth() + 1}`);
    
    const userMonthlyDoc = await userMonthlyRef.get();
    const userMonthlyUsage = userMonthlyDoc.exists ? userMonthlyDoc.data() : null;
    
    // Determine if request should be allowed
    let allowed = parameters.enabled;
    let reason = '';\n    \n    if (!allowed) {\n      reason = 'Monthly budget exhausted. Service temporarily unavailable.';\n    } else if (parameters.serviceLevel === 'emergency' && userTier === 'free') {\n      allowed = false;\n      reason = 'Budget constraints: Free tier temporarily limited. Please upgrade or try again later.';\n    }\n    \n    // Log budget check\n    logger.info('Budget allowance check', {\n      userId,\n      userTier,\n      allowed,\n      serviceLevel: parameters.serviceLevel,\n      budgetUtilization: budgetStatus.budgetUtilization,\n      remainingBudgetEUR: budgetStatus.remainingBudgetEUR\n    });\n    \n    return {\n      allowed,\n      reason,\n      serviceLevel: parameters.serviceLevel,\n      maxTokens: parameters.maxTokens,\n      recommendedModel: parameters.model,\n      budgetStatus: {\n        utilization: budgetStatus.budgetUtilization,\n        remainingEUR: budgetStatus.remainingBudgetEUR,\n        projectedSpend: budgetStatus.projectedMonthlySpend\n      },\n      userMonthlyUsage,\n      timestamp: new Date().toISOString()\n    };\n    \n  } catch (error) {\n    logger.error('Budget allowance check failed', {\n      error: error.message,\n      userId: context.auth?.uid\n    });\n    \n    throw new functions.https.HttpsError(\n      'internal',\n      'Failed to check budget allowance'\n    );\n  }\n});\n\n/**\n * Record OpenAI API usage after request completion\n */\nexports.recordApiUsage = functions.https.onCall(async (data, context) => {\n  try {\n    if (!context.auth) {\n      throw new functions.https.HttpsError(\n        'unauthenticated',\n        'Authentication required'\n      );\n    }\n    \n    const {\n      tokensIn,\n      tokensOut,\n      model = 'gpt-4',\n      userTier = 'free',\n      requestDuration,\n      success = true\n    } = data;\n    \n    if (!tokensIn || !tokensOut) {\n      throw new functions.https.HttpsError(\n        'invalid-argument',\n        'tokensIn and tokensOut are required'\n      );\n    }\n    \n    const userId = context.auth.uid;\n    \n    // Record the usage\n    const cost = await recordTokenUsage(userId, tokensIn, tokensOut, model, userTier);\n    \n    // Get updated budget status\n    const budgetStatus = await getCurrentBudgetUtilization();\n    \n    // Send alerts if budget thresholds are crossed\n    await checkBudgetAlerts(budgetStatus);\n    \n    return {\n      recorded: true,\n      cost,\n      budgetStatus: {\n        utilization: budgetStatus.budgetUtilization,\n        remainingEUR: budgetStatus.remainingBudgetEUR,\n        serviceLevel: determineServiceLevel(budgetStatus.budgetUtilization)\n      },\n      timestamp: new Date().toISOString()\n    };\n    \n  } catch (error) {\n    logger.error('API usage recording failed', {\n      error: error.message,\n      userId: context.auth?.uid\n    });\n    \n    throw new functions.https.HttpsError(\n      'internal',\n      'Failed to record API usage'\n    );\n  }\n});\n\n/**\n * Get budget status and recommendations\n */\nexports.getBudgetStatus = functions.https.onCall(async (data, context) => {\n  try {\n    // Allow unauthenticated access to general budget status for transparency\n    const budgetStatus = await getCurrentBudgetUtilization();\n    const serviceLevel = determineServiceLevel(budgetStatus.budgetUtilization);\n    \n    // Get user-specific data if authenticated\n    let userMonthlyUsage = null;\n    if (context.auth) {\n      const userId = context.auth.uid;\n      const now = new Date();\n      const userMonthlyRef = admin.firestore()\n        .collection('user_monthly_usage')\n        .doc(`${userId}_${now.getFullYear()}_${now.getMonth() + 1}`);\n      \n      const userMonthlyDoc = await userMonthlyRef.get();\n      userMonthlyUsage = userMonthlyDoc.exists ? userMonthlyDoc.data() : null;\n    }\n    \n    // Calculate recommendations\n    const recommendations = generateBudgetRecommendations(budgetStatus, serviceLevel);\n    \n    return {\n      budgetStatus,\n      serviceLevel,\n      userMonthlyUsage,\n      recommendations,\n      config: {\n        monthlyBudgetEUR: BUDGET_CONFIG.monthlyBudgetEUR,\n        throttlingThresholds: BUDGET_CONFIG.throttling\n      },\n      timestamp: new Date().toISOString()\n    };\n    \n  } catch (error) {\n    logger.error('Get budget status failed', { error: error.message });\n    \n    throw new functions.https.HttpsError(\n      'internal',\n      'Failed to get budget status'\n    );\n  }\n});\n\n/**\n * Generate budget recommendations\n */\nfunction generateBudgetRecommendations(budgetStatus, serviceLevel) {\n  const recommendations = [];\n  \n  if (budgetStatus.projectedMonthlySpend > BUDGET_CONFIG.monthlyBudgetEUR) {\n    recommendations.push({\n      type: 'budget_overrun',\n      severity: 'high',\n      message: `Projected monthly spend (€${budgetStatus.projectedMonthlySpend.toFixed(2)}) exceeds budget (€${BUDGET_CONFIG.monthlyBudgetEUR})`,\n      action: 'Consider implementing stricter usage limits or increasing budget'\n    });\n  }\n  \n  if (serviceLevel === 'warning') {\n    recommendations.push({\n      type: 'approaching_limit',\n      severity: 'medium',\n      message: '70% of monthly budget consumed',\n      action: 'Monitor usage closely and consider optimizing responses'\n    });\n  }\n  \n  if (serviceLevel === 'slowdown') {\n    recommendations.push({\n      type: 'service_degradation',\n      severity: 'high',\n      message: 'Service quality reduced due to budget constraints',\n      action: 'Users may experience shorter responses and longer processing times'\n    });\n  }\n  \n  if (serviceLevel === 'emergency') {\n    recommendations.push({\n      type: 'emergency_mode',\n      severity: 'critical',\n      message: 'Emergency mode active - free tier disabled',\n      action: 'Only premium users can access the service'\n    });\n  }\n  \n  if (budgetStatus.dailyBurnRate > (BUDGET_CONFIG.monthlyBudgetEUR / 30)) {\n    recommendations.push({\n      type: 'high_burn_rate',\n      severity: 'medium',\n      message: `Daily burn rate (€${budgetStatus.dailyBurnRate.toFixed(2)}) exceeds target`,\n      action: 'Consider implementing usage quotas per user'\n    });\n  }\n  \n  return recommendations;\n}\n\n/**\n * Check and send budget alerts\n */\nasync function checkBudgetAlerts(budgetStatus) {\n  try {\n    const alerts = [];\n    \n    // Check various alert thresholds\n    if (budgetStatus.budgetUtilization >= BUDGET_CONFIG.throttling.shutoffThreshold) {\n      alerts.push({\n        type: 'budget_exhausted',\n        severity: 'critical',\n        message: 'Monthly budget exhausted - service disabled',\n        budgetUtilization: budgetStatus.budgetUtilization\n      });\n    } else if (budgetStatus.budgetUtilization >= BUDGET_CONFIG.throttling.emergencyThreshold) {\n      alerts.push({\n        type: 'emergency_threshold',\n        severity: 'critical',\n        message: 'Emergency budget threshold reached - emergency mode activated',\n        budgetUtilization: budgetStatus.budgetUtilization\n      });\n    } else if (budgetStatus.budgetUtilization >= BUDGET_CONFIG.throttling.slowdownThreshold) {\n      alerts.push({\n        type: 'slowdown_threshold',\n        severity: 'high',\n        message: 'Slowdown threshold reached - service quality reduced',\n        budgetUtilization: budgetStatus.budgetUtilization\n      });\n    } else if (budgetStatus.budgetUtilization >= BUDGET_CONFIG.throttling.warningThreshold) {\n      alerts.push({\n        type: 'warning_threshold',\n        severity: 'medium',\n        message: 'Warning threshold reached - monitoring usage closely',\n        budgetUtilization: budgetStatus.budgetUtilization\n      });\n    }\n    \n    if (alerts.length > 0) {\n      // Store alerts\n      await admin.firestore().collection('budget_alerts').add({\n        alerts,\n        budgetStatus,\n        timestamp: new Date()\n      });\n      \n      logger.warn('Budget alerts generated', {\n        alertCount: alerts.length,\n        budgetUtilization: budgetStatus.budgetUtilization,\n        alerts\n      });\n    }\n    \n  } catch (error) {\n    logger.error('Failed to check budget alerts', { error: error.message });\n    // Don't throw - this is not critical\n  }\n}\n\n/**\n * Daily budget reset and cleanup function\n * Runs daily to clean up old records and reset counters\n */\nexports.dailyBudgetMaintenance = functions.pubsub\n  .schedule('0 0 * * *') // Run daily at midnight UTC\n  .onRun(async (context) => {\n    try {\n      logger.info('Daily budget maintenance started');\n      \n      // Get budget status\n      const budgetStatus = await getCurrentBudgetUtilization();\n      \n      // Clean up old token usage records (keep last 90 days)\n      const ninetyDaysAgo = new Date();\n      ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90);\n      \n      const oldRecordsQuery = admin.firestore()\n        .collection('token_usage')\n        .where('timestamp', '<', ninetyDaysAgo)\n        .limit(500);\n      \n      const oldRecords = await oldRecordsQuery.get();\n      \n      if (!oldRecords.empty) {\n        const batch = admin.firestore().batch();\n        oldRecords.docs.forEach(doc => {\n          batch.delete(doc.ref);\n        });\n        await batch.commit();\n        \n        logger.info('Cleaned up old token usage records', {\n          deletedCount: oldRecords.size\n        });\n      }\n      \n      // Generate daily budget report\n      const dailyReport = {\n        date: new Date().toISOString().split('T')[0],\n        budgetStatus,\n        serviceLevel: determineServiceLevel(budgetStatus.budgetUtilization),\n        recommendations: generateBudgetRecommendations(\n          budgetStatus, \n          determineServiceLevel(budgetStatus.budgetUtilization)\n        ),\n        timestamp: new Date()\n      };\n      \n      await admin.firestore()\n        .collection('daily_budget_reports')\n        .doc(dailyReport.date)\n        .set(dailyReport);\n      \n      logger.info('Daily budget maintenance completed', dailyReport);\n      \n      return dailyReport;\n      \n    } catch (error) {\n      logger.error('Daily budget maintenance failed', {\n        error: error.message,\n        stack: error.stack\n      });\n      throw error;\n    }\n  });\n"}
