
FastAPI backend for a psychological counseling platform with JWT authentication

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
### Permission denied for schema public

Grant permissions to your PostgreSQL user:
```sql
GRANT ALL PRIVILEGES ON SCHEMA public TO psych_admin;
```

Ensure virtual environment is activated and dependencies installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```