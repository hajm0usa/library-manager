# Library Management API

https://github.com/hajm0usa/library-manager

A small REST API for managing library books, users and loans built with FastAPI and MongoDB.

**Key features:**
- JWT-based authentication (`/token`)
- Role-based access control (`ADMIN`, `LIBRARIAN`, etc.)
- Book search, listing, create/update/delete
- Loan, return and renewal endpoints
- Async MongoDB access using `motor` / `pymongo`

**Requirements**
- Python 3.11+ (recommended)
- See `requirements.txt` for full dependency list

**Quick start (local)**

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment variables (example `.env`):

```
# MongoDB connection string
MONGO_URI=mongodb://localhost:27017/library

# JWT secret
SECRET_KEY=your-secret-key

# Admin user credentials
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-admin-passowrd
```

3. Run the app with Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or use Docker Compose:

```bash
docker-compose up --build
```

**API overview**

- GET /                       — health/root
- POST /token                 — obtain access token (OAuth2 password)
- Book endpoints (prefixed `/book`):
  - GET /book/book/{id}
  - GET /book/search
  - GET /book/list
  - POST /book/
  - PUT /book/book/{id}
  - DELETE /book/book/{id}

Other routers included: `/user`, `/loan`, `/loan_return`, `/loan_renewal`.

Open interactive API docs at `/docs` (Swagger UI) or `/redoc`.

Authentication: send `Authorization: Bearer <access_token>` header for protected endpoints.

Example: get a token and list books

```bash
# Get token (replace USER and PASS)
curl -X POST "http://localhost:8000/token" -F "username=USER" -F "password=PASS"

# Use token to list books
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/book/list
```

**Project structure (high level)**

- `main.py` — FastAPI app entrypoint
- `src/` — application package
  - `auth.py` — authentication helpers
  - `database.py` — MongoDB connection helpers
  - `routes/` — API route modules (book, user, loan, ...)
  - `crud/` — database CRUD logic
  - `models/` — Pydantic request/response models
