import json
import urllib.request

from pydantic import BaseModel, Field

from backend.tools.web_search import search_web


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"


SYSTEM_PROMPT = """
You are the external research agent for a cancer information
assistant.

Your job is to research information that cannot reliably be
answered from the faculty PDF knowledge base.

IMPORTANT RULES:

1. Use the provided external web search results as your research
   evidence.

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
    recent source proves the claim.

13. Only make claims that are supported by the supplied search
    results.

14. Return structured research evidence. Another agent will later
    synthesize and verify your research.

15. For questions asking for "latest", "newest", "most recent",
    or a specific current year, set currentness to CURRENT only
    when the supplied evidence clearly establishes that the
    information is current as of the requested time.

    If the evidence confirms a recent approval or development but
    does NOT establish that no newer relevant development exists,
    set currentness to POSSIBLY_CURRENT.

    Never use CURRENT merely because a source is recent.

16. When currentness is POSSIBLY_CURRENT, the summary and claims
    must use cautious wording such as "the latest approval found
    in the searched sources" rather than claiming it is definitively
    the latest approval.
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


def ask_ollama(prompt: str) -> str:
    payload = {
        "model": MODEL_NAME,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["response"]


def research_question(question: str) -> ResearchResult:
    """
    Research a question using free external web search and Qwen3.
    """

    try:
        # ---------------------------------------------------------
        # 1. Search authoritative sources first
        # ---------------------------------------------------------

        # Use the original question's first line as the concise
        # search topic. The full question, including verification
        # feedback, will still be sent to the research LLM below.
        search_topic = question.splitlines()[0].strip()

        authoritative_queries = [
            f"{search_topic} site:fda.gov",
            f"{search_topic} site:cancer.gov",
            f"{search_topic} site:nih.gov",
            f"{search_topic} site:cdc.gov",
        ]

        search_results = []

        for query in authoritative_queries:
            try:
                results = search_web(query, max_results=5)
                search_results.extend(results)
            except Exception as search_error:
                print(f"Search warning: {search_error}")

        # Remove duplicate URLs
        unique_results = []
        seen_urls = set()

        for result in search_results:
            url = result.get("url", "").strip()

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            unique_results.append(result)

        # ---------------------------------------------------------
        # 2. If authoritative searches returned too little,
        #    perform a broader search.
        # ---------------------------------------------------------

        if len(unique_results) < 3:
            try:
                broader_results = search_web(
                    question,
                    max_results=8,
                )

                for result in broader_results:
                    url = result.get("url", "").strip()

                    if not url or url in seen_urls:
                        continue

                    seen_urls.add(url)
                    unique_results.append(result)

            except Exception as search_error:
                print(f"Broader search warning: {search_error}")

        # ---------------------------------------------------------
        # 3. Fail safely if web search produced nothing
        # ---------------------------------------------------------

        if not unique_results:
            return ResearchResult(
                summary=(
                    "External web research could not be completed "
                    "because no search results were available."
                ),
                claims=[],
                sources=[],
                uncertainties=[
                    "No external web search results were available.",
                    "Current information could not be independently verified.",
                ],
                currentness="UNKNOWN",
            )

        # Limit evidence sent to the local model
        unique_results = unique_results[:15]

        # ---------------------------------------------------------
        # 4. Prepare evidence for Qwen3
        # ---------------------------------------------------------

        evidence_text = []

        for index, result in enumerate(unique_results, 1):
            evidence_text.append(
                f"""
SOURCE {index}

Title:
{result.get("title", "")}

URL:
{result.get("url", "")}

Search snippet:
{result.get("snippet", "")}
"""
            )

        evidence_block = "\n".join(evidence_text)

        prompt = f"""
Research question:

{question}

External web search results:

{evidence_block}

Using ONLY the supplied search results, produce a structured
research result.

Important:

- Do not invent information.
- Do not invent publication dates.
- Do not invent update dates.
- Do not invent URLs.
- Do not claim that something is "latest" unless the supplied
  evidence supports that conclusion.
- Prefer FDA/NCI/NIH/government sources when available.
- If sources disagree, explicitly mention the conflict.
- If the evidence is insufficient, say so.

STRICT EVIDENCE-TO-CLAIM RULES:

- Every claim must be directly supported by at least one
  supplied search result.
- Never introduce a drug, approval, cancer type, biomarker,
  indication, or treatment that is not explicitly supported
  by the supplied evidence.
- Do not use a source about general skin cancer to establish
  an FDA approval for melanoma.
- Do not use an approval for a different cancer or tumour
  type as evidence of a melanoma approval.
- Exclude irrelevant sources from the claims and summary.
- Do not claim that sources disagree merely because some
  search results are irrelevant.
- If only one relevant approval is found, describe it as
  the relevant approval found in the searched sources.
- If the evidence does not establish which approval is latest,
  explicitly state that the latest approval cannot be confirmed.
CLAIM CITATION RULES:

