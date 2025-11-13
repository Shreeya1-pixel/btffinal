#!/bin/bash

set -e

echo "Setting up Neuroverse AI..."

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher is required"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY not set in environment"
    echo "Please set it in your .env file"
fi

# Setup frontend
echo "Setting up frontend..."
cd frontend
npm install
cd ..

echo ""
echo "Setup complete!"
echo ""
echo "To start the application:"
echo "  1. Start Redis: redis-server"
echo "  2. Start Backend: source venv/bin/activate && python -m backend.main"
echo "  3. Start Frontend: cd frontend && npm run dev"
echo ""
echo "Or use Docker: docker-compose up --build"

