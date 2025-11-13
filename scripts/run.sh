#!/bin/bash

set -e

echo "Starting Neuroverse AI..."

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Running setup..."
    ./scripts/setup.sh
fi

# Activate venv
source venv/bin/activate

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Warning: Redis is not running"
    echo "Please start Redis: redis-server"
    exit 1
fi

# Start backend in background
echo "Starting backend..."
python -m backend.main &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Neuroverse AI is running!"
echo "Frontend: http://localhost:5173"
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM

wait

