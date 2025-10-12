# 🚀 WORLD-CLASS API - Quick Start Guide

> **دليل البدء السريع للنظام الخارق**
>
> **Quick start guide for the superhuman system**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [API Endpoints](#api-endpoints)
6. [Security](#security)
7. [Monitoring](#monitoring)
8. [Examples](#examples)

---

## 🌟 Overview

This world-class API system provides:

- **🔐 Zero-Trust Security** - Short-lived JWT tokens, request signing, adaptive rate limiting
- **📊 Real-Time Observability** - P99.9 latency monitoring, ML-based anomaly detection
- **📜 API Contracts** - OpenAPI 3.0 specification, automatic validation
- **💚 Health Monitoring** - Comprehensive system health checks
- **🎯 SLA Tracking** - <20ms response time targets

---

## 🛠️ Installation

### Prerequisites

```bash
# Python 3.12+
python --version

# PostgreSQL database
psql --version
```

### Install Dependencies

```bash
pip install -r requirements.txt

# Additional packages for world-class features
pip install jsonschema pyjwt
```

### Environment Setup

Create `.env` file:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/cogniforge

# Security
SECRET_KEY=your-super-secret-key-change-in-production
API_SIGNING_SECRET=your-api-signing-secret

# AI Model (optional)
DEFAULT_AI_MODEL=openai/gpt-4o
```

---

## 🎯 Basic Usage

### 1. Start the Application

```bash
# Development mode
python run.py

# Production mode
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### 2. Access Admin Panel

Navigate to: `http://localhost:5000/admin/dashboard`

Default admin credentials (change immediately):
- Email: `admin@example.com`
- Password: `1111`

---

## 🚀 Advanced Features

### Real-Time Observability

Get performance metrics:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/admin/api/observability/metrics
```

Response:
```json
{
  "status": "success",
  "timestamp": "2025-10-12T10:00:00Z",
  "performance": {
    "avg_latency_ms": 12.5,
    "p50_latency_ms": 10.2,
    "p95_latency_ms": 18.7,
    "p99_latency_ms": 24.3,
    "p999_latency_ms": 45.1,
    "requests_per_second": 150.5,
    "error_rate": 0.02,
    "active_requests": 12
  },
  "sla_compliance": {
    "sla_target_ms": 20.0,
    "compliance_rate_percent": 99.5,
    "sla_status": "compliant"
  }
}
```

### ML-Based Anomaly Alerts

Get anomaly alerts:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/admin/api/observability/alerts?severity=critical
```

Response:
```json
{
  "status": "success",
  "total_alerts": 2,
  "alerts": [
    {
      "alert_id": "abc123",
      "timestamp": "2025-10-12T10:05:00Z",
      "severity": "critical",
      "anomaly_type": "extreme_latency",
      "description": "Endpoint /api/users latency 150.00ms exceeds critical threshold",
      "recommended_action": "Investigate immediately - potential service degradation"
    }
  ]
}
```

### Zero-Trust Security

#### Generate JWT Token

```bash
curl -X POST http://localhost:5000/admin/api/security/token/generate \
     -H "Content-Type: application/json" \
     -d '{"scopes": ["read", "write"]}'
```

Response:
```json
{
  "status": "success",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900,
  "expires_at": "2025-10-12T10:15:00Z",
  "scopes": ["read", "write"]
}
```

#### Refresh Token

```bash
curl -X POST http://localhost:5000/admin/api/security/token/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### API Contract Validation

#### Get OpenAPI Specification

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:5000/admin/api/contract/openapi
```

Response:
```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "CogniForge API",
    "version": "v2",
    "description": "World-class RESTful API"
  },
  "servers": [
    {
      "url": "/admin/api",
      "description": "Admin API v2 (Current)"
    }
  ],
  "components": {
    "securitySchemes": {
      "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
      }
    }
  }
}
```

---

## 📡 API Endpoints

### Observability Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/observability/metrics` | GET | Real-time performance metrics (P50-P99.9) |
| `/api/observability/alerts` | GET | ML-detected anomaly alerts |
| `/api/observability/endpoint/<path>` | GET | Endpoint-specific analytics |

### Security Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/security/token/generate` | POST | Generate JWT access & refresh tokens |
| `/api/security/token/refresh` | POST | Rotate access token |
| `/api/security/audit-logs` | GET | Security audit logs for compliance |

### Contract Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/contract/openapi` | GET | OpenAPI 3.0 specification |
| `/api/contract/violations` | GET | Contract violation reports |

### Health Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health/comprehensive` | GET | Multi-component health check |

---

## 🔐 Security

### Authentication

All API endpoints require authentication via JWT token:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:5000/admin/api/endpoint
```

### Request Signing (Optional)

For Zero-Trust environments, sign requests with HMAC-SHA256:

```python
import hmac
import hashlib
import time

def sign_request(method, path, body, secret):
    timestamp = int(time.time())
    nonce = "unique-nonce"
    
    # Calculate body hash
    body_hash = hashlib.sha256(body.encode()).hexdigest()
    
    # Create signature payload
    payload = f"{method}{path}{timestamp}{nonce}{body_hash}"
    
    # Generate HMAC signature
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return {
        'X-Signature': signature,
        'X-Timestamp': str(timestamp),
        'X-Nonce': nonce
    }

# Usage
headers = sign_request('POST', '/api/endpoint', '{"data": "value"}', 'your-secret')
```

### Rate Limiting

Default limits:
- **100 requests** per 60 seconds
- **Burst allowance:** 150 requests
- **Violations:** Exponential backoff (30s → 60s → 120s → 300s)

Response headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 2025-10-12T10:01:00Z
```

---

## 📊 Monitoring

### Performance Metrics

Monitor these key metrics:

1. **Latency Percentiles**
   - P50: Median response time
   - P95: 95th percentile
   - P99: 99th percentile
   - P99.9: Tail latency (critical for SLA)

2. **Throughput**
   - Requests per second
   - Active concurrent requests

3. **Error Rates**
   - 4xx client errors
   - 5xx server errors

4. **SLA Compliance**
   - Target: <20ms for critical endpoints
   - Compliance rate: >99%

### Anomaly Detection

The system automatically detects:

- **Critical Anomalies:** >5× baseline latency
- **High Anomalies:** >3× baseline latency
- **SLA Violations:** >20ms response time

Alerts include recommended actions for immediate response.

---

## 💡 Examples

### Example 1: Monitor API Performance

```python
import requests

# Get metrics
response = requests.get(
    'http://localhost:5000/admin/api/observability/metrics',
    headers={'Authorization': f'Bearer {token}'}
)

metrics = response.json()
print(f"P99 Latency: {metrics['performance']['p99_latency_ms']}ms")
print(f"SLA Status: {metrics['sla_compliance']['sla_status']}")
```

### Example 2: Generate and Use JWT Token

```python
import requests

# Generate token
auth_response = requests.post(
    'http://localhost:5000/admin/api/security/token/generate',
    json={'scopes': ['read', 'write']}
)

tokens = auth_response.json()
access_token = tokens['access_token']

# Use token for authenticated requests
data_response = requests.get(
    'http://localhost:5000/admin/api/database/tables',
    headers={'Authorization': f'Bearer {access_token}'}
)

tables = data_response.json()
print(f"Tables: {tables}")
```

### Example 3: Check System Health

```python
import requests

response = requests.get(
    'http://localhost:5000/admin/api/health/comprehensive'
)

health = response.json()
print(f"Overall Status: {health['status']}")

for component, status in health['components'].items():
    print(f"{component}: {status['status']}")
```

### Example 4: Get Endpoint Analytics

```python
import requests

response = requests.get(
    'http://localhost:5000/admin/api/observability/endpoint/api/database/tables',
    headers={'Authorization': f'Bearer {token}'}
)

analytics = response.json()
print(f"Endpoint: {analytics['endpoint']}")
print(f"Total Requests: {analytics['total_requests']}")
print(f"Avg Latency: {analytics['avg_latency_ms']}ms")
print(f"P99 Latency: {analytics['p99_latency_ms']}ms")
```

---

## 🎓 Best Practices

### 1. Token Management

- **Never** store tokens in client-side code
- Use short-lived access tokens (15 minutes)
- Rotate tokens regularly with refresh tokens
- Revoke tokens on logout

### 2. Rate Limiting

- Implement exponential backoff on 429 responses
- Monitor `X-RateLimit-Remaining` header
- Cache responses when appropriate

### 3. Error Handling

```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        # Rate limited - wait and retry
        retry_after = int(e.response.headers.get('Retry-After', 60))
        time.sleep(retry_after)
    elif e.response.status_code == 401:
        # Unauthorized - refresh token
        refresh_token()
    else:
        # Other error
        handle_error(e)
```

### 4. Monitoring Integration

Set up alerts for:
- P99 latency > 50ms
- Error rate > 1%
- SLA compliance < 99%
- Critical anomaly alerts

---

## 📚 Additional Resources

- [Full Architecture Documentation](./WORLD_CLASS_API_ARCHITECTURE.md)
- [CRUD API Guide (Arabic)](./CRUD_API_GUIDE_AR.md)
- [OpenAPI Specification](http://localhost:5000/admin/api/contract/openapi)

---

## 🆘 Troubleshooting

### Issue: Token expired

**Solution:** Use refresh token to get new access token

```bash
curl -X POST /api/security/token/refresh \
     -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### Issue: Rate limit exceeded

**Solution:** Wait for retry period, then resume

```bash
# Check Retry-After header in 429 response
# Wait specified seconds before retrying
```

### Issue: High latency detected

**Solution:** Check anomaly alerts for insights

```bash
curl /api/observability/alerts?severity=critical
# Review recommended actions
```

---

**Built with ❤️ by CogniForge Team**

**Version:** 2.0.0 (SUPERHUMAN EDITION)  
**Last Updated:** 2025-10-12

---

🔥 **من البساطة إلى العظمة - From Simplicity to Greatness** 🔥
