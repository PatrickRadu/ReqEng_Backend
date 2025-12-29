# ReqEng_Backend
# ReqEng_Backend

FastAPI backend for a psychological counseling platform with JWT authentication.

## Features

- 🔐 JWT-based authentication
- 👤 User registration and login
- 🔒 Protected endpoints
- 🗄️ PostgreSQL database with SQLModel
- 🔑 Password hashing with Argon2
- 📧 Email validation

## Prerequisites

- Python 3.13+
- PostgreSQL
- pip

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd reqEng
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# or
.venv\Scripts\activate  # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database and user:

```sql
CREATE DATABASE psych_db;
CREATE USER psych_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE psych_db TO psych_admin;

-- Connect to the database
\c psych_db

-- Grant schema permissions
GRANT ALL PRIVILEGES ON SCHEMA public TO psych_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO psych_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO psych_admin;
```

### 5. Environment variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:

```env
SECRET_KEY=your-super-secret-key-change-this
POSTGRES_USER=psych_admin
POSTGRES_PASSWORD=your_password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=psych_db
```

**Important:** Generate a secure `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Run the application

```bash
fastapi dev main.py
```

The API will be available at:
- **Server:** http://127.0.0.1:8000
- **Docs:** http://127.0.0.1:8000/docs

## API Endpoints

### Public Endpoints

#### Register
```bash
POST /register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "role": "patient"  # or "psychologist"
}
```

#### Login
```bash
POST /login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Returns:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "patient"
  }
}
```

### Protected Endpoints

#### Hello World (Example)
```bash
GET /hello
Authorization: Bearer <your_token>
```

## Testing with curl

### 1. Register a user
```bash
curl -X POST "http://127.0.0.1:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User",
    "role": "patient"
  }'
```

### 2. Login and save token
```bash
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}' \
  | jq -r '.access_token')
```

### 3. Access protected endpoint
```bash
curl -X GET "http://127.0.0.1:8000/hello" \
  -H "Authorization: Bearer $TOKEN"
```

## Project Structure

```
reqEng/
├── main.py           # FastAPI app and endpoints
├── config.py         # Settings configuration
├── requirements.txt  # Python dependencies
├── .env             # Environment variables (not in git)
├── .env.example     # Environment template
├── db/
│   └── db.py        # Database configuration
└── model/
    └── models.py    # SQLModel models
```

## Database Models

### User
- `id` (int, primary key)
- `email` (string, unique)
- `full_name` (string)
- `role` (string: "patient" or "psychologist")
- `hashed_password` (string)

## Security

- Passwords are hashed using Argon2
- JWT tokens expire after 30 minutes
- SECRET_KEY must be kept secure and never committed to git
- CORS is configured for localhost development

## Development

Run with auto-reload:
```bash
fastapi dev main.py
```

Access interactive API docs:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Troubleshooting

### Permission denied for schema public

Grant permissions to your PostgreSQL user:
```sql
GRANT ALL PRIVILEGES ON SCHEMA public TO psych_admin;
```

### Module not found

Ensure virtual environment is activated and dependencies installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## License

[Your License]

## Contributing

[Your contribution guidelines]