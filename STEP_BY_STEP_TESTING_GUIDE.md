# STEP-BY-STEP TESTING GUIDE
# Shega Music Platform - Complete Testing Procedure
# Last Updated: April 24, 2026

## 🎯 PREREQUISITES

Before starting, ensure you have:
- [ ] Docker Desktop running
- [ ] Node.js 18+ installed
- [ ] Python 3.11+ installed
- [ ] Git installed

---

## STEP 1: Environment Setup (5 minutes)

### 1.1 Clone/Navigate to Project
```bash
cd c:\Users\u\Music\music-platform
```

### 1.2 Create Environment Files

**Backend `.env`:**
```bash
cd backend
cat > .env << 'EOF'
# Database (PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/shega_payments
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Security (REQUIRED - 32+ characters)
SECRET_KEY=your-super-secret-32-char-key-here!!

# JWT
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Navidrome
NAVIDROME_URL=http://localhost:4533
NAVIDROME_USER=admin
NAVIDROME_PASS=admin

# Redis (optional, falls back to memory)
REDIS_URL=redis://localhost:6379/0

# Provider Keys (get from providers)
TELEBIRR_APP_ID=
TELEBIRR_APP_KEY=
TELEBIRR_PRIVATE_KEY=
CHAPA_SECRET_KEY=
CHAPA_PUBLIC_KEY=

# App Settings
DEBUG=true
ENVIRONMENT=development
EOF
```

**Feishin `.env`:**
```bash
cd ../feishin
cat > .env << 'EOF'
# API Endpoints
SHEGA_API_URL=http://localhost:8000/api/v1
NAVIDROME_URL=http://localhost:4533
PUBLIC_API_URL=http://localhost:8000

# App
NODE_ENV=development
EOF
```

---

## STEP 2: Start Infrastructure (10 minutes)

### 2.1 Start PostgreSQL
```bash
docker run -d \
  --name shega-postgres \
  -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=shega_payments \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine

# Verify
sleep 5
docker ps | findstr shega-postgres
```

**Expected:** Container running on port 5432

### 2.2 Start Redis (Optional)
```bash
docker run -d \
  --name shega-redis \
  -p 6379:6379 \
  redis:7-alpine
```

### 2.3 Start Navidrome
```bash
docker run -d \
  --name navidrome \
  -p 4533:4533 \
  -v "${PWD}/music:/music:ro" \
  -v navidrome_data:/data \
  -e ND_SCANSCHEDULE=1h \
  deluan/navidrome:latest

# Verify
sleep 5
curl http://localhost:4533/rest/ping.view?u=admin&p=admin&v=1.16.1&c=test
```

**Expected:** XML response with `status="ok"`

---

## STEP 3: Backend Setup (10 minutes)

### 3.1 Virtual Environment
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
```

### 3.2 Install Dependencies
```bash
pip install -r requirements.txt

# Verify key packages
python -c "import sqlalchemy; import fastapi; import alembic; print('✓ All packages installed')"
```

### 3.3 Run Alembic Migrations
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial payment and playback tables"

# Apply migration
alembic upgrade head

# Verify tables
python << 'EOF'
from sqlalchemy import create_engine, inspect
engine = create_engine("postgresql://postgres:postgres@localhost:5432/shega_payments")
inspector = inspect(engine)
tables = inspector.get_table_names()
print("Tables created:", tables)
assert "payments" in tables or "song_access" in tables, "Migration failed!"
print("✓ Migration successful")
EOF
```

**Expected:** Tables: `payments`, `transactions`, `song_access`, `playback_sessions`, etc.

### 3.4 Start Backend Server
```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# OR production mode
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Verify:** Open http://localhost:8000/docs - Swagger UI should load

---

## STEP 4: Feishin Setup (5 minutes)

### 4.1 Install Dependencies
```bash
cd ../feishin
npm install
```

### 4.2 Start Feishin
```bash
# Development mode
npm run dev

# OR build and start
npm run build
npm start
```

**Verify:** Feishin window opens, can navigate to settings

---

## STEP 5: Authentication Flow (10 minutes)

### 5.1 Register User (via API)
```bash
# Register with device auto-detection
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -H "X-Device-Name: Test Laptop" \
  -H "X-Device-Type: desktop" \
  -H "X-OS: Windows" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "display_name": "Test User"
  }'
