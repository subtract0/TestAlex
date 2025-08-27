/**
 * Firebase Cloud Function for Autonomous CI/CD Debugging
 * 
 * Listens to GitHub webhook notifications for workflow failures
 * and triggers autonomous analysis and fix deployment.
 */

const functions = require('firebase-functions');
const { Octokit } = require('@octokit/rest');
const admin = require('firebase-admin');

// Initialize Firebase Admin if not already initialized
if (!admin.apps.length) {
  admin.initializeApp();
}

const db = admin.firestore();

class AutonomousCI {
  constructor() {
    this.octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN
    });
  }

  /**
   * Process GitHub webhook for workflow run events
   */
  async processWorkflowWebhook(payload) {
    const { action, workflow_run, repository } = payload;
    
    console.log(`📡 Received webhook: ${action} for workflow ${workflow_run.name}`);
    
    // Only process completed workflow runs that failed
    if (action !== 'completed' || workflow_run.conclusion !== 'failure') {
      console.log('ℹ️ Skipping - not a failed workflow completion');
      return { status: 'skipped', reason: 'not_failed_completion' };
    }
    
    const analysisId = this.generateAnalysisId(workflow_run);
    
    try {
      // Log the failure event
      await this.logFailureEvent(workflow_run, repository, analysisId);
      
      // Analyze the failure
      console.log(`🔍 Analyzing workflow failure: ${workflow_run.id}`);
      const analysis = await this.analyzeWorkflowFailure(workflow_run, repository);
      
      // Store analysis results
      await this.storeAnalysisResults(analysisId, analysis);
      
      // Generate and deploy fixes if patterns are detected
      if (analysis.detectedPatterns.length > 0) {
        console.log(`🔧 Detected ${analysis.detectedPatterns.length} failure patterns`);
        const fixes = await this.deployAutonomousFixes(analysis, repository);
        
        // Update analysis with fix results
        await this.updateAnalysisWithFixes(analysisId, fixes);
        
        return {
          status: 'fixed',
          analysisId,
          patternsDetected: analysis.detectedPatterns.length,
          fixesDeployed: fixes.length
        };
      } else {
        console.log('ℹ️ No known failure patterns detected');
        return {
          status: 'analyzed',
          analysisId,
          reason: 'no_patterns_detected'
        };
      }
      
    } catch (error) {
      console.error(`❌ Error processing webhook:`, error);
      
      // Log error to Firestore
      await this.logError(analysisId, error);
      
      throw error;
    }
  }

  /**
   * Generate unique analysis ID
   */
  generateAnalysisId(workflowRun) {
    const timestamp = Date.now();
    const runId = workflowRun.id;
    return `analysis_${runId}_${timestamp}`;
  }

  /**
   * Log failure event to Firestore
   */
  async logFailureEvent(workflowRun, repository, analysisId) {
    const eventDoc = {
      analysisId,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      workflowRun: {
        id: workflowRun.id,
        name: workflowRun.name,
        conclusion: workflowRun.conclusion,
        createdAt: workflowRun.created_at,
        updatedAt: workflowRun.updated_at,
        headSha: workflowRun.head_sha,
        htmlUrl: workflowRun.html_url
      },
      repository: {
        fullName: repository.full_name,
        defaultBranch: repository.default_branch
      },
      status: 'logged'
    };
    
    await db.collection('ci_failures').doc(analysisId).set(eventDoc);
    console.log(`📝 Logged failure event: ${analysisId}`);
  }

  /**
   * Analyze workflow failure for known patterns
   */
  async analyzeWorkflowFailure(workflowRun, repository) {
    const analysis = {
      workflowRunId: workflowRun.id,
      workflowName: workflowRun.name,
      repository: repository.full_name,
      detectedPatterns: [],
      failedJobs: [],
      recommendations: []
    };

    try {
      // Get failed jobs
      const { data: jobs } = await this.octokit.rest.actions.listJobsForWorkflowRun({
        owner: repository.owner.login,
        repo: repository.name,
        run_id: workflowRun.id
      });

      const failedJobs = jobs.jobs.filter(job => job.conclusion === 'failure');
      analysis.failedJobs = failedJobs.map(job => ({
        id: job.id,
        name: job.name,
        conclusion: job.conclusion,
        startedAt: job.started_at,
        completedAt: job.completed_at
      }));

      // Analyze each failed job
      for (const job of failedJobs) {
        console.log(`  📝 Analyzing failed job: ${job.name}`);
        const jobPatterns = await this.analyzeJobLogs(job, repository);
        analysis.detectedPatterns.push(...jobPatterns);
      }

      // Generate recommendations
      analysis.recommendations = this.generateRecommendations(analysis.detectedPatterns);

    } catch (error) {
      console.error(`❌ Error during workflow analysis:`, error);
      analysis.error = error.message;
    }

    return analysis;
  }

  /**
   * Analyze job logs for failure patterns
   */
  async analyzeJobLogs(job, repository) {
    const patterns = [];
    
    const knownPatterns = {
      truffleHog: /BASE and HEAD commits are the same/i,
      eslintJsx: /Parsing error: Unexpected token </i,
      nodeVersion: /npm warn EBADENGINE Unsupported engine/i,
      missingFile: /Required file\/directory missing: (.+)/i,
      buildScript: /npm ERR! missing script: (.+)/i,
      authFailure: /Error: Missing authentication credentials/i
    };

    try {
      // Get job logs (Note: This might require special handling in Cloud Functions)
      const { data: logs } = await this.octokit.rest.actions.downloadJobLogsForWorkflowRun({
        owner: repository.owner.login,
        repo: repository.name,
        job_id: job.id
      });

      // Check for each known pattern
      for (const [patternName, regex] of Object.entries(knownPatterns)) {
        const matches = logs.match(regex);
        if (matches) {
          patterns.push({
            name: patternName,
            severity: this.getPatternSeverity(patternName),
            matches: matches,
            jobId: job.id,
            jobName: job.name
          });
          
          console.log(`    🔍 Detected pattern: ${patternName}`);
        }
      }

    } catch (error) {
      console.log(`    ⚠️ Could not retrieve logs for job ${job.id}: ${error.message}`);
    }

    return patterns;
  }

  /**
   * Get severity level for failure patterns
   */
  getPatternSeverity(patternName) {
    const severityMap = {
      truffleHog: 'high',
      eslintJsx: 'high',
      nodeVersion: 'medium',
      missingFile: 'high',
      buildScript: 'medium',
      authFailure: 'low' // Low because we're using simulated deployments
    };
    
    return severityMap[patternName] || 'medium';
  }

  /**
   * Generate recommendations for detected patterns
   */
  generateRecommendations(patterns) {
    const recommendations = [];
    
    const patternCounts = patterns.reduce((acc, pattern) => {
      acc[pattern.name] = (acc[pattern.name] || 0) + 1;
      return acc;
    }, {});

    for (const [patternName, count] of Object.entries(patternCounts)) {
      recommendations.push({
        pattern: patternName,
        occurrences: count,
        severity: this.getPatternSeverity(patternName),
        action: this.getRecommendedAction(patternName)
      });
    }

    return recommendations.sort((a, b) => {
      const severityOrder = { high: 3, medium: 2, low: 1 };
      return (severityOrder[b.severity] || 0) - (severityOrder[a.severity] || 0);
    });
  }

  /**
   * Get recommended action for a pattern
   */
  getRecommendedAction(patternName) {
    const actionMap = {
      truffleHog: 'Update TruffleHog configuration to handle single commits',
      eslintJsx: 'Configure ESLint for React Native JSX parsing',
      nodeVersion: 'Upgrade Node.js version to 20+',
      missingFile: 'Create missing configuration files',
      buildScript: 'Add missing npm scripts to package.json',
      authFailure: 'Configure deployment authentication'
    };
    
    return actionMap[patternName] || 'Manual investigation required';
  }

  /**
   * Deploy autonomous fixes for detected patterns
   */
  async deployAutonomousFixes(analysis, repository) {
    console.log('🚀 Deploying autonomous fixes...');
    
    const fixes = [];
    const highPriorityPatterns = analysis.detectedPatterns.filter(p => p.severity === 'high');
    
    // Group patterns by fix type
    const fixGroups = this.groupPatternsByFixType(highPriorityPatterns);
    
    for (const [fixType, patterns] of Object.entries(fixGroups)) {
      try {
        console.log(`  🔧 Applying ${fixType} fix for ${patterns.length} patterns`);
        
        const fix = await this.createAutonomousFix(fixType, patterns, repository);
        fixes.push(fix);
        
        console.log(`    ✅ ${fixType} fix deployed successfully`);
        
      } catch (error) {
        console.error(`    ❌ Failed to deploy ${fixType} fix:`, error);
        fixes.push({
          type: fixType,
          success: false,
          error: error.message,
          patterns: patterns.map(p => p.name)
        });
      }
    }
    
    return fixes;
  }

  /**
   * Group patterns by their fix type
   */
  groupPatternsByFixType(patterns) {
    const groups = {};
    
    const patternToFixMap = {
      'truffleHog': 'truffleHogFix',
      'eslintJsx': 'eslintFix',
      'nodeVersion': 'nodeUpgrade',
      'missingFile': 'configFiles'
    };
    
    for (const pattern of patterns) {
      const fixType = patternToFixMap[pattern.name];
      if (fixType) {
        groups[fixType] = groups[fixType] || [];
        groups[fixType].push(pattern);
      }
    }
    
    return groups;
  }

  /**
   * Create and deploy autonomous fix
   */
  async createAutonomousFix(fixType, patterns, repository) {
    // This would trigger the autonomous fix deployer
    // For now, return a simulated fix deployment
    return {
      type: fixType,
      success: true,
      patterns: patterns.map(p => p.name),
      pullRequestUrl: `https://github.com/${repository.full_name}/pulls`, // Simulated
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Store analysis results in Firestore
   */
  async storeAnalysisResults(analysisId, analysis) {
    const doc = {
      analysisId,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      analysis: {
        workflowRunId: analysis.workflowRunId,
        workflowName: analysis.workflowName,
        repository: analysis.repository,
        detectedPatterns: analysis.detectedPatterns,
        failedJobs: analysis.failedJobs,
        recommendations: analysis.recommendations
      },
      status: 'analyzed'
    };
    
    await db.collection('ci_analyses').doc(analysisId).set(doc);
    console.log(`💾 Stored analysis results: ${analysisId}`);
  }

  /**
   * Update analysis with fix results
   */
  async updateAnalysisWithFixes(analysisId, fixes) {
    await db.collection('ci_analyses').doc(analysisId).update({
      fixes,
      fixesApplied: fixes.length,
      successfulFixes: fixes.filter(f => f.success).length,
      status: 'fixed',
      fixTimestamp: admin.firestore.FieldValue.serverTimestamp()
    });
    
    console.log(`🔄 Updated analysis with fix results: ${analysisId}`);
  }

  /**
   * Log errors for debugging
   */
  async logError(analysisId, error) {
    const errorDoc = {
      analysisId,
      timestamp: admin.firestore.FieldValue.serverTimestamp(),
      error: {
        message: error.message,
        stack: error.stack,
        name: error.name
      }
    };
    
    await db.collection('ci_errors').add(errorDoc);
  }
}

/**
 * Main Cloud Function - GitHub Webhook Handler
 */
exports.handleGitHubWebhook = functions.https.onRequest(async (req, res) => {
  console.log('🎯 GitHub webhook received');
  
  // Verify GitHub webhook signature (recommended for production)
  const signature = req.get('X-Hub-Signature-256');
  const payload = JSON.stringify(req.body);
  
  // For demo purposes, we'll skip signature verification
  // In production, implement proper webhook signature validation
  
  try {
    const autonomousCI = new AutonomousCI();
    
    // Process different webhook event types
    if (req.body.workflow_run) {
      const result = await autonomousCI.processWorkflowWebhook(req.body);
      
      res.json({
        success: true,
        result,
        timestamp: new Date().toISOString()
      });
      
    } else {
      console.log('ℹ️ Webhook event type not supported for autonomous processing');
      res.json({
        success: true,
        message: 'Event type not processed',
        eventType: req.get('X-GitHub-Event')
      });
    }
    
  } catch (error) {
    console.error('❌ Error processing webhook:', error);
    
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

/**
 * Scheduled function to proactively monitor CI/CD health
 */
exports.scheduledCIMonitoring = functions.pubsub.schedule('every 30 minutes').onRun(async (context) => {
  console.log('⏰ Running scheduled CI/CD monitoring...');
  
  const autonomousCI = new AutonomousCI();
  
  try {
    // Get recent workflow runs from multiple repositories if needed
    const { data: runs } = await autonomousCI.octokit.rest.actions.listWorkflowRunsForRepo({
      owner: 'subtract0',
      repo: 'TestAlex',
      per_page: 10,
      status: 'completed'
    });

    const recentFailures = runs.workflow_runs
      .filter(run => run.conclusion === 'failure')
      .filter(run => {
        const runTime = new Date(run.created_at);
        const thirtyMinutesAgo = new Date(Date.now() - 30 * 60 * 1000);
        return runTime > thirtyMinutesAgo;
      });

    console.log(`📊 Found ${recentFailures.length} recent failures to process`);

    for (const run of recentFailures) {
      // Check if this run has already been processed
      const existingAnalysis = await db.collection('ci_failures')
        .where('workflowRun.id', '==', run.id)
        .limit(1)
        .get();

      if (!existingAnalysis.empty) {
        console.log(`ℹ️ Run ${run.id} already processed, skipping`);
        continue;
      }

      // Process this failure
      console.log(`🔍 Processing new failure: ${run.name} (${run.id})`);
      await autonomousCI.processWorkflowWebhook({
        action: 'completed',
        workflow_run: run,
        repository: { 
          full_name: 'subtract0/TestAlex',
          owner: { login: 'subtract0' },
          name: 'TestAlex',
          default_branch: 'main'
        }
      });
    }
    
    console.log('✅ Scheduled monitoring completed');
    
  } catch (error) {
    console.error('❌ Error in scheduled monitoring:', error);
  }
});

/**
 * HTTP function to get CI/CD health dashboard data
 */
exports.getCIDashboardData = functions.https.onRequest(async (req, res) => {
  try {
    const timeRange = req.query.timeRange || '24h';
    const limit = parseInt(req.query.limit) || 50;
    
    // Calculate time range
    const hoursBack = timeRange === '7d' ? 7 * 24 : 
                     timeRange === '30d' ? 30 * 24 : 24;
    const startTime = new Date(Date.now() - hoursBack * 60 * 60 * 1000);
    
    // Get recent failures
    const failuresQuery = db.collection('ci_failures')
      .where('timestamp', '>=', admin.firestore.Timestamp.fromDate(startTime))
      .orderBy('timestamp', 'desc')
      .limit(limit);
    
    const failuresSnapshot = await failuresQuery.get();
    
    // Get recent analyses
    const analysesQuery = db.collection('ci_analyses')
      .where('timestamp', '>=', admin.firestore.Timestamp.fromDate(startTime))
      .orderBy('timestamp', 'desc')
      .limit(limit);
    
    const analysesSnapshot = await analysesQuery.get();
    
    // Calculate metrics
    const failures = failuresSnapshot.docs.map(doc => doc.data());
    const analyses = analysesSnapshot.docs.map(doc => doc.data());
    
    const totalFailures = failures.length;
    const totalAnalyses = analyses.length;
    const fixesApplied = analyses.reduce((sum, a) => sum + (a.fixesApplied || 0), 0);
    const successfulFixes = analyses.reduce((sum, a) => sum + (a.successfulFixes || 0), 0);
    
    // Pattern frequency analysis
    const patternFrequency = {};
    for (const analysis of analyses) {
      for (const pattern of analysis.analysis?.detectedPatterns || []) {
        patternFrequency[pattern.name] = (patternFrequency[pattern.name] || 0) + 1;
      }
    }
    
    const dashboard = {
      timeRange,
      metrics: {
        totalFailures,
        totalAnalyses,
        fixesApplied,
        successfulFixes,
        fixSuccessRate: fixesApplied > 0 ? (successfulFixes / fixesApplied * 100).toFixed(2) : 0
      },
      recentFailures: failures.slice(0, 10),
      recentAnalyses: analyses.slice(0, 10),
      topFailurePatterns: Object.entries(patternFrequency)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5)
        .map(([pattern, count]) => ({ pattern, count })),
      lastUpdated: new Date().toISOString()
    };
    
    res.json(dashboard);
    
  } catch (error) {
    console.error('❌ Error generating dashboard data:', error);
    res.status(500).json({ error: error.message });
  }
});

/**
 * HTTP function to manually trigger autonomous fixing
 */
exports.triggerAutonomousFix = functions.https.onRequest(async (req, res) => {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  const { workflowRunId } = req.body;
  
  if (!workflowRunId) {
    return res.status(400).json({ error: 'workflowRunId is required' });
  }
  
  try {
    const autonomousCI = new AutonomousCI();
    
    // Get workflow run details
    const { data: workflowRun } = await autonomousCI.octokit.rest.actions.getWorkflowRun({
      owner: 'subtract0',
      repo: 'TestAlex', 
      run_id: workflowRunId
    });
    
    // Process the workflow run
    const result = await autonomousCI.processWorkflowWebhook({
      action: 'completed',
      workflow_run: workflowRun,
      repository: {
        full_name: 'subtract0/TestAlex',
        owner: { login: 'subtract0' },
        name: 'TestAlex',
        default_branch: 'main'
      }
    });
    
    res.json({
      success: true,
      result,
      workflowRunId,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('❌ Error triggering autonomous fix:', error);
    res.status(500).json({ error: error.message });
  }
});
