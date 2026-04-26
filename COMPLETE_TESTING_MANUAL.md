# Music Platform - Complete Testing Manual

##  TABLE OF CONTENTS

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites & Environment Setup](#2-prerequisites--environment-setup)
3. [Navidrome Setup](#3-navidrome-setup)
4. [Authentication Tests](#4-authentication-tests)
5. [Payment System Tests](#5-payment-system-tests)
6. [Playback & Access Control Tests](#6-playback--access-control-tests)
7. [Recommendation System Tests](#7-recommendation-system-tests)
8. [Device Management Tests](#8-device-management-tests)
9. [Audio Quality Tests](#9-audio-quality-tests)
10. [Integration Tests](#10-integration-tests)
11. [Troubleshooting Guide](#11-troubleshooting-guide)

---

## 1. ARCHITECTURE OVERVIEW

### Directory Structure Clarification

```
backend/
 app/                          # Core FastAPI application
    api/                      # API endpoints (v1, v2)
       v1/
          playback.py      # NEW: Payment-aware playback
          payments_webhook.py
          recommendations.py
       deps.py              # Dependencies (get_db, get_current_user)
    core/                     # Core utilities
       config.py            # Settings
       security.py          # JWT, password hashing
       database.py          # SQLAlchemy setup
       cache.py             # Redis cache
    models/                   # SQLAlchemy models
       user.py
       song_access.py       # NEW: Purchase/Subscription tracking
       playback.py
       device.py
    services/                 # Business logic
       access_control_service.py    # NEW: Permission checking
       song_purchase_service.py     # NEW: Purchase flow
       audio_quality_service.py     # NEW: Quality selection
       navidrome_service.py         # NEW: Stream URL generation
       playback_session_service.py  # NEW: Session management
       recommendation_engine.py
       device_service.py
    repositories/             # Data access layer
    main.py                   # FastAPI app entry point

 apps/                         # Modular Django-style apps
    music/                    # Music library management
       models.py
       views.py
    payments/                 # Payment processing
        models.py
        views.py

 docker-compose.prod.yml       # Production stack
 docker-compose.yml            # Development stack
 requirements.txt
```

### Key Distinction:
- **`app/`** = FastAPI core (recommendations, playback, auth)
- **`apps/`** = Modular features (music library, payments processing)

---

## 2. PREREQUISITES & ENVIRONMENT SETUP

### Step 2.1: Install Required Tools

```bash
# Windows PowerShell (Run as Administrator)

# 1. Install Python 3.11+
python --version
# Should show: Python 3.11.x or higher

# 2. Install Node.js (for frontend)
node --version
# Should show: v18.x or higher

# 3. Install Docker Desktop
docker --version
# Should show: Docker version 24.x or higher

# 4. Install Git
git --version
```

### Step 2.2: Clone and Setup Project

```bash
# Navigate to project
cd c:\Users\u\Music\music-platform

# Create virtual environment
cd backend
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# If requirements.txt missing packages:
pip install fastapi uvicorn sqlalchemy pydantic redis celery requests aiohttp python-jose passlib python-multipart
```

### Step 2.3: Environment Configuration

Create `backend/.env`:

```env
# Database
DATABASE_URL=sqlite:///./music_platform.db
# OR for PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/music_platform

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (optional, falls back to memory)
REDIS_URL=redis://localhost:6379/0

# Navidrome
NAVIDROME_URL=http://localhost:4533
NAVIDROME_USER=admin
NAVIDROME_PASS=admin

# YouTube API (optional)
YOUTUBE_API_KEY=your_youtube_api_key

# Payment Providers (test keys)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# App Settings
DEBUG=true
ENVIRONMENT=development
```

---

## 3. NAVIDROME SETUP

### Step 3.1: Start Navidrome with Docker

```bash
# Create docker-compose for Navidrome
cd c:\Users\u\Music\music-platform

# Add to docker-compose.yml or create separate:
docker run -d \
  --name navidrome \
  -p 4533:4533 \
  -v "${PWD}/music:/music:ro" \
  -v "${PWD}/navidrome-data:/data" \
  -e ND_SCANSCHEDULE=1h \
  -e ND_LOGLEVEL=info \
  deluan/navidrome:latest

# Windows PowerShell:
docker run -d --name navidrome -p 4533:4533 -v "${PWD}\music:/music:ro" -v "${PWD}\navidrome-data:/data" -e ND_SCANSCHEDULE=1h deluan/navidrome:latest
```

### Step 3.2: Configure Navidrome

```bash
# 1. Open Navidrome UI
start http://localhost:4533

# 2. Create admin account (first run)
# Follow web UI prompts

# 3. Test Navidrome API
curl "http://localhost:4533/rest/ping.view?u=admin&p=admin&v=1.16.1&c=test"

# Expected: XML response with status="ok"
```

### Step 3.3: Add Music to Navidrome

```bash
# Place MP3/FLAC files in:
c:\Users\u\Music\music-platform\music\

# Structure:
# music/
#   Artist Name/
#     Album Name/
#       01 - Song Title.mp3
#       02 - Song Title.mp3

# Navidrome will auto-scan (every 1 hour) or trigger manual scan in UI
```

### Step 3.4: Get Song IDs from Navidrome

```bash
# Get all songs
curl "http://localhost:4533/rest/getSongs.view?u=admin&p=admin&v=1.16.1&c=test" | findstr "id title"

# Or use browser:
# http://localhost:4533/rest/getSongs.view?u=admin&p=admin&v=1.16.1&c=test
```

---

## 4. AUTHENTICATION TESTS

### Test 4.1: User Registration

```bash
# Endpoint: POST /auth/register
# Headers: Device info required

curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -H "device-name: Test iPhone" \
  -H "device-type: mobile" \
  -H "os: iOS" \
  -H "x-os-version: 17.0" \
  -H "x-app-version: 1.0.0" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "display_name": "Test User"
  }'

# Expected Response:
{
  "user": {
    "id": "uuid-string",
    "email": "test@example.com",
    "display_name": "Test User",
    "subscription_tier": "free",
    "max_devices": 5,
    "max_concurrent_streams": 1
  },
  "device": {
    "id": "device-uuid",
    "device_name": "Test iPhone",
    "device_type": "mobile",
    "is_trusted": false
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

** Success Criteria:**
- [ ] User created with UUID
- [ ] Device auto-registered
- [ ] JWT tokens returned
- [ ] Free tier assigned by default

### Test 4.2: User Login

```bash
# Save the access_token from response!

# Endpoint: POST /auth/login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -H "device-name: Test Laptop" \
  -H "device-type: desktop" \
  -H "os: Windows" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Expected: Same format as register, but existing device may update
```

** Success Criteria:**
- [ ] Returns tokens
- [ ] Device updated with new login time
- [ ] Failed attempts tracked

### Test 4.3: Token Refresh

```bash
# Endpoint: POST /auth/refresh

export REFRESH_TOKEN="eyJhbGciOiJIUzI1NiIs..."  # From login

curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"${REFRESH_TOKEN}\"}"

# Expected: New access_token and refresh_token
```

---

## 5. PAYMENT SYSTEM TESTS

### Test 5.1: Create Payment Intent for Song Purchase

```bash
# Endpoint: POST /payments/song-purchase?user_id={id}&song_id={id}
# Auth: Bearer token required

export ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIs..."
export USER_ID="user-uuid-from-register"
export SONG_ID="song-uuid-from-navidrome"

curl -X POST "http://localhost:8000/payments/song-purchase?user_id=${USER_ID}&song_id=${SONG_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json"

# Expected Response:
{
  "payment_intent_id": "pi_test_123456",
  "client_secret": "pi_test_secret_xxx",
  "amount": 0.99,
  "currency": "USD",
  "song_id": "song-uuid",
  "status": "requires_payment",
  "redirect_url": "https://checkout.stripe.com/..."
}
```

** Success Criteria:**
- [ ] Payment intent created
- [ ] Amount matches song price
- [ ] Client secret for Stripe.js

### Test 5.2: Simulate Payment Webhook (Test Mode)

```bash
# Endpoint: POST /webhooks/payment-confirmed
# This simulates Stripe webhook in test mode

curl -X POST "http://localhost:8000/webhooks/payment-confirmed" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: test-signature" \
  -d '{
    "payment_intent_id": "pi_test_123456",
    "status": "completed",
    "metadata": {
      "type": "song_purchase",
      "user_id": "'${USER_ID}'",
      "song_id": "'${SONG_ID}'",
      "price": 0.99
    }
  }'

# Expected Response:
{
  "received": true,
  "processed": true,
  "access_granted": true,
  "song_id": "song-uuid",
  "user_id": "user-uuid"
}
```

** Success Criteria:**
- [ ] Webhook received
- [ ] Access granted in database
- [ ] Cache invalidated

### Test 5.3: Check Access After Purchase

```bash
# Endpoint: GET /user/library

curl "http://localhost:8000/user/library" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

# Expected:
{
  "purchased_songs": [
    {
      "song_id": "song-uuid",
      "title": "Song Title",
      "artist": "Artist Name",
      "purchased_at": "2024-04-21T10:00:00Z"
    }
  ],
  "total_count": 1
}
```

---

## 6. PLAYBACK & ACCESS CONTROL TESTS

### Test 6.1: Playback - FREE Song

```bash
# Prerequisites: Set a song as is_free=true in database

export FREE_SONG_ID="free-song-uuid"
export DEVICE_ID="device-uuid-from-login"

curl -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "network-type: wifi" \
  -d '{
    "device_id": "'${DEVICE_ID}'",
    "network_type": "wifi"
  }'

# Expected Response (if recommendation returns free song):
{
  "status": "PLAYING",
  "song": {
    "id": "song-uuid",
    "title": "Free Song",
    "artist": "Artist",
    "duration": 180
  },
  "stream": {
    "url": "http://localhost:4533/rest/stream.view?id=...&maxBitRate=320",
    "quality": "high",
    "bitrate": 320,
    "codec": "aac"
  },
  "access": {
    "type": "free",
    "is_owned": false
  }
}
```

** Success Criteria:**
- [ ] Status is "PLAYING"
- [ ] Stream URL generated
- [ ] Access type shows "free"

### Test 6.2: Playback - PAYMENT_REQUIRED (Unpaid Song)

```bash
# Ensure song is NOT free and NOT purchased

export PAID_SONG_ID="paid-song-uuid"  # Not in user library

curl -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'${DEVICE_ID}'",
    "current_song_id": "'${PAID_SONG_ID}'"
  }'

# Expected Response:
{
  "status": "PAYMENT_REQUIRED",
  "message": "Purchase required to play full song",
  "song_preview": {
    "id": "paid-song-uuid",
    "title": "Premium Song",
    "artist": "Artist Name",
    "preview_url": "http://localhost:4533/rest/stream.view?id=...&time=30",
    "preview_duration": 30
  },
  "purchase_options": {
    "individual": {
      "price": 0.99,
      "currency": "USD",
      "purchase_url": "/api/v1/payments/song-purchase?user_id=...&song_id=..."
    },
    "subscription": {
      "available": true,
      "tiers": ["premium", "premium_plus"],
      "unlocks_all": true
    }
  }
}
```

** Success Criteria:**
- [ ] Status is "PAYMENT_REQUIRED"
- [ ] Preview URL provided (30-second clip)
- [ ] Purchase options shown
- [ ] Subscription alternative offered

### Test 6.3: Playback - OWNED Song (After Purchase)

```bash
# After completing Test 5.2 (payment webhook)

curl -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'${DEVICE_ID}'",
    "current_song_id": "'${SONG_ID}'",
    "network_type": "wifi"
  }'

# Expected:
{
  "status": "PLAYING",
  "access": {
    "type": "purchase",
    "is_owned": true
  },
  "stream": {
    "url": "...",
    "quality": "high",
    "bitrate": 320
  }
}
```

** Success Criteria:**
- [ ] Status is "PLAYING"
- [ ] Access type is "purchase"
- [ ] is_owned: true

### Test 6.4: Concurrent Stream Limit

```bash
# Test 1: Start first stream
curl -X POST "http://localhost:8000/play/start" ...
# Save session_id_1

# Test 2: Try second stream (free tier = limit 1)
curl -X POST "http://localhost:8000/play/start" ...

# Expected:
{
  "error": "CONCURRENT_LIMIT",
  "message": "Maximum 1 concurrent stream(s) reached",
  "max_streams": 1,
  "active_sessions": [
    {
      "session_id": "session-1",
      "device_id": "device-1",
      "started_at": "..."
    }
  ]
}
```

** Success Criteria:**
- [ ] Error code CONCURRENT_LIMIT
- [ ] Active sessions listed
- [ ] Suggestion to stop other device

### Test 6.5: Playback Heartbeat

```bash
# While playing, send heartbeat every 30 seconds

export SESSION_ID="session-uuid-from-start"

curl -X POST "http://localhost:8000/play/heartbeat" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'${SESSION_ID}'",
    "position_ms": 45000
  }'

# Expected:
{
  "ok": true,
  "session_active": true
}
```

### Test 6.6: Stop Playback

```bash
curl -X POST "http://localhost:8000/play/stop" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'${SESSION_ID}'"
  }'

# Expected:
{
  "stopped": true,
  "session_id": "session-uuid"
}
```

---

## 7. RECOMMENDATION SYSTEM TESTS

### Test 7.1: Get Next Song

```bash
curl "http://localhost:8000/recommendations/next?user_id=${USER_ID}&current_song_id=${SONG_ID}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

# Expected:
{
  "generated_at": "2024-04-21T10:00:00Z",
  "recommendations": [
    {
      "song_id": "recommended-song",
      "title": "...",
      "score": 87.5,
      "reasons": ["High completion rate", "Genre match"]
    }
  ]
}
```

### Test 7.2: Get Personalized Feed

```bash
curl "http://localhost:8000/recommendations/for-you?user_id=${USER_ID}&limit=12&location=ET" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

# Expected: 12 songs with mix of sources
```

### Test 7.3: Get Trending

```bash
curl "http://localhost:8000/recommendations/trending?location=ET&limit=10" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

# Expected: Songs ordered by hot score
```

---

## 8. DEVICE MANAGEMENT TESTS

### Test 8.1: List Devices

```bash
curl "http://localhost:8000/devices" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

# Expected:
{
  "devices": [
    {
      "id": "device-1",
      "device_name": "Test iPhone",
      "device_type": "mobile",
      "is_trusted": false,
      "last_active_at": "..."
    },
    {
      "id": "device-2",
      "device_name": "Test Laptop",
      "device_type": "desktop",
      "is_trusted": false
    }
  ]
}
```

### Test 8.2: Remove Device

```bash
export DEVICE_TO_REMOVE="device-2-uuid"

curl -X DELETE "http://localhost:8000/devices/${DEVICE_TO_REMOVE}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

# Expected:
{
  "removed": true
}
```

---

## 9. AUDIO QUALITY TESTS

### Test 9.1: Mobile + Mobile Data (Low Quality)

```bash
curl -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "network-type: mobile_data" \
  -H "network-quality: 0.3" \
  -d '{
    "device_id": "'${DEVICE_ID}'",
    "network_type": "mobile_data"
  }'

# Expected quality: "low" or "medium" (64-128 kbps)
# Reason: "Adjusted from high to low for mobile_data"
```

### Test 9.2: Desktop + WiFi (High Quality)

```bash
curl -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "network-type: wifi" \
  -H "network-quality: 0.9" \
  -d '{
    "device_id": "desktop-device-id",
    "network_type": "wifi"
  }'

# Expected quality: "high" or "lossless" (320+ kbps)
```

---

## 10. INTEGRATION TESTS

### Test 10.1: Full Playback Flow

```bash
#!/bin/bash
# full_flow_test.sh

echo "=== Step 1: Register User ==="
REGISTER=$(curl -s -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -H "device-name: iPhone" \
  -H "device-type: mobile" \
  -d '{"email":"test@flow.com","password":"Test123!"}')
echo $REGISTER | python -m json.tool

TOKEN=$(echo $REGISTER | python -c "import sys,json; print(json.load(sys.stdin)['tokens']['access_token'])")
USER_ID=$(echo $REGISTER | python -c "import sys,json; print(json.load(sys.stdin)['user']['id'])")
DEVICE_ID=$(echo $REGISTER | python -c "import sys,json; print(json.load(sys.stdin)['device']['id'])")

echo "=== Step 2: Try to Play (Expect PAYMENT_REQUIRED) ==="
curl -s -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\": \"$DEVICE_ID\"}"

echo ""
echo "=== Step 3: Purchase Song ==="
SONG_ID="your-song-uuid"
PAYMENT=$(curl -s -X POST "http://localhost:8000/payments/song-purchase?user_id=$USER_ID&song_id=$SONG_ID" \
  -H "Authorization: Bearer $TOKEN")
echo $PAYMENT | python -m json.tool

echo "=== Step 4: Simulate Payment Webhook ==="
curl -s -X POST "http://localhost:8000/webhooks/payment-confirmed" \
  -H "Content-Type: application/json" \
  -d "{\"payment_intent_id\": \"pi_test_123\", \"metadata\": {\"type\": \"song_purchase\", \"user_id\": \"$USER_ID\", \"song_id\": \"$SONG_ID\"}}"

echo ""
echo "=== Step 5: Play Successfully ==="
curl -s -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\": \"$DEVICE_ID\", \"current_song_id\": \"$SONG_ID\"}" | python -m json.tool

echo ""
echo "=== Step 6: Check Library ==="
curl -s "http://localhost:8000/user/library" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

---

## 11. TROUBLESHOOTING GUIDE

### Issue: "No module named 'sqlalchemy'"
```bash
cd backend
.venv\Scripts\activate
pip install sqlalchemy
```

### Issue: "Navidrome connection refused"
```bash
# Check if Navidrome is running
docker ps | findstr navidrome

# If not running:
docker start navidrome

# Or recreate:
docker run -d --name navidrome -p 4533:4533 -v navidrome-data:/data deluan/navidrome:latest
```

### Issue: "Port 8000 already in use"
```bash
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --port 8001
```

### Issue: "Access denied" on playback
```bash
# Check if access was granted
curl "http://localhost:8000/user/library" -H "Authorization: Bearer $TOKEN"

# Clear cache if needed
redis-cli FLUSHDB
```

### Issue: "Concurrent stream limit"
```bash
# List active sessions
curl "http://localhost:8000/user/sessions" -H "Authorization: Bearer $TOKEN"

# Stop all sessions
curl -X POST "http://localhost:8000/play/stop-all" -H "Authorization: Bearer $TOKEN"
```

---

##  FINAL CHECKLIST

### Pre-Testing:
- [ ] Navidrome running on :4533
- [ ] Backend running on :8000
- [ ] Database migrated
- [ ] Test user registered
- [ ] At least 1 song in Navidrome
- [ ] Song pricing configured (free or paid)

### Core Features:
- [ ] User registration/login
- [ ] Device auto-registration
- [ ] Playback with access control
- [ ] Payment flow (intent  webhook  access)
- [ ] Audio quality adaptation
- [ ] Concurrent stream limits
- [ ] Session heartbeat/stop

### Advanced Features:
- [ ] Recommendations working
- [ ] Trending songs
- [ ] Device management
- [ ] User library
- [ ] Subscription vs individual purchase

---

**Document Version:** 2.0  
**Last Updated:** April 21, 2026  
**Systems:** FastAPI + Navidrome + PostgreSQL/Redis

---

## 12. PAYMENT SYSTEM TESTS (PostgreSQL + Repository Pattern)

### 12.1: Database Connection Test

```bash
# Test PostgreSQL connection
cd backend
python -c "
from shared.db_postgres import get_sync_engine
engine = get_sync_engine()
with engine.connect() as conn:
    result = conn.execute(text('SELECT 1'))
    print('Database connection:', result.fetchone())
"

# Expected: (1,)
```

** Success Criteria:**
- [ ] PostgreSQL connection pool created
- [ ] Connection test passes

### 12.2: Alembic Migration Test

```bash
# Create initial migration
cd backend
alembic revision --autogenerate -m "Initial payment tables"

# Run migration
alembic upgrade head

# Verify tables created
psql $DATABASE_URL -c "\\dt"

# Expected output:
#              List of relations
#  Schema |      Name      | Type  | Owner
# --------+----------------+-------+--------
#  public | payments       | table | postgres
#  public | transactions   | table | postgres
```

** Success Criteria:**
- [ ] Migration created successfully
- [ ] Tables exist in database

### 12.3: Payment Service Unit Test (Mock Repository)

```bash
# Run unit test without database
cd backend
python -m pytest tests/test_payment_service.py -v

# Or manual test:
python << 'EOF'
import asyncio
from apps.payments.repositories.mock_repository import MockPaymentRepository
from apps.payments.services.payment_service_v2 import PaymentService
from apps.payments.schemas import PaymentCreate

async def test():
    repo = MockPaymentRepository()
    service = PaymentService(repo)
    
    result = await service.create_payment_intent(
        PaymentCreate(amount=100.00, currency="ETB", provider="chapa")
    )
    print("Created payment:", result.id)
    print("Status:", result.status)
    assert result.status == "pending"
    print(" Unit test passed!")

asyncio.run(test())
EOF
```

** Success Criteria:**
- [ ] Payment created without database
- [ ] Status is "pending"
- [ ] No SQLAlchemy/Postgres dependencies

### 12.4: PostgreSQL Repository Integration Test

```bash
# Requires running PostgreSQL
cd backend
python << 'EOF'
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db_postgres import get_async_db
from apps.payments.repositories.postgres_repository import PostgresPaymentRepository
from apps.payments.services.payment_service_v2 import PaymentService
from apps.payments.schemas import PaymentCreate

async def test():
    async for db in get_async_db():
        repo = PostgresPaymentRepository(db)
        service = PaymentService(repo)
        
        result = await service.create_payment_intent(
            PaymentCreate(
                user_id="user-123",
                amount=50.00,
                currency="ETB",
                provider="chapa"
            )
        )
        print("Payment created:", result.id)
        
        # Verify in database
        fetched = await service.get_payment(result.id)
        print("Fetched:", fetched.id, fetched.status)
        assert fetched.id == result.id
        print(" Integration test passed!")
        break

asyncio.run(test())
EOF
```

** Success Criteria:**
- [ ] Payment persisted to PostgreSQL
- [ ] Data retrieved correctly
- [ ] Connection pool working

### 12.5: Exception Handling Test

```bash
# Test PaymentNotFoundError
curl -X GET "http://localhost:8000/payments/nonexistent-id" \
  -H "Authorization: Bearer $TOKEN"

# Expected Response:
{
  "error": {
    "code": "PAYMENT_NOT_FOUND",
    "message": "Payment nonexistent-id not found",
    "details": {}
  }
}
```

** Success Criteria:**
- [ ] HTTP 404 status
- [ ] Error code: PAYMENT_NOT_FOUND
- [ ] Clean JSON response (no stack trace)

### 12.6: Duplicate Payment Prevention Test

```bash
# 1. Create payment with external_id
EXTERNAL_ID="order-123"
curl -X POST "http://localhost:8000/payments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"user-123\",
    \"amount\": 100,
    \"currency\": \"ETB\",
    \"provider\": \"chapa\",
    \"external_id\": \"${EXTERNAL_ID}\"
  }"

# 2. Try duplicate
# Should return 409 CONFLICT with error code DUPLICATE_PAYMENT
```

** Success Criteria:**
- [ ] First payment succeeds (201)
- [ ] Duplicate rejected (409)
- [ ] Error code: DUPLICATE_PAYMENT

### 12.7: Provider Unavailability Test

```bash
# Test when Chapa API is down
# (Simulate by setting wrong Chapa URL in config)

# Update .env temporarily:
CHAPA_BASE_URL=https://invalid-url

# Try payment
curl -X POST "http://localhost:8000/payments" ...

# Expected after timeout:
{
  "error": {
    "code": "PROVIDER_UNAVAILABLE",
    "message": "Payment provider is currently unavailable",
    "details": {
      "provider": "chapa",
      "retry_after": 60
    }
  }
}
```

** Success Criteria:**
- [ ] HTTP 503 status
- [ ] Error code: PROVIDER_UNAVAILABLE
- [ ] Retry information provided

### 12.8: Webhook Signature Verification Test

```bash
# Test with valid signature
curl -X POST "http://localhost:8000/webhooks/chapa" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: valid-signature" \
  -d '{"status": "success", "tx_ref": "order-123"}'

# Expected: 200, payment updated

# Test with invalid signature
curl -X POST "http://localhost:8000/webhooks/chapa" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: invalid-signature" \
  -d '{"status": "success", "tx_ref": "order-123"}'

# Expected:
{
  "error": {
    "code": "INVALID_SIGNATURE",
    "message": "Webhook signature verification failed",
    "details": {}
  }
}
```

** Success Criteria:**
- [ ] Valid signature accepted (200)
- [ ] Invalid signature rejected (401)
- [ ] Error code: INVALID_SIGNATURE

### 12.9: Configuration Validation Test

```bash
# Test with missing SECRET_KEY
unset SECRET_KEY
python -c "
from apps.payments.config_pydantic import get_settings
try:
    settings = get_settings()
except Exception as e:
    print('Validation error:', e)
"

# Expected: ValidationError: SECRET_KEY must be at least 32 characters

# Test with valid config
export SECRET_KEY="this-is-a-32-character-key!!"
python -c "
from apps.payments.config_pydantic import get_settings
settings = get_settings()
print('Config loaded:')
print('  App name:', settings.app_name)
print('  Pool size:', settings.db_pool_size)
print('  Telebirr enabled:', settings.telebirr_enabled)
"
```

** Success Criteria:**
- [ ] Missing SECRET_KEY raises ValidationError
- [ ] Valid config loads successfully
- [ ] Provider availability correctly detected

---

## 13. PERFORMANCE TESTS

### 13.1: Connection Pool Test

```bash
# Test concurrent connections
python << 'EOF'
import asyncio
import time
from shared.db_postgres import get_async_db

async def test_connection():
    async for db in get_async_db():
        result = await db.execute(text("SELECT pg_backend_pid()"))
        pid = result.scalar()
        return pid

async def main():
    start = time.time()
    tasks = [test_connection() for _ in range(50)]
    pids = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    unique_pids = len(set(pids))
    print(f"50 connections used {unique_pids} database PIDs")
    print(f"Time: {elapsed:.2f}s")
    print(f"Pool working: {unique_pids < 50}")

asyncio.run(main())
EOF
```

** Success Criteria:**
- [ ] Connections reuse database PIDs (pool working)
- [ ] 50 connections complete quickly (< 5s)

### 13.2: Repository Pattern Performance

```bash
# Compare direct SQL vs Repository
python << 'EOF'
import asyncio
import time
from apps.payments.repositories.mock_repository import MockPaymentRepository
from apps.payments.repositories.postgres_repository import PostgresPaymentRepository
from shared.db_postgres import get_async_db

async def benchmark_mock():
    repo = MockPaymentRepository()
    start = time.time()
    for i in range(100):
        await repo.create_payment({
            "user_id": f"user-{i}",
            "amount": 100,
            "currency": "ETB",
            "provider": "chapa"
        })
    return time.time() - start

async def benchmark_postgres():
    async for db in get_async_db():
        repo = PostgresPaymentRepository(db)
        start = time.time()
        for i in range(100):
            await repo.create_payment({
                "user_id": f"user-{i}",
                "amount": 100,
                "currency": "ETB",
                "provider": "chapa"
            })
        return time.time() - start

async def main():
    mock_time = await benchmark_mock()
    pg_time = await benchmark_postgres()
    
    print(f"Mock: {mock_time:.2f}s for 100 payments")
    print(f"PostgreSQL: {pg_time:.2f}s for 100 payments")
    print(f"Overhead: {(pg_time/mock_time):.1f}x")

asyncio.run(main())
EOF
```

** Success Criteria:**
- [ ] Mock repository is fast (< 1s for 100 ops)
- [ ] PostgreSQL repository reasonable speed (< 5s for 100 ops)

---

## 14. DEPLOYMENT CHECKLIST

### Pre-Deployment:
- [ ] Environment variables set (SECRET_KEY, DATABASE_URL, provider keys)
- [ ] PostgreSQL running and accessible
- [ ] Alembic migrations applied
- [ ] Unit tests pass (MockRepository)
- [ ] Integration tests pass (PostgreSQL)
- [ ] Exception handlers registered in main.py
- [ ] Pydantic Settings loaded without errors

### Post-Deployment:
- [ ] Health check endpoint responds
- [ ] Database connection pool initialized
- [ ] Payment creation works
- [ ] Webhook signature verification works
- [ ] Error responses are clean JSON (no stack traces)

---

**End of Payment System Tests**
