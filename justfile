# Justfile - Main orchestrator for Graph MCP MVP
# Usage: just <command> [args...]

# Default recipe to show available commands
default:
    @just --list

# Development setup and installation
setup:
    #!/usr/bin/env bash
    echo "🚀 Setting up Graph MCP MVP development environment..."
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        echo "📦 Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source ~/.bashrc
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
    
    echo "✅ Setup complete! Run 'just dev' to start development"

# Start development server
dev:
    #!/usr/bin/env bash
    echo "🔥 Starting development server..."
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start only Neo4j database
db:
    #!/usr/bin/env bash
    echo "🗄️  Starting Neo4j database..."
    docker-compose up -d neo4j
    echo "✅ Neo4j running at http://localhost:7474"
    echo "🔗 Bolt connection: bolt://localhost:7687"

# Start all services (app + database)
up:
    #!/usr/bin/env bash
    echo "🚀 Starting all services..."
    docker-compose up -d
    echo "✅ Services started!"
    echo "🌐 App: http://localhost:8000"
    echo "🗄️  Neo4j: http://localhost:7474"

# Stop all services
down:
    #!/usr/bin/env bash
    echo "🛑 Stopping all services..."
    docker-compose down
    echo "✅ Services stopped"

# Reset database (stop, remove volumes, start)
reset-db:
    #!/usr/bin/env bash
    echo "🔄 Resetting database..."
    docker-compose down -v
    docker-compose up -d neo4j
    echo "✅ Database reset complete"

# Code quality checks
check:
    #!/usr/bin/env bash
    echo "🔍 Running code quality checks..."
    uv run ruff check .
    uv run ruff format --check .
    echo "✅ Code quality checks passed"

# Format code
fmt:
    #!/usr/bin/env bash
    echo "🎨 Formatting code..."
    uv run ruff format .
    echo "✅ Code formatted"

# Lint code
lint:
    #!/usr/bin/env bash
    echo "🔍 Linting code..."
    uv run ruff check --fix .
    echo "✅ Linting complete"

# Type checking
types:
    #!/usr/bin/env bash
    echo "🔍 Running type checks..."
    uv run mypy app/
    echo "✅ Type checking complete"

# Run tests
test:
    #!/usr/bin/env bash
    echo "🧪 Running tests..."
    uv run pytest

# Run tests with coverage
test-cov:
    #!/usr/bin/env bash
    echo "🧪 Running tests with coverage..."
    uv run pytest --cov=app --cov-report=term-missing --cov-report=html

# Run specific test file
test-file file:
    #!/usr/bin/env bash
    echo "🧪 Running tests in {{file}}..."
    uv run pytest {{file}}

# Build Docker image
build:
    #!/usr/bin/env bash
    echo "🐳 Building Docker image..."
    docker-compose build

# Build and start in production mode
prod:
    #!/usr/bin/env bash
    echo "🚀 Building and starting production services..."
    docker-compose -f docker-compose.yml up -d --build
    echo "✅ Production services started"

# Clean up Docker resources
clean:
    #!/usr/bin/env bash
    echo "🧹 Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    echo "✅ Cleanup complete"

# Show logs
logs service="app":
    #!/usr/bin/env bash
    echo "📋 Showing logs for {{service}}..."
    docker-compose logs -f {{service}}

# Access Neo4j browser
neo4j-browser:
    #!/usr/bin/env bash
    echo "🌐 Opening Neo4j browser..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:7474
    elif command -v open &> /dev/null; then
        open http://localhost:7474
    else
        echo "🔗 Neo4j browser: http://localhost:7474"
    fi

# Access API documentation
docs:
    #!/usr/bin/env bash
    echo "📚 Opening API documentation..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8000/docs
    elif command -v open &> /dev/null; then
        open http://localhost:8000/docs
    else
        echo "🔗 API docs: http://localhost:8000/docs"
    fi

# Health check
health:
    #!/usr/bin/env bash
    echo "🏥 Checking service health..."
    echo "App health:"
    curl -s http://localhost:8000/health | jq . || echo "App not responding"
    echo "Neo4j health:"
    docker-compose exec neo4j cypher-shell -u neo4j -p password "RETURN 1" || echo "Neo4j not responding"

# Demo workflow execution
demo:
    #!/usr/bin/env bash
    echo "🎭 Running demo workflow..."
    curl -X POST http://localhost:8000/api/v1/workflow/demo \
        -H "Content-Type: application/json" | jq .

# Switch workflow engine
switch-engine engine:
    #!/usr/bin/env bash
    echo "🔄 Switching to {{engine}} engine..."
    curl -X PUT http://localhost:8000/api/v1/workflow/engine \
        -H "Content-Type: application/json" \
        -d "{\"engine\": \"{{engine}}\"}" | jq .

# Create a sample node
create-node:
    #!/usr/bin/env bash
    echo "📝 Creating sample node..."
    curl -X POST http://localhost:8000/api/v1/graph/nodes \
        -H "Content-Type: application/json" \
        -d '{"labels": ["Person"], "properties": {"name": "John Doe", "age": 30}}' | jq .

# Get graph statistics
graph-stats:
    #!/usr/bin/env bash
    echo "📊 Getting graph statistics..."
    curl -s http://localhost:8000/api/v1/graph/stats | jq .

# Full development workflow
dev-workflow:
    #!/usr/bin/env bash
    echo "🔄 Running full development workflow..."
    just check
    just test
    just up
    echo "✅ Development workflow complete!"
    echo "🌐 App: http://localhost:8000"
    echo "📚 Docs: http://localhost:8000/docs"

# Show project status
status:
    #!/usr/bin/env bash
    echo "📊 Project Status:"
    echo "=================="
    echo "Python version: $(python --version)"
    echo "uv version: $(uv --version)"
    echo "Docker containers:"
    docker-compose ps
    echo ""
    echo "Available endpoints:"
    echo "  App: http://localhost:8000"
    echo "  Docs: http://localhost:8000/docs"
    echo "  Health: http://localhost:8000/health"
    echo "  Neo4j: http://localhost:7474" 