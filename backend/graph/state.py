from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """
    Shared state passed between agents in the LangGraph workflow.
    """

    # Original user message
    question: str

    # Router/Triage decision
    route: dict[str, Any]

    # Faculty RAG evidence and answer
    faculty_evidence: str
    faculty_sources: list[dict[str, Any]]

    # Current external research
    research_evidence: str
    research_sources: list[dict[str, Any]]

    # Emergency/Safety result
    emergency_response: str
    emergency_type: str

    # Proposed combined answer
    proposed_answer: str

    # Verification result
    verification: str
    verification_status: str

    # Final answer returned to the user
    final_answer: str

    # General workflow metadata
    errors: list[str]