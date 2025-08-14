/**
 * Test data and fixtures for E2E testing
 */

export const TestUsers = {
  validUser: {
    email: 'test@acimguide.com',
    password: 'test123',
    name: 'Test User'
  },
  premiumUser: {
    email: 'premium@acimguide.com', 
    password: 'premium123',
    name: 'Premium User'
  },
  adminUser: {
    email: 'admin@acimguide.com',
    password: 'admin123',
    name: 'Admin User'
  }
};

export const TestMessages = {
  acimQuestions: [
    'What is lesson 1 of ACIM?',
    'Tell me about forgiveness in the Course',
    'What does the Holy Spirit teach us?',
    'How do I practice today\'s lesson?',
    'Explain the concept of miracles in ACIM',
    'What is the difference between perception and knowledge?',
    'How does ACIM define the ego?',
    'What is the purpose of the workbook?',
    'Tell me about the manual for teachers',
    'What does ACIM say about fear?'
  ],
  generalQuestions: [
    'Hello',
    'How are you?',
    'What can you help me with?',
    'Tell me a joke',
    'What\'s the weather like?'
  ],
  invalidInputs: [
    '', // empty message
    'A'.repeat(5000), // very long message
    '<script>alert(\'xss\')</script>', // potential XSS
    'SELECT * FROM users', // SQL injection attempt
    '\n\n\n', // just newlines
    '   ' // just spaces
  ]
};

export const PaymentTestData = {
  validCard: {
    number: '4242424242424242', // Stripe test card
    expiry: '12/25',
    cvc: '123',
    zip: '12345'
  },
  declinedCard: {
    number: '4000000000000002', // Declined card
    expiry: '12/25', 
    cvc: '123',
    zip: '12345'
  },
  insufficientFundsCard: {
    number: '4000000000009995', // Insufficient funds
    expiry: '12/25',
    cvc: '123',
    zip: '12345'
  },
  invalidCard: {
    number: '1111111111111111', // Invalid number
    expiry: '01/20', // Expired
    cvc: '12', // Invalid CVC
    zip: ''
  }
};

export const BlogTestData = {
  samplePosts: [
    {
      title: 'Daily ACIM Lesson: Finding Peace',
      slug: 'daily-acim-lesson-finding-peace',
      excerpt: 'Today\'s lesson from A Course in Miracles teaches us about finding inner peace through forgiveness.',
      content: 'A Course in Miracles lesson about peace and forgiveness...',
      date: '2024-01-15',
      tags: ['acim', 'peace', 'forgiveness', 'daily-lesson']
    },
    {
      title: 'Understanding the Holy Spirit\'s Voice',
      slug: 'understanding-holy-spirit-voice', 
      excerpt: 'Learn how to distinguish between the ego\'s voice and the Holy Spirit\'s guidance.',
      content: 'The Holy Spirit speaks to us in ways that bring peace...',
      date: '2024-01-14',
      tags: ['holy-spirit', 'guidance', 'acim', 'spiritual-practice']
    }
  ],
  ctaVariations: [
    'Start with CourseGPT',
    'Try CourseGPT Free',
    'Begin Your ACIM Journey',
    'Access CourseGPT Now',
    'Start Learning ACIM',
    'Get CourseGPT'
  ]
};

export const TestUrls = {
  staging: 'https://staging.acimguide.com',
  local: 'http://localhost:3000',
  blog: '/blog',
  chat: '/chat',
  purchase: '/purchase',
  courses: '/courses',
  login: '/login',
  signup: '/signup'
};

export const BrowserConfigs = {
  desktop: {
    viewport: { width: 1920, height: 1080 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  },
  mobile: {
    viewport: { width: 390, height: 844 }, // iPhone 12
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
  },
  tablet: {
    viewport: { width: 820, height: 1180 }, // iPad
    userAgent: 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
  }
};

export const PerformanceThresholds = {
  lighthouse: {
    performance: 80,
    accessibility: 90,
    bestPractices: 80,
    seo: 80
  },
  coreWebVitals: {
    lcp: 2500, // Largest Contentful Paint (ms)
    fid: 100,  // First Input Delay (ms)
    cls: 0.1   // Cumulative Layout Shift
  },
  pageLoad: {
    fast: 1000,
    acceptable: 3000,
    slow: 5000
  }
};

export const AccessibilityTestData = {
  keyboardNavigation: [
    'Tab',
    'Shift+Tab', 
    'Enter',
    'Space',
    'ArrowDown',
    'ArrowUp',
    'Escape'
  ],
  screenReaderElements: [
    'h1',
    'button',
    'input',
    'a',
    'img',
    'form',
    'nav'
  ]
};

export const ErrorTestScenarios = {
  network: [
    'offline',
    'slow-3g',
    'fast-3g'
  ],
  server: [
    500, // Internal server error
    503, // Service unavailable
    429, // Too many requests
    404  // Not found
  ],
  client: [
    'javascript-disabled',
    'cookies-disabled',
    'local-storage-full'
  ]
};

export default {
  TestUsers,
  TestMessages,
  PaymentTestData,
  BlogTestData,
  TestUrls,
  BrowserConfigs,
  PerformanceThresholds,
  AccessibilityTestData,
  ErrorTestScenarios
};
