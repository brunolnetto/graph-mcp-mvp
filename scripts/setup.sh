#!/bin/bash

# Graph MCP MVP Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up Graph MCP MVP development environment..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
fi

# Check if just is installed
if ! command -v just &> /dev/null; then
    echo "📦 Installing just..."
    if command -v cargo &> /dev/null; then
        cargo install just
    else
        echo "⚠️  Please install just manually: https://just.systems/man/en/"
        echo "   Or run: cargo install just"
    fi
fi

# Install dependencies
echo "📚 Installing Python dependencies..."
uv sync --dev

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file from template..."
    cp env.example .env
    echo "✅ Please edit .env with your configuration"
fi

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "  1. Edit .env with your configuration"
echo "  2. Run 'just dev' to start development"
echo "  3. Run 'just up' to start all services"
echo "  4. Visit http://localhost:8000/docs for API documentation" 