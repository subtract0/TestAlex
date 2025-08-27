#!/usr/bin/env node

/**
 * Secure Firebase Deployment Script
 * Replaces placeholder API keys with actual keys during build process
 * Prevents API keys from being committed to repository
 */

const fs = require('fs');
const path = require('path');

// Load environment variables from .env file
require('dotenv').config();

console.log('🔐 Starting secure deployment process...');

// Check for required environment variables
const requiredEnvVars = [
  'GOOGLE_CLOUD_API_KEY',
  'FIREBASE_PROJECT_ID'
];

const missingEnvVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingEnvVars.length > 0) {
  console.error('❌ Missing required environment variables:');
  missingEnvVars.forEach(varName => {
    console.error(`   - ${varName}`);
  });
  console.error('\nPlease set these environment variables in .env file before deploying.');
  console.error('GOOGLE_CLOUD_API_KEY: The Firebase Web API key from Google Cloud Console');
  console.error('FIREBASE_PROJECT_ID: Your Firebase project ID (default: acim-guide-production)');
  process.exit(1);
}

// Read the template HTML file
const templatePath = path.join(__dirname, '..', 'public', 'index.html');
let htmlContent = fs.readFileSync(templatePath, 'utf8');

// Replace the placeholder with actual API key
const actualApiKey = process.env.GOOGLE_CLOUD_API_KEY;
const actualProjectId = process.env.FIREBASE_PROJECT_ID || 'acim-guide-production';

console.log('🔄 Replacing API key placeholder with secure configuration...');

// Replace the placeholder API key
htmlContent = htmlContent.replace(
  'apiKey: "PLACEHOLDER_TO_BE_REPLACED_BY_BUILD_PROCESS"',
  `apiKey: "${actualApiKey}"`
);

// Verify the project ID matches
htmlContent = htmlContent.replace(
  /projectId: "acim-guide-production"/g,
  `projectId: "${actualProjectId}"`
);

// Write the processed HTML to a temporary deployment directory
const deployDir = path.join(__dirname, '..', 'deploy');
if (!fs.existsSync(deployDir)) {
  fs.mkdirSync(deployDir, { recursive: true });
}

const deployHtmlPath = path.join(deployDir, 'index.html');
fs.writeFileSync(deployHtmlPath, htmlContent);

console.log('✅ Secure HTML file created at:', deployHtmlPath);
console.log('🚀 Ready for Firebase deployment!');
console.log('');
console.log('Next steps:');
console.log('1. Deploy using: firebase deploy --only hosting --public deploy');
console.log('2. The deployed version will have the correct API key');
console.log('3. The source code repository remains secure');
console.log('');
console.log('⚠️  IMPORTANT: Never commit the deploy/ directory to version control!');
