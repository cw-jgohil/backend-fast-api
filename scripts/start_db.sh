#!/bin/bash

# Start PostgreSQL database with Docker Compose
echo "Starting PostgreSQL database..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start the database services
docker-compose up -d postgres pgadmin

echo "Database services started!"
echo ""
echo "PostgreSQL is running on: localhost:5432"
echo "pgAdmin is available at: http://localhost:8080"
echo "  Email: admin@fastapi.com"
echo "  Password: admin123"
echo ""
echo "To stop the database, run: docker-compose down"
echo "To view logs, run: docker-compose logs -f" 