```

**Save the response:**
- `access_token` → for authenticated requests
- `device_id` → for playback requests
- `user_id` → for user-specific operations

### 5.2 Verify Token Works
```bash
export TOKEN="<access_token_from_response>"

curl "http://localhost:8000/user/me" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Expected:** User profile with `subscription_tier: "free"`

### 5.3 Test Device Registration
```bash
curl "http://localhost:8000/devices" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Expected:** List with 1 device ("Test Laptop")

---

## STEP 6: Payment System Tests (15 minutes)

### 6.1 Configure Song Pricing
```bash
# Add a song to the database (via admin or seed)
# For testing, insert directly:

python << 'EOF'
from sqlalchemy import create_engine, text
engine = create_engine("postgresql://postgres:postgres@localhost:5432/shega_payments")
with engine.connect() as conn:
    # Create a PAID song
    conn.execute(text("""
        INSERT INTO song_pricing (id, song_id, is_free, individual_price, requires_premium)
        VALUES ('1', 'song-123', false, 0.99, false)
        ON CONFLICT DO NOTHING
    """))
    conn.commit()
    print("✓ Test song configured (price: $0.99)")
EOF
```

### 6.2 Test PAYMENT_REQUIRED Response
```bash
curl -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "<device_id_from_register>",
    "current_song_id": "song-123",
    "network_type": "wifi"
  }'
```

**Expected:**
```json
{
  "status": "PAYMENT_REQUIRED",
  "message": "Purchase required to play full song",
  "song_preview": {
    "preview_url": "http://localhost:4533/rest/stream.view?id=song-123&time=30",
    "preview_duration": 30
  },
  "purchase_options": {
    "individual": {
      "price": 0.99,
      "currency": "USD"
    }
  }
}
```

### 6.3 Create Payment Intent
```bash
curl -X POST "http://localhost:8000/payments/song-purchase" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "<user_id>",
    "song_id": "song-123"
  }'
```

**Expected:** Payment intent with `client_secret` and `redirect_url`

### 6.4 Simulate Payment Webhook
```bash
curl -X POST "http://localhost:8000/webhooks/payment-confirmed" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: test-signature" \
  -d '{
    "payment_intent_id": "pi_test_123",
    "status": "completed",
    "metadata": {
      "type": "song_purchase",
      "user_id": "<user_id>",
      "song_id": "song-123",
      "price": 0.99
    }
  }'
```

**Expected:** `{"received": true, "access_granted": true}`

### 6.5 Verify Access Granted
```bash
# Try playing again
curl -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "<device_id>",
    "current_song_id": "song-123",
    "network_type": "wifi"
  }'
```

**Expected:** `status: "PLAYING"` with stream URL

### 6.6 Check User Library
```bash
curl "http://localhost:8000/user/library" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Expected:** `song-123` in `purchased_songs` array

---

## STEP 7: Playback & Session Tests (15 minutes)

### 7.1 Test Free Song Playback
```bash
# Configure a free song
python << 'EOF'
from sqlalchemy import create_engine, text
engine = create_engine("postgresql://postgres:postgres@localhost:5432/shega_payments")
with engine.connect() as conn:
    conn.execute(text("""
        INSERT INTO song_pricing (id, song_id, is_free, individual_price)
        VALUES ('2', 'song-free', true, null)
        ON CONFLICT DO NOTHING
    """))
    conn.commit()
    print("✓ Free song configured")
EOF

# Play free song
curl -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "<device_id>",
    "current_song_id": "song-free",
    "network_type": "wifi"
  }'
```

**Expected:** `status: "PLAYING"`, `access.type: "free"`

### 7.2 Test Audio Quality Selection

**Desktop + WiFi (High Quality):**
```bash
curl -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Network-Type: wifi" \
  -H "X-Network-Quality: 0.9" \
  -d '{"device_id": "<device_id>", "network_type": "wifi"}'
```

**Expected:** `quality: "high"`, `bitrate: 320`

**Mobile + Mobile Data (Low Quality):**
```bash
curl -X POST "http://localhost:8000/play/start" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Network-Type: mobile_data" \
  -H "X-Network-Quality: 0.3" \
  -d '{"device_id": "<device_id>", "network_type": "mobile_data"}'
```

