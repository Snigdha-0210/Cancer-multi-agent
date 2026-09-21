from backend.graph.state import AgentState


def mock_rag_result():
    """
    Simulated output from the existing Faculty RAG Agent.

    This is only for testing the LangGraph state wiring.
    It does NOT replace the real RAG agent.
    """

    return {
        "answer": (
            "The faculty material identifies several established "
            "risk factors associated with melanoma."
        ),
        "sources": [
            {
                "document": "a-practical-guide-to-skin-cancer-2018.pdf",
                "page_start": 10,
                "page_end": 12,
                "section": "Skin Cancer: At-Risk Populations and Prevention",
                "source_year": 2018,
                "score": 0.82,
            }
        ],
    }


def rag_node_offline(state: AgentState) -> AgentState:
    """
    Offline version of the RAG LangGraph node.

    This tests only the state-management part of the node.
    """

    question = state["question"]

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    result = mock_rag_result()

    state["faculty_evidence"] = result["answer"]
    state["faculty_sources"] = result["sources"]

    return state


def main():
    state: AgentState = {
        "question": "What are the established risk factors for melanoma?",
        "errors": [],
    }

    result = rag_node_offline(state)

    print("=" * 70)
    print("LANGGRAPH FACULTY RAG OFFLINE TEST")
    print("=" * 70)

    print("Question:")
    print(result["question"])

    print()
    print("Faculty evidence:")
    print(result["faculty_evidence"])

    print()
    print("Faculty sources:")

    for source in result["faculty_sources"]:
        print(
            f"- {source['document']} "
            f"pages {source['page_start']}-"
            f"{source['page_end']} "
            f"(score: {source['score']:.4f})"
        )

    print()
    print("State wiring test completed successfully.")


if __name__ == "__main__":
    main()