#!/usr/bin/env node

/**
 * Health Check Monitoring Script
 * 
 * This script performs comprehensive health checks on all system components
 * including Firebase Functions, OpenAI API connectivity, and database status.
 */

const https = require('https');
const { execSync } = require('child_process');
require('dotenv').config();

class HealthChecker {
  constructor() {
    this.checks = [];
    this.results = {
      overall: 'unknown',
      timestamp: new Date().toISOString(),
      checks: {}
    };
  }

  // Add a health check to the suite
  addCheck(name, checkFunction, critical = true) {
    this.checks.push({ name, checkFunction, critical });
  }

  // Execute all health checks
  async runAllChecks() {
    console.log('🔍 Starting comprehensive health checks...\n');

    for (const check of this.checks) {
      try {
        console.log(`⏳ Running ${check.name}...`);
        const result = await check.checkFunction();
        
        this.results.checks[check.name] = {
          status: result.success ? 'healthy' : 'unhealthy',
          message: result.message,
          critical: check.critical,
          duration: result.duration || 0,
          details: result.details || {}
        };

        const icon = result.success ? '✅' : (check.critical ? '❌' : '⚠️');
        console.log(`${icon} ${check.name}: ${result.message}`);
        
        if (result.details && Object.keys(result.details).length > 0) {
          console.log(`   Details: ${JSON.stringify(result.details, null, 2)}`);
        }
        
      } catch (error) {
        this.results.checks[check.name] = {
          status: 'error',
          message: error.message,
          critical: check.critical,
          error: error.stack
        };
        
        const icon = check.critical ? '❌' : '⚠️';
        console.log(`${icon} ${check.name}: ERROR - ${error.message}`);
      }
      
      console.log(''); // Add spacing between checks
    }

    // Calculate overall health
    this.calculateOverallHealth();
    
    // Print summary
    this.printSummary();
    
    // Return results for programmatic use
    return this.results;
  }

  // Calculate overall system health
  calculateOverallHealth() {
    const criticalChecks = Object.entries(this.results.checks)
      .filter(([name, result]) => result.critical);
    
    const failedCritical = criticalChecks
      .filter(([name, result]) => result.status !== 'healthy');

    if (failedCritical.length > 0) {
      this.results.overall = 'critical';
    } else {
      const anyUnhealthy = Object.values(this.results.checks)
        .some(result => result.status !== 'healthy');
      
      this.results.overall = anyUnhealthy ? 'degraded' : 'healthy';
    }
  }

  // Print health check summary
  printSummary() {
    console.log('═══════════════════════════════════════');
    console.log('📊 HEALTH CHECK SUMMARY');
    console.log('═══════════════════════════════════════');
    
    const overallIcon = {
      'healthy': '🟢',
      'degraded': '🟡',
      'critical': '🔴',
      'unknown': '⚪'
    }[this.results.overall];
    
    console.log(`Overall Status: ${overallIcon} ${this.results.overall.toUpperCase()}`);
    console.log(`Timestamp: ${this.results.timestamp}`);
    console.log(`Total Checks: ${Object.keys(this.results.checks).length}`);
    
    const statusCounts = Object.values(this.results.checks).reduce((acc, result) => {
      acc[result.status] = (acc[result.status] || 0) + 1;
      return acc;
    }, {});
    
    console.log(`Healthy: ${statusCounts.healthy || 0}`);
    console.log(`Unhealthy: ${statusCounts.unhealthy || 0}`);
    console.log(`Errors: ${statusCounts.error || 0}`);
    console.log('═══════════════════════════════════════\n');
  }

  // Make HTTP request with timeout
  async makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const timeout = options.timeout || 5000;
      
      const urlObj = new URL(url);
      const requestOptions = {
        hostname: urlObj.hostname,
        port: urlObj.port || 443,
        path: urlObj.pathname + urlObj.search,
        method: options.method || 'GET',
        headers: options.headers || {},
        timeout
      };
      
      const request = https.request(requestOptions, (response) => {
        let data = '';
        
        response.on('data', (chunk) => {
          data += chunk;
        });
        
        response.on('end', () => {
          const duration = Date.now() - startTime;
          resolve({
            statusCode: response.statusCode,
            data,
            duration,
            headers: response.headers
          });
        });
      });
      
      request.on('timeout', () => {
        request.destroy();
        reject(new Error(`Request timeout after ${timeout}ms`));
      });
      
