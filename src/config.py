"""Application configuration management for Autonomous Recursive Research Engine."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field

    class Settings(BaseSettings):
        """Global system settings loaded from environment or .env file."""
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        # LLM Provider Configuration
        llm_provider: str = Field(default="openai", description="LLM provider: openai, gemini, groq, or ollama")
        llm_model: str = Field(default="gpt-4o-mini", description="Target model name")
        llm_temperature: float = Field(default=0.2, description="Sampling temperature for deterministic outputs")

        # API Keys
        openai_api_key: Optional[str] = Field(default=None)
        gemini_api_key: Optional[str] = Field(default=None)
        groq_api_key: Optional[str] = Field(default=None)

        # Local Ollama Config
        ollama_base_url: str = Field(default="http://localhost:11434")

        # Search Configuration
        search_provider: str = Field(default="duckduckgo", description="Search provider: duckduckgo or tavily")
        tavily_api_key: Optional[str] = Field(default=None)
        max_search_results_per_query: int = Field(default=5)

        # Recursive Execution Controls
        max_recursion_depth: int = Field(default=3, description="Maximum recursive loop iterations")
        max_sub_questions: int = Field(default=4, description="Max sub-questions generated per planning cycle")
        verification_threshold: float = Field(default=0.75, description="Confidence score threshold to accept claims")

        # Context Optimization
        enable_context_pruning: bool = Field(default=True, description="Enable dynamic token pruning")
        max_snippet_length_chars: int = Field(default=1200)

        # System Paths
        output_dir: Path = Field(default=Path("outputs"))
        log_level: str = Field(default="INFO")

except ImportError:  # Fallback lightweight settings class if pydantic-settings is not yet installed
    class Settings:  # type: ignore[no-redef]
        """Lightweight fallback configuration when pydantic-settings is not installed."""
        def __init__(self) -> None:
            self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
            self.llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
            self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            self.groq_api_key = os.getenv("GROQ_API_KEY")
            self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.search_provider = os.getenv("SEARCH_PROVIDER", "duckduckgo").lower()
            self.tavily_api_key = os.getenv("TAVILY_API_KEY")
            self.max_search_results_per_query = int(os.getenv("MAX_SEARCH_RESULTS_PER_QUERY", "5"))
            self.max_recursion_depth = int(os.getenv("MAX_RECURSION_DEPTH", "3"))
            self.max_sub_questions = int(os.getenv("MAX_SUB_QUESTIONS", "4"))
            self.verification_threshold = float(os.getenv("VERIFICATION_THRESHOLD", "0.75"))
            self.enable_context_pruning = os.getenv("ENABLE_CONTEXT_PRUNING", "true").lower() in ("true", "1", "yes")
            self.max_snippet_length_chars = int(os.getenv("MAX_SNIPPET_LENGTH_CHARS", "1200"))
            self.output_dir = Path(os.getenv("OUTPUT_DIR", "outputs"))
            self.log_level = os.getenv("LOG_LEVEL", "INFO")


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Retrieve or initialize singleton application settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.output_dir.mkdir(parents=True, exist_ok=True)
    return _settings
