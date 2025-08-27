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
  
  // Updated OpenAI Free Tier Allocations (2025)
  freeTokenAllocations: {
    premiumModels: {
      dailyAllocation: 250000,  // 250k tokens/day for premium models
      models: ['gpt-5-chat-latest', 'gpt-5', 'gpt-4.1', 'gpt-4o', 'o1', 'o3'],
      used: 0,
      resetDaily: true,
      priority: 'high-value-users'
    },
    budgetModels: {
      dailyAllocation: 2500000, // 2.5M tokens/day for budget models
      models: [
        'gpt-5-mini', 'gpt-5-nano', 'gpt-4.1-mini', 'gpt-4.1-nano',
        'gpt-4o-mini', 'o1-mini', 'o3-mini', 'o4-mini', 'codex-mini-latest'
      ],
      used: 0,
      resetDaily: true,
      priority: 'optimization-tasks'
    }
  },
  
  // OpenAI pricing (as of 2025 - adjust as needed)
  pricing: {
    // Premium models (250k free tokens/day)
    'gpt-5-chat-latest': {
      inputTokens: 0.05 / 1000,   // €0.05 per 1K input tokens (estimated)
      outputTokens: 0.10 / 1000,  // €0.10 per 1K output tokens (estimated)
      freeTier: 'premiumModels'
    },
    'gpt-4o-mini': {
      inputTokens: 0.01 / 1000,   // €0.01 per 1K input tokens
      outputTokens: 0.02 / 1000,  // €0.02 per 1K output tokens
      freeTier: 'budgetModels'
    },
    
    // Legacy models
    gpt4: {
      inputTokens: 0.03 / 1000,   // €0.03 per 1K input tokens
      outputTokens: 0.06 / 1000   // €0.06 per 1K output tokens
    },
    gpt4_turbo: {
      inputTokens: 0.01 / 1000,   // €0.01 per 1K input tokens  
      outputTokens: 0.03 / 1000   // €0.03 per 1K output tokens
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
      budgetConstrained: 'gpt-4o-mini',
      emergency: 'gpt-4o-mini'
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
    const daysSinceMonthStart = Math.max(1, Math.ceil((now - monthStart) / (1000 * 60 * 60 * 24)));
    const dailyBurnRate = totalCostEUR / daysSinceMonthStart;
    const projectedMonthlySpend = dailyBurnRate * 30; // Assume 30-day month
    
    return {
      totalCostEUR,
      budgetUtilization,
      remainingBudgetEUR,
      totalTokensIn,
      totalTokensOut,
      requestCount,
      dailyBurnRate,
      projectedMonthlySpend,
      monthStart: monthStart.toISOString(),
      monthEnd: monthEnd.toISOString()
    };
  } catch (error) {
    logger.error('Failed to get budget utilization', { error: error.message });
    throw error;
  }
}

/**
 * Calculate token usage cost
 */
function calculateCost(tokensIn, tokensOut, model = 'gpt-4o-mini') {
  const pricing = BUDGET_CONFIG.pricing[model] || BUDGET_CONFIG.pricing['gpt-4o-mini'];
  
  const inputCost = tokensIn * pricing.inputTokens;
  const outputCost = tokensOut * pricing.outputTokens;
  const totalCost = inputCost + outputCost;
  
  return {
    inputCost,
    outputCost,
    totalCost,
    model,
    tokensIn,
    tokensOut
  };
}

/**
 * Record token usage in Firestore
 */
