import json

from backend.agents.research_agent import research_question
from backend.graph.state import AgentState


def format_research_result(research_result) -> str:
    """
    Convert the structured Research Agent result into text
    that can be passed to later LangGraph nodes.
    """

    lines = []

    lines.append("SUMMARY:")
    lines.append(research_result.summary)

    lines.append("")
    lines.append("CLAIMS:")

    for claim in research_result.claims:
        lines.append(f"- {claim}")

    lines.append("")
    lines.append("SOURCES:")

    for source in research_result.sources:
        lines.append(f"- Title: {source.title}")
        lines.append(f"  Organization: {source.organization}")
        lines.append(f"  URL: {source.url}")
        lines.append(f"  Publication date: {source.publication_date}")
        lines.append(f"  Updated date: {source.updated_date}")
        lines.append(f"  Source type: {source.source_type}")

    lines.append("")
    lines.append("UNCERTAINTIES:")

    for uncertainty in research_result.uncertainties:
        lines.append(f"- {uncertainty}")

    lines.append("")
    lines.append("CURRENTNESS:")
    lines.append(research_result.currentness)

    return "\n".join(lines)


def research_node(state: AgentState) -> AgentState:
    """
    LangGraph node that runs the external Research Agent.

    It reads the user's question, performs current external
    research, and stores the structured research evidence
    in the shared LangGraph state.
    """

    question = state["question"]

    if not question.strip():
        raise ValueError("Question cannot be empty.")

    verification_status = state.get(
        "verification_status",
        "",
    )

    if verification_status == "FAIL":
        verification_result = state.get("verification", "")

        try:
            verification_data = json.loads(verification_result)
            unsupported_claims = verification_data.get(
                "unsupported_or_problematic_claims",
                [],
            )
            missing_information = verification_data.get(
                "missing_information",
                [],
            )
        except (json.JSONDecodeError, TypeError, AttributeError):
            unsupported_claims = []
            missing_information = []

        research_query = (
            f"Original question: {question}\n\n"
            "The previous answer failed verification. "
            "Investigate the following issues using reliable, "
            "authoritative and current sources:\n\n"
            "Unsupported claims:\n"
            + "\n".join(f"- {claim}" for claim in unsupported_claims)
            + "\n\nMissing information:\n"
            + "\n".join(f"- {item}" for item in missing_information)
        )
    else:
        research_query = question

    result = research_question(research_query)

    state["research_evidence"] = format_research_result(result)

    state["research_sources"] = [
        {
            "title": source.title,
            "organization": source.organization,
            "url": source.url,
            "publication_date": source.publication_date,
            "updated_date": source.updated_date,
            "source_type": source.source_type,
        }
        for source in result.sources
    ]

    return state


def main():
    """
    Standalone test for the Research LangGraph node.
    """

    state: AgentState = {
        "question": (
            "What is the latest FDA-approved treatment "
            "for melanoma in 2026?"
        ),
        "errors": [],
    }

    result = research_node(state)

    print("=" * 70)
    print("LANGGRAPH RESEARCH NODE TEST")
    print("=" * 70)

    print("Question:")
    print(result["question"])

    print()
    print("Research evidence:")
    print(result.get("research_evidence"))

    print()
    print("Research sources:")

    for source in result.get("research_sources", []):
        print(
            f"- {source.get('title')} "
            f"| {source.get('organization')} "
            f"| {source.get('publication_date')}"
        )


if __name__ == "__main__":
    main()