#!/usr/bin/env node

/**
 * CI-Friendly Health Check Script
 * 
 * This script performs health checks suitable for CI/CD environments
 * without requiring actual API keys or external service connections.
 */

console.log('🔍 Running CI-friendly health checks...\n');

class CIHealthChecker {
  constructor() {
    this.results = {
      overall: 'healthy',
      timestamp: new Date().toISOString(),
      checks: {}
    };
  }

  async checkFileStructure() {
    const startTime = Date.now();
    
    try {
      const fs = require('fs');
      const path = require('path');
      
      const requiredFiles = [
        'package.json',
        'firebase.json',
        'functions/index.js',
        'functions/package.json',
        '.eslintrc.json',
        'jest.config.js',
        'playwright.config.ts'
      ];
      
      const missingFiles = [];
      const details = {};
      
      for (const file of requiredFiles) {
        if (fs.existsSync(file)) {
          details[file] = 'EXISTS';
        } else {
          missingFiles.push(file);
          details[file] = 'MISSING';
        }
      }
      
      const duration = Date.now() - startTime;
      
      return {
        success: missingFiles.length === 0,
        message: missingFiles.length === 0 ? 
          `All ${requiredFiles.length} required files found` : 
          `Missing files: ${missingFiles.join(', ')}`,
        duration,
        details
      };
    } catch (error) {
      return {
        success: false,
        message: `File structure check failed: ${error.message}`,
        duration: Date.now() - startTime
      };
    }
  }

  async checkPackageIntegrity() {
    const startTime = Date.now();
    
    try {
      const packageJson = require('../package.json');
      const functionsPackageJson = require('../functions/package.json');
      
      const requiredScripts = [
        'build', 'test', 'lint', 'health-check',
        'test:e2e', 'deploy:staging', 'deploy:production'
      ];
      
      const missingScripts = [];
      
      for (const script of requiredScripts) {
        if (!packageJson.scripts[script]) {
          missingScripts.push(script);
        }
      }
      
      const duration = Date.now() - startTime;
      
      return {
        success: missingScripts.length === 0,
        message: missingScripts.length === 0 ? 
          'All required npm scripts configured' : 
          `Missing scripts: ${missingScripts.join(', ')}`,
        duration,
        details: {
          rootScripts: Object.keys(packageJson.scripts).length,
          functionsScripts: Object.keys(functionsPackageJson.scripts || {}).length
        }
      };
    } catch (error) {
      return {
        success: false,
        message: `Package integrity check failed: ${error.message}`,
        duration: Date.now() - startTime
      };
    }
  }

  async checkConfigurationFiles() {
    const startTime = Date.now();
    
    try {
      const fs = require('fs');
      
      const configFiles = [
        { file: 'firebase.json', required: true },
        { file: 'firestore.rules', required: true },
        { file: 'firestore.indexes.json', required: true },
        { file: '.env.template', required: true },
        { file: 'jest.config.js', required: true },
        { file: 'playwright.config.ts', required: true }
      ];
      
      const issues = [];
      const details = {};
      
      for (const config of configFiles) {
        if (fs.existsSync(config.file)) {
          details[config.file] = 'FOUND';
          
          // Additional validation for key files
          if (config.file === 'firebase.json') {
            const content = JSON.parse(fs.readFileSync(config.file, 'utf8'));
            if (!content.functions || !content.firestore || !content.hosting) {
              issues.push(`${config.file} missing required sections`);
            }
          }
        } else if (config.required) {
          issues.push(`Missing required file: ${config.file}`);
          details[config.file] = 'MISSING';
        }
      }
      
      const duration = Date.now() - startTime;
      
      return {
        success: issues.length === 0,
        message: issues.length === 0 ? 
          'All configuration files valid' : 
          `Configuration issues: ${issues.join('; ')}`,
        duration,
        details
      };
    } catch (error) {
      return {
        success: false,
        message: `Configuration check failed: ${error.message}`,
        duration: Date.now() - startTime
      };
    }
  }

