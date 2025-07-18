# FastAPI Backend Project

## Features
- Modular, professional architecture
- FastAPI with Pydantic, SQLAlchemy, Alembic
- Support for both SQLite and PostgreSQL databases
- User CRUD example
- Ready for production extension

## Folder Structure
```
app/
  api/        # API routers
  core/       # Core settings/config
  db/         # Database session/logic
  models/     # SQLAlchemy models
  schemas/    # Pydantic schemas
  services/   # Business logic
  tests/      # Pytest tests
  main.py     # App entry point
scripts/      # Database and setup scripts
```

## Quick Start

### Option 1: SQLite (Default)
```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./scripts/setup_db.sh

# Run
uvicorn app.main:app --reload
```

### Option 2: PostgreSQL with Docker (Recommended)
```bash
# Start database
./scripts/start_db.sh

# Configure environment
cp env.example .env
# Edit .env and set USE_POSTGRES=true

# Setup and run
./scripts/setup_db.sh
uvicorn app.main:app --reload
```

## Database Management

For detailed database setup and management instructions, see [DATABASE.md](./DATABASE.md).

### Quick Database Commands
```bash
# Start PostgreSQL with pgAdmin
./scripts/start_db.sh

# Setup database with migrations
./scripts/setup_db.sh

# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Test
```bash
pytest
```

## API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 