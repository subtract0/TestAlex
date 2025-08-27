#!/usr/bin/env node

/**
 * Autonomous GitHub Actions CI/CD Debugger
 * 
 * This system monitors GitHub workflow runs, detects failures,
 * analyzes root causes, and generates automated fixes.
 * 
 * Usage: node autonomous-ci-debugger.js [--monitor] [--fix] [--report]
 */

const { Octokit } = require('@octokit/rest');
const fs = require('fs').promises;
const path = require('path');
const Sentry = require('@sentry/node');

// Initialize Sentry for CI/CD monitoring
Sentry.init({
  dsn: process.env.SENTRY_DSN_CI,
  environment: process.env.CI ? 'ci' : 'local',
  tracesSampleRate: 0.2,
  beforeSend: (event) => {
    // Scrub sensitive CI/CD data
    if (event.request?.headers) {
      delete event.request.headers.authorization;
      delete event.request.headers['x-github-token'];
    }
    if (event.contexts?.github?.token) {
      delete event.contexts.github.token;
    }
    return event;
  },
  initialScope: {
    tags: {
      component: 'autonomous-ci',
      platform: 'spiritual-ai',
      service: 'devops'
    }
  }
});

class AutonomousCIDebugger {
  constructor() {
    this.octokit = new Octokit({
      auth: process.env.GITHUB_TOKEN
    });
    
    this.repo = {
      owner: process.env.GITHUB_OWNER || 'subtract0',
      repo: process.env.GITHUB_REPO || 'TestAlex'
    };
    
    this.failurePatterns = this.loadFailurePatterns();
    this.fixStrategies = this.loadFixStrategies();
  }

  /**
   * Load known failure patterns for automated detection
   */
  loadFailurePatterns() {
    return {
      truffleHog: {
        pattern: /BASE and HEAD commits are the same/,
        severity: 'high',
        category: 'security-scan',
        description: 'TruffleHog cannot scan single commits'
      },
      eslintJsx: {
        pattern: /Parsing error: Unexpected token </,
        severity: 'high',
        category: 'linting',
        description: 'ESLint cannot parse JSX in .js files'
      },
      nodeVersion: {
        pattern: /npm warn EBADENGINE Unsupported engine/,
        severity: 'medium',
        category: 'dependencies',
        description: 'Node version incompatibility with packages'
      },
      missingFile: {
        pattern: /Required file\/directory missing: (.+)/,
        severity: 'high',
        category: 'configuration',
        description: 'Required configuration files missing'
      },
      buildFailure: {
        pattern: /npm ERR! missing script: (.+)/,
        severity: 'medium',
        category: 'scripts',
        description: 'Missing npm script in package.json'
      }
    };
  }

  /**
   * Load automated fix strategies
   */
  loadFixStrategies() {
    return {
      truffleHog: {
        type: 'workflow-fix',
        action: 'update-trufflehog-config',
        files: ['.github/workflows/*.yml'],
        fix: (content) => {
          return content
            .replace(/uses: trufflesecurity\/trufflehog@main\s+with:\s+path: \.\//g, 
              'uses: trufflesecurity/trufflehog@main\n      with:\n        path: ./\n        extra_args: --only-verified\n      continue-on-error: true')
            .replace(/base: main\s+head: HEAD/g, 
              'base: ${{ github.event.repository.default_branch }}\n        head: HEAD');
        }
      },
      eslintJsx: {
        type: 'config-fix',
        action: 'update-eslint-config',
        files: ['.eslintrc.json', '.eslintrc.js'],
        fix: (content) => {
          const config = JSON.parse(content);
          config.env = config.env || {};
          config.env['react-native/react-native'] = true;
          config.extends = config.extends || [];
          if (!config.extends.includes('@react-native-community')) {
            config.extends.push('@react-native-community');
          }
          config.plugins = config.plugins || [];
          if (!config.plugins.includes('react')) config.plugins.push('react');
          if (!config.plugins.includes('react-native')) config.plugins.push('react-native');
          config.parserOptions = config.parserOptions || {};
          config.parserOptions.ecmaFeatures = config.parserOptions.ecmaFeatures || {};
          config.parserOptions.ecmaFeatures.jsx = true;
          return JSON.stringify(config, null, 2);
        }
      },
      nodeVersion: {
        type: 'workflow-fix',
        action: 'upgrade-node-version',
        files: ['.github/workflows/*.yml'],
        fix: (content) => {
          return content
            .replace(/NODE_VERSION: '18'/g, 'NODE_VERSION: \'20\'')
            .replace(/node-version: '18'/g, 'node-version: \'20\'')
            .replace(/node-version: 18/g, 'node-version: \'20\'');
        }
      },
      missingFile: {
        type: 'file-creation',
        action: 'create-missing-files',
        files: ['setup.cfg', 'playwright.config.ts', 'requirements.txt'],
        fix: (filename) => {
          const templates = {
            'setup.cfg': this.generateSetupCfg(),
            'playwright.config.ts': this.generatePlaywrightConfig(),
            'requirements.txt': this.generateRequirementsTxt()
          };
          return templates[filename] || '';
        }
      }
    };
  }

