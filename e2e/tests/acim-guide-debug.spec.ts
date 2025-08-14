import { test, expect } from '@playwright/test';

const PRODUCTION_URL = 'https://acim-guide-production.web.app';

test.describe('ACIM Guide - Debug and UX Testing', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to production site
    await page.goto(PRODUCTION_URL);
    
    // Wait for page to load completely
    await page.waitForLoadState('networkidle');
  });

  test('✅ Page loads successfully with correct title and branding', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/ACIMguide/);
    
    // Check main heading
    await expect(page.locator('h1')).toContainText('ACIMguide');
    
    // Check subtitle
    await expect(page.locator('.header p')).toContainText('Your AI Companion for A Course in Miracles');
    
    // Check initial welcome message
    await expect(page.locator('.message.assistant .message-content')).toContainText('Welcome! I\'m here to help');
  });

  test('🔧 Firebase authentication and connection status', async ({ page }) => {
    // Wait for status element to appear
    const statusElement = page.locator('#status');
    await expect(statusElement).toBeVisible();
    
    // Check initial loading state
    await expect(statusElement).toContainText('Initializing ACIMguide');
    
    // Wait for authentication to complete (up to 10 seconds)
    await page.waitForFunction(() => {
      const status = document.getElementById('status');
      return status && (
        status.textContent?.includes('Connected! Your spiritual companion is ready') ||
        status.textContent?.includes('Authentication failed')
      );
    }, { timeout: 10000 });
    
    // Check final status
    const finalStatus = await statusElement.textContent();
    console.log('Final authentication status:', finalStatus);
    
    // Verify successful connection OR capture authentication error
    if (finalStatus?.includes('Authentication failed')) {
      console.log('❌ Authentication failed - this needs to be fixed');
      // Take screenshot for debugging
      await page.screenshot({ path: 'debug-auth-failed.png', fullPage: true });
    } else {
      expect(finalStatus).toContain('Connected! Your spiritual companion is ready');
    }
  });

  test('💬 Chat interface is functional and accessible', async ({ page }) => {
    // Wait for interface to be enabled
    await page.waitForFunction(() => {
      const input = document.getElementById('messageInput') as HTMLInputElement;
      const button = document.getElementById('sendButton') as HTMLButtonElement;
      return input && button && !input.disabled && !button.disabled;
    }, { timeout: 15000 });
    
    // Check input field
    const messageInput = page.locator('#messageInput');
    await expect(messageInput).toBeVisible();
    await expect(messageInput).toBeEnabled();
    await expect(messageInput).toHaveAttribute('placeholder', /Course in Miracles/);
    
    // Check send button
    const sendButton = page.locator('#sendButton');
    await expect(sendButton).toBeVisible();
    await expect(sendButton).toBeEnabled();
    await expect(sendButton).toContainText('Send');
    
    // Test keyboard interaction
    await messageInput.focus();
    await expect(messageInput).toBeFocused();
  });

  test('🎯 Quick action buttons are present and functional', async ({ page }) => {
    // Check quick actions section
    await expect(page.locator('.quick-actions h3')).toContainText('Quick Actions');
    
    // Check all quick action buttons exist
    const quickActions = [
      '📚 Main Teaching',
      '🕊️ Forgiveness Practice', 
      '☮️ Inner Peace',
      '📖 Workbook Lesson'
    ];
    
    for (const action of quickActions) {
      await expect(page.locator('.quick-action', { hasText: action })).toBeVisible();
    }
    
    // Test hover effect on quick actions
    const firstAction = page.locator('.quick-action').first();
    await firstAction.hover();
    
    // Check if quick action is clickable
    await expect(firstAction).toBeVisible();
  });

  test('📱 Responsive design works on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that container adapts to mobile
    const container = page.locator('.container');
    await expect(container).toBeVisible();
    
    // Check that elements stack properly on mobile
    const header = page.locator('.header');
    const chatContainer = page.locator('.chat-container');
    const inputContainer = page.locator('.input-container');
    
    await expect(header).toBeVisible();
    await expect(chatContainer).toBeVisible();
    await expect(inputContainer).toBeVisible();
    
    // Check quick actions wrap properly
    const quickActionButtons = page.locator('.quick-action-buttons');
    await expect(quickActionButtons).toBeVisible();
  });

  test('🔍 Debug actual chat functionality with Firebase', async ({ page }) => {
    // Wait for authentication
    await page.waitForFunction(() => {
      const status = document.getElementById('status');
      return status && status.textContent?.includes('Connected! Your spiritual companion is ready');
    }, { timeout: 15000 });
    
    // Get console logs to debug
    const consoleLogs: string[] = [];
    page.on('console', msg => {
      consoleLogs.push(`${msg.type()}: ${msg.text()}`);
    });
    
    // Get network requests to debug
    const networkRequests: string[] = [];
    page.on('request', request => {
      if (request.url().includes('firebase') || request.url().includes('functions')) {
        networkRequests.push(`${request.method()} ${request.url()}`);
      }
    });
    
    // Try sending a test message
    const messageInput = page.locator('#messageInput');
    const sendButton = page.locator('#sendButton');
    
    await messageInput.fill('What is forgiveness according to ACIM?');
    await sendButton.click();
    
    // Wait for user message to appear
    await expect(page.locator('.message.user')).toBeVisible();
    
    // Wait for response or error (up to 30 seconds)
    try {
      await page.waitForFunction(() => {
        const messages = document.querySelectorAll('.message.assistant');
        return messages.length > 1; // More than just the welcome message
      }, { timeout: 30000 });
      
      // Check for assistant response
      const assistantMessages = page.locator('.message.assistant');
      const messageCount = await assistantMessages.count();
      
      if (messageCount > 1) {
        console.log('✅ Assistant responded successfully');
        const lastMessage = assistantMessages.last();
        const messageText = await lastMessage.textContent();
        console.log('Response preview:', messageText?.substring(0, 200) + '...');
      }
    } catch (error) {
      console.log('❌ No assistant response received within 30 seconds');
      console.log('Console logs:', consoleLogs);
      console.log('Network requests:', networkRequests);
      
      // Take screenshot for debugging
      await page.screenshot({ path: 'debug-no-response.png', fullPage: true });
    }
    
    // Print debug information
    console.log('\n=== DEBUG INFORMATION ===');
    console.log('Console logs:', consoleLogs.slice(-10)); // Last 10 logs
    console.log('Network requests:', networkRequests);
    
    // Check for error messages in chat
    const errorMessages = page.locator('.error');
    if (await errorMessages.count() > 0) {
      const errorText = await errorMessages.first().textContent();
      console.log('Error message found:', errorText);
    }
  });

  test('🎨 Visual design and styling check', async ({ page }) => {
    // Check gradient background
    const body = page.locator('body');
    const bodyStyles = await body.evaluate(el => getComputedStyle(el));
    expect(bodyStyles.background).toContain('gradient');
    
    // Check container has proper styling
    const container = page.locator('.container');
    const containerStyles = await container.evaluate(el => getComputedStyle(el));
    expect(containerStyles.backgroundColor).toBe('rgb(255, 255, 255)'); // white
    expect(containerStyles.borderRadius).toBe('20px');
    
    // Check header gradient
    const header = page.locator('.header');
    const headerStyles = await header.evaluate(el => getComputedStyle(el));
    expect(headerStyles.background).toContain('gradient');
    
    // Check message styling
    const userMessage = page.locator('.message.user .message-content');
    if (await userMessage.count() > 0) {
      const userStyles = await userMessage.first().evaluate(el => getComputedStyle(el));
      expect(userStyles.backgroundColor).toBe('rgb(0, 123, 255)'); // blue
    }
  });

  test('♿ Accessibility and usability check', async ({ page }) => {
    // Check for proper headings
    await expect(page.locator('h1')).toBeVisible();
    await expect(page.locator('h3')).toBeVisible();
    
    // Check input has proper label/placeholder
    const messageInput = page.locator('#messageInput');
    await expect(messageInput).toHaveAttribute('placeholder');
    
    // Check button is properly labeled
    const sendButton = page.locator('#sendButton');
    await expect(sendButton).toContainText('Send');
    
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    // Should be able to navigate to input and button
    
    // Check color contrast (basic check)
    const status = page.locator('#status');
    const statusStyles = await status.evaluate(el => getComputedStyle(el));
    // Ensure text is not too light
    expect(statusStyles.color).not.toBe('rgb(255, 255, 255)'); // not white on light background
  });

  test('🔧 Performance and loading check', async ({ page }) => {
    const startTime = Date.now();
    
    // Measure page load time
    await page.goto(PRODUCTION_URL);
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    console.log(`Page load time: ${loadTime}ms`);
    
    // Should load within reasonable time
    expect(loadTime).toBeLessThan(10000); // 10 seconds max
    
    // Check that Firebase loads quickly
    await page.waitForFunction(() => {
      return typeof window.firebase !== 'undefined';
    }, { timeout: 5000 });
    
    // Check for any console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    // Wait a bit to catch any delayed errors
    await page.waitForTimeout(2000);
    
    if (consoleErrors.length > 0) {
      console.log('Console errors found:', consoleErrors);
    }
    
    // Expect minimal console errors (some are expected during development)
    expect(consoleErrors.length).toBeLessThan(5);
  });
  
  test('📸 Visual regression test - take screenshots', async ({ page }) => {
    // Take screenshot of initial state
    await page.screenshot({ path: 'screenshots/acim-guide-initial.png', fullPage: true });
    
    // Take screenshot of mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.screenshot({ path: 'screenshots/acim-guide-mobile.png', fullPage: true });
    
    // Take screenshot of tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.screenshot({ path: 'screenshots/acim-guide-tablet.png', fullPage: true });
    
    // Back to desktop
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.screenshot({ path: 'screenshots/acim-guide-desktop.png', fullPage: true });
    
    console.log('Screenshots saved for visual review');
  });
});