- Every claim MUST end with at least one source reference in this exact format: [SOURCE 1].
- Use only source numbers that actually appear in the supplied search results.
- Do not create a claim if the supplied sources do not support it.
- A claim about an FDA approval must preserve the exact drug name, approval type,
  combination treatment, patient eligibility, and relevant treatment history
  supported by the source.
- Keep the treatment combination separate from the patient's eligibility criteria.
- Never invent a source reference just to satisfy this requirement.

Example:
[
  "The FDA granted accelerated approval to Drug X in combination with Drug Y for the specific patient population described in SOURCE 1. [SOURCE 1]"
]

CRITICAL MEDICAL EVIDENCE RULES:

- When reporting an FDA approval, preserve the complete approved indication
  as stated in the FDA source.
- Include relevant patient eligibility restrictions, disease stage,
  prior-treatment requirements, and combination-treatment requirements.
- Never generalize an approval for a specific patient population to all
  patients with that cancer.
- Do not omit restrictions simply to make the summary shorter.
- If the search snippet does not provide the complete indication, state
  that the complete indication must be checked on the FDA page.
- Distinguish an FDA approval from clinical-trial results, investigational
  treatments, and off-label use.
- Do not describe a treatment as the latest unless the evidence
  establishes that conclusion.

Return JSON with exactly these fields:

{{
    "summary": "short evidence-based summary",
    "claims": [
        "supported claim 1 [SOURCE 1]",
        "supported claim 2 [SOURCE 2]"
    ],
    "uncertainties": [
        "uncertainty 1"
    ],
    "currentness": "CURRENT / POSSIBLY_CURRENT / OUTDATED / UNKNOWN"
}}

Do NOT return a sources field.
Python will attach the original supplied sources separately.
"""

        # ---------------------------------------------------------
        # 5. Ask local Qwen3 to structure the evidence
        # ---------------------------------------------------------

        raw_response = ask_ollama(prompt)
        parsed = json.loads(raw_response)
        result = ResearchResult(
            summary=parsed.get("summary", ""),
            claims=parsed.get("claims", []),
            sources=[
                ResearchSource(
                    title=source.get("title", ""),
                    organization="FDA / Government / Medical source",
                    url=source.get("url", ""),
                    publication_date="",
                    updated_date="",
                    source_type="external web search",
                )
                for source in unique_results
            ],
            uncertainties=parsed.get("uncertainties", []),
            currentness=parsed.get("currentness", "UNKNOWN"),
        )

        # ---------------------------------------------------------
        # Deterministic source-reference validation
        # ---------------------------------------------------------
        import re

        valid_source_numbers = set(range(1, len(unique_results) + 1))
        validated_claims = []

        for claim in result.claims:
            references = re.findall(
                r"\[SOURCE\s+(\d+)\]",
                claim,
                flags=re.IGNORECASE,
            )

            # Reject claims without source references.
            if not references:
                result.uncertainties.append(
                    f"A claim was excluded because it had no source reference: "
                    f"{claim}"
                )
                continue

            # Reject claims referencing nonexistent sources.
            referenced_numbers = {
                int(number) for number in references
            }

            if not referenced_numbers.issubset(valid_source_numbers):
                result.uncertainties.append(
                    f"A claim was excluded because it referenced an invalid "
                    f"source number: {claim}"
                )
                continue

            validated_claims.append(claim)

        result.claims = validated_claims

        # ---------------------------------------------------------
        # Deterministic currentness safeguard
        # ---------------------------------------------------------
        latest_keywords = [
            "latest",
            "current",
            "newest",
            "most recent",
            "up-to-date",
        ]
        question_lower = question.lower()
        is_currentness_question = any(
            keyword in question_lower
            for keyword in latest_keywords
        )

        if is_currentness_question:
            result.currentness = "POSSIBLY_CURRENT"
            result.uncertainties.append(
                "The searched sources contain relevant information, "
                "but the available search evidence does not establish "
                "that no newer relevant approval or development exists."
            )

            # Avoid presenting an unverified absence of newer
            # approvals as an established fact.
            unsupported_latest_phrases = [
                "no later approval was found",
                "no newer approval was found",
                "this is the latest approval",
                "this is definitively the latest",
                "no newer development exists",
            ]
            for phrase in unsupported_latest_phrases:
                if phrase in result.summary.lower():
                    result.summary = (
                        result.summary.replace(
                            phrase,
                            "no later relevant approval was established "
                            "by the available search evidence",
                        )
                    )

        return result

    except Exception as error:
        print()
        print("=" * 70)
        print("RESEARCH AGENT - LOCAL RESEARCH UNAVAILABLE")
        print("=" * 70)
        print(f"Reason: {error}")

        return ResearchResult(
            summary=(
                "External research could not be completed reliably."
            ),
            claims=[],
            sources=[],
            uncertainties=[
                "The Research Agent encountered an error.",
                "Current information could not be independently verified.",
            ],
            currentness="UNKNOWN",
        )


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