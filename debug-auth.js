const admin = require('firebase-admin');

// Initialize Firebase Admin SDK
const serviceAccount = require('./service-account-key.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  projectId: 'acim-guide-production'
});

async function checkAndEnableAuth() {
  try {
    console.log('🔧 Checking Firebase Authentication configuration...');
    
    // Check current auth config
    const authConfig = await admin.auth().getConfig();
    console.log('📋 Current auth config:', JSON.stringify(authConfig, null, 2));
    
    // Try to update config to enable anonymous auth
    const updatedConfig = await admin.auth().updateConfig({
      signInOptions: [
        {
          providerId: 'anonymous',
          enabled: true
        }
      ]
    });
    
    console.log('✅ Updated auth config:', JSON.stringify(updatedConfig, null, 2));
    console.log('🎉 Anonymous authentication should now be enabled!');
    
  } catch (error) {
    console.error('❌ Error checking/updating auth config:', error);
    
    if (error.code === 'auth/insufficient-permission') {
      console.log('💡 You may need to manually enable anonymous authentication in the Firebase Console:');
      console.log('   1. Go to https://console.firebase.google.com/project/acim-guide-production/authentication/providers');
      console.log('   2. Enable "Anonymous" authentication provider');
    }
  }
  
  process.exit(0);
}

checkAndEnableAuth();
