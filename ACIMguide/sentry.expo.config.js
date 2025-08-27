/**
 * Sentry Expo Configuration for ACIMguide Mobile App
 * Handles source map uploads during Expo build process
 */

const { withSentry } = require('@sentry/react-native/expo');

/**
 * Expo configuration with Sentry integration
 */
const expoConfig = {
  expo: {
    name: 'ACIMguide',
    slug: 'acimguide',
    version: '1.0.0',
    orientation: 'portrait',
    icon: './assets/icon.png',
    userInterfaceStyle: 'automatic',
    splash: {
      image: './assets/splash.png',
      resizeMode: 'contain',
      backgroundColor: '#ffffff'
    },
    assetBundlePatterns: [
      '**/*'
    ],
    ios: {
      supportsTablet: true,
      bundleIdentifier: 'com.acimguide.app'
    },
    android: {
      adaptiveIcon: {
        foregroundImage: './assets/adaptive-icon.png',
        backgroundColor: '#FFFFFF'
      },
      package: 'com.acimguide.app'
    },
    web: {
      favicon: './assets/favicon.png'
    },
    extra: {
      // Sentry DSN for mobile app (read from environment)
      sentryDsnMobile: process.env.SENTRY_DSN_MOBILE,
      env: process.env.NODE_ENV || 'development',
      
      // Spiritual AI platform context
      platform: 'spiritual-ai',
      service: 'acimguide-mobile',
      contentPolicy: 'acim_pure',
      
      // EAS Build configuration
      eas: {
        projectId: process.env.EAS_PROJECT_ID
      }
    },
    
    // Sentry-specific configuration for builds
    hooks: {
      postPublish: [
        {
          file: 'sentry-expo/upload-sourcemaps',
          config: {
            organization: 'testalex-spiritual-ai',
            project: 'acimguide-mobile',
            authToken: process.env.SENTRY_AUTH_TOKEN,
            setCommits: true,
            deployEnv: process.env.NODE_ENV || 'development',
            release: process.env.EAS_BUILD_GIT_COMMIT_HASH || 'unknown'
          }
        }
      ]
    }
  }
};

/**
 * Export configuration with Sentry wrapper
 * Automatically handles source map uploads and error reporting setup
 */
module.exports = withSentry(expoConfig, {
  // Sentry configuration options
  organization: 'testalex-spiritual-ai',
  project: 'acimguide-mobile',
  authToken: process.env.SENTRY_AUTH_TOKEN,
  
  // Source map upload configuration
  sourcemaps: {
    // Upload source maps for better error debugging
    rewrite: true,
    // Strip source maps from bundle in production
    stripPrefix: ['webpack://_N_E/'],
    // Validate source maps before upload
    validate: true,
    // Clean old releases to save storage
    cleanArtifacts: true
  },
  
  // Release configuration
  release: {
    // Set release name based on git commit
    name: process.env.EAS_BUILD_GIT_COMMIT_HASH || `mobile-${Date.now()}`,
    // Deploy environment
    deploy: {
      env: process.env.NODE_ENV || 'development'
    },
    // Set commits for release tracking
    setCommits: {
      auto: true
    }
  },
  
  // Silent mode for CI/CD builds
  silent: process.env.CI === 'true',
  
  // Debug mode for development
  debug: process.env.NODE_ENV === 'development'
});