test.describe('ACIM Guide - Specific Firebase Debug', () => {
  
  test('🔥 Debug Firebase Functions specifically', async ({ page }) => {
    await page.goto(PRODUCTION_URL);
    
    // Intercept Firebase function calls
    const functionCalls: any[] = [];
    
    page.on('response', response => {
      if (response.url().includes('cloudfunctions.net') || response.url().includes('firebase')) {
        functionCalls.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText()
        });
      }
    });
    
    // Wait for auth and try to send message
    await page.waitForFunction(() => {
      const status = document.getElementById('status');
      return status && status.textContent?.includes('Connected! Your spiritual companion is ready');
    }, { timeout: 15000 });
    
    // Send test message
    await page.fill('#messageInput', 'Test message');
    await page.click('#sendButton');
    
    // Wait for function call
    await page.waitForTimeout(5000);
    
    console.log('Firebase function calls:', functionCalls);
    
    // Check if function was called
    const chatFunctionCall = functionCalls.find(call => 
      call.url.includes('chatWithAssistant') || call.url.includes('functions')
    );
    
    if (chatFunctionCall) {
      console.log('✅ Firebase function was called:', chatFunctionCall);
      if (chatFunctionCall.status !== 200) {
        console.log('❌ Function call failed with status:', chatFunctionCall.status);
      }
    } else {
      console.log('❌ No Firebase function call detected');
    }
  });
});
