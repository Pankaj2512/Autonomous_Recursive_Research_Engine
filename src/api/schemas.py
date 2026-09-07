"""REST API schemas for research requests and responses."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel, Field

    class ResearchRequest(BaseModel):
        """Input payload to start a research job."""
        topic: str = Field(..., description="Target query or research topic.", example="Recursive Language Models in Multi-Agent AI")
        max_depth: Optional[int] = Field(default=None, description="Max recursion depth limit.")
        provider: Optional[str] = Field(default=None, description="Override LLM provider (openai, gemini, groq, ollama).")
        async_execution: bool = Field(default=False, description="Run in background asynchronously.")

    class TaskStatusResponse(BaseModel):
        """Job status and progress telemetry."""
        task_id: str
        status: str  # queued, in_progress, completed, failed
        topic: str
        recursion_depth: int
        nodes_executed: int
        trace_logs: List[Dict[str, Any]]
        created_at: float
        completed_at: Optional[float] = None
        error: Optional[str] = None

    class ReportResponse(BaseModel):
        """Completed research report payload."""
        task_id: str
        topic: str
        final_report: str
        verification_summary: Dict[str, Any]
        sources_count: int

except ImportError:
    from dataclasses import dataclass, field

    @dataclass
    class ResearchRequest:  # type: ignore[no-redef]
        topic: str
        max_depth: Optional[int] = None
        provider: Optional[str] = None
        async_execution: bool = False

    @dataclass
    class TaskStatusResponse:  # type: ignore[no-redef]
        task_id: str
        status: str
        topic: str
        recursion_depth: int
        nodes_executed: int
        trace_logs: List[Dict[str, Any]]
        created_at: float
        completed_at: Optional[float] = None
        error: Optional[str] = None

    @dataclass
    class ReportResponse:  # type: ignore[no-redef]
        task_id: str
        topic: str
        final_report: str
        verification_summary: Dict[str, Any]
        sources_count: int
