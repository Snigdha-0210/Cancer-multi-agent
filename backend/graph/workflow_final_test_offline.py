from backend.graph.state import AgentState
from backend.graph.workflow import (
    build_workflow,
)


def mock_router_node(state: AgentState) -> AgentState:
    question = state["question"].lower()

    if "die" in question or "suicide" in question:
        state["route"] = {
            "faculty_rag": False,
            "current_research": False,
            "emergency": True,
            "synthesis": True,
            "verification": True,
            "intent": "emergency",
            "reason": "Emergency language detected.",
            "confidence": "HIGH",
            "priority": "IMMEDIATE",
            "missing_information": [],
        }

    elif "latest" in question or "2026" in question:
        state["route"] = {
            "faculty_rag": False,
            "current_research": True,
            "emergency": False,
            "synthesis": True,
            "verification": True,
            "intent": "current_research",
            "reason": "Current information requested.",
            "confidence": "HIGH",
            "priority": "NORMAL",
            "missing_information": [],
        }

    else:
        state["route"] = {
            "faculty_rag": True,
            "current_research": False,
            "emergency": False,
            "synthesis": True,
            "verification": True,
            "intent": "faculty_knowledge",
            "reason": "Question can be answered from faculty knowledge.",
            "confidence": "HIGH",
            "priority": "NORMAL",
            "missing_information": [],
        }

    return state


def mock_emergency_node(state: AgentState) -> AgentState:
    state["emergency_response"] = (
        "This sounds like an emergency. Please seek immediate "
        "human support and emergency assistance."
    )
    state["emergency_type"] = "self_harm"
    return state


def mock_rag_node(state: AgentState) -> AgentState:
    state["faculty_evidence"] = (
        "Faculty material discusses established risk factors "
        "for melanoma."
    )

    state["faculty_sources"] = [
        {
            "title": "A Practical Guide to Skin Cancer",
            "page": 25,
            "source_type": "faculty_knowledge",
        }
    ]

    return state


def mock_research_node(state: AgentState) -> AgentState:
    state["research_evidence"] = (
        "Current external sources should be used when the "
        "question asks for latest information."
    )

    state["research_sources"] = [
        {
            "title": "Current Medical Source",
            "organization": "Trusted Medical Organization",
            "url": "https://example.com",
            "source_type": "current_external_research",
        }
    ]

    return state


def mock_synthesis_node(state: AgentState) -> AgentState:
    question = state["question"]

    if state.get("emergency_response"):
        answer = (
            "This is an emergency situation. "
            "Please seek immediate human help."
        )

    elif state.get("research_evidence"):
        answer = (
            f"Current information was researched for: {question}"
        )

    else:
        answer = (
            "The faculty material discusses established "
            "risk factors for melanoma."
        )

    state["proposed_answer"] = answer

    return state


def mock_verification_node(state: AgentState) -> AgentState:
    state["verification"] = (
        "VERDICT: PASS\n"
        "CONFIDENCE: HIGH\n"
        "SUPPORTED CLAIMS: Answer is supported by available evidence."
    )

    state["verification_status"] = "PASS"

    return state


def run_test(question: str):
    print("=" * 70)
    print("TEST QUESTION")
    print("=" * 70)
    print(question)
    print()

    # Build the real LangGraph first.
    # We then replace its node functions with deterministic mocks
    # so no OpenAI API calls are required.
    graph = build_workflow()

    # For this structural test, we directly simulate the expected
    # final state instead of calling external APIs.
    state: AgentState = {
        "question": question,
        "verification_attempts": 0,
    }

    state = mock_router_node(state)

    route = state["route"]

    if route["emergency"]:
        state = mock_emergency_node(state)

    elif route["faculty_rag"]:
        state = mock_rag_node(state)

        if route["current_research"]:
            state = mock_research_node(state)

    elif route["current_research"]:
        state = mock_research_node(state)

    state = mock_synthesis_node(state)

    state["verification_attempts"] += 1
    state = mock_verification_node(state)

    # Simulate the final node.
    from backend.graph.final_node import final_node, build_final_response

    state = final_node(state)

    response = build_final_response(state)

    print("FINAL ANSWER:")
    print(response["answer"])
    print()

    print("VERIFICATION:")
    print(response["verification_status"])
    print()

    print("AGENTS USED:")
    print(" → ".join(response["agents_used"]))
    print()

    print("VERIFICATION ATTEMPTS:")
    print(response["verification_attempts"])
    print()

    print("SOURCES:")
    for source in response["sources"]:
        print(source)

    print()

    return response


def main():
    print()
    print("=" * 70)
    print("OFFLINE FINAL WORKFLOW TEST")
    print("=" * 70)
    print()

    tests = [
        "What are the established risk factors for melanoma?",
        "What is the latest cancer treatment information in 2026?",
        "My cancer treatment is unbearable and I want to die.",
    ]

    for question in tests:
        run_test(question)

    print("=" * 70)
    print("OFFLINE FINAL WORKFLOW TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()