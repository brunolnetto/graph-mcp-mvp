# Project Roadmap

This document outlines the future development direction for the Graph-MCP-MVP project.

---

## Current Status (Completed)

We have successfully built a robust foundation for the application, divided into four key phases:

-   **Phase 1: Project Scaffolding and Foundation:** Established the project structure, Docker environment, dependency management with `uv`, and core application skeleton.
-   **Phase 2: Testing and Iterative Debugging:** Implemented a comprehensive test suite with `pytest` and resolved initial build, dependency, and mocking issues.
-   **Phase 3: Implementing Real Components and Refactoring:** Replaced mock components with real `Neo4jClient` and `MCPClient` implementations and refactored the API to be modular and dependency-injected.
-   **Phase 4: The Final Testing Push:** Completed a final, intensive testing cycle to ensure the entire refactored application is stable, reliable, and warning-free.

The application now has a fully passing test suite with good coverage, a swappable workflow engine architecture, and real clients for interacting with Neo4j and MCP servers.

---

## Next Steps

With the foundation secure, we can now focus on building out the core business logic and features.

### Phase 5: Enhance Workflow Engines

The current workflow engines are minimal stubs. The next critical step is to implement their core logic.

-   [ ] **Implement `CrewAIEngine`:** Develop the logic to define and run a Crew AI workflow using the provided configuration.
-   [ ] **Implement `LangGraphEngine`:** Build the state machine and graph logic required to execute a LangGraph workflow.
-   [ ] **Integrate `MCPClient`:** Both engines should use the dependency-injected `MCPClient` to discover and call external tools during a workflow run.
-   [ ] **Add Unit Tests:** Create dedicated tests for each engine's logic.

### Phase 6: Expand Graph Database Functionality

The `Neo4jClient` is functional but can be extended to support more complex graph operations.

-   [ ] **Implement Graph Algorithms:** Add methods to the `Neo4jClient` for common graph algorithms (e.g., pathfinding, community detection).
-   [ ] **Create Advanced Query Endpoints:** Expose the new graph algorithm capabilities through dedicated API endpoints.
-   [ ] **Improve Graph Visualization:** Plan for a simple front-end or a standard data format output (e.g., GraphML) that can be used with visualization tools.

### Phase 7: Finalize API and Improve Production-Readiness

This phase focuses on polishing the application to make it ready for real-world use.

-   [ ] **Address `TODO`s:** Search the codebase for any remaining `TODO` comments and address them.
-   [ ] **Increase Test Coverage:** Re-run coverage reports and add tests for any remaining logic gaps in the API and core clients.
-   [ ] **Implement Robust Logging:** Enhance logging throughout the application to provide clear insights into runtime behavior.
-   [ ] **Standardize Error Handling:** Ensure all API endpoints return consistent and informative error responses.
-   [ ] **Generate API Documentation:** Leverage FastAPI's automatic OpenAPI/Swagger documentation and add detailed descriptions for all endpoints and models.

### Phase 8: Deployment and CI/CD

The final step is to automate the deployment process.

-   [ ] **Create Production `docker-compose.yml`:** Build a compose file optimized for a production deployment.
-   [ ] **Set up CI/CD Pipeline:** Create a pipeline (e.g., using GitHub Actions) to automatically run tests, lint, and build Docker images on every push to `master`.
-   [ ] **Configure Secrets Management:** Implement a strategy for securely managing production secrets (e.g., API keys, database credentials). 