**Expected:** `quality: "low"` or `"medium"`, reason mentions "mobile_data"

### 7.3 Test Playback Session

**Start Playback:**
```bash
# Response contains session.id
export SESSION_ID="<session_id_from_play_response>"
```

**Send Heartbeat:**
```bash
# Every 30 seconds while playing
curl -X POST "http://localhost:8000/play/heartbeat" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'${SESSION_ID}'",
    "position_ms": 45000
  }'
```

**Expected:** `{"ok": true, "session_active": true}`

**Stop Playback:**
```bash
curl -X POST "http://localhost:8000/play/stop" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "'${SESSION_ID}'"}'
```

**Expected:** `{"stopped": true}`

### 7.4 Test Concurrent Stream Limit

**Start First Stream:**
```bash
# Free tier: max 1 concurrent stream
# Start first playback and save session_id
```

**Try Second Stream:**
```bash
# Attempt second playback from same user
curl -X POST "http://localhost:8000/play/start" ...
```

**Expected:**
```json
{
  "error": "CONCURRENT_LIMIT",
  "message": "Maximum 1 concurrent stream(s) reached",
  "max_streams": 1,
  "active_sessions": [...]
}
```

---

## STEP 8: Recommendation System Tests (10 minutes)

### 8.1 Get Next Song
```bash
curl "http://localhost:8000/recommendations/next?user_id=<user_id>" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Expected:** Song recommendation with `score` and `reasons`

### 8.2 Get Personalized Feed
```bash
curl "http://localhost:8000/recommendations/for-you?user_id=<user_id>&limit=12&location=ET" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Expected:** 12 songs with mix of sources

### 8.3 Get Trending
```bash
curl "http://localhost:8000/recommendations/trending?location=ET&limit=10" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Expected:** Songs ordered by trending score

---

## STEP 9: Exception Handling Tests (10 minutes)

### 9.1 Payment Not Found (404)
```bash
curl "http://localhost:8000/payments/nonexistent-id" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Expected:**
```json
{
  "error": {
    "code": "PAYMENT_NOT_FOUND",
    "message": "Payment nonexistent-id not found",
    "details": {}
  }
}
```

### 9.2 Invalid Payment State (400)
```bash
# Try to confirm already-completed payment
curl -X POST "http://localhost:8000/payments/<completed_id>/confirm" \
  -H "Authorization: Bearer ${TOKEN}"
```

**Expected:**
```json
{
  "error": {
    "code": "INVALID_PAYMENT_STATE",
    "message": "Payment cannot be processed in current state",
    "details": {"current_status": "completed"}
  }
}
```

### 9.3 Validation Error (422)
```bash
# Send invalid data
curl -X POST "http://localhost:8000/payments/song-purchase" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
```

**Expected:** Field validation errors in standard format

---

## STEP 10: Repository Pattern Unit Tests (10 minutes)

### 10.1 Test with Mock Repository (No Database)
```bash
cd backend

# Run unit tests
python -m pytest tests/unit/test_payment_service.py -v
```

**Expected:** All tests pass without PostgreSQL running

### 10.2 Manual Mock Test
```bash
python << 'EOF'
import asyncio
from apps.payments.repositories.mock_repository import MockPaymentRepository
from apps.payments.services.payment_service_v2 import PaymentService

async def test():
    repo = MockPaymentRepository()
    service = PaymentService(repo)
    
    result = await service.create_payment_intent(
        type('obj', (object,), {
            'amount': 100.00,
            'currency': 'ETB',
            'provider': 'chapa',
            'model_dump': lambda: {'amount': 100, 'currency': 'ETB', 'provider': 'chapa'}
        })()
    )
    print("✓ Payment created without database:", result.id)
    print("✓ Status:", result.status)

asyncio.run(test())
EOF
```

---

## STEP 11: Feishin Integration Tests (10 minutes)

### 11.1 Verify API Integration
```bash
# Feishin should be running on :3000 (or Electron window)

# Test from Feishin DevTools console:
fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'feishin@test.com',
    password: 'Test123!',
    display_name: 'Feishin User'
  })
}).then(r => r.json()).then(console.log)
```

