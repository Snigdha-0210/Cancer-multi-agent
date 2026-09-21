from backend.graph.state import AgentState
from backend.rag.rag_agent import answer_with_rag


def rag_node(state: AgentState) -> AgentState:
    """
    LangGraph node that runs the Faculty Knowledge RAG Agent.

    It reads the user's question from the shared state,
    retrieves relevant faculty PDF evidence, generates a
    grounded answer, and stores the evidence and sources
    back into the shared state.
    """

    question = state["question"]

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    result = answer_with_rag(question)

    state["faculty_evidence"] = result.get("answer", "")

    state["faculty_sources"] = result.get("sources", [])

    return state


def main():
    """
    Standalone test for the Faculty RAG LangGraph node.
    """

    state: AgentState = {
        "question": "What are the established risk factors for melanoma?",
        "errors": [],
    }

    result = rag_node(state)

    print("=" * 70)
    print("LANGGRAPH FACULTY RAG NODE TEST")
    print("=" * 70)

    print("Question:")
    print(result["question"])

    print()
    print("Faculty RAG evidence:")
    print(result.get("faculty_evidence"))

    print()
    print("Faculty sources:")

    for source in result.get("faculty_sources", []):
        print(
            f"- {source.get('document')} "
            f"pages {source.get('page_start')}-"
            f"{source.get('page_end')} "
            f"(score: {source.get('score', 0):.4f})"
        )


if __name__ == "__main__":
    main()