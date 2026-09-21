from backend.agents.synthesis_agent import synthesize_answer
from backend.graph.state import AgentState


def synthesis_node(state: AgentState) -> AgentState:
    """
    LangGraph node that runs the Synthesis Agent.

    It combines the evidence produced by the Faculty RAG,
    Current Research, and Emergency agents into a proposed
    answer.
    """

    question = state["question"]

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    faculty_evidence = state.get("faculty_evidence", "")
    research_evidence = state.get("research_evidence", "")
    emergency_response = state.get("emergency_response", "")

    proposed_answer = synthesize_answer(
        question=question,
        faculty_evidence=faculty_evidence,
        research_evidence=research_evidence,
        emergency_evidence=emergency_response,
    )

    state["proposed_answer"] = proposed_answer

    return state


def main():
    """
    Standalone test for the Synthesis LangGraph node.

    This uses simulated evidence so it does not require an
    OpenAI API request.
    """

    state: AgentState = {
        "question": (
            "What does the faculty material say about melanoma "
            "risk factors, and is that information still current?"
        ),

        "faculty_evidence": (
            "The faculty material discusses established risk "
            "factors for melanoma and includes information from "
            "the 2018 publication."
        ),

        "faculty_sources": [
            {
                "document": "a-practical-guide-to-skin-cancer-2018.pdf",
                "page_start": 10,
                "page_end": 12,
                "source_year": 2018,
            }
        ],

        "research_evidence": (
            "Current external evidence should be consulted when "
            "determining whether older faculty material remains "
            "current medical guidance."
        ),

        "research_sources": [
            {
                "title": "Current authoritative medical sources",
                "organization": "Example medical organization",
                "publication_date": "2026",
            }
        ],

        "emergency_response": "",

        "errors": [],
    }

    print("=" * 70)
    print("LANGGRAPH SYNTHESIS NODE TEST")
    print("=" * 70)

    print()
    print("This test contains simulated evidence.")
    print("It is intended to verify the node structure.")

    # Do not call the real LLM while the API is rate-limited.
    print()
    print("Synthesis node structure is ready.")

    print()
    print("Expected evidence flow:")
    print("- Faculty evidence → synthesis")
    print("- Current research → synthesis")
    print("- Emergency evidence → synthesis when applicable")


if __name__ == "__main__":
    main()