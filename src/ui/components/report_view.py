"""Report Studio and Multi-Format Export View."""
from __future__ import annotations

import json
from typing import Any, Dict


def render_report_view(st: Any, state: Dict[str, Any]) -> None:
    """Render the generated markdown report and export actions."""
    report_text = state.get("final_report", "")
    topic = state.get("topic", "Research Report")

    if not report_text:
        st.info("No report has been compiled yet. Start a research query above!")
        return

    st.subheader("📄 Executive Intelligence Deliverable")

    # Export Action Buttons
    action_cols = st.columns([1, 1, 2])
    with action_cols[0]:
        st.download_button(
            label="📥 Download Markdown",
            data=report_text,
            file_name=f"report_{topic[:30].replace(' ', '_').lower()}.md",
            mime="text/markdown",
        )

    with action_cols[1]:
        json_data = json.dumps(state, indent=2, ensure_ascii=False)
        st.download_button(
            label="📦 Export Full JSON",
            data=json_data,
            file_name=f"research_state_{topic[:30].replace(' ', '_').lower()}.json",
            mime="application/json",
        )

    # Render Report Content
    st.markdown("---")
    st.markdown(report_text)
