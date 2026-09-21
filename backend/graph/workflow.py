from langgraph.graph import StateGraph, START, END

from backend.graph.state import AgentState
from backend.graph.router_node import router_node
from backend.graph.emergency_node import emergency_node
from backend.graph.rag_node import rag_node
from backend.graph.research_node import research_node
from backend.graph.synthesis_node import synthesis_node
from backend.graph.verification_node import verification_node


def route_after_router(state: AgentState) -> str:
    """
    Decide which agent branch should run after the router.

    Emergency has the highest priority.
    Otherwise, faculty RAG and/or current research are selected.
    """

    route = state.get("route", {})

    if route.get("emergency"):
        return "emergency"

    faculty_rag = route.get("faculty_rag", False)
    current_research = route.get("current_research", False)

    if faculty_rag and current_research:
        return "faculty_and_research"

    if faculty_rag:
        return "faculty"

    if current_research:
        return "research"

    return "synthesis"


def route_after_faculty(state: AgentState) -> str:
    """
    After faculty RAG, determine whether current external research
    is also required.
    """

    route = state.get("route", {})

    if route.get("current_research"):
        return "research"

    return "synthesis"


def route_after_verification(state: AgentState) -> str:
    """
    Decide what happens after verification.

    PASS → final answer.

    FAIL → for now, stop at END.

    We will later add a controlled retry/research loop.
    """

    verification_status = state.get("verification_status", "UNKNOWN")

    if verification_status == "PASS":
        return "final"

    return "failed_verification"


def build_workflow():
    """
    Build and compile the LangGraph workflow.
    """

    graph = StateGraph(AgentState)

    # ---------------------------------------------------------
    # ADD NODES
    # ---------------------------------------------------------

    graph.add_node("router", router_node)
    graph.add_node("emergency", emergency_node)
    graph.add_node("faculty_rag", rag_node)
    graph.add_node("research", research_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("verification", verification_node)

    # ---------------------------------------------------------
    # START → ROUTER
    # ---------------------------------------------------------

    graph.add_edge(START, "router")

    # ---------------------------------------------------------
    # ROUTER → APPROPRIATE BRANCH
    # ---------------------------------------------------------

    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "emergency": "emergency",
            "faculty": "faculty_rag",
            "research": "research",
            "faculty_and_research": "faculty_rag",
            "synthesis": "synthesis",
        },
    )

    # ---------------------------------------------------------
    # FACULTY RAG → RESEARCH OR SYNTHESIS
    # ---------------------------------------------------------

    graph.add_conditional_edges(
        "faculty_rag",
        route_after_faculty,
        {
            "research": "research",
            "synthesis": "synthesis",
        },
    )

    # ---------------------------------------------------------
    # RESEARCH → SYNTHESIS
    # ---------------------------------------------------------

    graph.add_edge("research", "synthesis")

    # ---------------------------------------------------------
    # EMERGENCY → SYNTHESIS
    # ---------------------------------------------------------

    graph.add_edge("emergency", "synthesis")

    # ---------------------------------------------------------
    # SYNTHESIS → VERIFICATION
    # ---------------------------------------------------------

    graph.add_edge("synthesis", "verification")

    # ---------------------------------------------------------
    # VERIFICATION → FINAL / FAILURE
    # ---------------------------------------------------------

    graph.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "final": END,
            "failed_verification": END,
        },
    )

    # ---------------------------------------------------------
    # COMPILE
    # ---------------------------------------------------------

    return graph.compile()


workflow = build_workflow()


def main():
    print("=" * 70)
    print("LANGGRAPH WORKFLOW")
    print("=" * 70)

    print()
    print("Workflow compiled successfully.")
    print()

    print("Nodes:")
    print("  1. router")
    print("  2. emergency")
    print("  3. faculty_rag")
    print("  4. research")
    print("  5. synthesis")
    print("  6. verification")

    print()
    print("Main flow:")
    print("  START")
    print("    ↓")
    print("  ROUTER")
    print("    ↓")
    print("  appropriate agent branch")
    print("    ↓")
    print("  SYNTHESIS")
    print("    ↓")
    print("  VERIFICATION")
    print("    ↓")
    print("  END")

    print()
    print("LangGraph workflow is ready.")


if __name__ == "__main__":
    main()