      request.on('error', (error) => {
        reject(error);
      });
      
      request.end();
    });
  }
}

// Initialize health checker
const healthChecker = new HealthChecker();

// Environment Variables Check
healthChecker.addCheck('Environment Variables', async () => {
  const startTime = Date.now();
  const requiredVars = [
    'OPENAI_API_KEY',
    'FIREBASE_PROJECT_ID',
    'OPENAI_ASSISTANT_ID',
    'ANDROID_OAUTH_CLIENT_ID'
  ];
  
  const missingVars = [];
  const details = {};
  
  for (const varName of requiredVars) {
    const value = process.env[varName];
    if (!value) {
      missingVars.push(varName);
      details[varName] = 'MISSING';
    } else if (value.includes('placeholder') || value.includes('your_')) {
      missingVars.push(varName);
      details[varName] = 'PLACEHOLDER';
    } else {
      // Mask sensitive values for logging
      const masked = value.length > 8 
        ? `${value.substring(0, 4)}...${value.substring(value.length - 4)}`
        : '****';
      details[varName] = `OK (${masked})`;
    }
  }
  
  const duration = Date.now() - startTime;
  
  if (missingVars.length > 0) {
    return {
      success: false,
      message: `Missing or invalid variables: ${missingVars.join(', ')}`,
      duration,
      details
    };
  }
  
  return {
    success: true,
    message: 'All required environment variables are set',
    duration,
    details
  };
}, true);

// Firebase Functions Health Check
healthChecker.addCheck('Firebase Functions', async () => {
  const startTime = Date.now();
  
  try {
    // Check if firebase CLI is available
    execSync('firebase --version', { stdio: 'pipe' });
    
    // Get project info
    const projectInfo = execSync('firebase projects:list --json', { stdio: 'pipe' }).toString();
    let projects;
    
    try {
      const parsed = JSON.parse(projectInfo);
      // Handle different possible response structures
      if (Array.isArray(parsed)) {
        projects = parsed;
      } else if (parsed.result && Array.isArray(parsed.result)) {
        projects = parsed.result;
      } else if (parsed.projects && Array.isArray(parsed.projects)) {
        projects = parsed.projects;
      } else {
        return {
          success: false,
          message: 'Firebase CLI returned unexpected response structure',
          duration: Date.now() - startTime,
          details: { responseStructure: Object.keys(parsed) }
        };
      }
    } catch (parseError) {
      return {
        success: false,
        message: `Failed to parse Firebase CLI response: ${parseError.message}`,
        duration: Date.now() - startTime
      };
    }
    
    const currentProject = projects.find(p => p.projectId === process.env.FIREBASE_PROJECT_ID);
    
    const duration = Date.now() - startTime;
    
    if (!currentProject) {
      return {
        success: false,
        message: `Project ${process.env.FIREBASE_PROJECT_ID} not found in Firebase CLI`,
        duration
      };
    }
    
    return {
      success: true,
      message: `Firebase project "${currentProject.displayName}" is accessible`,
      duration,
      details: {
        projectId: currentProject.projectId,
        displayName: currentProject.displayName
      }
    };
    
  } catch (error) {
    const duration = Date.now() - startTime;
    return {
      success: false,
      message: `Firebase CLI error: ${error.message}`,
      duration
    };
  }
}, true);

