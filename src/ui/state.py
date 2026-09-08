"""Session state management for the Streamlit research dashboard."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def init_session_state(st_module: Any) -> None:
    """Initialize default state keys in Streamlit session_state."""
    defaults: Dict[str, Any] = {
        "research_state": None,
        "is_running": False,
        "current_stage": "idle",
        "execution_logs": [],
        "research_history": [],
        "selected_sub_question": None,
        "active_tab": "Overview",
    }
    for key, val in defaults.items():
        if key not in st_module.session_state:
            st_module.session_state[key] = val


def reset_research_state(st_module: Any) -> None:
    """Clear active session state for a fresh research execution."""
    st_module.session_state["research_state"] = None
    st_module.session_state["is_running"] = True
    st_module.session_state["current_stage"] = "initiating"
    st_module.session_state["execution_logs"] = []


def record_completed_run(st_module: Any, topic: str, final_state: Dict[str, Any]) -> None:
    """Append completed research run to session history."""
    st_module.session_state["research_state"] = final_state
    st_module.session_state["is_running"] = False
    st_module.session_state["current_stage"] = "completed"

    entry = {
        "topic": topic,
        "depth": final_state.get("recursion_depth", 0),
        "sources_count": len(final_state.get("sources", [])),
        "sub_questions_count": len(final_state.get("sub_questions", [])),
        "final_report": final_state.get("final_report", ""),
        "timestamp": final_state.get("trace_logs", [{}])[-1].get("timestamp", 0) if final_state.get("trace_logs") else 0,
    }
    st_module.session_state["research_history"].append(entry)