async function recordTokenUsage(userId, tokensIn, tokensOut, model = 'gpt-4o-mini', userTier = 'free') {
  try {
    const cost = calculateCost(tokensIn, tokensOut, model);
    const timestamp = new Date();
    
    // Store in Firestore
    await admin.firestore().collection('token_usage').add({
      userId,
      tokensIn,
      tokensOut,
      model,
      userTier,
      costEUR: cost.totalCost,
      inputCostEUR: cost.inputCost,
      outputCostEUR: cost.outputCost,
      timestamp,
      month: `${timestamp.getFullYear()}-${String(timestamp.getMonth() + 1).padStart(2, '0')}`
    });
    
    logger.info('Token usage recorded', {
      userId,
      tokensIn,
      tokensOut,
      model,
      costEUR: cost.totalCost
    });
    
    return cost.totalCost;
  } catch (error) {
    logger.error('Failed to record token usage', { error: error.message, userId });
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
    let reason = '';
    
    if (!allowed) {
      reason = 'Monthly budget exhausted. Service temporarily unavailable.';
    } else if (parameters.serviceLevel === 'emergency' && userTier === 'free') {
      allowed = false;
      reason = 'Budget constraints: Free tier temporarily limited. Please upgrade or try again later.';
    }
    
    // Log budget check
    logger.info('Budget allowance check', {
      userId,
      userTier,
      allowed,
      serviceLevel: parameters.serviceLevel,
      budgetUtilization: budgetStatus.budgetUtilization,
      remainingBudgetEUR: budgetStatus.remainingBudgetEUR
    });
    
    return {
      allowed,
      reason,
      serviceLevel: parameters.serviceLevel,
      maxTokens: parameters.maxTokens,
      recommendedModel: parameters.model,
      budgetStatus: {
        utilization: budgetStatus.budgetUtilization,
        remainingEUR: budgetStatus.remainingBudgetEUR,
        projectedSpend: budgetStatus.projectedMonthlySpend
      },
      userMonthlyUsage,
      timestamp: new Date().toISOString()
    };
    
  } catch (error) {
    logger.error('Budget allowance check failed', {
      error: error.message,
      userId: (context.auth && context.auth.uid)
    });
    
    throw new functions.https.HttpsError(
      'internal',
      'Failed to check budget allowance'
    );
  }
});

/**
 * Record OpenAI API usage after request completion
 */
exports.recordApiUsage = functions.https.onCall(async (data, context) => {
  try {
    if (!context.auth) {
      throw new functions.https.HttpsError(
        'unauthenticated',
        'Authentication required'
      );
    }
    
    const {
      tokensIn,
      tokensOut,
      model = 'gpt-4o-mini',
      userTier = 'free',
      requestDuration,
      success = true
    } = data;
    
    if (!tokensIn || !tokensOut) {
      throw new functions.https.HttpsError(
        'invalid-argument',
        'tokensIn and tokensOut are required'
      );
    }
    
    const userId = context.auth.uid;
    
    // Record the usage
    const cost = await recordTokenUsage(userId, tokensIn, tokensOut, model, userTier);
    
    // Get updated budget status
    const budgetStatus = await getCurrentBudgetUtilization();
    
    return {
      recorded: true,
      cost,
      budgetStatus: {
        utilization: budgetStatus.budgetUtilization,
        remainingEUR: budgetStatus.remainingBudgetEUR,
        serviceLevel: determineServiceLevel(budgetStatus.budgetUtilization)
      },
      timestamp: new Date().toISOString()
    };
    
  } catch (error) {
    logger.error('API usage recording failed', {
      error: error.message,
      userId: (context.auth && context.auth.uid)
    });
    
    throw new functions.https.HttpsError(
      'internal',
      'Failed to record API usage'
    );
  }
});

/**
 * Get budget status and recommendations
 */
exports.getBudgetStatus = functions.https.onCall(async (data, context) => {
  try {
    // Allow unauthenticated access to general budget status for transparency
    const budgetStatus = await getCurrentBudgetUtilization();
    const serviceLevel = determineServiceLevel(budgetStatus.budgetUtilization);
    
    // Get user-specific data if authenticated
    let userMonthlyUsage = null;
    if (context.auth) {
      const userId = context.auth.uid;
      const now = new Date();
      const userMonthlyRef = admin.firestore()
        .collection('user_monthly_usage')
        .doc(`${userId}_${now.getFullYear()}_${now.getMonth() + 1}`);
      
      const userMonthlyDoc = await userMonthlyRef.get();
      userMonthlyUsage = userMonthlyDoc.exists ? userMonthlyDoc.data() : null;
    }
    
    return {
      budgetStatus,
      serviceLevel,
      userMonthlyUsage,
      config: {
        monthlyBudgetEUR: BUDGET_CONFIG.monthlyBudgetEUR,
        throttlingThresholds: BUDGET_CONFIG.throttling
      },
      timestamp: new Date().toISOString()
    };
    
  } catch (error) {
    logger.error('Get budget status failed', { error: error.message });
    
    throw new functions.https.HttpsError(
      'internal',
      'Failed to get budget status'
    );
  }
});
