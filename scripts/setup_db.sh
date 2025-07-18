#!/bin/bash

# Setup database with migrations
echo "Setting up database..."

# Check if we're in the right directory
if [ ! -f "alembic.ini" ]; then
    echo "Error: Please run this script from the backend-fast-api directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Seed database with initial RBAC data
echo "Seeding database with initial data..."
python -c "from app.db import seed_rbac; seed_rbac()"

echo "Database setup complete!"
echo ""
echo "To start the FastAPI server, run: uvicorn app.main:app --reload" 