/**
 * K6 Load Test Script for CogniForge API
 * 
 * This script performs load testing on the API endpoints to ensure
 * they can handle expected traffic volumes.
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '1m', target: 20 },   // Stay at 20 users
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    errors: ['rate<0.1'],              // Error rate must be below 10%
  },
};

// Base URL - will be overridden in CI/CD
const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000';

export default function () {
  // Test health endpoint
  const healthResponse = http.get(`${BASE_URL}/api/v1/health`);
  
  const healthCheck = check(healthResponse, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  errorRate.add(!healthCheck);
  
  // Test database health endpoint
  const dbHealthResponse = http.get(`${BASE_URL}/api/v1/database/health`);
  
  const dbHealthCheck = check(dbHealthResponse, {
    'db health status is 200': (r) => r.status === 200,
  });
  
  errorRate.add(!dbHealthCheck);
  
  sleep(1);
}

/**
 * Setup function - runs once at the start
 */
export function setup() {
  console.log('Starting load test...');
  console.log(`Target URL: ${BASE_URL}`);
}

/**
 * Teardown function - runs once at the end
 */
export function teardown(data) {
  console.log('Load test completed');
}
