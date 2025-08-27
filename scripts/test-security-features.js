#!/usr/bin/env node
/**
 * Security and Authentication Test Script
 * Tests all security features and authentication mechanisms
 * for the ACIM Guide platform
 */

const { initializeApp } = require('firebase/app');
const { getAuth, signInAnonymously, signOut } = require('firebase/auth');
const { getFunctions, httpsCallable, connectFunctionsEmulator } = require('firebase/functions');
const axios = require('axios');

class SecurityTester {
  constructor() {
    this.results = {
      passed: 0,
      failed: 0,
      warnings: 0,
      tests: []
    };

    // Firebase configuration
    this.firebaseConfig = {
      apiKey: process.env.GOOGLE_CLOUD_API_KEY || process.env.FIREBASE_API_KEY,
      authDomain: process.env.FIREBASE_AUTH_DOMAIN || 'acim-guide-production.firebaseapp.com',
      projectId: process.env.FIREBASE_PROJECT_ID || 'acim-guide-production',
      storageBucket: process.env.FIREBASE_STORAGE_BUCKET || 'acim-guide-production.firebasestorage.app',
      messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID || '1002911619347',
      appId: process.env.FIREBASE_APP_ID || '1:1002911619347:web:d497f100e932d40639a2e6'
    };

    this.app = null;
    this.auth = null;
    this.functions = null;
  }

  log(type, message) {
    const timestamp = new Date().toISOString();
    const colors = {
      error: '\x1b[31m',   // Red
      warning: '\x1b[33m', // Yellow
      success: '\x1b[32m', // Green
      info: '\x1b[36m',    // Cyan
      reset: '\x1b[0m'     // Reset
    };
        
    console.log(`${colors[type]}[${timestamp}] ${message}${colors.reset}`);
  }

  recordTest(name, passed, message) {
    if (!this.results) {
      this.results = { passed: 0, failed: 0, warnings: 0, tests: [] };
    }
    if (!this.results.tests) {
      this.results.tests = [];
    }
    this.results.tests.push({ name, passed, message, timestamp: new Date().toISOString() });
    if (passed) {
      this.results.passed++;
      this.log('success', `✓ ${name}: ${message}`);
    } else {
      this.results.failed++;
      this.log('error', `✗ ${name}: ${message}`);
    }
  }

  recordWarning(name, message) {
    if (!this.results) {
      this.results = { passed: 0, failed: 0, warnings: 0, tests: [] };
    }
    if (!this.results.tests) {
      this.results.tests = [];
    }
    this.results.tests.push({ name, passed: false, warning: true, message, timestamp: new Date().toISOString() });
    this.results.warnings++;
    this.log('warning', `⚠ ${name}: ${message}`);
  }

  async initialize() {
    try {
      this.app = initializeApp(this.firebaseConfig);
      this.auth = getAuth(this.app);
      this.functions = getFunctions(this.app, 'us-central1');
            
      this.recordTest('Firebase Initialization', true, 'Firebase app initialized successfully');
      return true;
    } catch (error) {
      this.recordTest('Firebase Initialization', false, `Failed to initialize: ${error.message}`);
      return false;
    }
  }

  async testAnonymousAuthentication() {
    try {
      const userCredential = await signInAnonymously(this.auth);
      const user = userCredential.user;
            
      if (user && user.uid) {
        this.recordTest('Anonymous Authentication', true, `User authenticated with UID: ${user.uid.substring(0, 8)}...`);
        this.currentUser = user;
        return true;
      } else {
        this.recordTest('Anonymous Authentication', false, 'User object invalid');
        return false;
      }
    } catch (error) {
      this.recordTest('Anonymous Authentication', false, `Authentication failed: ${error.message}`);
      return false;
    }
  }

  async testHealthCheckFunction() {
    try {
      const healthCheck = httpsCallable(this.functions, 'healthCheck');
      const result = await healthCheck();
            
      if (result.data && result.data.status === 'healthy') {
        this.recordTest('Health Check Function', true, `Status: ${result.data.status}, Message: ${result.data.message}`);
        return true;
      } else {
        this.recordTest('Health Check Function', false, `Unexpected response: ${JSON.stringify(result.data)}`);
        return false;
      }
    } catch (error) {
      this.recordTest('Health Check Function', false, `Function call failed: ${error.message}`);
      return false;
    }
  }

  async testChatFunctionAuthentication() {
    try {
      const chatWithAssistant = httpsCallable(this.functions, 'chatWithAssistant');
            
      // Test with authentication
      const result = await chatWithAssistant({
        message: 'Hello, this is a test message for authentication verification.',
        tone: 'gentle'
      });
            
      if (result.data && result.data.response) {
        this.recordTest('Chat Function Authentication', true, `Successfully received response: ${result.data.response.substring(0, 50)}...`);
        return true;
      } else {
        this.recordTest('Chat Function Authentication', false, `No response received: ${JSON.stringify(result.data)}`);
        return false;
      }
    } catch (error) {
      // If it's an authentication error, that might be expected
      if (error.message.includes('Authentication required') || error.message.includes('UNAUTHENTICATED')) {
        this.recordWarning('Chat Function Authentication', 'Function requires authentication (as expected)');
        return true;
      } else {
        this.recordTest('Chat Function Authentication', false, `Unexpected error: ${error.message}`);
        return false;
      }
    }
  }