// OpenAI API Health Check
healthChecker.addCheck('OpenAI API', async () => {
  const startTime = Date.now();
  
  if (!process.env.OPENAI_API_KEY) {
    return {
      success: false,
      message: 'OpenAI API key not configured',
      duration: Date.now() - startTime
    };
  }
  
  try {
    // Test OpenAI API connectivity
    const response = await healthChecker.makeRequest('https://api.openai.com/v1/models', {
      timeout: 10000,
      headers: {
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });
    
    const duration = Date.now() - startTime;
    
    if (response.statusCode === 200) {
      const models = JSON.parse(response.data);
      return {
        success: true,
        message: `OpenAI API accessible (${models.data.length} models available)`,
        duration,
        details: {
          responseTime: `${response.duration}ms`,
          modelsCount: models.data.length
        }
      };
    } else {
      return {
        success: false,
        message: `OpenAI API returned status ${response.statusCode}`,
        duration
      };
    }
    
  } catch (error) {
    const duration = Date.now() - startTime;
    return {
      success: false,
      message: `OpenAI API connection failed: ${error.message}`,
      duration
    };
  }
}, true);

// Security Configuration Check
healthChecker.addCheck('Security Configuration', async () => {
  const startTime = Date.now();
  const issues = [];
  const details = {};
  
  try {
    // Check if .env is in .gitignore
    const gitignore = require('fs').readFileSync('.gitignore', 'utf8');
    if (!gitignore.includes('.env')) {
      issues.push('.env not in .gitignore');
    } else {
      details.gitignore = 'OK (.env excluded)';
    }
    
    // Check if keystore is in .gitignore
    if (!gitignore.includes('*.keystore')) {
      issues.push('keystore files not excluded in .gitignore');
    } else {
      details.keystoreIgnore = 'OK (keystore files excluded)';
    }
    
    // Check for pre-commit hooks
    const preCommitExists = require('fs').existsSync('.git/hooks/pre-commit');
    if (preCommitExists) {
      details.preCommitHook = 'OK (pre-commit hook installed)';
    } else {
      issues.push('pre-commit hook not installed');
    }
    
    const duration = Date.now() - startTime;
    
    if (issues.length > 0) {
      return {
        success: false,
        message: `Security issues found: ${issues.join(', ')}`,
        duration,
        details
      };
    }
    
    return {
      success: true,
      message: 'Security configuration is properly set up',
      duration,
      details
    };
    
  } catch (error) {
    const duration = Date.now() - startTime;
    return {
      success: false,
      message: `Error checking security configuration: ${error.message}`,
      duration
    };
  }
}, false);

// Test Suite Health Check
healthChecker.addCheck('Test Suite', async () => {
  const startTime = Date.now();
  
  try {
    // Run Jest tests
    const output = execSync('npm test -- --passWithNoTests', { stdio: 'pipe' }).toString();
    const duration = Date.now() - startTime;
    
    // Parse test results - look for multiple patterns
    let passedTests = 0;
    
    // Try to find "Tests: X passed" pattern first
    const testResultsPattern1 = output.match(/Tests:\s*(\d+)\s+passed/);
    if (testResultsPattern1) {
      passedTests = parseInt(testResultsPattern1[1]);
    } else {
      // Alternative pattern: just count passed tests if pattern not found
      const passedPattern = output.match(/✓.*?/g);
      if (passedPattern) {
        passedTests = passedPattern.length;
      }
    }
    
    return {
      success: true,
      message: `Test suite passed (${passedTests} tests)`,
      duration,
      details: {
        passedTests,
        output: output.split('\n').slice(-5).join('\n') // Last 5 lines
      }
    };
    
  } catch (error) {
    const duration = Date.now() - startTime;
    return {
      success: false,
      message: `Test suite failed: ${error.message}`,
      duration,
      details: {
        error: error.stdout ? error.stdout.toString() : error.message
      }
    };
  }
}, false);

// Disk Space Check
healthChecker.addCheck('Disk Space', async () => {
  const startTime = Date.now();
  
  try {
    const diskUsage = execSync('df -h .', { stdio: 'pipe' }).toString();
    const lines = diskUsage.trim().split('\n');
    const usage = lines[1].split(/\s+/);
    
    const used = usage[4].replace('%', '');
    const available = usage[3];
    
    const duration = Date.now() - startTime;
    
    if (parseInt(used) > 90) {
      return {
        success: false,
        message: `Disk space critically low: ${used}% used`,
        duration,
        details: { usedPercent: used, available }
      };
    }
    
    return {
      success: true,
      message: `Disk space healthy: ${used}% used, ${available} available`,
      duration,
      details: { usedPercent: used, available }
    };
    
  } catch (error) {
    const duration = Date.now() - startTime;
    return {
      success: false,
      message: `Could not check disk space: ${error.message}`,
      duration
    };
  }
}, false);

// Main execution
async function main() {
  try {
    console.log('🚀 ACIM Guide - System Health Check');
    console.log('═══════════════════════════════════════\n');
    
    const results = await healthChecker.runAllChecks();
    
    // Exit with appropriate code
    if (results.overall === 'critical') {
      process.exit(1);
    } else if (results.overall === 'degraded') {
      process.exit(2);
    } else {
      process.exit(0);
    }
    
  } catch (error) {
    console.error('❌ Health check failed:', error.message);
    process.exit(1);
  }
}

// Run health checks if this script is executed directly
if (require.main === module) {
  main();
}

module.exports = HealthChecker;
