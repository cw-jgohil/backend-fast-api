#!/bin/bash

echo "🚀 FastAPI Backend Status"
echo "========================="

# Check if we're in the right directory
if [ ! -f "alembic.ini" ]; then
    echo "❌ Error: Please run this script from the backend-fast-api directory"
    exit 1
fi

echo ""
echo "📊 Database Status:"
if docker-compose ps | grep -q "Up"; then
    echo "✅ PostgreSQL: Running"
    echo "✅ pgAdmin: Running"
    echo "   - Database: localhost:5432"
    echo "   - pgAdmin: http://localhost:8080"
    echo "   - Login: admin@fastapi.com / admin123"
else
    echo "❌ Database containers not running"
    echo "   Run: ./scripts/start_db.sh"
fi

echo ""
echo "🔧 Environment:"
if [ -f ".env" ]; then
    if grep -q "USE_POSTGRES=true" .env; then
        echo "✅ Using PostgreSQL"
    else
        echo "✅ Using SQLite"
    fi
else
    echo "❌ No .env file found"
fi

echo ""
echo "🌐 FastAPI Server:"
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Server running on http://localhost:8000"
    echo "   - API Docs: http://localhost:8000/docs"
    echo "   - ReDoc: http://localhost:8000/redoc"
else
    echo "❌ Server not running"
    echo "   Run: uvicorn app.main:app --reload"
fi

echo ""
echo "📁 Quick Commands:"
echo "   Start DB:    ./scripts/start_db.sh"
echo "   Stop DB:     docker-compose down"
echo "   Setup DB:    ./scripts/setup_db.sh"
echo "   Start API:   uvicorn app.main:app --reload"
echo "   View Logs:   docker-compose logs -f" 