"""Streamlit Web Dashboard for Autonomous Recursive Research Engine."""
from __future__ import annotations

import sys
from typing import Any

try:
    import streamlit as st
except ImportError:
    print("Streamlit is not installed. Install with: pip install streamlit")
    sys.exit(1)

from src.ui.components.audit_panel import render_audit_panel
from src.ui.components.report_view import render_report_view
from src.ui.components.runner import execute_ui_research
from src.ui.components.sidebar import render_sidebar
from src.ui.components.tree_view import render_tree_view
from src.ui.state import init_session_state


def main() -> None:
    """Main dashboard application layout."""
    st.set_page_config(
        page_title="Recursive Research Engine",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state(st)

    # Render Sidebar Controls
    config = render_sidebar(st)

    # Main Header
    st.title("🧠 Autonomous Recursive Research Engine")
    st.caption("Prime Agent RLM Architecture • Model Context Protocol • Self-Verification Loop")

    # Research Input Bar
    with st.container():
        query_cols = st.columns([5, 1])
        with query_cols[0]:
            topic_input = st.text_input(
                "Research Inquiry",
                placeholder="e.g. Model Context Protocol in Multi-Agent Architecture, State of Quantum Machine Learning...",
                label_visibility="collapsed",
            )
        with query_cols[1]:
            start_btn = st.button("🚀 Investigate", type="primary", use_container_width=True)

    # Handle Trigger
    if start_btn:
        if not topic_input.strip():
            st.warning("Please enter a research topic first.")
        else:
            execute_ui_research(st, topic=topic_input.strip(), max_depth=config["max_depth"])

    # Active State Content Display
    state = st.session_state.get("research_state")
    if state:
        st.markdown("---")
        tabs = st.tabs([
            "📄 Executive Report",
            "🌳 Recursive Tree & Graph",
            "🛡️ Verification Audit",
            "📜 Execution Logs",
        ])

        with tabs[0]:
            render_report_view(st, state)

        with tabs[1]:
            render_tree_view(st, state)

        with tabs[2]:
            render_audit_panel(st, state)

        with tabs[3]:
            st.subheader("📜 Node Execution Telemetry")
            trace_logs = state.get("trace_logs", [])
            for log in trace_logs:
                node = str(log.get("node", "")).upper()
                msg = log.get("message", "")
                st.markdown(f"- **`[{node}]`** {msg}")

    # Prior Session History
    history = st.session_state.get("research_history", [])
    if len(history) > 1:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🕒 Previous Inquiries")
        for h in history[:-1]:
            st.sidebar.caption(f"• {h.get('topic')[:30]}...")


if __name__ == "__main__":
    main()
