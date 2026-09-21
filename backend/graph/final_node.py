from backend.graph.state import AgentState


def collect_sources(state: AgentState) -> list[dict]:
    """
    Collect source information from the agents that actually
    contributed evidence.
    """

    sources = []

    faculty_sources = state.get("faculty_sources", [])
    research_sources = state.get("research_sources", [])

    for source in faculty_sources:
        source_copy = dict(source)
        source_copy["source_category"] = "faculty_knowledge"
        sources.append(source_copy)

    for source in research_sources:
        source_copy = dict(source)
        source_copy["source_category"] = "current_external_research"
        sources.append(source_copy)

    return sources


def collect_agents_used(state: AgentState) -> list[str]:
    """
    Determine which agents actually contributed to this workflow.
    """

    agents = []

    route = state.get("route", {})

    if route:
        agents.append("router")

    if state.get("faculty_evidence"):
        agents.append("faculty_rag")

    if state.get("research_evidence"):
        agents.append("research")

    if state.get("emergency_response"):
        agents.append("emergency")

    if state.get("proposed_answer"):
        agents.append("synthesis")

    if state.get("verification"):
        agents.append("verification")

    return agents


def final_node(state: AgentState) -> AgentState:
    """
    Convert the internal workflow state into the final answer.

    Only a verified answer is allowed to become the normal
    final response.
    """

    verification_status = state.get(
        "verification_status",
        "UNKNOWN",
    )

    proposed_answer = state.get(
        "proposed_answer",
        "",
    )

    if verification_status == "PASS":
        state["final_answer"] = proposed_answer

    elif verification_status == "FAIL":
        state["final_answer"] = (
            "I couldn't verify the answer with sufficient confidence. "
            "The available evidence may be incomplete or require "
            "additional current verification."
        )

    else:
        state["final_answer"] = (
            "I couldn't complete verification of this answer."
        )

    return state


def build_final_response(state: AgentState) -> dict:
    """
    Create the clean response object that the API/frontend
    will eventually receive.
    """

    return {
        "answer": state.get("final_answer", ""),
        "verification_status": state.get(
            "verification_status",
            "UNKNOWN",
        ),
        "sources": collect_sources(state),
        "agents_used": collect_agents_used(state),
        "verification_attempts": state.get(
            "verification_attempts",
            0,
        ),
    }


def main():
    """
    Offline structural test.
    """

    print("=" * 70)
    print("FINAL NODE TEST")
    print("=" * 70)

    state = {
        "question": "What are the risk factors for melanoma?",
        "route": {
            "faculty_rag": True,
            "current_research": False,
            "emergency": False,
        },
        "faculty_evidence": (
            "Faculty material contains information about "
            "melanoma risk factors."
        ),
        "faculty_sources": [
            {
                "document": "a-practical-guide-to-skin-cancer-2018.pdf",
                "page_start": 10,
                "page_end": 12,
                "source_year": 2018,
            }
        ],
        "proposed_answer": (
            "The faculty material discusses established "
            "risk factors for melanoma."
        ),
        "verification": (
            "VERDICT: PASS\n"
            "CONFIDENCE: HIGH"
        ),
        "verification_status": "PASS",
        "verification_attempts": 1,
        "errors": [],
    }

    final_node(state)

    response = build_final_response(state)

    print()
    print("Final answer:")
    print(response["answer"])

    print()
    print("Verification status:")
    print(response["verification_status"])

    print()
    print("Sources:")
    for source in response["sources"]:
        print(source)

    print()
    print("Agents used:")
    print(" → ".join(response["agents_used"]))

    print()
    print(
        "Verification attempts:",
        response["verification_attempts"],
    )

    print()
    print("=" * 70)
    print("FINAL NODE TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
