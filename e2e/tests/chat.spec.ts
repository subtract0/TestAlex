import { test, expect } from '@playwright/test';
import { ChatPage } from '../utils/chat-page';

test.describe('Chat Interface E2E Tests', () => {
  let chatPage: ChatPage;

  test.beforeEach(async ({ page }) => {
    chatPage = new ChatPage(page);
    await chatPage.navigateToChat();
  });

  test('should display chat interface correctly', async ({ page }) => {
    // Verify chat container is visible
    await expect(page.locator('[data-testid="chat-container"], .chat-container')).toBeVisible();
    
    // Verify input and send button are present
    await expect(page.locator('input, textarea')).toBeVisible();
    await expect(page.locator('button:has-text("Send"), button[type="submit"]')).toBeVisible();
  });

  test('should send and receive messages', async ({ page }) => {
    const testMessage = 'What is lesson 1 of ACIM about?';
    
    await chatPage.sendMessage(testMessage);
    const response = await chatPage.waitForAIResponse();
    
    expect(response.length).toBeGreaterThan(20);
    expect(response.toLowerCase()).toMatch(/lesson|acim|miracle|perception|forgiveness/);
  });

  test('should validate ACIM content authenticity', async ({ page }) => {
    await chatPage.testACIMConversation();
  });

  test('should handle quick actions', async ({ page }) => {
    await chatPage.testQuickActions();
  });

  test('should handle error scenarios gracefully', async ({ page }) => {
    await chatPage.testErrorHandling();
  });

  test('should be accessible via keyboard navigation', async ({ page }) => {
    await chatPage.testChatAccessibility();
  });

  test('should perform well under load', async ({ page }) => {
    await chatPage.testChatPerformance();
  });

  test('should work correctly on mobile devices', async ({ page }) => {
    await chatPage.testMobileChat();
  });

  test('should allow clearing chat history', async ({ page }) => {
    // Send a test message first
    await chatPage.sendMessage('Test message for clearing');
    await chatPage.waitForAIResponse();
    
    // Then clear chat
    await chatPage.clearChat();
  });

  test('should handle special ACIM queries', async ({ page }) => {
    const specialQueries = [
      'Show me today\'s workbook lesson',
      'What does the Course say about the Holy Spirit?',
      'Help me understand forgiveness',
      'Explain the difference between perception and knowledge',
      'What is a miracle according to ACIM?'
    ];

    for (const query of specialQueries) {
      await chatPage.sendMessage(query);
      const response = await chatPage.waitForAIResponse();
      
      // Verify response quality
      expect(response.length).toBeGreaterThan(50);
      expect(response).not.toContain('error');
      expect(response).not.toContain('I don\'t know');
      
      // Verify ACIM-specific content
      expect(response.toLowerCase()).toMatch(/course|acim|lesson|holy spirit|forgiveness|miracle/);
    }
  });

  test('should maintain conversation context', async ({ page }) => {
    // Send initial message
    await chatPage.sendMessage('Tell me about ACIM lesson 1');
    const firstResponse = await chatPage.waitForAIResponse();
    
    // Send follow-up that requires context
    await chatPage.sendMessage('Can you explain that in simpler terms?');
    const secondResponse = await chatPage.waitForAIResponse();
    
    expect(firstResponse.length).toBeGreaterThan(20);
    expect(secondResponse.length).toBeGreaterThan(20);
    expect(secondResponse.toLowerCase()).toMatch(/lesson|simple|explain/);
  });

  test('should handle long conversations', async ({ page }) => {
    // Simulate a longer conversation
    const conversationFlow = [
      'What is ACIM?',
      'How many lessons are in the workbook?',
      'What\'s the main goal of the course?',
      'Tell me about forgiveness',
      'How do I practice daily lessons?'
    ];

    for (let i = 0; i < conversationFlow.length; i++) {
      const query = conversationFlow[i];
      await chatPage.sendMessage(query);
      const response = await chatPage.waitForAIResponse();
      
      expect(response.length).toBeGreaterThan(30);
      console.log(`Message ${i + 1}: "${query}" -> Response length: ${response.length}`);
    }
  });

  test('should handle network interruptions gracefully', async ({ page }) => {
    // Test offline scenario simulation
    await page.context().setOffline(true);
    
    await chatPage.sendMessage('Test message while offline');
    
    // Wait a bit for error handling
    await page.waitForTimeout(3000);
    
    // Re-enable network
    await page.context().setOffline(false);
    
    // Should recover and work normally
    await chatPage.sendMessage('Test message after reconnection');
    const response = await chatPage.waitForAIResponse();
    
    expect(response.length).toBeGreaterThan(0);
  });
});
