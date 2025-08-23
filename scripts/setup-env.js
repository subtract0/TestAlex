#!/usr/bin/env node

/**
 * Secure Environment Setup Script
 * This script helps set up environment variables securely
 */

const fs = require('fs');
const path = require('path');

const ENV_FILE = path.join(__dirname, '..', '.env');
const ENV_TEMPLATE = path.join(__dirname, '..', '.env.template');

console.log('🔒 ACIM Guide - Secure Environment Setup');
console.log('========================================\n');

// Check if .env already exists
if (fs.existsSync(ENV_FILE)) {
  console.log('✅ .env file already exists');
  
  // Validate required environment variables
  require('dotenv').config({ path: ENV_FILE });
  
  const requiredVars = [
    'OPENAI_API_KEY',
    'GOOGLE_CLOUD_API_KEY',
    'FIREBASE_PROJECT_ID',
    'ASSISTANT_ID'
  ];
  
  console.log('\n🔍 Validating environment variables...');
  let allValid = true;
  
  requiredVars.forEach(varName => {
    const value = process.env[varName];
    if (!value || value.includes('your_') || value.includes('placeholder')) {
      console.log(`❌ ${varName}: Missing or contains placeholder`);
      allValid = false;
    } else {
      // Show first and last 4 characters for verification
      const masked = value.length > 8 
        ? `${value.substring(0, 4)}...${value.substring(value.length - 4)}`
        : '****';
      console.log(`✅ ${varName}: ${masked}`);
    }
  });
  
  if (allValid) {
    console.log('\n🎉 All environment variables are properly configured!');
  } else {
    console.log('\n⚠️  Some environment variables need attention.');
    console.log('Please update your .env file with the actual values.');
  }
  
} else {
  console.log('❌ .env file not found');
  if (fs.existsSync(ENV_TEMPLATE)) {
    console.log('📋 Creating .env from template...');
    fs.copyFileSync(ENV_TEMPLATE, ENV_FILE);
    console.log('✅ .env file created from template');
    console.log('\n🔧 Next steps:');
    console.log('1. Edit .env file with your actual API keys');
    console.log('2. Run this script again to validate');
  } else {
    console.log('❌ .env.template not found');
  }
}

console.log('\n🛡️  Security reminders:');
console.log('- Never commit .env files to version control');
console.log('- Rotate API keys regularly');
console.log('- Use different keys for development and production');
console.log('- Monitor API key usage in your dashboards');
