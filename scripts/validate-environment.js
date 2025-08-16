#!/usr/bin/env node
/**
 * Environment Validation Script
 * Validates all required environment variables and API configurations
 * for the ACIM Guide platform
 */

const fs = require('fs');
const path = require('path');

class EnvironmentValidator {
    constructor() {
        this.errors = [];
        this.warnings = [];
        this.successes = [];
        this.requiredVars = [
            'OPENAI_API_KEY',
            'ASSISTANT_ID',
            'VECTOR_STORE_ID',
            'GOOGLE_CLOUD_API_KEY',
            'FIREBASE_PROJECT_ID',
            'FIREBASE_AUTH_DOMAIN',
            'FIREBASE_STORAGE_BUCKET',
            'FIREBASE_MESSAGING_SENDER_ID',
            'FIREBASE_APP_ID'
        ];
        
        // For functions/.env, Firebase variables have different names to avoid reserved prefixes
        this.functionsRequiredVars = [
            'OPENAI_API_KEY',
            'ASSISTANT_ID',
            'VECTOR_STORE_ID',
            'GOOGLE_CLOUD_API_KEY',
            'ACIM_PROJECT_ID',
            'ACIM_AUTH_DOMAIN',
            'ACIM_STORAGE_BUCKET',
            'ACIM_MESSAGING_SENDER_ID',
            'ACIM_APP_ID'
        ];
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

    validateEnvFile(filePath) {
        this.log('info', `Validating ${filePath}...`);
        
        if (!fs.existsSync(filePath)) {
            this.errors.push(`Environment file not found: ${filePath}`);
            return false;
        }

        const content = fs.readFileSync(filePath, 'utf8');
        const lines = content.split('\n');
        const envVars = {};

        // Parse environment file
        lines.forEach((line, index) => {
            line = line.trim();
            if (line && !line.startsWith('#')) {
                const [key, ...valueParts] = line.split('=');
                if (key && valueParts.length > 0) {
                    const value = valueParts.join('=').replace(/^["']|["']$/g, '');
                    envVars[key] = value;
                }
            }
        });

        // Check required variables - use different list for functions/.env
        const varsToCheck = filePath.includes('functions/.env') ? this.functionsRequiredVars : this.requiredVars;
        varsToCheck.forEach(varName => {
            if (!envVars[varName]) {
                this.errors.push(`Missing required environment variable: ${varName} in ${filePath}`);
            } else if (envVars[varName].length < 10) {
                this.warnings.push(`Suspiciously short value for ${varName} in ${filePath}`);
            } else {
                this.successes.push(`✓ ${varName} configured in ${filePath}`);
            }
        });

        // Validate OpenAI API key format
        if (envVars.OPENAI_API_KEY) {
            if (!envVars.OPENAI_API_KEY.startsWith('sk-proj-')) {
                this.warnings.push('OpenAI API key format may be outdated (expected sk-proj- prefix)');
            }
        }

        // Validate Firebase project ID consistency
        if (envVars.FIREBASE_PROJECT_ID && envVars.FIREBASE_AUTH_DOMAIN) {
            const expectedDomain = `${envVars.FIREBASE_PROJECT_ID}.firebaseapp.com`;
            if (envVars.FIREBASE_AUTH_DOMAIN !== expectedDomain) {
                this.warnings.push(`Firebase auth domain mismatch. Expected: ${expectedDomain}, Got: ${envVars.FIREBASE_AUTH_DOMAIN}`);
            }
        }

        return true;
    }

    async validateGoogleCloudAuth() {
        this.log('info', 'Validating Google Cloud authentication...');
        
        const { spawn } = require('child_process');
        
        return new Promise((resolve) => {
            const gcloudAuth = spawn('gcloud', ['auth', 'application-default', 'print-access-token'], {
                stdio: 'pipe'
            });
            
            gcloudAuth.on('close', (code) => {
                if (code === 0) {
                    this.successes.push('✓ Google Cloud Application Default Credentials configured');
                    resolve(true);
                } else {
                    this.errors.push('Google Cloud Application Default Credentials not configured');
                    resolve(false);
                }
            });
            
            gcloudAuth.on('error', (err) => {
                this.errors.push(`Google Cloud CLI not available: ${err.message}`);
                resolve(false);
            });
        });
    }

    async validateFirebaseProject() {
        this.log('info', 'Validating Firebase project configuration...');
        
        const { spawn } = require('child_process');
        
        return new Promise((resolve) => {
            const firebaseList = spawn('firebase', ['projects:list'], {
                stdio: 'pipe'
            });
            
            let output = '';
            firebaseList.stdout.on('data', (data) => {
                output += data.toString();
            });
            
            firebaseList.on('close', (code) => {
                if (code === 0) {
                    if (output.includes('acim-guide-production')) {
                        this.successes.push('✓ Firebase acim-guide-production project accessible');
                    }
                    if (output.includes('acim-guide-test')) {
                        this.successes.push('✓ Firebase acim-guide-test project accessible');
                    }
                    resolve(true);
                } else {
                    this.errors.push('Firebase CLI not configured or projects not accessible');
                    resolve(false);
                }
            });
            
            firebaseList.on('error', (err) => {
                this.errors.push(`Firebase CLI not available: ${err.message}`);
                resolve(false);
            });
        });
    }

    validateGitignore() {
        this.log('info', 'Validating .gitignore for security...');
        
        const gitignorePath = path.join(process.cwd(), '.gitignore');
        if (!fs.existsSync(gitignorePath)) {
            this.warnings.push('.gitignore file not found');
            return;
        }

        const content = fs.readFileSync(gitignorePath, 'utf8');
        const sensitivePatterns = ['.env', '*.key', '*.json', 'service-account*'];
        
        sensitivePatterns.forEach(pattern => {
            if (content.includes(pattern)) {
                this.successes.push(`✓ .gitignore includes ${pattern}`);
            } else {
                this.warnings.push(`Consider adding ${pattern} to .gitignore for security`);
            }
        });
    }

    async run() {
        this.log('info', '🚀 Starting ACIM Guide Environment Validation');
        this.log('info', '=' .repeat(60));

        // Validate main .env file
        this.validateEnvFile('.env');
        
        // Validate functions .env file
        this.validateEnvFile('functions/.env');
        
        // Validate authentication
        await this.validateGoogleCloudAuth();
        await this.validateFirebaseProject();
        
        // Validate security
        this.validateGitignore();

        // Print results
        this.log('info', '=' .repeat(60));
        this.log('info', '📊 VALIDATION RESULTS:');
        
        if (this.successes.length > 0) {
            this.log('success', `✅ SUCCESSES (${this.successes.length}):`);
            this.successes.forEach(success => {
                this.log('success', `  ${success}`);
            });
        }
        
        if (this.warnings.length > 0) {
            this.log('warning', `⚠️  WARNINGS (${this.warnings.length}):`);
            this.warnings.forEach(warning => {
                this.log('warning', `  ${warning}`);
            });
        }
        
        if (this.errors.length > 0) {
            this.log('error', `❌ ERRORS (${this.errors.length}):`);
            this.errors.forEach(error => {
                this.log('error', `  ${error}`);
            });
        }
        
        this.log('info', '=' .repeat(60));
        
        const hasErrors = this.errors.length > 0;
        const hasWarnings = this.warnings.length > 0;
        
        if (!hasErrors && !hasWarnings) {
            this.log('success', '🎉 Environment validation passed! All systems are ready.');
            process.exit(0);
        } else if (!hasErrors && hasWarnings) {
            this.log('warning', '⚠️  Environment validation passed with warnings. Consider reviewing warnings.');
            process.exit(0);
        } else {
            this.log('error', '❌ Environment validation failed. Please fix errors before proceeding.');
            process.exit(1);
        }
    }
}

// Run validation if called directly
if (require.main === module) {
    const validator = new EnvironmentValidator();
    validator.run().catch(console.error);
}

module.exports = EnvironmentValidator;
