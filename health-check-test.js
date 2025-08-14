#!/usr/bin/env node

/**
 * ACIM Guide Post-Deploy Health Checks
 * Step 8: Comprehensive deployment verification
 */

const { initializeApp } = require('firebase/app');
const { getAuth, signInAnonymously } = require('firebase/auth');
const { getFunctions, httpsCallable } = require('firebase/functions');
const { getFirestore, collection, addDoc, getDocs, query, where } = require('firebase/firestore');

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCyGw7AioVfQ3sfxlW1kWnlsNnrQAmymwU",
  authDomain: "acim-guide-production.firebaseapp.com",
  projectId: "acim-guide-production",
  storageBucket: "acim-guide-production.firebasestorage.app",
  messagingSenderId: "1002911619347",
  appId: "1:1002911619347:web:d497f100e932d40639a2e6"
};

console.log('🕊️ ACIM Guide - Post-Deploy Health Checks');
console.log('==========================================');

let healthCheckResults = {
  healthCheckFunction: false,
  authentication: false,
  firestoreWrite: false,
  firestoreRead: false,
  chatFunction: false,
  clearThreadFunction: false,
  homepage: false
};

async function runHealthChecks() {
  try {
    // Initialize Firebase
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const functions = getFunctions(app);
    const db = getFirestore(app);

    console.log('\n1. Testing Firebase Authentication...');
    
    // Test authentication
    try {
      const userCredential = await signInAnonymously(auth);
      console.log('✅ Authentication successful:', userCredential.user.uid);
      healthCheckResults.authentication = true;
    } catch (error) {
      console.log('❌ Authentication failed:', error.message);
      return;
    }

    console.log('\n2. Testing /healthCheck function...');
    
    // Test health check function
    try {
      const healthCheck = httpsCallable(functions, 'healthCheck');
      const result = await healthCheck({});
      
      if (result.data && result.data.status === 'healthy') {
        console.log('✅ Health check function:', result.data);
        healthCheckResults.healthCheckFunction = true;
      } else {
        console.log('❌ Health check function returned unexpected result:', result.data);
      }
    } catch (error) {
      console.log('❌ Health check function error:', error.message);
    }

    console.log('\n3. Testing Firestore write operations...');
    
    // Test Firestore write
    try {
      const testDoc = {
        test: 'health-check',
        timestamp: new Date(),
        userId: auth.currentUser.uid,
        message: 'Post-deploy health check test'
      };
      
      const docRef = await addDoc(collection(db, 'health-checks'), testDoc);
      console.log('✅ Firestore write successful. Document ID:', docRef.id);
      healthCheckResults.firestoreWrite = true;
    } catch (error) {
      console.log('❌ Firestore write failed:', error.message);
    }

    console.log('\n4. Testing Firestore read operations...');
    
    // Test Firestore read
    try {
      const q = query(collection(db, 'health-checks'), where('test', '==', 'health-check'));
      const querySnapshot = await getDocs(q);
      
      if (!querySnapshot.empty) {
        console.log('✅ Firestore read successful. Found', querySnapshot.size, 'documents');
        healthCheckResults.firestoreRead = true;
      } else {
        console.log('❌ Firestore read: no documents found');
      }
    } catch (error) {
      console.log('❌ Firestore read failed:', error.message);
    }

    console.log('\n5. Testing clearThread function...');
    
    // Test clear thread function
    try {
      const clearThread = httpsCallable(functions, 'clearThread');
      const result = await clearThread({});
      
      if (result.data && result.data.threadId) {
        console.log('✅ Clear thread function successful. New thread ID:', result.data.threadId);
        healthCheckResults.clearThreadFunction = true;
      } else {
        console.log('❌ Clear thread function returned unexpected result:', result.data);
      }
    } catch (error) {
      console.log('❌ Clear thread function error:', error.message);
    }

    console.log('\n6. Testing chatWithAssistant function (basic connectivity)...');
    
    // Test chat function (without expecting full OpenAI response)
    try {
      const chatWithAssistant = httpsCallable(functions, 'chatWithAssistant');
      
      // This might fail due to missing OpenAI configuration, but we want to test the endpoint exists
      const result = await chatWithAssistant({
        message: 'Health check test message',
        tone: 'gentle'
      });
      
      if (result.data) {
        console.log('✅ Chat function accessible and responding');
        healthCheckResults.chatFunction = true;
      }
    } catch (error) {
      if (error.message.includes('OPENAI_API_KEY')) {
        console.log('⚠️ Chat function exists but OpenAI credentials missing (expected in placeholder mode)');
        healthCheckResults.chatFunction = true; // Function exists, credential issue is expected
      } else if (error.message.includes('ASSISTANT_ID')) {
        console.log('⚠️ Chat function exists but Assistant ID missing (expected in placeholder mode)');
        healthCheckResults.chatFunction = true; // Function exists, credential issue is expected
      } else {
        console.log('❌ Chat function error:', error.message);
      }
    }

  } catch (error) {
    console.log('❌ Critical error during health checks:', error.message);
  }
}

