from backend.agents.router_agent import route_question
from backend.graph.state import AgentState


def router_node(state: AgentState) -> AgentState:
    """
    LangGraph node that runs the existing Router/Triage Agent.

    It reads the user's question from the shared state,
    calls the router agent, and stores the routing decision
    back into the shared state.
    """

    question = state["question"]

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    decision = route_question(question)

    state["route"] = {
        "faculty_rag": decision.faculty_rag,
        "current_research": decision.current_research,
        "emergency": decision.emergency,
        "synthesis": decision.synthesis,
        "verification": decision.verification,
        "intent": decision.intent,
        "reason": decision.reason,
        "confidence": decision.confidence,
        "priority": decision.priority,
        "missing_information": decision.missing_information,
    }

    return state


def main():
    """
    Simple standalone test for the Router LangGraph node.
    """

    state: AgentState = {
        "question": "What are the risk factors for melanoma?",
        "errors": [],
    }

    result = router_node(state)

    print("=" * 70)
    print("LANGGRAPH ROUTER NODE TEST")
    print("=" * 70)

    print("Question:")
    print(result["question"])

    print()
    print("Routing decision:")

    route = result["route"]

    for key, value in route.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()