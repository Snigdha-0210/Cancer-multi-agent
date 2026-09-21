from langgraph.graph import StateGraph, START, END

from backend.graph.state import AgentState
from backend.graph.workflow import (
    route_after_verification,
    MAX_VERIFICATION_ATTEMPTS,
)


# ---------------------------------------------------------
# TEST COUNTER
# ---------------------------------------------------------

research_calls = 0
synthesis_calls = 0
verification_calls = 0


# ---------------------------------------------------------
# MOCK ROUTER
# ---------------------------------------------------------

def mock_router(state: AgentState) -> AgentState:
    state["route"] = {
        "faculty_rag": False,
        "current_research": True,
        "emergency": False,
        "synthesis": True,
        "verification": True,
    }

    return state


# ---------------------------------------------------------
# MOCK RESEARCH
# ---------------------------------------------------------

def mock_research(state: AgentState) -> AgentState:
    global research_calls

    research_calls += 1

    state["research_evidence"] = (
        f"Research evidence generated during research call "
        f"{research_calls}."
    )

    return state


# ---------------------------------------------------------
# MOCK SYNTHESIS
# ---------------------------------------------------------

def mock_synthesis(state: AgentState) -> AgentState:
    global synthesis_calls

    synthesis_calls += 1

    state["proposed_answer"] = (
        f"Answer generated during synthesis call "
        f"{synthesis_calls}."
    )

    return state


# ---------------------------------------------------------
# MOCK VERIFICATION
# ---------------------------------------------------------

def mock_verification(state: AgentState) -> AgentState:
    global verification_calls

    verification_calls += 1

    attempts = state.get("verification_attempts", 0)

    state["verification_attempts"] = attempts + 1

    # First verification deliberately FAILS.
    if verification_calls == 1:
        state["verification_status"] = "FAIL"

        state["verification"] = (
            "VERDICT: FAIL\n"
            "The answer requires additional evidence."
        )

    # Second verification succeeds.
    else:
        state["verification_status"] = "PASS"

        state["verification"] = (
            "VERDICT: PASS\n"
            "The revised answer is adequately supported."
        )

    return state


# ---------------------------------------------------------
# ROUTER
# ---------------------------------------------------------

def test_route_after_router(state: AgentState) -> str:
    return "research"


# ---------------------------------------------------------
# BUILD TEST GRAPH
# ---------------------------------------------------------

def build_retry_test_graph():

    graph = StateGraph(AgentState)

    graph.add_node("router", mock_router)
    graph.add_node("research", mock_research)
    graph.add_node("synthesis", mock_synthesis)
    graph.add_node("verification", mock_verification)

    graph.add_edge(
        START,
        "router",
    )

    graph.add_conditional_edges(
        "router",
        test_route_after_router,
        {
            "research": "research",
        },
    )

    graph.add_edge(
        "research",
        "synthesis",
    )

    graph.add_edge(
        "synthesis",
        "verification",
    )

    graph.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "final": END,
            "retry_research": "research",
            "verification_failed": END,
        },
    )

    return graph.compile()


# ---------------------------------------------------------
# MAIN TEST
# ---------------------------------------------------------

def main():

    global research_calls
    global synthesis_calls
    global verification_calls

    research_calls = 0
    synthesis_calls = 0
    verification_calls = 0

    print("=" * 70)
    print("OFFLINE VERIFICATION RETRY TEST")
    print("=" * 70)

    print()
    print("No OpenAI API calls will be made.")
    print()

    workflow = build_retry_test_graph()

    initial_state = {
        "question": "Test verification retry behaviour.",
        "verification_attempts": 0,
        "errors": [],
    }

    result = workflow.invoke(initial_state)

    print("WORKFLOW RESULT")
    print("-" * 70)

    print(
        f"Research calls: "
        f"{research_calls}"
    )

    print(
        f"Synthesis calls: "
        f"{synthesis_calls}"
    )

    print(
        f"Verification calls: "
        f"{verification_calls}"
    )

    print(
        f"Verification attempts recorded: "
        f"{result.get('verification_attempts')}"
    )

    print(
        f"Final verification status: "
        f"{result.get('verification_status')}"
    )

    print()
    print("Verification result:")
    print(result.get("verification", ""))

    print()
    print("Expected behaviour:")
    print("  First verification → FAIL")
    print("  FAIL → Research")
    print("  Research → Synthesis")
    print("  Synthesis → Verification")
    print("  Second verification → PASS")
    print("  PASS → END")

    print()

    # -----------------------------------------------------
    # ASSERTIONS
    # -----------------------------------------------------

    assert research_calls == 2, (
        f"Expected 2 research calls, "
        f"got {research_calls}"
    )

    assert synthesis_calls == 2, (
        f"Expected 2 synthesis calls, "
        f"got {synthesis_calls}"
    )

    assert verification_calls == 2, (
        f"Expected 2 verification calls, "
        f"got {verification_calls}"
    )

    assert result.get("verification_status") == "PASS", (
        "Expected final verification status to be PASS."
    )

    assert result.get("verification_attempts") == 2, (
        "Expected exactly 2 verification attempts."
    )

    print("=" * 70)
    print("VERIFICATION RETRY TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()