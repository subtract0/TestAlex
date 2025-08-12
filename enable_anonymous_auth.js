const admin = require('firebase-admin');

// Initialize Firebase Admin SDK
const serviceAccount = require('./functions/serviceAccountKey.json');

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  projectId: 'acim-guide-test'
});

async function enableAnonymousAuth() {
  try {
    console.log('Enabling Anonymous Authentication...');
    
    // Note: Firebase Admin SDK doesn't directly support enabling auth providers
    // This needs to be done through the Firebase console or REST API
    console.log('Anonymous Authentication must be enabled through Firebase Console');
    console.log('Go to: https://console.firebase.google.com/project/acim-guide-test/authentication/providers');
    console.log('1. Click "Add new provider"');
    console.log('2. Select "Anonymous"');
    console.log('3. Toggle "Enable" to ON');
    console.log('4. Click "Save"');
    
  } catch (error) {
    console.error('Error:', error);
  }
}

enableAnonymousAuth();
