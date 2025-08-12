import { Page, expect, Locator } from '@playwright/test';
import { TestHelpers } from './test-helpers';

export class ChatPage {
  private helpers: TestHelpers;
  
  // Chat interface selectors
  private chatContainer: Locator;
  private messageInput: Locator;
  private sendButton: Locator;
  private messagesList: Locator;
  private typingIndicator: Locator;
  private quickActions: Locator;
  private clearChatButton: Locator;

  constructor(private page: Page) {
    this.helpers = new TestHelpers(page);
    
    // Initialize locators - adjust selectors based on actual app structure
    this.chatContainer = page.locator('[data-testid="chat-container"]');
    this.messageInput = page.locator('[data-testid="message-input"], input[placeholder*="message"], textarea[placeholder*="message"]');
    this.sendButton = page.locator('[data-testid="send-button"], button[type="submit"], button:has-text("Send")');
    this.messagesList = page.locator('[data-testid="messages-list"], .messages, .chat-messages');
    this.typingIndicator = page.locator('[data-testid="typing-indicator"], .typing-indicator');
    this.quickActions = page.locator('[data-testid="quick-actions"], .quick-actions');
    this.clearChatButton = page.locator('[data-testid="clear-chat"], button:has-text("Clear")');
  }

  /**
   * Navigate to chat interface
   */
  async navigateToChat(): Promise<void> {
    await this.page.goto('/chat');
    await this.helpers.waitForNetworkIdle();
    await this.helpers.waitForStableElement(this.chatContainer);
  }

  /**
   * Send a message in the chat
   */
  async sendMessage(message: string): Promise<void> {
    await this.helpers.waitForStableElement(this.messageInput);
    await this.messageInput.fill(message);
    await this.sendButton.click();
    
    // Wait for message to appear in chat
    await expect(this.messagesList).toContainText(message);
    await this.helpers.waitForNetworkIdle();
  }

  /**
   * Wait for AI response
   */
  async waitForAIResponse(timeout = 30000): Promise<string> {
    // Wait for typing indicator to appear and disappear
    await this.typingIndicator.waitFor({ state: 'visible', timeout: 5000 }).catch(() => {
      // If no typing indicator, that's okay
    });
    
    await this.typingIndicator.waitFor({ state: 'hidden', timeout }).catch(() => {
      // If typing indicator doesn't appear, still wait for response
    });
    
    // Get the latest message (should be the AI response)
    const messages = this.messagesList.locator('[data-testid="message"], .message');
    const lastMessage = messages.last();
    await this.helpers.waitForStableElement(lastMessage);
    
    const responseText = await lastMessage.textContent() || '';
    return responseText;
  }

  /**
   * Test ACIM-specific conversation flow
   */
  async testACIMConversation(): Promise<void> {
    // Test different types of ACIM queries
    const acimQueries = [
      "What is lesson 1 about?",
      "Explain forgiveness according to ACIM",
      "Tell me about the Holy Spirit",
      "How do I practice today's lesson?",
      "What does ACIM say about miracles?"
    ];

    for (const query of acimQueries) {
      await this.sendMessage(query);
      const response = await this.waitForAIResponse();
      
      // Validate that response contains ACIM content
      const isValidACIMResponse = await this.helpers.validateACIMContent(response);
      expect(isValidACIMResponse).toBeTruthy();
      
      // Check response quality
      expect(response.length).toBeGreaterThan(50); // Substantial response
      expect(response).not.toContain('error'); // No error messages
      expect(response).not.toContain('I don\'t know'); // Should have ACIM knowledge
    }
  }

  /**
   * Test chat functionality with quick actions
   */
  async testQuickActions(): Promise<void> {
    if (await this.quickActions.count() > 0) {
      const quickActionButtons = this.quickActions.locator('button');
      const count = await quickActionButtons.count();
      
      for (let i = 0; i < Math.min(count, 3); i++) { // Test first 3 quick actions
        const button = quickActionButtons.nth(i);
        const buttonText = await button.textContent();
        
        await button.click();
        await this.helpers.waitForNetworkIdle();
        
        // Verify that clicking the quick action resulted in some chat activity
        const messagesCount = await this.messagesList.locator('[data-testid="message"], .message').count();
        expect(messagesCount).toBeGreaterThan(0);
      }
    }
  }

  /**
   * Test chat performance under load
   */
  async testChatPerformance(): Promise<void> {
    const startTime = Date.now();
    
    // Send multiple messages quickly
    const messages = [
      "Test message 1",
      "Test message 2", 
      "Test message 3"
    ];
    
    for (const msg of messages) {
      await this.sendMessage(msg);
    }
    
    // Wait for all responses
    for (let i = 0; i < messages.length; i++) {
      await this.waitForAIResponse();
    }
    
    const endTime = Date.now();
    const totalTime = endTime - startTime;
    
    // Performance assertion - should handle 3 messages in under 2 minutes
    expect(totalTime).toBeLessThan(120000);
  }

  /**
   * Test chat error handling
   */
  async testErrorHandling(): Promise<void> {
    // Test very long message
    const longMessage = "A".repeat(5000);
    await this.messageInput.fill(longMessage);
    await this.sendButton.click();
    
    // Should handle gracefully - either process or show appropriate error
    await this.page.waitForTimeout(2000);
    
    // Test empty message
    await this.messageInput.fill("");
    const isDisabled = await this.sendButton.isDisabled();
    expect(isDisabled).toBeTruthy(); // Send button should be disabled for empty messages
  }

  /**
   * Test chat accessibility
   */
  async testChatAccessibility(): Promise<void> {
    // Test keyboard navigation
    await this.messageInput.press('Tab');
    await expect(this.sendButton).toBeFocused();
    
    // Test ARIA labels
    const inputAriaLabel = await this.messageInput.getAttribute('aria-label');
    expect(inputAriaLabel).toBeTruthy();
    
    // Test screen reader support
    const chatRole = await this.chatContainer.getAttribute('role');
    expect(chatRole).toMatch(/log|region|main/);
  }

  /**
   * Clear chat history
   */
  async clearChat(): Promise<void> {
    if (await this.clearChatButton.isVisible()) {
      await this.clearChatButton.click();
      
      // Confirm clear if there's a confirmation dialog
      const confirmButton = this.page.locator('button:has-text("Confirm"), button:has-text("Yes"), button:has-text("OK")');
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
      }
      
      // Verify chat is cleared
      await this.helpers.waitForNetworkIdle();
      const messagesCount = await this.messagesList.locator('[data-testid="message"], .message').count();
      expect(messagesCount).toBe(0);
    }
  }

  /**
   * Test responsive design on mobile
   */
  async testMobileChat(): Promise<void> {
    await this.helpers.setMobileViewport();
    await this.page.reload();
    await this.helpers.waitForNetworkIdle();
    
    // Chat should still be functional on mobile
    await expect(this.chatContainer).toBeVisible();
    await expect(this.messageInput).toBeVisible();
    await expect(this.sendButton).toBeVisible();
    
    // Test mobile-specific interactions
    await this.sendMessage("Mobile test message");
    const response = await this.waitForAIResponse();
    expect(response.length).toBeGreaterThan(0);
  }
}
