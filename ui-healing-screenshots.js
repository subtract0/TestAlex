// UI Healing System - Step 1: Screenshot Analysis
// This script captures screenshots at key resolutions for evaluation

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const TARGET_URL = 'https://acim-guide-production.web.app';

// Create screenshots directory
const screenshotsDir = path.join(__dirname, 'ui-screenshots');
if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
}

async function captureScreenshots() {
    const browser = await chromium.launch();
    
    // Desktop viewports to test
    const viewports = [
        { name: 'laptop-1366x768', width: 1366, height: 768 },     // Your 15.6" display
        { name: 'desktop-1920x1080', width: 1920, height: 1080 },  // Common desktop
        { name: 'tablet-768x1024', width: 768, height: 1024 },     // iPad
        { name: 'mobile-375x667', width: 375, height: 667 }        // iPhone
    ];

    for (const viewport of viewports) {
        console.log(`📸 Capturing ${viewport.name} (${viewport.width}x${viewport.height})`);
        
        const context = await browser.newContext({
            viewport: { width: viewport.width, height: viewport.height }
        });
        
        const page = await context.newPage();
        
        try {
            // Navigate to the site
            await page.goto(TARGET_URL, { waitUntil: 'networkidle', timeout: 10000 });
            
            // Wait for Firebase to initialize
            await page.waitForTimeout(3000);
            
            // Take full page screenshot
            await page.screenshot({
                path: path.join(screenshotsDir, `${viewport.name}-fullpage.png`),
                fullPage: true
            });
            
            // Take viewport screenshot (what user sees without scrolling)
            await page.screenshot({
                path: path.join(screenshotsDir, `${viewport.name}-viewport.png`),
                fullPage: false
            });
            
            // Take specific component screenshots if possible
            try {
                // Header area
                const header = page.locator('.header');
                if (await header.count() > 0) {
                    await header.screenshot({
                        path: path.join(screenshotsDir, `${viewport.name}-header.png`)
                    });
                }
                
                // Chat container
                const chatContainer = page.locator('.chat-container');
                if (await chatContainer.count() > 0) {
                    await chatContainer.screenshot({
                        path: path.join(screenshotsDir, `${viewport.name}-chat.png`)
                    });
                }
                
                // Input area
                const inputArea = page.locator('.input-section');
                if (await inputArea.count() > 0) {
                    await inputArea.screenshot({
                        path: path.join(screenshotsDir, `${viewport.name}-input.png`)
                    });
                }
                
            } catch (componentError) {
                console.warn(`Some components not found for ${viewport.name}:`, componentError.message);
            }
            
        } catch (error) {
            console.error(`Error capturing ${viewport.name}:`, error.message);
        }
        
        await context.close();
    }
    
    await browser.close();
    
    console.log('✅ Screenshots captured successfully!');
    console.log(`📁 Screenshots saved to: ${screenshotsDir}`);
    
    // List captured files
    const files = fs.readdirSync(screenshotsDir);
    console.log('\n📋 Captured files:');
    files.forEach(file => {
        console.log(`   - ${file}`);
    });
}

// Test basic functionality and take a sample screenshot
async function testBasicFunctionality() {
    console.log('🧪 Testing basic chat functionality...');
    
    const browser = await chromium.launch();
    const context = await browser.newContext({
        viewport: { width: 1366, height: 768 }
    });
    const page = await context.newPage();
    
    try {
        await page.goto(TARGET_URL, { waitUntil: 'networkidle', timeout: 10000 });
        await page.waitForTimeout(3000);
        
        // Check if input is available and functional
        const messageInput = page.locator('textarea, input[type="text"]');
        if (await messageInput.count() > 0) {
            console.log('✅ Message input found');
            
            // Test typing (but don't send to avoid API costs)
            await messageInput.fill('Hello ACIM Guide');
            await page.waitForTimeout(1000);
            
            // Clear the input
            await messageInput.clear();
            
            // Take a screenshot with input focused
            await page.screenshot({
                path: path.join(screenshotsDir, 'functional-test-input-focused.png')
            });
        } else {
            console.log('❌ No message input found');
        }
        
        // Check authentication state
        const statusElement = page.locator('.status');
        if (await statusElement.count() > 0) {
            const statusText = await statusElement.textContent();
            console.log(`📊 Status: ${statusText}`);
        }
        
        // Check logo
        const logoElement = page.locator('.logo');
        if (await logoElement.count() > 0) {
            console.log('✅ Logo element found');
            const logoSrc = await logoElement.getAttribute('src');
            console.log(`🖼️  Logo src: ${logoSrc}`);
        } else {
            console.log('❌ Logo element not found');
        }
        
    } catch (error) {
        console.error('❌ Functionality test error:', error.message);
    }
    
    await context.close();
    await browser.close();
}

// Main execution
async function main() {
    console.log('🎭 UI Healing System - Step 1: Screenshot Analysis');
    console.log(`🌐 Target URL: ${TARGET_URL}`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    
    await testBasicFunctionality();
    await captureScreenshots();
    
    console.log('');
    console.log('🎯 Next Steps:');
    console.log('   1. Review screenshots in ./ui-screenshots/');
    console.log('   2. Score against style guide (Step 2)');  
    console.log('   3. Identify components scoring <8/10');
    console.log('   4. Implement fixes (Step 3)');
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = { captureScreenshots, testBasicFunctionality };
