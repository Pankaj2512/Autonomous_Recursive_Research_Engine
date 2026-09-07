"""FastAPI application for Autonomous Recursive Research Engine."""
from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from typing import Any, Dict, Optional

from src.config import get_settings
from src.graph.workflow import run_research_workflow
from src.mcp.server import get_mcp_server

logger = logging.getLogger(__name__)

# In-memory task storage for demo/POC
_TASKS: Dict[str, Dict[str, Any]] = {}

try:
    from fastapi import BackgroundTasks, FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import PlainTextResponse

    from src.api.schemas import ReportResponse, ResearchRequest, TaskStatusResponse

    app = FastAPI(
        title="Autonomous Recursive Research Engine (Prime Agent RLM) API",
        version="0.1.0",
        description="REST API for autonomous recursive research orchestration with LangGraph and MCP.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _execute_background_research(task_id: str, topic: str, max_depth: Optional[int], provider: Optional[str]) -> None:
        """Worker thread executing the research graph."""
        if provider:
            os.environ["LLM_PROVIDER"] = provider

        try:
            _TASKS[task_id]["status"] = "in_progress"
            final_state = run_research_workflow(topic=topic, max_depth=max_depth)
            _TASKS[task_id]["status"] = "completed"
            _TASKS[task_id]["completed_at"] = time.time()
            _TASKS[task_id]["final_state"] = final_state
        except Exception as exc:
            logger.exception(f"Background research task {task_id} failed: {exc}")
            _TASKS[task_id]["status"] = "failed"
            _TASKS[task_id]["completed_at"] = time.time()
            _TASKS[task_id]["error"] = str(exc)

    @app.get("/health")
    def health_check() -> Dict[str, str]:
        """Health and liveness probe."""
        return {"status": "ok", "service": "Autonomous Recursive Research Engine"}

    @app.get("/api/v1/mcp/tools")
    def list_mcp_tools() -> Dict[str, Any]:
        """List all Model Context Protocol (MCP) tools registered with the engine."""
        server = get_mcp_server()
        return {"server": server.server_name, "tools": server.list_tools()}

    @app.post("/api/v1/research", response_model=TaskStatusResponse)
    def start_research(request: ResearchRequest, background_tasks: BackgroundTasks) -> TaskStatusResponse:
        """Trigger an autonomous recursive research session."""
        task_id = str(uuid.uuid4())[:8]
        _TASKS[task_id] = {
            "task_id": task_id,
            "topic": request.topic,
            "status": "queued",
            "created_at": time.time(),
            "completed_at": None,
            "error": None,
            "final_state": {},
        }

        if request.async_execution:
            background_tasks.add_task(
                _execute_background_research,
                task_id,
                request.topic,
                request.max_depth,
                request.provider,
            )
            return TaskStatusResponse(
                task_id=task_id,
                status="queued",
                topic=request.topic,
                recursion_depth=0,
                nodes_executed=0,
                trace_logs=[],
                created_at=_TASKS[task_id]["created_at"],
            )
        else:
            # Synchronous execution
            _execute_background_research(task_id, request.topic, request.max_depth, request.provider)
            state = _TASKS[task_id].get("final_state", {})
            return TaskStatusResponse(
                task_id=task_id,
                status=_TASKS[task_id]["status"],
                topic=request.topic,
                recursion_depth=state.get("recursion_depth", 0),
                nodes_executed=len(state.get("trace_logs", [])),
                trace_logs=state.get("trace_logs", []),
                created_at=_TASKS[task_id]["created_at"],
                completed_at=_TASKS[task_id]["completed_at"],
                error=_TASKS[task_id].get("error"),
            )

    @app.get("/api/v1/research/{task_id}", response_model=TaskStatusResponse)
    def get_research_status(task_id: str) -> TaskStatusResponse:
        """Poll the status and trace history of an ongoing or completed research task."""
        if task_id not in _TASKS:
            raise HTTPException(status_code=404, detail="Research task not found.")

        task = _TASKS[task_id]
        state = task.get("final_state", {})
        return TaskStatusResponse(
            task_id=task_id,
            status=task["status"],
            topic=task["topic"],
            recursion_depth=state.get("recursion_depth", 0),
            nodes_executed=len(state.get("trace_logs", [])),
            trace_logs=state.get("trace_logs", []),
            created_at=task["created_at"],
            completed_at=task.get("completed_at"),
            error=task.get("error"),
        )

    @app.get("/api/v1/research/{task_id}/report")
    def get_research_report(task_id: str, format: str = "json") -> Any:
        """Retrieve the final synthesized markdown intelligence report."""
        if task_id not in _TASKS:
            raise HTTPException(status_code=404, detail="Research task not found.")

        task = _TASKS[task_id]
        if task["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Task is currently '{task['status']}', not completed yet.")

        state = task.get("final_state", {})
        report_text = state.get("final_report", "No report available.")

        if format.lower() == "markdown":
            return PlainTextResponse(report_text, media_type="text/markdown")

        history = state.get("verification_history", [])
        return ReportResponse(
            task_id=task_id,
            topic=task["topic"],
            final_report=report_text,
            verification_summary=history[-1] if history else {},
            sources_count=len(state.get("sources", [])),
        )

except ImportError:
    class MockApp:  # type: ignore[no-redef]
        """Fallback mock app if FastAPI is not installed in the environment."""
        pass

    app = MockApp()  # type: ignore[assignment]
