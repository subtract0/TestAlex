/**
 * Jest Test Setup for ACIM Guide
 * Configures test environment for Firebase, Node.js, and web testing
 */

// Polyfills for Node.js environment
global.TextEncoder = require('util').TextEncoder;
global.TextDecoder = require('util').TextDecoder;

// Mock Firebase Admin SDK for tests
jest.mock('firebase-admin', () => ({
  apps: [],
  initializeApp: jest.fn(() => ({
    firestore: jest.fn(() => ({
      collection: jest.fn(() => ({
        doc: jest.fn(() => ({
          set: jest.fn(),
          get: jest.fn(() => Promise.resolve({ exists: false, data: () => ({}) })),
          update: jest.fn(),
          delete: jest.fn()
        })),
        add: jest.fn(() => Promise.resolve({ id: 'test-doc-id' })),
        where: jest.fn(() => ({
          limit: jest.fn(() => ({
            get: jest.fn(() => Promise.resolve({ empty: true, docs: [] }))
          }))
        }))
      }))
    }))
  })),
  firestore: jest.fn(() => ({
    collection: jest.fn(() => ({
      doc: jest.fn(),
      add: jest.fn()
    }))
  }))
}));

// Mock Firebase Functions for tests
jest.mock('firebase-functions', () => ({
  https: {
    onCall: jest.fn((fn) => fn)
  },
  pubsub: {
    schedule: jest.fn(() => ({
      onRun: jest.fn()
    }))
  },
  logger: {
    info: jest.fn(),
    warn: jest.fn(),
    error: jest.fn()
  }
}));

// Mock OpenAI SDK
jest.mock('openai', () => {
  return jest.fn().mockImplementation(() => ({
    beta: {
      threads: {
        create: jest.fn(() => Promise.resolve({ id: 'test-thread-id' })),
        retrieve: jest.fn(() => Promise.resolve({ id: 'test-thread-id' })),
        messages: {
          create: jest.fn(() => Promise.resolve({ id: 'test-message-id' })),
          list: jest.fn(() => Promise.resolve({ 
            data: [
              { 
                role: 'assistant', 
                run_id: 'test-run-id',
                content: [{ text: { value: 'Test response from CourseGPT' } }]
              }
            ]
          }))
        },
        runs: {
          create: jest.fn(() => Promise.resolve({ id: 'test-run-id', status: 'completed' })),
          retrieve: jest.fn(() => Promise.resolve({ id: 'test-run-id', status: 'completed' }))
        }
      }
    }
  }));
});

// Mock environment variables for tests
process.env.NODE_ENV = 'test';
process.env.OPENAI_API_KEY = 'test-openai-key';
process.env.ASSISTANT_ID = 'test-assistant-id';
process.env.GOOGLE_CLOUD_API_KEY = 'test-firebase-key';
process.env.FIREBASE_PROJECT_ID = 'test-project';

// Global test timeout
jest.setTimeout(10000);

// Console setup for cleaner test output
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (args[0]?.includes?.('Warning:') || args[0]?.includes?.('ReactDOMTestUtils')) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