### 11.2 Test Playback from Feishin
```bash
# In Feishin DevTools:
import { shegaApi } from './api/shega'

// Should trigger payment modal for paid songs
shegaApi.startPlayback(deviceId, { songId: 'paid-song-123' })
  .then(response => {
    if (response.status === 'PAYMENT_REQUIRED') {
      console.log('Payment modal should appear')
    }
  })
```

---

## STEP 12: Performance Tests (Optional, 10 minutes)

### 12.1 Connection Pool Test
```bash
python << 'EOF'
import asyncio
import time
from shared.db_postgres import get_async_db

async def test_connection():
    async for db in get_async_db():
        result = await db.execute(text("SELECT pg_backend_pid()"))
        return result.scalar()

async def main():
    start = time.time()
    tasks = [test_connection() for _ in range(50)]
    pids = await asyncio.gather(*tasks)
    elapsed = time.time() - start
    
    unique = len(set(pids))
    print(f"50 connections: {unique} unique PIDs ({elapsed:.2f}s)")
    print(f"✓ Pool working: {unique < 50}")

asyncio.run(main())
EOF
```

### 12.2 Concurrent Playback Test
```bash
# Test 20 concurrent playbacks
python << 'EOF'
import asyncio
import aiohttp

async def play(session, token, device_id):
    async with session.post(
        'http://localhost:8000/play/start',
        headers={'Authorization': f'Bearer {token}'},
        json={'device_id': device_id, 'network_type': 'wifi'}
    ) as resp:
        return await resp.json()

async def main():
    # This should respect max_concurrent_streams limit
    print("Testing concurrent streams...")

asyncio.run(main())
EOF
```

---

## ✅ SUCCESS CHECKLIST

### Infrastructure:
- [ ] PostgreSQL running on :5432
- [ ] Redis running on :6379 (optional)
- [ ] Navidrome running on :4533
- [ ] Backend running on :8000
- [ ] Feishin running

### Authentication:
- [ ] User registered successfully
- [ ] JWT token received
- [ ] Device auto-registered
- [ ] Token refresh works

### Payment System:
- [ ] PAYMENT_REQUIRED response for unpaid songs
- [ ] Payment intent created
- [ ] Webhook grants access
- [ ] Song plays after purchase
- [ ] User library shows purchased songs

### Playback:
- [ ] Free songs play immediately
- [ ] Audio quality adapts to network
- [ ] Heartbeat keeps session alive
- [ ] Concurrent stream limit enforced
- [ ] Session cleanup works

### Error Handling:
- [ ] 404 returns clean JSON (no stack trace)
- [ ] 409 for duplicate payments
- [ ] 422 for validation errors
- [ ] 503 for provider unavailability

### Integration:
- [ ] Feishin connects to backend
- [ ] Payment modal appears for paid songs
- [ ] Audio plays through Feishin player

---

## 🚨 TROUBLESHOOTING

### PostgreSQL Connection Refused
```bash
docker start shega-postgres
# Or recreate:
docker run -d --name shega-postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
```

### Alembic Migration Failed
```bash
# Reset and retry
docker exec shega-postgres psql -U postgres -c "DROP DATABASE shega_payments;"
docker exec shega-postgres psql -U postgres -c "CREATE DATABASE shega_payments;"
alembic upgrade head
```

### Port 8000 Already in Use
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
# Or use different port: uvicorn app.main:app --port 8001
```

### Payment Webhook Not Working
```bash
# Check backend logs
# Verify webhook secret configured
# Use ngrok for external webhooks: ngrok http 8000
```

---

## 📊 TEST SUMMARY

| Category | Tests | Status |
|----------|-------|--------|
| Environment Setup | 3 | ⬜ |
| Authentication | 4 | ⬜ |
| Payment System | 6 | ⬜ |
| Playback & Sessions | 5 | ⬜ |
| Recommendations | 3 | ⬜ |
| Exception Handling | 3 | ⬜ |
| Repository Pattern | 2 | ⬜ |
| Feishin Integration | 2 | ⬜ |
| Performance | 2 | ⬜ |
| **Total** | **30** | **⬜** |

---

**Document Version:** 3.0  
**Last Updated:** April 24, 2026  
**Systems:** PostgreSQL, Redis, Navidrome, FastAPI, Feishin
