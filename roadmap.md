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

## Phase 5: Enhance Workflow Engines (**Completed**)

-   [x] **Implement `CrewAIEngine`:** Orchestrates linear workflows, validates config, resolves dependencies, and calls tools via `MCPClient`.
-   [x] **Implement `LangGraphEngine`:** Executes workflows as state machines/graphs, supports branching, and handles cycles and errors.
-   [x] **Integrate `MCPClient`:** Both engines use the dependency-injected `MCPClient` for tool execution.
-   [x] **Add Unit Tests:** Comprehensive unit and API integration tests for both engines, covering happy path, edge cases, and error branches.

**Additional Achievements:**
- Centralized logging is in place.
- API supports engine selection and validates config per engine.
- TDD practices are enforced, with all tests passing and high coverage.

**The workflow engine system is now robust, TDD-driven, and fully API-integrated.**

---

## Next Steps

The project is now ready to move forward to Phase 6.

### Phase 6: Expand Graph Database Functionality

-   [ ] **Implement Graph Algorithms:** Add methods to the `Neo4jClient` for common graph algorithms (e.g., pathfinding, community detection).
-   [ ] **Create Advanced Query Endpoints:** Expose the new graph algorithm capabilities through dedicated API endpoints.
-   [ ] **Improve Graph Visualization:** Plan for a simple front-end or a standard data format output (e.g., GraphML) that can be used with visualization tools.

### Phase 7: Finalize API and Improve Production-Readiness

-   [ ] **Address `TODO`s:** Search the codebase for any remaining `TODO` comments and address them.
-   [ ] **Increase Test Coverage:** Re-run coverage reports and add tests for any remaining logic gaps in the API and core clients.
-   [ ] **Implement Robust Logging:** Enhance logging throughout the application to provide clear insights into runtime behavior. (**Partially complete**)
-   [ ] **Standardize Error Handling:** Ensure all API endpoints return consistent and informative error responses. (**Partially complete**)
-   [ ] **Generate API Documentation:** Leverage FastAPI's automatic OpenAPI/Swagger documentation and add detailed descriptions for all endpoints and models.

### Phase 8: Deployment and CI/CD

-   [ ] **Create Production `docker-compose.yml`:** Build a compose file optimized for a production deployment.
-   [ ] **Set up CI/CD Pipeline:** Create a pipeline (e.g., using GitHub Actions) to automatically run tests, lint, and build Docker images on every push to `master`.
-   [ ] **Configure Secrets Management:** Implement a strategy for securely managing production secrets (e.g., API keys, database credentials).

### Phase 9: Add a Prototyping UI

-   [ ] **Choose a Library:** Select a suitable rapid-prototyping library like [Streamlit](https://streamlit.io/) or [Gradio](https://www.gradio.app/).
-   [ ] **Design the UI:** Create a simple interface that allows users to:
    -   Switch the active workflow engine.
    -   Define and execute a workflow.
    -   View the results from the workflow.
    -   Interact with the graph database (e.g., run simple queries, view stats).
-   [ ] **Integrate with API:** The UI should interact with our existing FastAPI backend to perform these actions.
-   [ ] **Containerize the UI:** Add the UI as a new service in `docker-compose.yml` so it can be run alongside the rest of the application stack. 