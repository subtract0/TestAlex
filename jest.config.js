module.exports = {
  // Test environment
  testEnvironment: 'jsdom',
  
  // TypeScript and JSX support
  preset: 'ts-jest',
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
    '^.+\\.(js|jsx)$': ['babel-jest', {
      presets: [
        ['@babel/preset-env', { targets: { node: 'current' } }],
        ['@babel/preset-react', { runtime: 'automatic' }]
      ]
    }]
  },
  
  // Test file patterns
  testMatch: [
    '**/__tests__/**/*.(js|ts|tsx)',
    '**/tests/**/*.test.(js|ts|tsx)',
    '**/*.test.(js|ts|tsx)',
    '**/*.spec.(js|ts|tsx)'
  ],
  
  // Files to ignore during testing
  testPathIgnorePatterns: [
    '/node_modules/',
    '/google-cloud-sdk/',
    '/e2e/',
    '/playwright-report/',
    '/test-results/',
    '/coverage/',
    '/htmlcov/',
    '/ACIMguide/', // React Native - separate test env needed
    '/android-native/', // Android native - separate test env
    '/venv/',
    '/.venv/'
  ],
  
  // Module name mapping for React Native/Expo components
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1'
  },
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  
  // Coverage configuration
  collectCoverage: false, // Run separately
  collectCoverageFrom: [
    // Include JS/TS files for backend and scripts
    'functions/**/*.{js,ts}',
    'scripts/**/*.{js,ts}',
    'monitoring/**/*.{js,ts}',
    '*.{js,ts}',
    
    // Exclude test files and build artifacts
    '!**/*.test.{js,ts}',
    '!**/*.spec.{js,ts}',
    '!**/node_modules/**',
    '!**/google-cloud-sdk/**',
    '!**/coverage/**',
    '!**/htmlcov/**',
    '!**/e2e/**',
    '!**/test-results/**',
    '!**/playwright-report/**',
    '!**/dist/**',
    '!**/build/**',
    '!**/.venv/**',
    '!**/venv/**',
    '!**/ACIMguide/**', // React Native
    '!**/android-native/**', // Android native
    '!playwright.config.ts',
    '!jest.config.js',
    '!babel.config.js',
    '!**/.eslintrc.js'
  ],
  
  // Coverage thresholds (lowered for initial implementation)
  coverageThreshold: {
    global: {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50
    }
  },
  
  // Coverage reporters
  coverageReporters: [
    'text',
    'lcov',
    'html',
    'json-summary'
  ],
  
  // Global test timeout
  testTimeout: 10000,
  
  // Module file extensions
  moduleFileExtensions: ['js', 'ts', 'tsx', 'json']
};
