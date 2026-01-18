"""
Visualize the LangGraph workflow.

This script generates a PNG diagram of the agent workflow graph.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.workflow_langgraph import LangGraphWorkflow


def main():
    """Generate and save graph visualization."""
    workflow = LangGraphWorkflow()

    # Get the graph
    graph = workflow.graph

    try:
        # Generate Mermaid diagram
        mermaid_code = graph.get_graph().draw_mermaid()

        print("=" * 60)
        print("LangGraph Workflow Diagram (Mermaid)")
        print("=" * 60)
        print(mermaid_code)
        print("=" * 60)
        print()
        print("Copy the above Mermaid code to: https://mermaid.live")
        print("to visualize the graph interactively.")

        # Save to file
        with open("workflow_graph.mermaid", "w") as f:
            f.write(mermaid_code)

        print()
        print("✅ Saved to: workflow_graph.mermaid")

    except Exception as e:
        print(f"Error generating diagram: {e}")
        print("Tip: Install graphviz: brew install graphviz")


if __name__ == "__main__":
    main()
