from backend.agents.verifier_agent import verify_answer
from backend.graph.state import AgentState


def build_verification_evidence(state: AgentState) -> str:
    """
    Combine the evidence available in AgentState into a single
    evidence package for the Verification Agent.
    """

    evidence_parts = []

    faculty_evidence = state.get("faculty_evidence", "")
    research_evidence = state.get("research_evidence", "")
    emergency_response = state.get("emergency_response", "")

    if faculty_evidence:
        evidence_parts.append(
            "=== FACULTY KNOWLEDGE EVIDENCE ===\n"
            + faculty_evidence
        )

    if research_evidence:
        evidence_parts.append(
            "=== CURRENT RESEARCH EVIDENCE ===\n"
            + research_evidence
        )

    if emergency_response:
        evidence_parts.append(
            "=== EMERGENCY/SAFETY EVIDENCE ===\n"
            + emergency_response
        )

    return "\n\n".join(evidence_parts)


def verification_node(state: AgentState) -> AgentState:
    """
    LangGraph node that runs the Verification Agent.

    It checks the proposed answer against the evidence available
    in the shared state.
    """

    question = state["question"]
    proposed_answer = state.get("proposed_answer", "")

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    if not proposed_answer.strip():
        raise ValueError("Proposed answer cannot be empty.")

    evidence = build_verification_evidence(state)

    verification_result = verify_answer(
        question=question,
        proposed_answer=proposed_answer,
        evidence=evidence,
    )

    state["verification"] = verification_result

    # Extract the overall verdict from the structured text
    # returned by the current Verification Agent.
    verification_upper = verification_result.upper()

    if "VERDICT: PASS" in verification_upper:
        state["verification_status"] = "PASS"
    elif "VERDICT: FAIL" in verification_upper:
        state["verification_status"] = "FAIL"
    else:
        state["verification_status"] = "UNKNOWN"

    return state


def main():
    """
    Standalone structural test for the Verification Node.

    No OpenAI request is made here because the API is currently
    rate-limited.
    """

    state: AgentState = {
        "question": (
            "What does the faculty material say about melanoma "
            "risk factors, and is that information still current?"
        ),

        "faculty_evidence": (
            "The faculty material discusses established melanoma "
            "risk factors. The source was published in 2018."
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
            "Current external evidence should be consulted to "
            "determine whether older faculty information remains "
            "current medical guidance."
        ),

        "research_sources": [
            {
                "title": "Current authoritative medical sources",
                "organization": "Example medical organization",
                "publication_date": "2026",
            }
        ],

        "proposed_answer": (
            "The faculty material discusses melanoma risk factors. "
            "Because the faculty source is from 2018, it should not "
            "automatically be treated as current medical guidance."
        ),

        "errors": [],
    }

    evidence = build_verification_evidence(state)

    print("=" * 70)
    print("LANGGRAPH VERIFICATION NODE TEST")
    print("=" * 70)

    print()
    print("Question:")
    print(state["question"])

    print()
    print("Proposed answer:")
    print(state["proposed_answer"])

    print()
    print("Evidence supplied to verifier:")
    print(evidence)

    print()
    print("Verification node structure is ready.")
    print("Live verifier call is intentionally not executed.")


if __name__ == "__main__":
    main()