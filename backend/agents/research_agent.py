from openai import OpenAI
from pydantic import BaseModel, Field

from backend.config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are the external research agent for a cancer information
assistant.

Your job is to research information that cannot reliably be
answered from the faculty PDF knowledge base.

IMPORTANT RULES:

1. Research the user's question using external web sources.

2. Prefer authoritative and trustworthy sources.

3. For medical and cancer-related questions, prioritize:
   - FDA
   - National Cancer Institute (NCI)
   - National Institutes of Health (NIH)
   - CDC
   - recognized government health agencies
   - recognized medical organizations
   - peer-reviewed medical literature

4. Pay close attention to publication dates and update dates.

5. If the user asks for latest, current, recent, newest, or
   a specific year, prioritize recent sources.

6. Never present old information as current information.

7. Do not invent sources, URLs, dates, approvals, treatments,
   statistics, or medical recommendations.

8. If reliable current information cannot be established,
   clearly state that.

9. Do not diagnose the patient.

10. Do not prescribe treatment or medication.

11. Clearly distinguish:
    - directly supported findings
    - uncertainty
    - conflicts between sources

12. If the question contains a claim such as "latest",
    "newest", or "most recent", do not assume that finding one
    recent source proves the claim. Look for evidence that allows
    the recency claim to be established.

13. Return structured research evidence. Another agent will later
    synthesize and verify your research.
"""


class ResearchSource(BaseModel):
    title: str = ""
    organization: str = ""
    url: str = ""
    publication_date: str = ""
    updated_date: str = ""
    source_type: str = ""


class ResearchResult(BaseModel):
    summary: str
    claims: list[str] = Field(default_factory=list)
    sources: list[ResearchSource] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    currentness: str = ""


def research_question(question: str) -> ResearchResult:
    """
    Research a question using external web search and return
    structured evidence.
    """

    response = client.responses.parse(
        model="gpt-5.6-luna",
        instructions=SYSTEM_PROMPT,
        tools=[
            {
                "type": "web_search",
            }
        ],
        input=question,
        text_format=ResearchResult,
    )

    return response.output_parsed


def main():
    question = (
        "What is the latest FDA-approved treatment for melanoma "
        "in 2026?"
    )

    print("=" * 70)
    print("STRUCTURED RESEARCH AGENT TEST")
    print("=" * 70)

    print(f"QUESTION:\n{question}")

    result = research_question(question)

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(result.summary)

    print("=" * 70)
    print("CLAIMS")
    print("=" * 70)

    for claim in result.claims:
        print(f"- {claim}")

    print("=" * 70)
    print("SOURCES")
    print("=" * 70)

    for source in result.sources:
        print(f"Title: {source.title}")
        print(f"Organization: {source.organization}")
        print(f"URL: {source.url}")
        print(f"Publication date: {source.publication_date}")
        print(f"Updated date: {source.updated_date}")
        print(f"Source type: {source.source_type}")
        print("-" * 70)

    print("=" * 70)
    print("UNCERTAINTIES")
    print("=" * 70)

    for uncertainty in result.uncertainties:
        print(f"- {uncertainty}")

    print("=" * 70)
    print("CURRENTNESS")
    print("=" * 70)
    print(result.currentness)


if __name__ == "__main__":
    main()