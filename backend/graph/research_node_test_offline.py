from backend.graph.state import AgentState


def mock_research_result():
    """
    Simulated output from the existing Research Agent.

    This is only for testing LangGraph state wiring.
    It does not replace the real Research Agent.
    """

    return {
        "summary": (
            "Current external evidence indicates that recent "
            "melanoma treatment information should be checked "
            "against authoritative sources."
        ),
        "claims": [
            "Current treatment information should be verified using authoritative sources."
        ],
        "sources": [
            {
                "title": "FDA oncology approval information",
                "organization": "FDA",
                "url": "https://www.fda.gov/",
                "publication_date": "2026",
                "updated_date": "2026",
                "source_type": "government",
            }
        ],
        "uncertainties": [],
        "currentness": (
            "Evidence is intended to represent current external "
            "information and must be checked against the source date."
        ),
    }


def format_research_result(result: dict) -> str:
    lines = []

    lines.append("SUMMARY:")
    lines.append(result["summary"])

    lines.append("")
    lines.append("CLAIMS:")

    for claim in result["claims"]:
        lines.append(f"- {claim}")

    lines.append("")
    lines.append("SOURCES:")

    for source in result["sources"]:
        lines.append(f"- Title: {source['title']}")
        lines.append(f"  Organization: {source['organization']}")
        lines.append(f"  URL: {source['url']}")
        lines.append(
            f"  Publication date: {source['publication_date']}"
        )
        lines.append(
            f"  Updated date: {source['updated_date']}"
        )
        lines.append(
            f"  Source type: {source['source_type']}"
        )

    lines.append("")
    lines.append("UNCERTAINTIES:")

    for uncertainty in result["uncertainties"]:
        lines.append(f"- {uncertainty}")

    lines.append("")
    lines.append("CURRENTNESS:")
    lines.append(result["currentness"])

    return "\n".join(lines)


def research_node_offline(state: AgentState) -> AgentState:
    """
    Offline version of the Research LangGraph node.

    This tests only state management and formatting.
    """

    question = state["question"]

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    result = mock_research_result()

    state["research_evidence"] = format_research_result(result)

    state["research_sources"] = result["sources"]

    return state


def main():
    state: AgentState = {
        "question": (
            "What is the latest FDA-approved treatment "
            "for melanoma in 2026?"
        ),
        "errors": [],
    }

    result = research_node_offline(state)

    print("=" * 70)
    print("LANGGRAPH RESEARCH NODE OFFLINE TEST")
    print("=" * 70)

    print("Question:")
    print(result["question"])

    print()
    print("Research evidence:")
    print(result["research_evidence"])

    print()
    print("Research sources:")

    for source in result["research_sources"]:
        print(
            f"- {source['title']} "
            f"| {source['organization']} "
            f"| {source['publication_date']}"
        )

    print()
    print("State wiring test completed successfully.")


if __name__ == "__main__":
    main()