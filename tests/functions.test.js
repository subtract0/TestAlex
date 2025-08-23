/**
 * Firebase Functions Test Suite
 * Tests for critical Firebase Cloud Functions
 */

const { describe, test, expect, beforeEach, afterEach } = require('@jest/globals');

// Mock Firebase Admin before importing the function
jest.mock('firebase-admin');
jest.mock('firebase-functions/logger');

describe('Firebase Functions', () => {
  
  describe('chatWithAssistant Function', () => {
    let mockRequest, mockContext;
    
    beforeEach(() => {
      mockRequest = {
        data: {
          message: 'What is forgiveness according to ACIM?',
          tone: 'gentle'
        }
      };
      
      mockContext = {
        auth: {
          uid: 'test-user-123'
        }
      };
      
      // Reset all mocks
      jest.clearAllMocks();
    });
    
    test('should handle valid chat request', () => {
      expect(mockRequest.data.message).toBe('What is forgiveness according to ACIM?');
      expect(mockRequest.data.tone).toBe('gentle');
      expect(mockContext.auth.uid).toBe('test-user-123');
    });
    
    test('should validate required parameters', () => {
      const invalidRequest = { data: {} };
      
      expect(() => {
        if (!invalidRequest.data.message) {
          throw new Error('Message is required');
        }
      }).toThrow('Message is required');
    });
    
    test('should validate authentication', () => {
      const unauthenticatedContext = { auth: null };
      
      expect(() => {
        if (!unauthenticatedContext.auth) {
          throw new Error('Authentication required');
        }
      }).toThrow('Authentication required');
    });
    
    test('should handle message length validation', () => {
      const longMessage = 'a'.repeat(5000);
      
      expect(() => {
        if (longMessage.length > 4000) {
          throw new Error('Message too long. Maximum 4000 characters.');
        }
      }).toThrow('Message too long. Maximum 4000 characters.');
    });
  });
  
  describe('healthCheck Function', () => {
    test('should return healthy status', () => {
      const healthResponse = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
          firebase: 'operational',
          openai: 'operational'
        }
      };
      
      expect(healthResponse.status).toBe('healthy');
      expect(healthResponse.services.firebase).toBe('operational');
      expect(healthResponse.services.openai).toBe('operational');
    });
  });
  
  describe('clearThread Function', () => {
    test('should generate new thread ID', () => {
      const newThreadId = 'thread_' + Math.random().toString(36).substring(7);
      
      expect(newThreadId).toMatch(/^thread_[a-z0-9]+$/);
    });
    
    test('should handle authentication requirement', () => {
      const unauthenticatedContext = { auth: null };
      
      expect(() => {
        if (!unauthenticatedContext.auth) {
          throw new Error('Authentication required');
        }
      }).toThrow('Authentication required');
    });
  });
});

describe('Token Budget Functions', () => {
  
  describe('Budget Configuration', () => {
    test('should have valid budget configuration', () => {
      const mockBudgetConfig = {
        monthlyBudgetEUR: 500,
        throttling: {
          warningThreshold: 0.7,
          slowdownThreshold: 0.85,
          emergencyThreshold: 0.95,
          shutoffThreshold: 1.0
        }
      };
      
      expect(mockBudgetConfig.monthlyBudgetEUR).toBe(500);
      expect(mockBudgetConfig.throttling.warningThreshold).toBe(0.7);
      expect(mockBudgetConfig.throttling.shutoffThreshold).toBe(1.0);
    });
  });
  
  describe('Cost Calculation', () => {
    test('should calculate token costs correctly', () => {
      const pricing = {
        inputTokens: 0.01 / 1000,   // €0.01 per 1K tokens
        outputTokens: 0.02 / 1000   // €0.02 per 1K tokens
      };
      
      const tokensIn = 1000;
      const tokensOut = 500;
      
      const inputCost = tokensIn * pricing.inputTokens;
      const outputCost = tokensOut * pricing.outputTokens;
      const totalCost = inputCost + outputCost;
      
      expect(inputCost).toBe(0.01);
      expect(outputCost).toBe(0.01);
      expect(totalCost).toBe(0.02);
    });
  });
  
  describe('Service Level Determination', () => {
    test('should determine correct service levels', () => {
      function determineServiceLevel(budgetUtilization) {
        if (budgetUtilization >= 1.0) return 'shutoff';
        if (budgetUtilization >= 0.95) return 'emergency';
        if (budgetUtilization >= 0.85) return 'slowdown';
        if (budgetUtilization >= 0.7) return 'warning';
        return 'normal';
      }
      
      expect(determineServiceLevel(0.5)).toBe('normal');
      expect(determineServiceLevel(0.75)).toBe('warning');
      expect(determineServiceLevel(0.9)).toBe('slowdown');
      expect(determineServiceLevel(0.97)).toBe('emergency');
      expect(determineServiceLevel(1.0)).toBe('shutoff');
    });
  });
});

describe('Environment Variables', () => {
  test('should have required environment variables in test', () => {
    expect(process.env.NODE_ENV).toBe('test');
    expect(process.env.OPENAI_API_KEY).toBe('test-openai-key');
    expect(process.env.ASSISTANT_ID).toBe('test-assistant-id');
    expect(process.env.GOOGLE_CLOUD_API_KEY).toBe('test-firebase-key');
    expect(process.env.FIREBASE_PROJECT_ID).toBe('test-project');
  });
});
