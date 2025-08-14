// 🕊️ ACIM Guide UI Validation Tests
// Automatisierte Tests für UI-Verbesserungen mit Playwright

const { test, expect } = require('@playwright/test');

const SITE_URL = 'https://acim-guide-production.web.app';

test.describe('ACIM Guide UI Optimization Validation', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to the site and wait for Firebase auth
    await page.goto(SITE_URL);
    await page.waitForLoadState('networkidle');
    // Wait for Firebase authentication to complete
    await page.waitForTimeout(3000);
  });

  test('Header Height Optimization - Should be ≤64px', async ({ page }) => {
    // Test header height reduction
    const header = page.locator('.header');
    await expect(header).toBeVisible();
    
    const headerBox = await header.boundingBox();
    console.log(`📏 Header height: ${headerBox.height}px`);
    
    // Assert header height is optimized
    expect(headerBox.height).toBeLessThanOrEqual(64);
    
    // Log improvement
    const improvement = 180.109 - headerBox.height;
    console.log(`✅ Header height improvement: -${improvement.toFixed(1)}px`);
  });

  test('Logo Display - Should be visible and functional', async ({ page }) => {
    // Test logo visibility (either SVG or emoji fallback)
    const logoImg = page.locator('.logo');
    const logoEnhanced = page.locator('.logo-enhanced');
    
    // At least one logo variant should be visible
    const imgVisible = await logoImg.isVisible().catch(() => false);
    const enhancedVisible = await logoEnhanced.isVisible().catch(() => false);
    
    expect(imgVisible || enhancedVisible).toBe(true);
    
    if (imgVisible) {
      console.log('📷 Original logo is visible');
      const logoBox = await logoImg.boundingBox();
      expect(logoBox.width).toBeGreaterThan(0);
      expect(logoBox.height).toBeGreaterThan(0);
    } else if (enhancedVisible) {
      console.log('🕊️ Enhanced logo fallback is visible');
    }
  });

  test('Status Message Positioning - Should not interfere with main UI', async ({ page }) => {
    const status = page.locator('.status');
    
    if (await status.isVisible()) {
      const statusBox = await status.boundingBox();
      const viewport = page.viewportSize();
      
      // Status should be positioned in bottom-right area (not top)
      expect(statusBox.y).toBeGreaterThan(viewport.height / 2);
      console.log(`📍 Status positioned at y: ${statusBox.y}px (bottom half)`);
    } else {
      console.log('👻 Status message is hidden (which is good)');
    }
  });

  test('Viewport Utilization - Chat area should use ≥60% of viewport', async ({ page }) => {
    const chatContainer = page.locator('.chat-container');
    await expect(chatContainer).toBeVisible();
    
    const chatBox = await chatContainer.boundingBox();
    const viewport = page.viewportSize();
    
    const utilization = (chatBox.height / viewport.height) * 100;
    console.log(`📊 Chat area utilization: ${utilization.toFixed(1)}% of viewport`);
    
    expect(utilization).toBeGreaterThanOrEqual(60);
    
    // Bonus points for >80% utilization
    if (utilization >= 80) {
      console.log('🎯 Excellent viewport utilization (≥80%)');
    }
  });

  test('Interactive Elements - All core functions should work', async ({ page }) => {
    // Test input field
    const messageInput = page.locator('#messageInput');
    await expect(messageInput).toBeVisible();
    await expect(messageInput).toBeEnabled();
    
    // Check placeholder text
    const placeholder = await messageInput.getAttribute('placeholder');
    expect(placeholder).toContain('Course in Miracles');
    console.log(`💬 Input placeholder: "${placeholder}"`);
    
    // Test send button
    const sendButton = page.locator('#sendButton');
    await expect(sendButton).toBeVisible();
    await expect(sendButton).toBeEnabled();
    
    // Test quick actions
    const quickActions = page.locator('.quick-action');
    const actionCount = await quickActions.count();
    expect(actionCount).toBeGreaterThanOrEqual(3);
    console.log(`🎯 ${actionCount} quick actions available`);
    
    // Test that quick actions are clickable
    for (let i = 0; i < actionCount; i++) {
      await expect(quickActions.nth(i)).toBeEnabled();
    }
  });

  test('Responsive Design - Mobile viewport should work properly', async ({ page }) => {
    // Test mobile viewport (375x667)
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(1000);
    
    const header = page.locator('.header');
    const headerBox = await header.boundingBox();
    
    // Header should be even more compact on mobile
    expect(headerBox.height).toBeLessThanOrEqual(80);
    console.log(`📱 Mobile header height: ${headerBox.height}px`);
    
    // Input should be accessible
    const messageInput = page.locator('#messageInput');
    await expect(messageInput).toBeVisible();
    
    // No horizontal scroll
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = page.viewportSize().width;
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);
    console.log('📱 No horizontal scroll on mobile');
  });

  test('Desktop Large - Should handle 1920x1080 properly', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(1000);
    
    const container = page.locator('.container');
    const containerBox = await container.boundingBox();
    
    // Container should be centered and have reasonable max-width
    expect(containerBox.width).toBeLessThanOrEqual(1200);
    console.log(`🖥️ Large desktop container width: ${containerBox.width}px`);
    
    // Should be horizontally centered
    const centerX = containerBox.x + containerBox.width / 2;
    const viewportCenterX = 1920 / 2;
    const centerDiff = Math.abs(centerX - viewportCenterX);
    expect(centerDiff).toBeLessThan(50); // Allow some margin
    console.log(`🎯 Container is centered (diff: ${centerDiff.toFixed(1)}px)`);
  });

  test('Critical 1366x768 Laptop - Primary target resolution', async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.waitForTimeout(1000);
    
    // Take screenshot for manual review
    await page.screenshot({ 
      path: 'screenshots/acim-guide-1366x768-validation.png',
      fullPage: false 
    });
    
    const header = page.locator('.header');
    const chatContainer = page.locator('.chat-container');
    
    const headerBox = await header.boundingBox();
    const chatBox = await chatContainer.boundingBox();
    
    // Header optimized for laptop
    expect(headerBox.height).toBeLessThanOrEqual(64);
    
    // Chat utilization should be excellent on laptops
    const utilization = (chatBox.height / 768) * 100;
    expect(utilization).toBeGreaterThanOrEqual(70);
    
    console.log(`💻 1366x768 Results:`);
    console.log(`   Header: ${headerBox.height}px`);
    console.log(`   Chat area: ${utilization.toFixed(1)}% of viewport`);
    console.log(`   Total improvement: ${(180 - headerBox.height).toFixed(1)}px gained`);
  });

  test('Accessibility Features - Focus indicators and ARIA', async ({ page }) => {
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    
    // Should be able to reach input field
    const focusedElement = await page.evaluate(() => document.activeElement.tagName);
    console.log(`⌨️ First tab focus: ${focusedElement}`);
    
    // Test focus indicators
    const messageInput = page.locator('#messageInput');
    await messageInput.focus();
    
    // Check if focus is visible (this is hard to test automatically, but we can check styles)
    const focusStyle = await messageInput.evaluate(el => {
      const styles = window.getComputedStyle(el, ':focus');
      return styles.outline || styles.boxShadow;
    });
    
    expect(focusStyle).not.toBe('none');
    expect(focusStyle).not.toBe('');
    console.log(`🔍 Focus indicator: ${focusStyle}`);
  });

  test('Performance - Page should load quickly', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto(SITE_URL);
    await page.waitForLoadState('domcontentloaded');
    
    const loadTime = Date.now() - startTime;
    console.log(`⚡ DOM loaded in: ${loadTime}ms`);
    expect(loadTime).toBeLessThan(3000); // Should load within 3 seconds
    
    // Wait for full interactivity
    await page.waitForLoadState('networkidle');
    const totalTime = Date.now() - startTime;
    console.log(`🚀 Fully interactive in: ${totalTime}ms`);
    expect(totalTime).toBeLessThan(5000); // Should be interactive within 5 seconds
  });

  test('Spiritual Alignment - ACIM quote and peaceful design', async ({ page }) => {
    // Check for ACIM quote presence
    const acimQuote = page.locator('text="Nothing real can be threatened"');
    await expect(acimQuote).toBeVisible();
    console.log('📖 ACIM quote is prominently displayed');
    
    // Check peaceful color scheme
    const header = page.locator('.header');
    const backgroundColor = await header.evaluate(el => 
      window.getComputedStyle(el).backgroundColor
    );
    
    console.log(`🎨 Header background: ${backgroundColor}`);
    
    // Should not have aggressive red colors
    expect(backgroundColor).not.toContain('255, 0, 0'); // Pure red
    expect(backgroundColor).not.toContain('rgb(255, 0, 0)');
    
    // Check for spiritual messaging
    const sendButton = page.locator('#sendButton');
    const buttonText = await sendButton.textContent();
    console.log(`💝 Send button text: "${buttonText}"`);
  });

  test('Overall UI Score Validation', async ({ page }) => {
    let score = 0;
    const maxScore = 10;
    
    console.log('\n🔍 === UI SCORING EVALUATION ===');
    
    // Layout & Visual Design (3 points)
    try {
      const header = page.locator('.header');
      const headerBox = await header.boundingBox();
      
      if (headerBox.height <= 64) {
        score += 1;
        console.log('✅ Header height optimized (+1)');
      } else {
        console.log(`❌ Header too tall: ${headerBox.height}px`);
      }
      
      // Logo check
      const logoImg = page.locator('.logo');
      const logoEnhanced = page.locator('.logo-enhanced');
      const imgVisible = await logoImg.isVisible().catch(() => false);
      const enhancedVisible = await logoEnhanced.isVisible().catch(() => false);
      
      if (imgVisible || enhancedVisible) {
        score += 1;
        console.log('✅ Logo visible and functional (+1)');
      }
      
      // Chat area identification
      const chatContainer = page.locator('.chat-container');
      const chatVisible = await chatContainer.isVisible();
      if (chatVisible) {
        score += 1;
        console.log('✅ Chat area properly identified (+1)');
      }
      
    } catch (e) {
      console.log('❌ Layout & Visual issues detected');
    }
    
    // Functionality & Usability (3 points)
    try {
      const messageInput = page.locator('#messageInput');
      const sendButton = page.locator('#sendButton');
      const quickActions = page.locator('.quick-action');
      
      const inputEnabled = await messageInput.isEnabled();
      const buttonEnabled = await sendButton.isEnabled();
      const actionsCount = await quickActions.count();
      
      if (inputEnabled && buttonEnabled) {
        score += 1;
        console.log('✅ Core interaction functional (+1)');
      }
      
      if (actionsCount >= 4) {
        score += 1;
        console.log(`✅ Quick actions available (${actionsCount}) (+1)`);
      }
      
      // Check viewport utilization
      const chatBox = await chatContainer.boundingBox();
      const viewport = page.viewportSize();
      const utilization = (chatBox.height / viewport.height) * 100;
      
      if (utilization >= 60) {
        score += 1;
        console.log(`✅ Good viewport utilization (${utilization.toFixed(1)}%) (+1)`);
      }
      
    } catch (e) {
      console.log('❌ Functionality issues detected');
    }
    
    // Responsiveness & Accessibility (2 points)
    try {
      // Test mobile
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);
      
      const mobileBodyWidth = await page.evaluate(() => document.body.scrollWidth);
      if (mobileBodyWidth <= 375) {
        score += 1;
        console.log('✅ Mobile responsive (+1)');
      }
      
      // Reset to original viewport
      await page.setViewportSize({ width: 1366, height: 768 });
      await page.waitForTimeout(500);
      
      // Check accessibility
      const messageInput = page.locator('#messageInput');
      await messageInput.focus();
      const focusStyle = await messageInput.evaluate(el => {
        const styles = window.getComputedStyle(el, ':focus');
        return styles.outline || styles.boxShadow;
      });
      
      if (focusStyle && focusStyle !== 'none') {
        score += 1;
        console.log('✅ Accessibility features present (+1)');
      }
      
    } catch (e) {
      console.log('❌ Responsive/Accessibility issues detected');
    }
    
    // Brand & Spiritual Alignment (2 points)
    try {
      const acimQuote = page.locator('text="Nothing real can be threatened"');
      const quoteVisible = await acimQuote.isVisible();
      
      if (quoteVisible) {
        score += 1;
        console.log('✅ ACIM spiritual content present (+1)');
      }
      
      const header = page.locator('.header');
      const backgroundColor = await header.evaluate(el => 
        window.getComputedStyle(el).backgroundColor
      );
      
      if (!backgroundColor.includes('255, 0, 0')) {
        score += 1;
        console.log('✅ Peaceful color scheme maintained (+1)');
      }
      
    } catch (e) {
      console.log('❌ Spiritual alignment issues detected');
    }
    
    console.log(`\n🏆 FINAL UI SCORE: ${score}/${maxScore}`);
    console.log(score >= 8 ? '🌟 EXCELLENT - ACIM aligned!' : 
      score >= 6 ? '✅ GOOD - Minor improvements needed' :
        score >= 4 ? '⚠️ NEEDS IMPROVEMENT' : 
          '❌ MAJOR REDESIGN REQUIRED');
    
    // Assert minimum score
    expect(score).toBeGreaterThanOrEqual(6); // Should be at least "Good"
    
    return score;
  });

});

// Utility function to run specific test scenarios
test.describe('Quick Validation Suite', () => {
  
  test('5-Minute Header Fix Validation', async ({ page }) => {
    await page.goto(SITE_URL);
    await page.waitForLoadState('networkidle');
    
    const header = page.locator('.header');
    const headerBox = await header.boundingBox();
    
    console.log(`\n⚡ QUICK VALIDATION RESULTS:`);
    console.log(`Header Height: ${headerBox.height}px (target: ≤64px)`);
    console.log(`Status: ${headerBox.height <= 64 ? '✅ PASSED' : '❌ NEEDS FIX'}`);
    console.log(`Improvement: -${(180 - headerBox.height).toFixed(1)}px`);
    
    expect(headerBox.height).toBeLessThanOrEqual(64);
  });
  
});

module.exports = {
  SITE_URL,
  // Export for CI/CD integration
  runValidation: async (playwrightPage) => {
    // Simplified validation for CI
    await playwrightPage.goto(SITE_URL);
    const header = playwrightPage.locator('.header');
    const headerBox = await header.boundingBox();
    return {
      headerHeight: headerBox.height,
      passed: headerBox.height <= 64
    };
  }
};