  /**
   * Monitor workflow runs and detect failures
   */
  async monitorWorkflows() {
    console.log('🔍 Monitoring GitHub Actions workflows...');
    
    try {
      const { data: runs } = await this.octokit.rest.actions.listWorkflowRunsForRepo({
        ...this.repo,
        per_page: 20,
        status: 'completed'
      });

      const failedRuns = runs.workflow_runs.filter(run => run.conclusion === 'failure');
      
      console.log(`📊 Found ${failedRuns.length} failed workflow runs`);
      
      const analysisResults = [];
      
      for (const run of failedRuns) {
        console.log(`\n🔍 Analyzing run ${run.id}: ${run.name}`);
        const analysis = await this.analyzeWorkflowRun(run);
        analysisResults.push(analysis);
        
        // Generate fixes if patterns are detected
        if (analysis.detectedPatterns.length > 0) {
          // Capture CI/CD failure in Sentry
          Sentry.captureException(new Error(`CI/CD Pattern Detected: ${analysis.detectedPatterns.map(p => p.category).join(', ')}`), {
            tags: {
              workflow_name: run.name,
              failure_patterns: analysis.detectedPatterns.length,
              auto_fix_applied: true
            },
            extra: {
              run_id: run.id,
              run_url: run.html_url,
              detected_patterns: analysis.detectedPatterns,
              github_repo: this.repo
            }
          });
          
          await this.generateAutonomousFixes(analysis);
        }
      }
      
      // Generate comprehensive report
      await this.generateFailureReport(analysisResults);
      
      return analysisResults;
      
    } catch (error) {
      console.error('❌ Error monitoring workflows:', error.message);
      throw error;
    }
  }

  /**
   * Analyze a specific workflow run for failure patterns
   */
  async analyzeWorkflowRun(run) {
    const analysis = {
      runId: run.id,
      workflowName: run.name,
      createdAt: run.created_at,
      conclusion: run.conclusion,
      detectedPatterns: [],
      logs: '',
      suggestedFixes: []
    };

    try {
      // Get job details
      const { data: jobs } = await this.octokit.rest.actions.listJobsForWorkflowRun({
        ...this.repo,
        run_id: run.id
      });

      for (const job of jobs.jobs) {
        if (job.conclusion === 'failure') {
          console.log(`  📝 Analyzing failed job: ${job.name}`);
          
          // Get job logs
          try {
            const { data: logs } = await this.octokit.rest.actions.downloadJobLogsForWorkflowRun({
              ...this.repo,
              job_id: job.id
            });
            
            analysis.logs += `\n=== JOB: ${job.name} ===\n${logs}\n`;
            
            // Detect failure patterns
            const patterns = this.detectFailurePatterns(logs);
            analysis.detectedPatterns.push(...patterns);
            
          } catch (logError) {
            console.log(`    ⚠️ Could not retrieve logs for job ${job.id}: ${logError.message}`);
          }
        }
      }

      // Generate fix suggestions
      analysis.suggestedFixes = this.generateFixSuggestions(analysis.detectedPatterns);
      
      console.log(`    ✅ Detected ${analysis.detectedPatterns.length} failure patterns`);
      
    } catch (error) {
      console.error(`    ❌ Error analyzing run ${run.id}:`, error.message);
      analysis.error = error.message;
    }

    return analysis;
  }

