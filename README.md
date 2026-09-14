# AI E-Commerce & Sanal Market Backend

Production-ready, high-performance Sanal Market / Online Grocery e-commerce backend built with Python 3.13, FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic, Pydantic V2, Argon2id, and Pytest.

---

## 🛠️ Tech Stack

- **Framework**: FastAPI (v0.141)
- **Database**: PostgreSQL 16 (via Homebrew / Docker)
- **ORM**: SQLAlchemy 2.0 (with DB Check Constraints & Relations)
- **Migrations**: Alembic 1.19
- **Validation**: Pydantic V2 (Pre-validators, computed fields & custom error contracts)
- **Security & Auth**: Argon2id (`argon2-cffi`), JWT (jose), Bcrypt fallback, Rate Limiting (`slowapi`), Sensitive Log Sanitization
- **Testing**: Pytest 8.3 + FastAPI TestClient (25 automated unit & integration tests)

---

## 🌟 Key Features

- **Production-Grade Authentication**:
  - Email trim & lowercase normalization.
  - Strict password policy (min 8 chars, uppercase, lowercase, digit, special char, max 128).
  - Argon2id password hashing & timing-safe verification.
  - User enumeration mitigation with identical 401 `INVALID_CREDENTIALS` responses.
  - Rate limiting (5 attempts/min on register/login).
  - Automated log masking for sensitive fields (`password`, `token`, `authorization`).

- **Sanal Market / Grocery Catalog (Categories & Products)**:
  - **Category Domain**: Hierarchical parent-child tree, slugify with conflict resolution, `GET /categories/{id}/products` endpoint.
  - **Safe Category Deletion**: Hard delete prevented if active products are attached; soft-deactivates category (`is_active=False`) instead.
  - **Product Domain**:
    - Measurement units (`UnitType` enum: `kg`, `gram`, `piece`, `liter`, `pack`), price, discount_price, stock_quantity, SKU, `is_organic`, and `origin`.
    - **DB Check Constraints**: `stock_quantity >= 0` and `price > 0` enforced at database schema level.
    - **Dynamic Product Status**: Computed automatically from `stock_quantity` and `is_active` (`in_stock`, `out_of_stock`, `inactive`).
  - **Filtering & Search**: Category ID/slug, min/max price, unit, status (`in_stock`, `out_of_stock`, `inactive`), search keywords, organic flag, sorting, and pagination.

---

## 🚀 Quickstart & Setup

### 1. Requirements & Environment
Ensure Python 3.13 and PostgreSQL are installed and running.

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables (`.env`)
Create a `.env` file in the project root:
```env
DATABASE_URL=postgresql+psycopg://ecommerce:ecommerce_password@localhost:5432/ecommerce_db
SECRET_KEY=your_secure_random_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
HASH_ALGORITHM=argon2
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_REGISTER=5/minute
```

### 3. Database Migrations
Apply Alembic migrations to create tables and database check constraints:
```bash
alembic upgrade head
```

### 4. Seed Sanal Market Data (Optional)
Populate real grocery items (Domates, Biber, Pirinç, Kıyma, Süt, Maden Suyu vb.):
```bash
PYTHONPATH=. python scripts/seed_market_data.py
```

### 5. Run Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
Swagger API Docs available at: 👉 **http://127.0.0.1:8000/docs**

---

## 🧪 Running Automated Tests

Run the full Pytest unit and integration test suite:
```bash
PYTHONPATH=. pytest -v
```

All 25 tests run in an isolated in-memory test database without mutating your live database.
