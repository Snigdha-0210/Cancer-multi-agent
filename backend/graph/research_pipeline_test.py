from backend.agents.research_agent import research_question
from backend.agents.synthesis_agent import synthesize_answer
from backend.agents.verifier_agent import verify_answer


def format_research_evidence(research_result) -> str:
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


def main():

    question = (
        "What is the latest FDA-approved treatment for melanoma "
        "in 2026?"
    )

    print("=" * 70)
    print("RESEARCH → SYNTHESIS → VERIFICATION")
    print("=" * 70)

    # ---------------------------------------------------------
    # STEP 1 — RESEARCH
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("STEP 1: RESEARCH")
    print("=" * 70)

    research_result = research_question(question)

    research_evidence = format_research_evidence(
        research_result
    )

    print(research_evidence)

    # ---------------------------------------------------------
    # STEP 2 — SYNTHESIS
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("STEP 2: SYNTHESIS")
    print("=" * 70)

    proposed_answer = synthesize_answer(
        question=question,
        faculty_evidence="",
        research_evidence=research_evidence,
        emergency_evidence="",
    )

    print(proposed_answer)

    # ---------------------------------------------------------
    # STEP 3 — VERIFICATION
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("STEP 3: VERIFICATION")
    print("=" * 70)

    verification = verify_answer(
        question=question,
        proposed_answer=proposed_answer,
        evidence=research_evidence,
    )

    print(verification)

    print()
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()