  async checkAgentFramework() {
    const startTime = Date.now();
    
    try {
      const fs = require('fs');
      const path = require('path');
      
      const agentDirectories = [
        'agents/core',
        'agents/specialized', 
        'agents/templates',
        'orchestration'
      ];
      
      const missingDirs = [];
      const details = {};
      
      for (const dir of agentDirectories) {
        if (fs.existsSync(dir) && fs.lstatSync(dir).isDirectory()) {
          const files = fs.readdirSync(dir);
          details[dir] = `${files.length} files`;
        } else {
          missingDirs.push(dir);
          details[dir] = 'MISSING';
        }
      }
      
      const duration = Date.now() - startTime;
      
      return {
        success: missingDirs.length === 0,
        message: missingDirs.length === 0 ? 
          'Agent framework structure intact' : 
          `Missing directories: ${missingDirs.join(', ')}`,
        duration,
        details
      };
    } catch (error) {
      return {
        success: false,
        message: `Agent framework check failed: ${error.message}`,
        duration: Date.now() - startTime
      };
    }
  }

  async checkTestFramework() {
    const startTime = Date.now();
    
    try {
      const { execSync } = require('child_process');
      
      // Check if test files exist
      const testDirs = ['tests/', '__tests__/', 'e2e/'];
      const existingDirs = testDirs.filter(dir => {
        try {
          return require('fs').lstatSync(dir).isDirectory();
        } catch {
          return false;
        }
      });
      
      // Validate test configuration without running tests
      const jestConfigExists = require('fs').existsSync('jest.config.js');
      const playwrightConfigExists = require('fs').existsSync('playwright.config.ts');
      
      const duration = Date.now() - startTime;
      
      return {
        success: existingDirs.length > 0 && jestConfigExists && playwrightConfigExists,
        message: `Test framework ready - ${existingDirs.length} test directories found`,
        duration,
        details: {
          testDirectories: existingDirs,
          jestConfig: jestConfigExists,
          playwrightConfig: playwrightConfigExists
        }
      };
    } catch (error) {
      return {
        success: false,
        message: `Test framework check failed: ${error.message}`,
        duration: Date.now() - startTime
      };
    }
  }

  async checkSentryIntegration() {
    const startTime = Date.now();
    
    try {
      const fs = require('fs');
      const path = require('path');
      
      // Check Sentry configuration files
      const sentryFiles = [
        'functions/sentry-config.js',
        'ACIMguide/sentry.config.js', 
        'sentry_python_config.py',
        'sentry-alerts-dashboards-config.json',
        'SENTRY_INTEGRATION_GUIDE.md'
      ];
      
      const missingSentryFiles = [];
      const sentryDetails = {};
      
      for (const file of sentryFiles) {
        if (fs.existsSync(file)) {
          sentryDetails[file] = 'CONFIGURED';
        } else {
          missingSentryFiles.push(file);
          sentryDetails[file] = 'MISSING';
        }
      }
      
      // Check if Sentry packages are installed
      const packageJson = require('../package.json');
      const functionsPackageJson = require('../functions/package.json');
      
      const hasSentryNode = packageJson.devDependencies && packageJson.devDependencies['@sentry/node'];
      const hasSentryFunctions = functionsPackageJson.dependencies && 
        (functionsPackageJson.dependencies['@sentry/serverless'] || functionsPackageJson.dependencies['@sentry/tracing']);
      
      sentryDetails.sentry_node_installed = hasSentryNode ? 'YES' : 'NO';
      sentryDetails.sentry_functions_installed = hasSentryFunctions ? 'YES' : 'NO';
      
      // Check CI workflow has Sentry integration
      const ciWorkflow = fs.existsSync('.github/workflows/ci-improved.yml') ? 
        fs.readFileSync('.github/workflows/ci-improved.yml', 'utf8') : '';
      const hasSentryCIIntegration = ciWorkflow.includes('sentry-cli') || ciWorkflow.includes('SENTRY_AUTH_TOKEN');
      sentryDetails.ci_sentry_integration = hasSentryCIIntegration ? 'CONFIGURED' : 'MISSING';
      
      // Validate Sentry health without making actual API calls
      const duration = Date.now() - startTime;
      const configuredFiles = sentryFiles.length - missingSentryFiles.length;
      const totalChecks = configuredFiles + (hasSentryNode ? 1 : 0) + (hasSentryFunctions ? 1 : 0) + (hasSentryCIIntegration ? 1 : 0);
      
      return {
        success: configuredFiles >= 3 && (hasSentryNode || hasSentryFunctions),
        message: `Sentry integration: ${configuredFiles}/${sentryFiles.length} files configured, ${totalChecks} checks passed`,
        duration,
        details: sentryDetails
      };
    } catch (error) {
      return {
        success: false,
        message: `Sentry integration check failed: ${error.message}`,
        duration: Date.now() - startTime
      };
    }
  }