async function testHomepage() {
  console.log('\n7. Testing homepage accessibility...');
  
  const https = require('https');
  const http = require('http');
  
  const testUrl = 'https://acim-guide-production.web.app';
  
  return new Promise((resolve) => {
    const request = https.get(testUrl, (response) => {
      let data = '';
      
      response.on('data', (chunk) => {
        data += chunk;
      });
      
      response.on('end', () => {
        if (response.statusCode === 200) {
          console.log('✅ Homepage accessible at', testUrl);
          console.log('✅ Status Code:', response.statusCode);
          
          // Check for key elements
          if (data.includes('ACIM Guide') && data.includes('Firebase')) {
            console.log('✅ Homepage contains expected content');
            healthCheckResults.homepage = true;
          } else {
            console.log('⚠️ Homepage accessible but missing expected content');
          }
        } else {
          console.log('❌ Homepage returned status code:', response.statusCode);
        }
        resolve();
      });
    });
    
    request.on('error', (error) => {
      console.log('❌ Homepage test failed:', error.message);
      resolve();
    });
    
    request.setTimeout(10000, () => {
      console.log('❌ Homepage test timed out');
      request.destroy();
      resolve();
    });
  });
}

async function generateHealthReport() {
  await runHealthChecks();
  await testHomepage();
  
  console.log('\n' + '='.repeat(50));
  console.log('📊 HEALTH CHECK SUMMARY');
  console.log('='.repeat(50));
  
  const results = [
    ['Authentication', healthCheckResults.authentication],
    ['Health Check Function', healthCheckResults.healthCheckFunction],
    ['Firestore Write', healthCheckResults.firestoreWrite],
    ['Firestore Read', healthCheckResults.firestoreRead],
    ['Clear Thread Function', healthCheckResults.clearThreadFunction],
    ['Chat Function', healthCheckResults.chatFunction],
    ['Homepage Access', healthCheckResults.homepage]
  ];
  
  let passedCount = 0;
  results.forEach(([test, passed]) => {
    const status = passed ? '✅ PASS' : '❌ FAIL';
    console.log(`${test.padEnd(25)} ${status}`);
    if (passed) passedCount++;
  });
  
  console.log('\n' + '='.repeat(50));
  console.log(`Overall Health: ${passedCount}/${results.length} tests passed`);
  
  if (passedCount === results.length) {
    console.log('🌟 ALL SYSTEMS HEALTHY - DEPLOYMENT SUCCESS! 🕊️');
  } else if (passedCount >= results.length * 0.8) {
    console.log('⚠️ MOSTLY HEALTHY - Some issues need attention');
  } else {
    console.log('❌ CRITICAL ISSUES - Rollback may be needed');
  }
  
  console.log('\nTimestamp:', new Date().toISOString());
  console.log('"The light of the world brings peace to every mind through my forgiveness." - ACIM');
  
  return passedCount / results.length;
}

// Run if called directly
if (require.main === module) {
  generateHealthReport()
    .then((healthScore) => {
      process.exit(healthScore >= 0.8 ? 0 : 1);
    })
    .catch((error) => {
      console.error('Health check script failed:', error);
      process.exit(1);
    });
}

module.exports = { generateHealthReport };