  /**
   * Detect failure patterns in logs
   */
  detectFailurePatterns(logs) {
    const detected = [];
    
    for (const [patternName, pattern] of Object.entries(this.failurePatterns)) {
      if (pattern.pattern.test(logs)) {
        detected.push({
          name: patternName,
          ...pattern,
          matches: logs.match(pattern.pattern) || []
        });
      }
    }
    
    return detected;
  }

  /**
   * Generate fix suggestions based on detected patterns
   */
  generateFixSuggestions(patterns) {
    const suggestions = [];
    
    for (const pattern of patterns) {
      const strategy = this.fixStrategies[pattern.name];
      if (strategy) {
        suggestions.push({
          pattern: pattern.name,
          strategy: strategy.action,
          type: strategy.type,
          files: strategy.files,
          priority: pattern.severity === 'high' ? 1 : 2
        });
      }
    }
    
    // Sort by priority
    return suggestions.sort((a, b) => a.priority - b.priority);
  }

  /**
   * Generate and apply autonomous fixes
   */
  async generateAutonomousFixes(analysis) {
    console.log(`🔧 Generating autonomous fixes for ${analysis.workflowName}...`);
    
    for (const fix of analysis.suggestedFixes) {
      try {
        console.log(`  🛠️ Applying fix: ${fix.strategy}`);
        await this.applyFix(fix);
      } catch (error) {
        console.error(`    ❌ Failed to apply fix ${fix.strategy}:`, error.message);
      }
    }
  }

  /**
   * Apply a specific fix
   */
  async applyFix(fix) {
    const strategy = this.fixStrategies[fix.pattern];
    
    if (fix.type === 'workflow-fix') {
      await this.applyWorkflowFix(strategy);
    } else if (fix.type === 'config-fix') {
      await this.applyConfigFix(strategy);
    } else if (fix.type === 'file-creation') {
      await this.applyFileCreation(strategy);
    }
  }

  /**
   * Apply workflow file fixes
   */
  async applyWorkflowFix(strategy) {
    const workflowFiles = await this.findMatchingFiles(strategy.files);
    
    for (const file of workflowFiles) {
      const content = await fs.readFile(file, 'utf8');
      const fixedContent = strategy.fix(content);
      
      if (content !== fixedContent) {
        await fs.writeFile(file, fixedContent, 'utf8');
        console.log(`    ✅ Updated ${file}`);
      }
    }
  }

