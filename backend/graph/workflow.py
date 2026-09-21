from langgraph.graph import StateGraph, START, END

from backend.graph.state import AgentState
from backend.graph.router_node import router_node
from backend.graph.emergency_node import emergency_node
from backend.graph.rag_node import rag_node
from backend.graph.research_node import research_node
from backend.graph.synthesis_node import synthesis_node
from backend.graph.verification_node import verification_node
from backend.graph.final_node import final_node


MAX_VERIFICATION_ATTEMPTS = 2


def route_after_router(state: AgentState) -> str:
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
    route = state.get("route", {})

    if route.get("current_research"):
        return "research"

    return "synthesis"


def verification_node_with_counter(
    state: AgentState,
) -> AgentState:
    current_attempts = state.get(
        "verification_attempts",
        0,
    )

    state["verification_attempts"] = (
        current_attempts + 1
    )

    return verification_node(state)


def route_after_verification(state: AgentState) -> str:
    verification_status = state.get(
        "verification_status",
        "UNKNOWN",
    )

    attempts = state.get(
        "verification_attempts",
        0,
    )

    if verification_status == "PASS":
        return "final"

    if (
        verification_status == "FAIL"
        and attempts < MAX_VERIFICATION_ATTEMPTS
    ):
        return "retry_research"

    return "verification_failed"


def build_workflow():
    """
    Build the complete multi-agent LangGraph.
    """

    graph = StateGraph(AgentState)

    # ---------------------------------------------------------
    # AGENT NODES
    # ---------------------------------------------------------

    graph.add_node(
        "router",
        router_node,
    )

    graph.add_node(
        "emergency",
        emergency_node,
    )

    graph.add_node(
        "faculty_rag",
        rag_node,
    )

    graph.add_node(
        "research",
        research_node,
    )

    graph.add_node(
        "synthesis",
        synthesis_node,
    )

    graph.add_node(
        "verification",
        verification_node_with_counter,
    )

    # ---------------------------------------------------------
    # FINAL NODE
    # ---------------------------------------------------------

    graph.add_node(
        "final",
        final_node,
    )

    # ---------------------------------------------------------
    # START
    # ---------------------------------------------------------

    graph.add_edge(
        START,
        "router",
    )

    # ---------------------------------------------------------
    # ROUTER
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
    # FACULTY RAG
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
    # RESEARCH
    # ---------------------------------------------------------

    graph.add_edge(
        "research",
        "synthesis",
    )

    # ---------------------------------------------------------
    # EMERGENCY
    # ---------------------------------------------------------

    graph.add_edge(
        "emergency",
        "synthesis",
    )

    # ---------------------------------------------------------
    # SYNTHESIS
    # ---------------------------------------------------------

    graph.add_edge(
        "synthesis",
        "verification",
    )

    # ---------------------------------------------------------
    # VERIFICATION
    # ---------------------------------------------------------

    graph.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "final": "final",
            "retry_research": "research",
            "verification_failed": "final",
        },
    )

    # ---------------------------------------------------------
    # FINAL
    # ---------------------------------------------------------

    graph.add_edge(
        "final",
        END,
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
    print("  7. final")

    print()
    print(
        "Verification retry limit:",
        MAX_VERIFICATION_ATTEMPTS,
        "attempts",
    )

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

    print()
    print("  PASS")
    print("    ↓")
    print("  FINAL")
    print("    ↓")
    print("  END")

    print()
    print("  FAIL")
    print("    ↓")
    print("  RESEARCH")
    print("    ↓")
    print("  SYNTHESIS")
    print("    ↓")
    print("  VERIFICATION")

    print()
    print("LangGraph workflow is ready.")


if __name__ == "__main__":
    main()