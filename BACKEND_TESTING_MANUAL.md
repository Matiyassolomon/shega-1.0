# Backend Testing Manual - Music Platform
## Complete Step-by-Step Testing Guide

**Version**: 1.0  
**Date**: April 20, 2026  
**Purpose**: Verify all backend endpoints are working correctly

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Health & Monitoring Tests](#health--monitoring-tests)
4. [Authentication Tests](#authentication-tests)
5. [Payment System Tests](#payment-system-tests)
6. [Marketplace Tests](#marketplace-tests)
7. [Database & Cache Tests](#database--cache-tests)
8. [Recommendation Tests](#recommendation-tests)
9. [Integration Tests](#integration-tests)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
```bash
# Install curl (Windows 10/11 has it built-in)
# Install jq for JSON formatting (optional but recommended)
choco install jq
```

### Environment Variables
Create a `.env.test` file:
```env
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
TEST_USER_ID=1
TEST_USERNAME=testuser
TEST_PASSWORD=testpass
```

---

## Environment Setup

### Step 1: Start Backend Services

#### Option A: Local Development (SQLite)
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### Option B: Docker Production (PostgreSQL + Redis)
```bash
# Copy environment file
cp .env.production.example .env.production
# Edit with your values

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

**Expected Output:**
```
                Name                              Command               State                    Ports
---------------------------------------------------------------------------------------------------------------
music-platform-backend          gunicorn -w 4 -k uvicorn.w ...   Up      0.0.0.0:8000->8000/tcp
music-platform-celery           celery -A app.core.celery  ...   Up
music-platform-celery-beat       celery -A app.core.celery  ...   Up
music-platform-postgres           docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp
music-platform-rabbitmq           docker-entrypoint.sh rabbi ...   Up      0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp
music-platform-redis              docker-entrypoint.sh redis ...   Up      0.0.0.0:6379->6379/tcp
```

---

## Health & Monitoring Tests

### Test 1: Basic Health Check
```bash
curl -s http://localhost:8000/health | jq .
```

**Expected Output:**
```json
{
  "status": "healthy",
  "timestamp": 1713628800,
  "service": "music-platform-backend"
}
```

**✅ Success Criteria:**
- HTTP Status: 200 OK
- Response contains `status: "healthy"`
- Timestamp is present

---

### Test 2: Database Health Check
```bash
curl -s http://localhost:8000/health/live | jq .
```

**Expected Output:**
```json
{
  "status": "alive",
  "database": "connected",
  "timestamp": 1713628800
}
```

**✅ Success Criteria:**
- Database shows as "connected"
- No error messages

---

### Test 3: Readiness Check
```bash
curl -s http://localhost:8000/health/ready | jq .
```

**Expected Output:**
```json
{
  "status": "ready",
  "database": "ok",
  "cache": "ok",
  "services": {
    "postgres": "connected",
    "redis": "connected",
    "rabbitmq": "connected"
  }
}
```

**✅ Success Criteria:**
- All services show as "connected"
- Status is "ready"

---

### Test 4: Cache Health Check
```bash
curl -s http://localhost:8000/health/cache | jq .
```

**Expected Output:**
```json
{
  "status": "healthy",
  "type": "redis",
  "connected_clients": 5,
  "used_memory_human": "1.5M",
  "uptime_in_seconds": 3600
}
```

**✅ Success Criteria:**
- Cache type shows correctly (redis or memory)
- Status is "healthy"

---

## Authentication Tests

### Test 5: Login Endpoint
```bash
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass"
  }' | jq .
```

**Expected Output:**
```json
{
  "success": true,
  "message": "Music Platform Authentication Successful",
  "userId": "1",
  "token": "music_platform_token_1713628800",
  "expires_in": 3600
}
```

**✅ Success Criteria:**
- HTTP Status: 200 OK
- `success: true`
- Token is present
- `expires_in` is set

---

### Test 6: Auth Status Check
```bash
curl -s http://localhost:8000/auth/status | jq .
```

**Expected Output:**
```json
{
  "authenticated": true,
  "platform": "music_platform",
  "message": "Music Platform authentication is active"
}
```

**✅ Success Criteria:**
- `authenticated: true`
- Platform is "music_platform"

---

## Payment System Tests

### Test 7: Create Payment Intent
```bash
curl -s -X POST http://localhost:8000/payments/intent \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 199,
    "currency": "ETB",
    "payment_method": "telebirr_h5",
    "payment_type": "subscription_monthly",
    "user_id": 1
  }' | jq .
```

**Expected Output:**
```json
{
  "payment_intent_id": "pi_test_123456",
  "client_secret": "pi_test_secret_123456",
  "status": "requires_payment_method",
  "amount": 199,
  "currency": "ETB",
  "payment_method": "telebirr_h5",
  "redirect_url": "https://api.telebirr.et/payment/pi_test_123456"
}
```

**✅ Success Criteria:**
- HTTP Status: 201 Created
- `payment_intent_id` is generated
- `client_secret` is present
- Status is "requires_payment_method"

---

### Test 8: Legacy Payment Creation
```bash
curl -s -X POST http://localhost:8000/payment/create \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 99,
    "method": "telebirr",
    "user_id": 1,
    "payment_type": "song_purchase"
  }' | jq .
```

**Expected Output:**
```json
{
  "id": 1,
  "user_id": 1,
  "amount": 99,
  "method": "telebirr",
  "payment_type": "song_purchase",
  "status": "pending",
  "created_at": "2024-04-20T10:00:00Z",
  "redirect_url": "https://api.telebirr.et/payment/1"
}
```

**✅ Success Criteria:**
- Payment ID is generated
- Status is "pending"
- `redirect_url` is present for H5 flow

---

### Test 9: Confirm Payment
```bash
curl -s -X POST http://localhost:8000/payment/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "payment_id": 1
  }' | jq .
```

**Expected Output:**
```json
{
  "payment_id": 1,
  "status": "completed",
  "verified": true,
  "transaction_id": "txn_test_123456"
}
```

**✅ Success Criteria:**
- Status changes to "completed"
- `verified: true`
- `transaction_id` is present

---

### Test 10: Get Payment Providers
```bash
curl -s http://localhost:8000/payments/providers | jq .
```

**Expected Output:**
```json
{
  "providers": [
    {
      "id": "telebirr_h5",
      "name": "Telebirr H5",
      "enabled": true,
      "supported_methods": ["mobile_money"]
    },
    {
      "id": "mpesa",
      "name": "M-Pesa",
      "enabled": true,
      "supported_methods": ["mobile_money"]
    },
    {
      "id": "telebirr_legacy",
      "name": "Telebirr Legacy",
      "enabled": true,
      "supported_methods": ["api"]
    }
  ]
}
```

**✅ Success Criteria:**
- At least 3 providers listed
- All providers show `enabled: true`

---

### Test 11: Check Subscription Status
```bash
curl -s "http://localhost:8000/payments/subscription-status?user_id=1" | jq .
```

**Expected Output:**
```json
{
  "user_id": 1,
  "subscribed": true,
  "subscription_type": "monthly",
  "expiry_date": "2024-05-20T10:00:00Z",
  "days_remaining": 30
}
```

**✅ Success Criteria:**
- Subscription status is accurate
- Expiry date is in the future
- `days_remaining` is positive

---

## Marketplace Tests

### Test 12: Get Marketplace Items
```bash
curl -s http://localhost:8000/marketplace | jq .
```

**Expected Output:**
```json
{
  "items": [
    {
      "id": 1,
      "playlist_id": "playlist_123",
      "seller_id": 1,
      "title": "Ethiopian Jazz Classics",
      "price": 49.99,
      "description": "Collection of classic Ethiopian jazz tracks",
      "track_count": 25,
      "created_at": "2024-04-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**✅ Success Criteria:**
- Items array is present
- Each item has required fields
- Pagination info is correct

---

### Test 13: Buy Playlist
```bash
curl -s -X POST http://localhost:8000/marketplace/buy-playlist \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_id": 2,
    "playlist_id": "playlist_123"
  }' | jq .
```

**Expected Output:**
```json
{
  "buyer_id": 2,
  "purchased": true,
  "playlist_id": "playlist_123",
  "payment_id": 2,
  "download_url": "http://localhost:8000/marketplace/download/playlist_123"
}
```

**✅ Success Criteria:**
- `purchased: true`
- `payment_id` is generated
- `download_url` is present

---

## Database & Cache Tests

### Test 14: Database Connection Pool Stats
```bash
curl -s http://localhost:8000/admin/db-stats \
  -H "X-Admin-API-Key: admin123" | jq .
```

**Expected Output:**
```json
{
  "database_type": "postgresql",
  "pool_size": 20,
  "checked_in": 15,
  "checked_out": 5,
  "overflow": 0,
  "status": "healthy"
}
```

**✅ Success Criteria:**
- Database type is correct
- Pool statistics are reasonable
- Status is "healthy"

---

### Test 15: Cache Operations
```bash
# Set cache value
curl -s -X POST http://localhost:8000/admin/cache-test \
  -H "Content-Type: application/json" \
  -H "X-Admin-API-Key: admin123" \
  -d '{
    "key": "test_key",
    "value": "test_value",
    "ttl": 60
  }' | jq .
```

**Expected Output:**
```json
{
  "success": true,
  "operation": "set",
  "key": "test_key",
  "ttl": 60
}
```

**✅ Success Criteria:**
- `success: true`
- Operation is acknowledged

---

## Recommendation Tests

### Test 16: Get Recommendations
```bash
curl -s "http://localhost:8000/recommendations/playlists?user_id=1&location=Addis%20Ababa" | jq .
```

**Expected Output:**
```json
{
  "recommendations": [
    {
      "id": "rec_123",
      "type": "playlist",
      "title": "Ethiopian Hip Hop Mix",
      "confidence": 0.95,
      "reason": "Based on your listening history",
      "playlist_id": "playlist_456"
    }
  ],
  "generated_at": "2024-04-20T10:00:00Z",
  "user_id": 1
}
```

**✅ Success Criteria:**
- Recommendations array is present
- Each has confidence score
- Generated timestamp is recent

---

## Integration Tests

### Test 17: Full Payment Flow
```bash
# Step 1: Create payment
echo "=== Step 1: Creating Payment ==="
PAYMENT=$(curl -s -X POST http://localhost:8000/payment/create \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 199,
    "method": "telebirr_h5",
    "user_id": 1,
    "payment_type": "subscription_monthly"
  }')

PAYMENT_ID=$(echo $PAYMENT | jq -r '.id')
echo "Payment ID: $PAYMENT_ID"
echo $PAYMENT | jq .

# Step 2: Confirm payment
echo "=== Step 2: Confirming Payment ==="
curl -s -X POST http://localhost:8000/payment/confirm \
  -H "Content-Type: application/json" \
  -d "{\"payment_id\": $PAYMENT_ID}" | jq .

# Step 3: Check subscription
echo "=== Step 3: Checking Subscription ==="
curl -s "http://localhost:8000/payments/subscription-status?user_id=1" | jq .
```

**Expected Output:**
```
=== Step 1: Creating Payment ===
Payment ID: 1
{
  "id": 1,
  "amount": 199,
  "status": "pending"
}
=== Step 2: Confirming Payment ===
{
  "payment_id": 1,
  "status": "completed",
  "verified": true
}
=== Step 3: Checking Subscription ===
{
  "user_id": 1,
  "subscribed": true,
  "subscription_type": "monthly"
}
```

**✅ Success Criteria:**
- Payment created successfully
- Payment confirmed without errors
- Subscription status is active

---

### Test 18: Frontend Proxy Test
```bash
# Test through Vite proxy
curl -s http://localhost:5173/api/health | jq .
```

**Expected Output:**
```json
{
  "status": "healthy",
  "timestamp": 1713628800,
  "service": "music-platform-backend"
}
```

**✅ Success Criteria:**
- Same response as direct backend call
- No proxy errors
- Frontend and backend are connected

---

## Troubleshooting

### Common Issues & Solutions

#### Issue 1: Connection Refused
**Error:** `curl: (7) Failed to connect to localhost port 8000`

**Solution:**
```bash
# Check if backend is running
docker-compose -f docker-compose.prod.yml ps

# Restart backend
docker-compose -f docker-compose.prod.yml restart backend

# Or start locally
cd backend && uvicorn app.main:app --reload
```

---

#### Issue 2: Database Connection Failed
**Error:** `sqlalchemy.exc.OperationalError: connection refused`

**Solution:**
```bash
# Check PostgreSQL status
docker-compose -f docker-compose.prod.yml logs postgres

# Verify database URL
echo $DATABASE_URL

# Should be: postgresql://music_user:secure_password@postgres:5432/music_platform
```

---

#### Issue 3: Cache Not Working
**Error:** Redis connection errors

**Solution:**
```bash
# Check Redis status
docker-compose -f docker-compose.prod.yml logs redis

# Test Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Should return: PONG
```

---

#### Issue 4: Payment Provider Not Available
**Error:** `Provider telebirr_h5 not registered`

**Solution:**
```bash
# Check environment variables
cat .env.production | grep TELEBIRR

# Should show:
# TELEBIRR_ENABLED=true
# TELEBIRR_APP_ID=xxx
# TELEBIRR_APP_SECRET=xxx
```

---

## Summary Checklist

### ✅ Core Services
- [ ] Backend server starts without errors
- [ ] Health check returns 200 OK
- [ ] Database connection is established
- [ ] Cache service is running

### ✅ Authentication
- [ ] Login endpoint returns token
- [ ] Auth status check works
- [ ] Token expiration is set

### ✅ Payments
- [ ] Payment intent creation works
- [ ] Legacy payment API works
- [ ] Payment confirmation succeeds
- [ ] Subscription status is accurate
- [ ] Multiple providers are available

### ✅ Marketplace
- [ ] Marketplace items are listed
- [ ] Playlist purchase works
- [ ] Download URLs are generated

### ✅ Monitoring
- [ ] Database stats are available
- [ ] Cache operations work
- [ ] All health endpoints respond

### ✅ Integration
- [ ] Full payment flow completes
- [ ] Frontend proxy works
- [ ] Celery workers are processing

---

## Next Steps

After successful testing:

1. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: Add production-ready backend with PostgreSQL, Redis, Docker"
   git push origin main
   ```

2. **Deploy to Production**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Monitor Deployment**
   - Check Grafana: http://localhost:3000
   - Check logs: `docker-compose -f docker-compose.prod.yml logs -f`

4. **Scale as Needed**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --scale backend=4
   ```

---

**✅ Testing Complete! Your backend is production-ready.**
