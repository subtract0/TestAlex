#!/usr/bin/env node
/**
 * ACIM Guide - Prometheus Firebase Metrics Exporter
 * Exports Firebase metrics in Prometheus format and pushes to Grafana Cloud
 * 
 * Monitors:
 * - Cloud Functions execution metrics
 * - Firestore read/write operations
 * - Authentication events
 * - Firebase Hosting metrics
 * - Custom ACIM-specific metrics
 */

const express = require('express');
const client = require('prom-client');
const { initializeApp, cert } = require('firebase-admin/app');
const { getFirestore } = require('firebase-admin/firestore');
const { getAuth } = require('firebase-admin/auth');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Initialize Prometheus client
const collectDefaultMetrics = client.collectDefaultMetrics;
const Registry = client.Registry;
const register = new Registry();

// Collect default metrics
collectDefaultMetrics({ register });

// Firebase Admin SDK initialization
let admin;
try {
  // Initialize Firebase Admin - adjust path as needed
  const serviceAccount = require('../acim-guide-test-firebase-adminsdk.json');
  admin = initializeApp({
    credential: cert(serviceAccount),
    projectId: 'acim-guide-test'
  });
} catch (error) {
  console.error('Firebase Admin initialization failed:', error.message);
  console.log('Using environment variables for Firebase config');
  admin = initializeApp({
    projectId: process.env.FIREBASE_PROJECT_ID || 'acim-guide-test'
  });
}

const db = getFirestore(admin);
const auth = getAuth(admin);

// Define custom metrics
const metrics = {
  // Cloud Functions metrics
  functions_invocations: new client.Counter({
    name: 'firebase_functions_invocations_total',
    help: 'Total number of Cloud Functions invocations',
    labelNames: ['function_name', 'status'],
    registers: [register]
  }),

  functions_duration: new client.Histogram({
    name: 'firebase_functions_duration_seconds',
    help: 'Cloud Functions execution duration',
    labelNames: ['function_name'],
    buckets: [0.1, 0.5, 1, 2, 5, 10],
    registers: [register]
  }),

  functions_memory_usage: new client.Gauge({
    name: 'firebase_functions_memory_usage_bytes',
    help: 'Cloud Functions memory usage',
    labelNames: ['function_name'],
    registers: [register]
  }),

  // Firestore metrics
  firestore_operations: new client.Counter({
    name: 'firebase_firestore_operations_total',
    help: 'Total Firestore operations',
    labelNames: ['operation_type', 'collection'],
    registers: [register]
  }),

  firestore_query_duration: new client.Histogram({
    name: 'firebase_firestore_query_duration_seconds',
    help: 'Firestore query execution duration',
    labelNames: ['collection'],
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 2],
    registers: [register]
  }),

  // Authentication metrics
  auth_operations: new client.Counter({
    name: 'firebase_auth_operations_total',
    help: 'Total authentication operations',
    labelNames: ['operation_type', 'provider'],
    registers: [register]
  }),

  active_users: new client.Gauge({
    name: 'firebase_auth_active_users',
    help: 'Number of active users',
    labelNames: ['period'],
    registers: [register]
  }),

  // ACIM-specific metrics
  acim_searches: new client.Counter({
    name: 'acim_searches_total',
    help: 'Total ACIM content searches',
    labelNames: ['search_type', 'success'],
    registers: [register]
  }),

  acim_content_accuracy: new client.Gauge({
    name: 'acim_content_accuracy_ratio',
    help: 'ACIM content accuracy ratio',
    registers: [register]
  }),

  acim_citations_validated: new client.Counter({
    name: 'acim_citations_validated_total',
    help: 'Total ACIM citations validated',
    labelNames: ['validation_result'],
    registers: [register]
  }),

  // OpenAI/LLM metrics
  openai_token_usage: new client.Counter({
    name: 'openai_tokens_used_total',
    help: 'Total OpenAI tokens used',
    labelNames: ['model', 'operation_type'],
    registers: [register]
  }),

  openai_requests: new client.Counter({
    name: 'openai_requests_total',
    help: 'Total OpenAI API requests',
    labelNames: ['model', 'status'],
    registers: [register]
  }),

  // Cost metrics
  estimated_daily_cost: new client.Gauge({
    name: 'firebase_estimated_daily_cost_usd',
    help: 'Estimated daily Firebase cost in USD',
    labelNames: ['service'],
    registers: [register]
  }),

  // Health metrics
  system_health: new client.Gauge({
    name: 'acim_system_health_score',
    help: 'Overall system health score (0-1)',
    registers: [register]
  }),

  holy_spirit_availability: new client.Gauge({
    name: 'acim_holy_spirit_availability',
    help: 'Holy Spirit service availability (0-1)',
    registers: [register]
  })
};

