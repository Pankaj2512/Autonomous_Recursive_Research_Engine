"""Live agent execution handler and telemetry tracker for Streamlit."""
from __future__ import annotations

import time
from typing import Any, Dict

from src.graph.workflow import run_research_workflow
from src.ui.state import record_completed_run, reset_research_state


def execute_ui_research(st: Any, topic: str, max_depth: int) -> Dict[str, Any]:
    """Execute research workflow with live progress updates and metrics."""
    reset_research_state(st)

    progress_container = st.container()
    with progress_container:
        status_box = st.empty()
        progress_bar = st.progress(0.1)
        telemetry_cols = st.columns(4)

        metric_stage = telemetry_cols[0].empty()
        metric_depth = telemetry_cols[1].empty()
        metric_questions = telemetry_cols[2].empty()
        metric_time = telemetry_cols[3].empty()

        metric_stage.metric("Stage", "Planning")
        metric_depth.metric("Depth", "0 / " + str(max_depth))
        metric_questions.metric("Sub-Inquiries", "0")
        metric_time.metric("Time Elapsed", "0.0s")

    start_time = time.time()

    status_box.info(f"🧠 Prime Supervisor is decomposing topic: **'{topic}'**...")
    progress_bar.progress(0.25)

    try:
        # Run graph workflow
        final_state = run_research_workflow(topic=topic, max_depth=max_depth)

        elapsed = time.time() - start_time
        progress_bar.progress(1.0)
        status_box.success(f"✅ Research completed in **{elapsed:.2f}s**!")

        # Update telemetry
        depth = final_state.get("recursion_depth", 0)
        sq_count = len(final_state.get("sub_questions", []))
        src_count = len(final_state.get("sources", []))

        metric_stage.metric("Stage", "Completed")
        metric_depth.metric("Depth", f"{depth} / {max_depth}")
        metric_questions.metric("Sub-Inquiries", str(sq_count))
        metric_time.metric("Time Elapsed", f"{elapsed:.1f}s")

        record_completed_run(st, topic, final_state)
        return final_state

    except Exception as exc:
        progress_bar.progress(1.0)
        status_box.error(f"❌ Research failed: {str(exc)}")
        st.session_state["is_running"] = False
        st.session_state["current_stage"] = "failed"
        return {"error": str(exc)}
