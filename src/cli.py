"""Interactive Command-Line Interface (CLI) for Autonomous Recursive Research Engine."""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict

from src.config import get_settings
from src.graph.workflow import run_research_workflow


def _slugify(text: str) -> str:
    """Convert text to safe filename slug."""
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "_", text)[:50]


def run_cli() -> None:
    """Entry point for terminal CLI execution."""
    parser = argparse.ArgumentParser(
        description="Autonomous Recursive Research Engine (Prime Agent RLM)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--topic",
        "-t",
        type=str,
        default=None,
        help="Target research topic or query to investigate.",
    )
    parser.add_argument(
        "--max-depth",
        "-d",
        type=int,
        default=None,
        help="Maximum recursive loop iterations (default from config: 3).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Directory or file path to save the generated report.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Override LLM provider (openai, gemini, groq, ollama, mock).",
    )

    args = parser.parse_args()

    topic = args.topic
    if not topic:
        print("\n==================================================================")
        print("  AUTONOMOUS RECURSIVE RESEARCH ENGINE (Prime Agent RLM)")
        print("==================================================================")
        try:
            topic = input("\nEnter research topic: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

    if not topic:
        print("Error: Research topic cannot be empty.")
        sys.exit(1)

    settings = get_settings()
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider

    # Try rich terminal formatting
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.markdown import Markdown

        console = Console()
        console.print(
            Panel.fit(
                f"[bold cyan]Autonomous Recursive Research Engine[/bold cyan]\n"
                f"[dim]Topic:[/dim] [bold]{topic}[/bold]\n"
                f"[dim]Provider:[/dim] {args.provider or settings.llm_provider} | "
                f"[dim]Search:[/dim] {settings.search_provider}",
                border_style="cyan",
            )
        )

        start_time = time.time()
        with console.status("[bold green]Executing recursive agent workflow...", spinner="dots"):
            final_state = run_research_workflow(topic=topic, max_depth=args.max_depth)
        elapsed = time.time() - start_time

        # Print trace logs summary
        table = Table(title="Execution Trace History", show_header=True, header_style="bold magenta")
        table.add_column("Node", style="cyan")
        table.add_column("Details", style="white")

        for log in final_state.get("trace_logs", []):
            table.add_row(str(log.get("node", "")).upper(), str(log.get("message", "")))

        console.print(table)

        # Print verification metrics
        history = final_state.get("verification_history", [])
        if history:
            last_eval = history[-1]
            conf = last_eval.get("confidence_score", 0.0) * 100
            halluc = last_eval.get("hallucination_score", 0.0)
            console.print(
                Panel(
                    f"[bold]Verification Status:[/bold] {'[green]PASSED[/green]' if last_eval.get('sufficient') else '[yellow]PARTIAL[/yellow]'}\n"
                    f"[bold]Grounding Confidence:[/bold] {conf:.1f}%\n"
                    f"[bold]Hallucination Score:[/bold] {halluc:.2f}\n"
                    f"[bold]Reasoning:[/bold] {last_eval.get('reasoning', '')}",
                    title="Audit & Self-Reflection",
                    border_style="green" if last_eval.get("sufficient") else "yellow",
                )
            )

        report = final_state.get("final_report", "No report generated.")
        console.print("\n", Panel(Markdown(report), title="[bold]Synthesized Intelligence Report[/bold]", border_style="blue"))

    except ImportError:
        # Graceful ANSI fallback
        print(f"\n[*] Starting research on: {topic}")
        start_time = time.time()
        final_state = run_research_workflow(topic=topic, max_depth=args.max_depth)
        elapsed = time.time() - start_time

        print(f"\n[+] Execution completed in {elapsed:.2f}s")
        print("\n--- Execution Trace ---")
        for log in final_state.get("trace_logs", []):
            print(f"[{log.get('node', '').upper()}] {log.get('message', '')}")

        report = final_state.get("final_report", "No report generated.")
        print("\n==================================================================")
        print("  SYNTHESIZED INTELLIGENCE REPORT")
        print("==================================================================\n")
        print(report)

    # Save output to disk
    out_dir = Path(args.output) if args.output else settings.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"report_{_slugify(topic)}_{int(time.time())}.md"
    out_path = out_dir / filename
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final_state.get("final_report", ""))

    print(f"\n[✓] Report saved to: {out_path}\n")


if __name__ == "__main__":
    run_cli()
