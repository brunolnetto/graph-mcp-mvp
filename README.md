# Graph MCP MVP

This project is a FastAPI application that serves as a proof-of-concept for a system that integrates a graph database ([Neo4j](https://neo4j.com/)) and a swappable workflow engine architecture ([CrewAI](https://www.crewai.com/) / [LangGraph](https://langchain-ai.github.io/langgraph/)), all accessible via a unified API. The system is designed to interact with external AI models and tools through the Model Context Protocol (MCP).

## Key Features

-   **Modular Architecture**: A clean separation of concerns between the API, core clients, and workflow engines.
-   **Swappable Engines**: The ability to switch between different workflow engines (`CrewAI`, `LangGraph`) at runtime.
-   **Graph Database Integration**: Uses Neo4j to store and query complex, interconnected data.
-   **MCP Client**: Interacts with an MCP-compliant server to leverage external AI tools and models.
-   **Dockerized Environment**: Fully containerized using Docker and `docker-compose` for consistent development and deployment.
-   **Modern Tooling**: Utilizes `uv` for fast package management, `ruff` for linting and formatting, and `just` as a command runner.

---

## Getting Started

### Prerequisites

-   [Docker](https://www.docker.com/products/docker-desktop/) and `docker-compose`
-   [just](https://just.systems/man/en/chapter_4.html), a command runner.

### Setup

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd graph-mcp-mvp
    ```

2.  **Configure Environment**
    Create a `.env` file from the example template.
    ```bash
    cp env.example .env
    ```
    You can modify the default values in `.env` if needed, but the defaults are configured to work with the provided `docker-compose.yml`.

3.  **Run the Setup Command**
    This command will build the Docker containers, install all dependencies using `uv`, and start the services (`api`, `neo4j`).
    ```bash
    just setup
    ```

The API will be available at [http://localhost:8000](http://localhost:8000).

---

## Development

The `justfile` provides convenient commands for common development tasks.

-   **Start Services**:
    ```bash
    # Start all services in the background
    just up
    ```
-   **Stop Services**:
    ```bash
    # Stop and remove all services
    just down
    ```
-   **View Logs**:
    ```bash
    # Follow logs for the API service
    just logs
    ```
-   **Run Tests**:
    ```bash
    # Run the full test suite
    just test

    # Run tests with coverage report
    just test-cov
    ```
-   **Code Quality**:
    ```bash
    # Lint all files
    just lint

    # Format all files
    just format
    ```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to enforce code style and quality on every commit. Hooks include:
- ruff (linting)
- black (formatting)
- isort (import sorting)
- end-of-file-fixer

To set up pre-commit:

```bash
pip install pre-commit
pre-commit install
```

This will automatically run the hooks on staged files at every commit.

### API Documentation

Once the application is running, you can access the interactive API documentation:

-   **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
-   **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Neo4j Database

-   **Neo4j Browser**: Access the browser UI at [http://localhost:7474](http://localhost:7474).
-   **Credentials**: Use the credentials specified in your `.env` file (default: `neo4j`/`password`).

---

## Project Roadmap

For a detailed overview of the project's current status and future development plans, please see the [Roadmap.md](Roadmap.md) file.
