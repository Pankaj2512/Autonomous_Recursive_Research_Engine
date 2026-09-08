"""Sidebar configuration panel for the Streamlit dashboard."""
from __future__ import annotations

import os
from typing import Any, Dict

from src.config import get_settings


def render_sidebar(st: Any) -> Dict[str, Any]:
    """Render the configuration controls in the sidebar and return active settings."""
    settings = get_settings()

    st.sidebar.title("⚙️ Engine Controls")
    st.sidebar.caption("Recursive Language Model (RLM) Parameters")

    # LLM Settings
    st.sidebar.subheader("LLM Provider")
    providers = ["openai", "gemini", "groq", "ollama", "mock"]
    default_idx = providers.index(settings.llm_provider) if settings.llm_provider in providers else 0
    selected_provider = st.sidebar.selectbox("Provider", providers, index=default_idx)

    model_name = st.sidebar.text_input(
        "Model Name",
        value=settings.llm_model,
        help="Target model identifier (e.g. gpt-4o-mini, gemini-1.5-pro, llama3:8b)",
    )

    temperature = st.sidebar.slider(
        "Sampling Temperature",
        min_value=0.0,
        max_value=1.0,
        value=float(settings.llm_temperature),
        step=0.05,
    )

    # Recursive Orchestration Parameters
    st.sidebar.subheader("Recursive Budget & Guardrails")
    max_depth = st.sidebar.slider(
        "Max Recursion Depth",
        min_value=1,
        max_value=5,
        value=int(settings.max_recursion_depth),
        help="Maximum cycles the Prime Agent can recurse to resolve knowledge gaps.",
    )

    verification_threshold = st.sidebar.slider(
        "Verification Threshold",
        min_value=0.50,
        max_value=0.95,
        value=float(settings.verification_threshold),
        step=0.05,
        help="Confidence score required before report synthesis is approved.",
    )

    # Search & Tool Options
    st.sidebar.subheader("Tool Integrations (MCP)")
    search_providers = ["duckduckgo", "tavily"]
    default_s_idx = search_providers.index(settings.search_provider) if settings.search_provider in search_providers else 0
    search_provider = st.sidebar.selectbox("Search Tool", search_providers, index=default_s_idx)

    # API Keys Section
    with st.sidebar.expander("🔑 API Keys Override", expanded=False):
        api_key_input = st.text_input(
            f"{selected_provider.upper()} API Key",
            type="password",
            help="Leave empty to use existing environment variable.",
        )
        if api_key_input:
            if selected_provider == "openai":
                os.environ["OPENAI_API_KEY"] = api_key_input
            elif selected_provider == "gemini":
                os.environ["GEMINI_API_KEY"] = api_key_input
            elif selected_provider == "groq":
                os.environ["GROQ_API_KEY"] = api_key_input

        if search_provider == "tavily":
            tavily_key = st.text_input("Tavily API Key", type="password")
            if tavily_key:
                os.environ["TAVILY_API_KEY"] = tavily_key

    # Update runtime environment
    os.environ["LLM_PROVIDER"] = selected_provider
    os.environ["LLM_MODEL"] = model_name
    os.environ["SEARCH_PROVIDER"] = search_provider

    return {
        "provider": selected_provider,
        "model": model_name,
        "temperature": temperature,
        "max_depth": max_depth,
        "verification_threshold": verification_threshold,
        "search_provider": search_provider,
    }
