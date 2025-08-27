const admin = require('firebase-admin');

// Initialize Firebase Admin SDK with service account
const serviceAccount = require('./service-account-key.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  projectId: 'acim-guide-production'
});

async function initializeFirebaseAuth() {
  try {
    console.log('🔧 Initializing Firebase Authentication...');
    
    // First, try to create a test anonymous user to trigger auth initialization
    console.log('📝 Creating anonymous test user to initialize auth...');
    
    const user = await admin.auth().createUser({
      uid: 'test-anonymous-user-init'
    });
    
    console.log('✅ Test user created successfully:', user.uid);
    
    // Now delete the test user
    await admin.auth().deleteUser('test-anonymous-user-init');
    console.log('🗑️  Test user cleaned up');
    
    console.log('🎉 Firebase Authentication should now be initialized!');
    console.log('📋 Auth is ready for anonymous authentication');
    
    return true;
    
  } catch (error) {
    console.error('❌ Failed to initialize Firebase Auth:', error);
    
    if (error.code === 'auth/configuration-not-found') {
      console.log('💡 Authentication needs to be manually enabled in Firebase Console');
      console.log('🔗 Go to: https://console.firebase.google.com/project/acim-guide-production/authentication/providers');
      console.log('📋 Enable "Anonymous" authentication provider');
    }
    
    return false;
  }
}

initializeFirebaseAuth().then((success) => {
  process.exit(success ? 0 : 1);
}).catch((error) => {
  console.error('💥 Script failed:', error);
  process.exit(1);
});