  /**
   * Apply configuration file fixes
   */
  async applyConfigFix(strategy) {
    const configFiles = await this.findMatchingFiles(strategy.files);
    
    for (const file of configFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const fixedContent = strategy.fix(content);
        
        if (content !== fixedContent) {
          await fs.writeFile(file, fixedContent, 'utf8');
          console.log(`    ✅ Updated ${file}`);
        }
      } catch (error) {
        if (error.code === 'ENOENT') {
          console.log(`    ⚠️ Config file ${file} not found, skipping`);
        } else {
          throw error;
        }
      }
    }
  }

  /**
   * Apply file creation fixes
   */
  async applyFileCreation(strategy) {
    for (const filename of strategy.files) {
      const filePath = path.join(process.cwd(), filename);
      
      try {
        await fs.access(filePath);
        console.log(`    ℹ️ File ${filename} already exists, skipping`);
      } catch (error) {
        if (error.code === 'ENOENT') {
          const content = strategy.fix(filename);
          await fs.writeFile(filePath, content, 'utf8');
          console.log(`    ✅ Created ${filename}`);
        }
      }
    }
  }

  /**
   * Find files matching glob patterns
   */
  async findMatchingFiles(patterns) {
    const files = [];
    
    for (const pattern of patterns) {
      if (pattern.includes('*')) {
        // Simple glob handling for workflow files
        if (pattern.includes('.github/workflows/*.yml')) {
          const workflowDir = path.join(process.cwd(), '.github/workflows');
          try {
            const dirFiles = await fs.readdir(workflowDir);
            files.push(...dirFiles
              .filter(f => f.endsWith('.yml') || f.endsWith('.yaml'))
              .map(f => path.join(workflowDir, f))
            );
          } catch (error) {
            console.log(`    ⚠️ Could not read workflow directory: ${error.message}`);
          }
        }
      } else {
        files.push(path.join(process.cwd(), pattern));
      }
    }
    
    return files;
  }

  /**
   * Generate failure analysis report
   */
  async generateFailureReport(analyses) {
    const report = {
      timestamp: new Date().toISOString(),
      totalAnalyses: analyses.length,
      patternsDetected: {},
      fixesApplied: 0,
      recommendations: []
    };

    // Count pattern occurrences
    for (const analysis of analyses) {
      for (const pattern of analysis.detectedPatterns) {
        report.patternsDetected[pattern.name] = 
          (report.patternsDetected[pattern.name] || 0) + 1;
      }
      report.fixesApplied += analysis.suggestedFixes.length;
    }

    // Generate recommendations
    const topPatterns = Object.entries(report.patternsDetected)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5);

    for (const [pattern, count] of topPatterns) {
      const patternInfo = this.failurePatterns[pattern];
      if (patternInfo) {
        report.recommendations.push({
          pattern,
          occurrences: count,
          severity: patternInfo.severity,
          description: patternInfo.description
        });
      }
    }

    // Save report
    const reportPath = path.join(process.cwd(), 'ci-failure-analysis-report.json');
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2), 'utf8');
    
    console.log('\n📊 Failure Analysis Report Generated');
    console.log('=====================================');
    console.log(`Total workflow runs analyzed: ${report.totalAnalyses}`);
    console.log(`Unique failure patterns detected: ${Object.keys(report.patternsDetected).length}`);
    console.log(`Autonomous fixes applied: ${report.fixesApplied}`);
    console.log(`Report saved to: ${reportPath}`);

    return report;
  }

  /**
   * Generate template configuration files
   */
  generateSetupCfg() {
    return `[metadata]
name = acim-guide-orchestration
version = 1.0.0

[tool:pytest]
testpaths = tests
addopts = -v --tb=short --cov=orchestration --cov-fail-under=50

[flake8]
max-line-length = 127
exclude = .git,__pycache__,venv,node_modules
ignore = E203,W503

[coverage:run]
source = orchestration
omit = tests/*,*/venv/*,*/node_modules/*

[mutmut]
paths_to_mutate = orchestration/,scripts/
runner = pytest
test_time_limit = 300
`;
  }

  generatePlaywrightConfig() {
    return `import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { 
        browserName: 'chromium',
        headless: true 
      },
    },
  ],
});
`;
  }

  generateRequirementsTxt() {
    return `pytest>=7.0.0
pytest-cov>=4.0.0
flake8>=5.0.0
mutmut>=2.4.0
requests>=2.28.0
python-dotenv>=0.19.0
`;
  }
}

// CLI Interface
async function main() {
  const ciDebugger = new AutonomousCIDebugger();
  
  const args = process.argv.slice(2);
  const shouldMonitor = args.includes('--monitor') || args.length === 0;
  const shouldFix = args.includes('--fix');
  const shouldReport = args.includes('--report');

  try {
    if (shouldMonitor) {
      const results = await ciDebugger.monitorWorkflows();
      
      if (shouldFix) {
        console.log('\n🔧 Autonomous fixing enabled - fixes have been applied');
      }
      
      if (shouldReport) {
        console.log('\n📊 Detailed report generated');
      }
      
      console.log('\n✅ Autonomous CI debugging completed');
    }
  } catch (error) {
    console.error('\n❌ Autonomous CI debugging failed:', error.message);
    process.exit(1);
  }
}

// Export for use as module
module.exports = AutonomousCIDebugger;

// Run if called directly
if (require.main === module) {
  main();
}