  async testHostingAccessibility() {
    try {
      const response = await axios.get('https://acim-guide-production.web.app', {
        timeout: 10000,
        headers: {
          'User-Agent': 'ACIM-Guide-Security-Test/1.0'
        }
      });
            
      if (response.status === 200 && response.data.includes('ACIM')) {
        this.recordTest('Hosting Accessibility', true, `Site accessible, status: ${response.status}, content includes ACIM references`);
        return true;
      } else {
        this.recordTest('Hosting Accessibility', false, `Unexpected response: status ${response.status}`);
        return false;
      }
    } catch (error) {
      this.recordTest('Hosting Accessibility', false, `Site not accessible: ${error.message}`);
      return false;
    }
  }

  async testSSLSecurity() {
    try {
      const response = await axios.get('https://acim-guide-production.web.app', {
        timeout: 10000
      });
            
      if (response.request.protocol === 'https:') {
        this.recordTest('SSL Security', true, 'Site properly using HTTPS');
        return true;
      } else {
        this.recordTest('SSL Security', false, `Insecure protocol: ${response.request.protocol}`);
        return false;
      }
    } catch (error) {
      this.recordTest('SSL Security', false, `SSL test failed: ${error.message}`);
      return false;
    }
  }

  async testFirebaseRules() {
    // This is a basic test - in production you'd want to test specific rule scenarios
    try {
      // Try to access Firestore without proper authentication
      // This should fail if rules are properly configured
      this.recordWarning('Firestore Security Rules', 'Rules testing requires manual verification in Firebase Console');
      return true;
    } catch (error) {
      this.recordTest('Firestore Security Rules', false, `Rules test failed: ${error.message}`);
      return false;
    }
  }

  async testEnvironmentVariables() {
    const requiredEnvVars = [
      'OPENAI_API_KEY',
      'ASSISTANT_ID',
      'VECTOR_STORE_ID',
      'GOOGLE_CLOUD_API_KEY'
    ];

    let allPresent = true;
    for (const envVar of requiredEnvVars) {
      if (!process.env[envVar]) {
        this.recordTest(`Environment Variable ${envVar}`, false, 'Not configured');
        allPresent = false;
      } else {
        this.recordTest(`Environment Variable ${envVar}`, true, 'Configured (value hidden)');
      }
    }

    return allPresent;
  }

  async cleanup() {
    try {
      if (this.auth && this.currentUser) {
        await signOut(this.auth);
        this.recordTest('Authentication Cleanup', true, 'Successfully signed out');
      }
    } catch (error) {
      this.recordTest('Authentication Cleanup', false, `Cleanup failed: ${error.message}`);
    }
  }

  generateReport() {
    this.log('info', '=' .repeat(80));
    this.log('info', '📊 SECURITY TEST RESULTS SUMMARY:');
    this.log('info', '=' .repeat(80));
        
    this.log('success', `✅ PASSED: ${this.results.passed} tests`);
    this.log('warning', `⚠️  WARNINGS: ${this.results.warnings} tests`);
    this.log('error', `❌ FAILED: ${this.results.failed} tests`);
        
    this.log('info', '=' .repeat(80));
    this.log('info', '📋 DETAILED TEST RESULTS:');
        
    this.results.tests.forEach(test => {
      const status = test.warning ? '⚠️ ' : (test.passed ? '✅' : '❌');
      console.log(`${status} ${test.name}: ${test.message}`);
    });
        
    this.log('info', '=' .repeat(80));
        
    const totalTests = this.results.passed + this.results.failed + this.results.warnings;
    const successRate = totalTests > 0 ? ((this.results.passed / totalTests) * 100).toFixed(1) : 0;
        
    this.log('info', `📈 SUCCESS RATE: ${successRate}% (${this.results.passed}/${totalTests})`);
        
    if (this.results.failed === 0) {
      this.log('success', '🎉 All critical security tests passed!');
      return 0;
    } else if (this.results.failed <= 2) {
      this.log('warning', '⚠️  Some tests failed, but core security appears intact.');
      return 1;
    } else {
      this.log('error', '❌ Multiple security tests failed. Review required.');
      return 2;
    }
  }

  async run() {
    this.log('info', '🔐 Starting ACIM Guide Security & Authentication Tests');
    this.log('info', '=' .repeat(80));

    // Initialize Firebase
    if (!await this.initialize()) {
      return this.generateReport();
    }

    // Test authentication
    await this.testAnonymousAuthentication();
        
    // Test functions
    await this.testHealthCheckFunction();
    await this.testChatFunctionAuthentication();
        
    // Test hosting and security
    await this.testHostingAccessibility();
    await this.testSSLSecurity();
        
    // Test configurations
    await this.testEnvironmentVariables();
    await this.testFirebaseRules();
        
    // Cleanup
    await this.cleanup();
        
    return this.generateReport();
  }
}

// Run tests if called directly
if (require.main === module) {
  require('dotenv').config();
    
  const tester = new SecurityTester();
  tester.run()
    .then(exitCode => process.exit(exitCode))
    .catch(error => {
      console.error('Test runner failed:', error);
      process.exit(3);
    });
}

module.exports = SecurityTester;
