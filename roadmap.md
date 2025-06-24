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

## Backlog / Technical Debt

- **Consolidate Workflow Schemas and Engine Abstraction:**
    [ ] Refactor the workflow system to use a single, canonical (engine-agnostic) workflow schema for all engines.
    [ ] Update the `WorkflowEngine` base class to require this schema as input/output.
    [ ] Refactor both `CrewAIEngine` and `LangGraphEngine` to translate from the canonical schema to their internal formats.
    [ ] Add/expand tests to ensure workflows run identically (parity) across all engines.
    [ ] This will simplify API logic, improve maintainability, and make it easier to add new engines in the future.

---

## Next Steps

The project is now focused on production readiness and polish for MVP compliance.

### Phase 6: Expand Graph Database Functionality (**In Progress**)

-   [x] **Implement Shortest Path Algorithm:** `/api/v1/graph/shortest-path` endpoint and client logic are complete and tested.
-   [ ] **(Optional) Implement Community Detection:** Can be added in a future phase if analytics are needed.
-   [ ] **(Optional) Improve Graph Visualization:** Plan for a simple front-end or a standard data format output (e.g., GraphML) for future visualization needs.

### Phase 7: Finalize API and Improve Production-Readiness (**Current Focus**)

-   [ ] **Address `TODO`s:**
        - [x] `app/api/routes/graph.py`: Implement real shortest path logic (already done)
        - [x] `app/engines/langgraph_engine.py`: Evaluate edge.condition if present (now implemented)
-   [ ] **Increase Test Coverage:** Re-run coverage reports and add tests for any remaining logic gaps in the API and core clients.
-   [ ] **Implement Robust Logging:** Enhance logging throughout the application to provide clear insights into runtime behavior. (**Partially complete**)
-   [ ] **Standardize Error Handling:** Ensure all API endpoints return consistent and informative error responses. (**Partially complete**)
-   [ ] **Generate API Documentation:** Leverage FastAPI's automatic OpenAPI/Swagger documentation and add detailed descriptions for all endpoints and models.

### Phase 8: Deployment and CI/CD

-   [ ] **Create Production `docker-compose.yml`:** Build a compose file optimized for a production deployment.
-   [ ] **Set up CI/CD Pipeline:** Create a pipeline (e.g., using GitHub Actions) to automatically run tests, lint, and build Docker images on every push to `master`.
-   [ ] **Configure Secrets Management:** Implement a strategy for securely managing production secrets (e.g., API keys, database credentials).

### Phase 9: Add a Prototyping UI (Optional)

-   [ ] **Choose a Library:** Select a suitable rapid-prototyping library like [Streamlit](https://streamlit.io/) or [Gradio](https://www.gradio.app/).
-   [ ] **Design the UI:** Create a simple interface that allows users to:
    -   Switch the active workflow engine.
    -   Define and execute a workflow.
    -   View the results from the workflow.
    -   Interact with the graph database (e.g., run simple queries, view stats).
-   [ ] **Integrate with API:** The UI should interact with our existing FastAPI backend to perform these actions.
-   [ ] **Containerize the UI:** Add the UI as a new service in `docker-compose.yml` so it can be run alongside the rest of the application stack.

---

**Note:**
- Advanced graph analytics and visualization are now considered optional/future work.
- The current focus is on production readiness, polish, and MVP compliance.
- TODOs are being actively tracked and addressed. 
