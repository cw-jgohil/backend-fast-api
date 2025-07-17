# FastAPI Backend Project

## Features
- Modular, professional architecture
- FastAPI with Pydantic, SQLAlchemy, Alembic
- Local SQLite database for development
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
```

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --reload
```

## Test
```bash
pytest
``` 