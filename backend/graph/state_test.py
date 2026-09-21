from backend.graph.state import AgentState


def main():

    state: AgentState = {
        "question": "What are the risk factors for melanoma?",
        "route": {
            "faculty_rag": True,
            "current_research": False,
            "emergency": False,
            "synthesis": True,
            "verification": True,
        },
        "errors": [],
    }

    print("=" * 70)
    print("LANGGRAPH STATE TEST")
    print("=" * 70)

    print("Question:")
    print(state["question"])

    print()
    print("Route:")
    print(state["route"])

    print()
    print("State created successfully.")


if __name__ == "__main__":
    main()