"""Configuration management for the Graph MCP MVP application."""

from typing import List, Literal
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Use ConfigDict instead of class-based config
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    # Application
    app_name: str = "Graph MCP MVP"
    version: str = "0.1.0"
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
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])
    cors_allow_credentials: bool = Field(default=True)
    
    # API
    api_v1_str: str = Field(default="/api/v1")


# Global settings instance
settings = Settings() 