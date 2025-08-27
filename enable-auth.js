const { JWT } = require('google-auth-library');
const { readFileSync } = require('fs');

async function enableAnonymousAuth() {
  try {
    // Load service account
    const serviceAccountKey = JSON.parse(readFileSync('./service-account-key.json', 'utf8'));
    
    // Create JWT client
    const client = new JWT({
      email: serviceAccountKey.client_email,
      key: serviceAccountKey.private_key,
      scopes: [
        'https://www.googleapis.com/auth/firebase',
        'https://www.googleapis.com/auth/cloud-identity'
      ]
    });
    
    // Get access token
    const accessToken = await client.authorize();
    console.log('🔑 Got access token for service account');
    
    // Enable anonymous authentication
    const response = await fetch(`https://identitytoolkit.googleapis.com/admin/v2/projects/acim-guide-production/config?updateMask=signIn.anonymous.enabled`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${accessToken.access_token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        signIn: {
          anonymous: {
            enabled: true
          }
        }
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ Anonymous authentication enabled successfully!');
      console.log('📋 Config:', result);
      return true;
    } else {
      const error = await response.text();
      console.error('❌ Failed to enable anonymous auth:', error);
      return false;
    }
    
  } catch (error) {
    console.error('💥 Script failed:', error);
    return false;
  }
}

// Use global fetch (Node.js 18+)
if (typeof fetch === 'undefined') {
  global.fetch = require('node-fetch');
}

enableAnonymousAuth().then((success) => {
  process.exit(success ? 0 : 1);
});