  async checkSpiritualIntegrity() {
    const startTime = Date.now();
    
    try {
      const fs = require('fs');
      
      // Check for spiritual content protection in configurations
      const protectionChecks = [];
      const details = {};
      
      // Check Firebase Functions has spiritual content scrubbing
      if (fs.existsSync('functions/sentry-config.js')) {
        const sentryConfig = fs.readFileSync('functions/sentry-config.js', 'utf8');
        const hasACIMScrubbing = sentryConfig.includes('scrubACIMContent') || sentryConfig.includes('ACIM_CONTENT_REDACTED');
        protectionChecks.push(hasACIMScrubbing);
        details.firebase_functions_protection = hasACIMScrubbing ? 'ENABLED' : 'MISSING';
      }
      
      // Check Python config has spiritual content protection
      if (fs.existsSync('sentry_python_config.py')) {
        const pythonConfig = fs.readFileSync('sentry_python_config.py', 'utf8');
        const hasPythonScrubbing = pythonConfig.includes('scrub_acim_content') || pythonConfig.includes('spiritual_integrity');
        protectionChecks.push(hasPythonScrubbing);
        details.python_systems_protection = hasPythonScrubbing ? 'ENABLED' : 'MISSING';
      }
      
      // Check mobile app has protection
      if (fs.existsSync('ACIMguide/sentry.config.js')) {
        const mobileConfig = fs.readFileSync('ACIMguide/sentry.config.js', 'utf8');
        const hasMobileScrubbing = mobileConfig.includes('scrubACIMContentMobile') || mobileConfig.includes('spiritual_integrity');
        protectionChecks.push(hasMobileScrubbing);
        details.mobile_app_protection = hasMobileScrubbing ? 'ENABLED' : 'MISSING';
      }
      
      // Check alerts configuration protects spiritual content
      if (fs.existsSync('sentry-alerts-dashboards-config.json')) {
        const alertsConfig = fs.readFileSync('sentry-alerts-dashboards-config.json', 'utf8');
        const hasProtectedConfig = alertsConfig.includes('spiritual-ai') || alertsConfig.includes('acim_pure');
        protectionChecks.push(hasProtectedConfig);
        details.alerts_spiritual_context = hasProtectedConfig ? 'CONFIGURED' : 'MISSING';
      }
      
      const duration = Date.now() - startTime;
      const passedChecks = protectionChecks.filter(check => check).length;
      
      return {
        success: passedChecks >= 2, // At least 2 components must have spiritual protection
        message: `Spiritual integrity protection: ${passedChecks}/${protectionChecks.length} components secured`,
        duration,
        details: {
          ...details,
          protection_score: `${passedChecks}/${protectionChecks.length}`,
          acim_purity_maintained: passedChecks >= 2 ? 'YES' : 'AT_RISK'
        }
      };
    } catch (error) {
      return {
        success: false,
        message: `Spiritual integrity check failed: ${error.message}`,
        duration: Date.now() - startTime
      };
    }
  }

  printSummary() {
    console.log('═══════════════════════════════════════');
    console.log('📊 CI HEALTH CHECK SUMMARY');
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
    
    // Exit with appropriate code
    if (this.results.overall === 'critical') {
      console.log('❌ Critical issues found - failing CI');
      process.exit(1);
    } else if (this.results.overall === 'degraded') {
      console.log('⚠️ Some issues found - proceeding with warnings');
      process.exit(0);
    } else {
      console.log('✅ All checks passed - CI healthy');
      process.exit(0);
    }
  }
}

