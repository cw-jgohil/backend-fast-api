# Database Management Guide

This guide covers different ways to run and manage your database for the FastAPI backend.

## Option 1: PostgreSQL with Docker (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- Ports 5432 and 8080 available

### Quick Start

1. **Start the database:**
   ```bash
   cd backend-fast-api
   ./scripts/start_db.sh
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env and set USE_POSTGRES=true
   ```

3. **Setup database:**
   ```bash
   ./scripts/setup_db.sh
   ```

4. **Start FastAPI server:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Access Points
- **PostgreSQL Database:** `localhost:5432`
- **pgAdmin (Web Interface):** `http://localhost:8080`
  - Email: `admin@fastapi.com`
  - Password: `admin123`

### Useful Commands
```bash
# View database logs
docker-compose logs -f postgres

# Stop database
docker-compose down

# Restart database
docker-compose restart

# Reset database (WARNING: This deletes all data)
docker-compose down -v
docker-compose up -d
```

## Option 2: SQLite (Default)

### Quick Start
```bash
cd backend-fast-api
./scripts/setup_db.sh
uvicorn app.main:app --reload
```

### Database File
- Location: `backend-fast-api/app.db`
- No additional setup required
- Good for development and small applications

## Option 3: External PostgreSQL

### Setup
1. Install PostgreSQL on your system
2. Create a database and user
3. Set environment variables:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
   ```
4. Run setup script:
   ```bash
   ./scripts/setup_db.sh
   ```

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_POSTGRES` | `false` | Set to `true` to use PostgreSQL |
| `DATABASE_URL` | `sqlite:///./app.db` | Direct database URL override |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `fastapi_db` | PostgreSQL database name |
| `POSTGRES_USER` | `fastapi_user` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `fastapi_password` | PostgreSQL password |

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using the port
   lsof -i :5432
   # Kill the process or change ports in docker-compose.yml
   ```

2. **Database connection failed:**
   - Check if Docker containers are running: `docker-compose ps`
   - Check logs: `docker-compose logs postgres`
   - Verify environment variables in `.env`

3. **Migration errors:**
   ```bash
   # Reset migrations (WARNING: Deletes all data)
   rm -rf alembic/versions/*
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

### Performance Tips

1. **For Development:**
   - Use SQLite for faster startup
   - Use PostgreSQL for production-like testing

2. **For Production:**
   - Always use PostgreSQL
   - Configure connection pooling
   - Set up proper backups

## Database Extensions

### VS Code Extensions
- **PostgreSQL** by Microsoft
- **SQLite** by qwtel
- **Database Client** by cweijan

### GUI Tools
- **pgAdmin** (included with Docker setup)
- **DBeaver** (free, supports multiple databases)
- **TablePlus** (paid, excellent UI)
- **Sequel Pro** (free, macOS only) 