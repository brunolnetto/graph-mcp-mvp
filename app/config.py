"""Configuration management for the Graph MCP MVP application."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Pydantic v2 config
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

    # Application
    app_env: str = Field(default="development")  # development, production, testing
    app_name: str = Field(default="Graph MCP MVP")
    project_name: str = Field(default="Graph MCP MVP")
    version: str = Field(default="0.1.0")
    description: str = Field(default="Minimal FastAPI application with MCP, Neo4j, and workflow engine swapping")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Database
    neo4j_uri: str = Field(default="bolt://localhost:7687")
    neo4j_user: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password")
    neo4j_database: str = Field(default="neo4j")

    # MCP
    mcp_server_url: str = Field(default="http://localhost:8001")
    mcp_api_key: str = Field(default="")
    mcp_timeout: int = Field(default=30)

    # Workflow Engine
    default_workflow_engine: Literal["crewai", "langgraph"] = Field(default="crewai")
    workflow_engine_timeout: int = Field(default=300)

    # CORS
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])
    cors_allow_credentials: bool = Field(default=True)

    # Security
    secret_key: str = Field(default="your-secret-key-here-change-in-production")
    access_token_expire_minutes: int = Field(default=30)

    # API
    api_v1_str: str = Field(default="/api/v1")

    # Docker
    docker_image_name: str = Field(default="graph-mcp-mvp")

# Global settings instance
settings = Settings()