// Main execution
async function main() {
  const checker = new CIHealthChecker();
  
  console.log('⏳ Running File Structure check...');
  const fileStructure = await checker.checkFileStructure();
  checker.results.checks['File Structure'] = {
    status: fileStructure.success ? 'healthy' : 'unhealthy',
    message: fileStructure.message,
    duration: fileStructure.duration,
    details: fileStructure.details
  };
  console.log(`${fileStructure.success ? '✅' : '❌'} File Structure: ${fileStructure.message}`);
  
  console.log('⏳ Running Package Integrity check...');
  const packageIntegrity = await checker.checkPackageIntegrity();
  checker.results.checks['Package Integrity'] = {
    status: packageIntegrity.success ? 'healthy' : 'unhealthy',
    message: packageIntegrity.message,
    duration: packageIntegrity.duration,
    details: packageIntegrity.details
  };
  console.log(`${packageIntegrity.success ? '✅' : '❌'} Package Integrity: ${packageIntegrity.message}`);
  
  console.log('⏳ Running Configuration Files check...');
  const configFiles = await checker.checkConfigurationFiles();
  checker.results.checks['Configuration Files'] = {
    status: configFiles.success ? 'healthy' : 'unhealthy',
    message: configFiles.message,
    duration: configFiles.duration,
    details: configFiles.details
  };
  console.log(`${configFiles.success ? '✅' : '❌'} Configuration Files: ${configFiles.message}`);
  
  console.log('⏳ Running Agent Framework check...');
  const agentFramework = await checker.checkAgentFramework();
  checker.results.checks['Agent Framework'] = {
    status: agentFramework.success ? 'healthy' : 'unhealthy',
    message: agentFramework.message,
    duration: agentFramework.duration,
    details: agentFramework.details
  };
  console.log(`${agentFramework.success ? '✅' : '⚠️'} Agent Framework: ${agentFramework.message}`);
  
  console.log('⏳ Running Test Framework check...');
  const testFramework = await checker.checkTestFramework();
  checker.results.checks['Test Framework'] = {
    status: testFramework.success ? 'healthy' : 'unhealthy',
    message: testFramework.message,
    duration: testFramework.duration,
    details: testFramework.details
  };
  console.log(`${testFramework.success ? '✅' : '❌'} Test Framework: ${testFramework.message}`);
  
  console.log('⏳ Running Sentry Integration check...');
  const sentryIntegration = await checker.checkSentryIntegration();
  checker.results.checks['Sentry Integration'] = {
    status: sentryIntegration.success ? 'healthy' : 'unhealthy',
    message: sentryIntegration.message,
    duration: sentryIntegration.duration,
    details: sentryIntegration.details
  };
  console.log(`${sentryIntegration.success ? '✅' : '⚠️'} Sentry Integration: ${sentryIntegration.message}`);
  
  console.log('⏳ Running Spiritual Integrity check...');
  const spiritualIntegrity = await checker.checkSpiritualIntegrity();
  checker.results.checks['Spiritual Integrity'] = {
    status: spiritualIntegrity.success ? 'healthy' : 'unhealthy',
    message: spiritualIntegrity.message,
    duration: spiritualIntegrity.duration,
    details: spiritualIntegrity.details
  };
  console.log(`${spiritualIntegrity.success ? '🕊️' : '⚠️'} Spiritual Integrity: ${spiritualIntegrity.message}`);
  
  // Calculate overall health
  const hasFailures = [fileStructure, packageIntegrity, configFiles, testFramework]
    .some(result => !result.success);
  
  const hasCriticalFailures = [spiritualIntegrity].some(result => !result.success);
  
  if (hasCriticalFailures) {
    checker.results.overall = 'critical'; // Spiritual integrity is non-negotiable
  } else if (hasFailures) {
    checker.results.overall = 'degraded';
  } else {
    checker.results.overall = 'healthy';
  }
  
  // Print summary
  checker.printSummary();
}

// Handle errors gracefully
if (require.main === module) {
  main().catch((error) => {
    console.error('❌ Health check script failed:', error.message);
    process.exit(1);
  });
}

module.exports = { CIHealthChecker };