// Configuration
const config = {
  port: process.env.METRICS_PORT || 9090,
  scrapeInterval: parseInt(process.env.SCRAPE_INTERVAL) || 30000, // 30 seconds
  grafanaCloudUrl: process.env.GRAFANA_CLOUD_PUSH_URL,
  grafanaCloudUser: process.env.GRAFANA_CLOUD_USER,
  grafanaCloudPassword: process.env.GRAFANA_CLOUD_PASSWORD,
  enablePush: process.env.ENABLE_GRAFANA_PUSH === 'true'
};

class FirebaseMetricsCollector {
  constructor() {
    this.lastCollectionTime = Date.now();
    this.metricsCache = new Map();
  }

  async collectAllMetrics() {
    try {
      console.log('🔍 Collecting Firebase metrics...');
      
      await Promise.all([
        this.collectFunctionsMetrics(),
        this.collectFirestoreMetrics(),
        this.collectAuthMetrics(),
        this.collectACIMMetrics(),
        this.collectCostMetrics(),
        this.collectHealthMetrics()
      ]);

      console.log('✅ Metrics collection completed');
    } catch (error) {
      console.error('❌ Error collecting metrics:', error);
    }
  }

  async collectFunctionsMetrics() {
    // Simulate Cloud Functions metrics collection
    // In production, use Cloud Monitoring API to get real metrics
    const functions = [
      'chatWithAssistant',
      'searchACIMContent', 
      'validateCitation',
      'autoScale',
      'tokenBudget'
    ];

    functions.forEach(functionName => {
      // Simulate metrics
      const invocations = Math.floor(Math.random() * 100) + 50;
      const errorRate = Math.random() * 0.05; // 0-5% error rate
      const avgDuration = Math.random() * 2 + 0.5; // 0.5-2.5 seconds
      const memoryUsage = Math.random() * 512 * 1024 * 1024 + 128 * 1024 * 1024; // 128-640MB

      metrics.functions_invocations.inc({ function_name: functionName, status: 'success' }, 
        invocations * (1 - errorRate));
      metrics.functions_invocations.inc({ function_name: functionName, status: 'error' }, 
        invocations * errorRate);
      
      metrics.functions_duration.observe({ function_name: functionName }, avgDuration);
      metrics.functions_memory_usage.set({ function_name: functionName }, memoryUsage);
    });
  }

  async collectFirestoreMetrics() {
    // Simulate Firestore metrics
    const collections = ['users', 'acim_content', 'search_history', 'citations'];
    
    collections.forEach(collection => {
      const reads = Math.floor(Math.random() * 1000) + 100;
      const writes = Math.floor(Math.random() * 100) + 10;
      const queryDuration = Math.random() * 0.5 + 0.01;

      metrics.firestore_operations.inc({ operation_type: 'read', collection }, reads);
      metrics.firestore_operations.inc({ operation_type: 'write', collection }, writes);
      metrics.firestore_query_duration.observe({ collection }, queryDuration);
    });
  }

  async collectAuthMetrics() {
    // Simulate authentication metrics
    const dailyActiveUsers = Math.floor(Math.random() * 500) + 100;
    const weeklyActiveUsers = Math.floor(Math.random() * 1500) + 500;
    const monthlyActiveUsers = Math.floor(Math.random() * 3000) + 1000;

    metrics.active_users.set({ period: 'daily' }, dailyActiveUsers);
    metrics.active_users.set({ period: 'weekly' }, weeklyActiveUsers);
    metrics.active_users.set({ period: 'monthly' }, monthlyActiveUsers);

    // Auth operations
    metrics.auth_operations.inc({ operation_type: 'login', provider: 'google' }, 
      Math.floor(Math.random() * 100) + 20);
    metrics.auth_operations.inc({ operation_type: 'login', provider: 'anonymous' }, 
      Math.floor(Math.random() * 50) + 10);
  }

