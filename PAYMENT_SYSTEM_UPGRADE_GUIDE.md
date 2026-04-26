# PAYMENT_SYSTEM_UPGRADE_GUIDE.md

## Shega-1.0 Payment System - Production PostgreSQL Upgrade

This document describes the four-pillar upgrade to production-ready payment infrastructure.

---

## 1. DATABASE MIGRATION (Alembic + PostgreSQL)

### Files Created:
- `backend/alembic.ini` - Alembic configuration
- `backend/alembic/env.py` - Auto-detects models from apps/payments/models.py
- `backend/shared/db_postgres.py` - PostgreSQL with connection pooling (psycopg2/asyncpg)

### Migration Commands:

```bash
cd backend

# 1. Initialize Alembic (if not exists)
alembic init alembic

# 2. Create migration
alembic revision --autogenerate -m "Initial payment tables"

# 3. Run migration
alembic upgrade head

# 4. Rollback (if needed)
alembic downgrade -1
```

### Environment Variables:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/shega_payments
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

---

## 2. CUSTOM EXCEPTION FRAMEWORK

### Files Created:
- `backend/apps/payments/exceptions.py` - Exception hierarchy
- `backend/apps/payments/exception_handlers.py` - FastAPI handlers

### Exception Hierarchy:
```
PaymentError (base)
 ProviderUnavailableError (503)
 SignatureVerificationError (401)
 PaymentNotFoundError (404)
 DuplicatePaymentError (409)
 InvalidPaymentStateError (400)
 InsufficientFundsError (402)
 CurrencyNotSupportedError (400)
 ValidationError (422)
 ConfigurationError (500)
 RefundError (400)
 TimeoutError (504)
```

### Register in main.py:
```python
from apps.payments.exception_handlers import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

### Response Format:
```json
{
  "error": {
    "code": "PAYMENT_NOT_FOUND",
    "message": "Payment not found",
    "details": {}
  }
}
```

---

## 3. SECURE CONFIGURATION (Pydantic Settings)

### Files Created:
- `backend/apps/payments/config_pydantic.py` - Pydantic Settings

### Environment Variables Required:
```env
# Security (REQUIRED - no defaults)
SECRET_KEY=your-32-char-minimum-secret-key

# Database
DATABASE_URL=postgresql://...

# Provider Keys (no hardcoded defaults)
TELEBIRR_APP_ID=
TELEBIRR_APP_KEY=
TELEBIRR_PRIVATE_KEY=
TELEBIRR_PUBLIC_KEY=

CHAPA_SECRET_KEY=
CHAPA_PUBLIC_KEY=

CBE_MERCHANT_ID=
CBE_API_KEY=
CBE_PRIVATE_KEY=

# Feature Flags
ENABLE_REFUNDS=true
AUTO_CAPTURE=true
```

### Usage:
```python
from apps.payments.config_pydantic import get_settings

settings = get_settings()

# Access with validation
secret = settings.secret_key  # Fails if not set

# Provider config
telebirr_config = settings.get_provider_config("telebirr")
if settings.telebirr_enabled:
    # Initialize provider
```

---

## 4. SERVICE DECOUPLING (Repository Pattern)

### Files Created:
- `backend/apps/payments/repositories/base.py` - Interface
- `backend/apps/payments/repositories/postgres_repository.py` - PostgreSQL impl
- `backend/apps/payments/repositories/mock_repository.py` - Test mock
- `backend/apps/payments/services/payment_service_v2.py` - Decoupled service

### Architecture:
```
API Layer (FastAPI)
    
PaymentService (business logic)
    
PaymentRepositoryInterface (abstract)
    
     PostgresPaymentRepository (production)
     MockPaymentRepository (testing)
     MongoPaymentRepository (future)
```

### Production Usage:
```python
from apps.payments.repositories.postgres_repository import PostgresPaymentRepository
from apps.payments.services.payment_service_v2 import PaymentService
from shared.db_postgres import get_async_db

async def get_payment_service(
    db: AsyncSession = Depends(get_async_db)
) -> PaymentService:
    repo = PostgresPaymentRepository(db)
    return PaymentService(repo)

@app.post("/payments")
async def create_payment(
    data: PaymentCreate,
    service: PaymentService = Depends(get_payment_service)
):
    return await service.create_payment_intent(data)
```

### Testing Usage:
```python
import pytest
from apps.payments.repositories.mock_repository import MockPaymentRepository
from apps.payments.services.payment_service_v2 import PaymentService

@pytest.fixture
def payment_service():
    repo = MockPaymentRepository()
    return PaymentService(repo)

async def test_create_payment(payment_service):
    result = await payment_service.create_payment_intent(
        PaymentCreate(amount=100, currency="ETB", provider="chapa")
    )
    assert result.amount == "100"
    assert result.status == "pending"
```

---

## INTEGRATION STEPS

### Step 1: Update main.py
```python
# backend/main.py

from apps.payments.exception_handlers import register_exception_handlers
from apps.payments.config_pydantic import get_settings

# Load settings
settings = get_settings()

# Create app
app = FastAPI(
    debug=settings.is_development,
    title=settings.app_name
)

# Register exception handlers
register_exception_handlers(app)

# Include payment routers
from apps.payments.api.routes import router as payments_router
app.include_router(payments_router, prefix="/payments")
```

### Step 2: Update Docker Compose
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: shega_payments
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    
  backend:
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/shega_payments
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - postgres
      - redis
```

### Step 3: Run Migrations
```bash
cd backend
alembic upgrade head
```

---

## TESTING

### Unit Tests (No Database):
```python
# tests/test_payment_service.py
import pytest
from apps.payments.repositories.mock_repository import MockPaymentRepository
from apps.payments.services.payment_service_v2 import PaymentService
from apps.payments.schemas import PaymentCreate

@pytest.fixture
def service():
    return PaymentService(MockPaymentRepository())

async def test_create_payment(service):
    result = await service.create_payment_intent(
        PaymentCreate(amount=100, currency="ETB", provider="chapa")
    )
    assert result.status == "pending"
```

### Integration Tests (With PostgreSQL):
```bash
# Test with real database
cd backend
pytest tests/integration/test_payments.py -v
```

---

## FILES SUMMARY

| File | Purpose |
|------|---------|
| `alembic.ini` | Alembic configuration |
| `alembic/env.py` | Auto-detect models |
| `shared/db_postgres.py` | PostgreSQL connection pool |
| `apps/payments/exceptions.py` | Exception hierarchy |
| `apps/payments/exception_handlers.py` | FastAPI handlers |
| `apps/payments/config_pydantic.py` | Pydantic Settings |
| `apps/payments/repositories/base.py` | Repository interface |
| `apps/payments/repositories/postgres_repository.py` | PostgreSQL impl |
| `apps/payments/repositories/mock_repository.py` | Test mock |
| `apps/payments/services/payment_service_v2.py` | Decoupled service |

---

## SECURITY CHECKLIST

- [ ] No hardcoded secrets in code
- [ ] SECRET_KEY environment variable set (32+ chars)
- [ ] Provider keys in environment variables
- [ ] Database credentials in env vars
- [ ] Debug mode disabled in production
- [ ] Error handlers hide internal details in production
- [ ] Webhook signatures verified

---

## NEXT STEPS

1. Copy files to backend directory
2. Set environment variables in .env
3. Run migrations: `alembic upgrade head`
4. Update main.py to use new handlers
5. Write tests using MockPaymentRepository
6. Deploy with PostgreSQL
