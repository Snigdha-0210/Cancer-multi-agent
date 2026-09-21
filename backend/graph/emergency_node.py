from backend.agents.emergency_agent import handle_emergency
from backend.graph.state import AgentState


def emergency_node(state: AgentState) -> AgentState:
    """
    LangGraph node that runs the Emergency/Safety Agent.

    It reads the user's question from the shared state,
    calls the existing emergency agent, and stores the
    emergency response back into the shared state.
    """

    question = state["question"]

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    result = handle_emergency(question)

    state["emergency_response"] = result.response
    state["emergency_type"] = result.emergency_type

    return state


def main():
    """
    Standalone test for the Emergency LangGraph node.
    """

    state: AgentState = {
        "question": "My cancer treatment is unbearable and I want to die.",
        "errors": [],
    }

    result = emergency_node(state)

    print("=" * 70)
    print("LANGGRAPH EMERGENCY NODE TEST")
    print("=" * 70)

    print("Question:")
    print(result["question"])

    print()
    print("Emergency type:")
    print(result.get("emergency_type"))

    print()
    print("Emergency response:")
    print(result.get("emergency_response"))


if __name__ == "__main__":
    main()