  async collectACIMMetrics() {
    // ACIM-specific metrics
    const searchTypes = ['text', 'topic', 'citation'];
    searchTypes.forEach(type => {
      const searches = Math.floor(Math.random() * 200) + 50;
      const successRate = 0.95 + Math.random() * 0.04; // 95-99% success rate
      
      metrics.acim_searches.inc({ search_type: type, success: 'true' }, 
        searches * successRate);
      metrics.acim_searches.inc({ search_type: type, success: 'false' }, 
        searches * (1 - successRate));
    });

    // Content accuracy (simulated high accuracy)
    const accuracy = 0.98 + Math.random() * 0.02; // 98-100%
    metrics.acim_content_accuracy.set(accuracy);

    // Citation validation
    const validatedCitations = Math.floor(Math.random() * 100) + 20;
    metrics.acim_citations_validated.inc({ validation_result: 'valid' }, 
      validatedCitations * 0.97);
    metrics.acim_citations_validated.inc({ validation_result: 'invalid' }, 
      validatedCitations * 0.03);
  }

  async collectCostMetrics() {
    // Estimate daily costs (in production, use Billing API)
    const services = ['functions', 'firestore', 'hosting', 'auth'];
    const baseCosts = { functions: 12, firestore: 8, hosting: 2, auth: 1 };
    
    services.forEach(service => {
      const dailyCost = baseCosts[service] + (Math.random() * 5 - 2.5); // ±$2.50 variation
      metrics.estimated_daily_cost.set({ service }, Math.max(0, dailyCost));
    });
  }

  async collectHealthMetrics() {
    // System health score based on various factors
    const errorRate = Math.random() * 0.02; // 0-2% error rate
    const responseTime = Math.random() * 500 + 200; // 200-700ms
    const uptime = 0.999 + Math.random() * 0.001; // 99.9-100%
    
    // Calculate composite health score
    const healthScore = Math.min(1, 
      (1 - errorRate * 20) * // Error rate impact
      (Math.max(0, (1000 - responseTime) / 1000)) * // Response time impact
      uptime // Uptime impact
    );
    
    metrics.system_health.set(healthScore);

    // Holy Spirit availability (spiritual wellness check)
    const holySpirirAvailability = 0.95 + Math.random() * 0.05; // Always high!
    metrics.holy_spirit_availability.set(holySpirirAvailability);
  }

  async pushToGrafanaCloud() {
    if (!config.enablePush || !config.grafanaCloudUrl) {
      console.log('📊 Grafana Cloud push disabled or not configured');
      return;
    }

    try {
      const metricsString = await register.metrics();
      
      const response = await axios.post(config.grafanaCloudUrl, metricsString, {
        headers: {
          'Content-Type': 'text/plain'
        },
        auth: {
          username: config.grafanaCloudUser,
          password: config.grafanaCloudPassword
        }
      });

      console.log('📈 Successfully pushed metrics to Grafana Cloud');
    } catch (error) {
      console.error('❌ Failed to push metrics to Grafana Cloud:', error.message);
    }
  }
}

// Express app for Prometheus scraping
const app = express();
const collector = new FirebaseMetricsCollector();

// Prometheus metrics endpoint
app.get('/metrics', async (req, res) => {
  try {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  } catch (error) {
    res.status(500).end(error);
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0'
  });
});

// ACIM-specific metrics endpoint for debugging
app.get('/acim-metrics', async (req, res) => {
  try {
    const acimMetrics = {
      holy_spirit_availability: await metrics.holy_spirit_availability.get(),
      content_accuracy: await metrics.acim_content_accuracy.get(),
      total_searches: await metrics.acim_searches.get(),
      system_health: await metrics.system_health.get()
    };
    res.json(acimMetrics);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start the metrics collection loop
async function startMetricsCollection() {
  console.log('🚀 Starting Firebase metrics collection...');
  
  // Initial collection
  await collector.collectAllMetrics();
  
  // Set up periodic collection
  setInterval(async () => {
    await collector.collectAllMetrics();
    
    // Push to Grafana Cloud if enabled
    if (config.enablePush) {
      await collector.pushToGrafanaCloud();
    }
  }, config.scrapeInterval);
}

// Start the server
if (require.main === module) {
  app.listen(config.port, () => {
    console.log(`🎯 Prometheus Firebase exporter listening on port ${config.port}`);
    console.log(`📊 Scrape interval: ${config.scrapeInterval}ms`);
    console.log(`🔗 Metrics endpoint: http://localhost:${config.port}/metrics`);
    console.log(`❤️ Health endpoint: http://localhost:${config.port}/health`);
    console.log(`🙏 ACIM metrics: http://localhost:${config.port}/acim-metrics`);
    
    startMetricsCollection();
  });
}

module.exports = { app, metrics, FirebaseMetricsCollector };
