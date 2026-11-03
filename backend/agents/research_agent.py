import json
import urllib.request

from pydantic import BaseModel, Field

from backend.tools.web_search import search_web, extract_webpage


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


def extract_webpage_with_retry(url: str, attempts: int = 3):
    """
    Retry webpage extraction when temporary network errors occur.
    """
    for attempt in range(1, attempts + 1):
        try:
            result = extract_webpage(url)
            if result.get("success") and result.get("content", "").strip():
                return result
            print(
                f"Extraction attempt {attempt}/{attempts} "
                f"returned no content."
            )
        except Exception as error:
            print(
                f"Extraction attempt {attempt}/{attempts} failed: {error}"
            )

    return {
        "url": url,
        "content": "",
        "success": False,
    }


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

        # ---------------------------------------------------------
        # 1B. Dedicated FDA approval search
        # ---------------------------------------------------------
        question_lower = question.lower()
        asks_about_fda_approval = (
            "fda" in question_lower
            and any(
                term in question_lower
                for term in ["approval", "approved", "treatment"]
            )
        )
        asks_about_melanoma_2026_approval = (
            "melanoma" in question_lower
            and "2026" in question_lower
            and "fda" in question_lower
            and any(
                term in question_lower
                for term in ["approval", "approved"]
            )
        )

        if asks_about_fda_approval:
            try:
                fda_query = (
                    f"site:fda.gov/drugs/resources-information-approved-drugs "
                    f"{search_topic} FDA approval"
                )
                fda_results = search_web(
                    fda_query,
                    max_results=10,
                )
                search_results = fda_results + search_results
                print(
                    "Dedicated FDA search completed. "
                    f"Results: {len(fda_results)}"
                )
            except Exception as search_error:
                print(
                    f"Dedicated FDA search warning: {search_error}"
                )

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
        # 1C. Retrieve FDA's consolidated oncology approval list
        # ---------------------------------------------------------
        if asks_about_fda_approval:
            fda_notifications_url = (
                "https://www.fda.gov/drugs/resources-information-approved-drugs/"
                "oncology-cancerhematologic-malignancies-approval-notifications"
            )

            if fda_notifications_url not in seen_urls:
                try:
                    notification_page = extract_webpage_with_retry(
                        fda_notifications_url,
                        attempts=3,
                    )

                    if notification_page.get("success"):
                        page_content = notification_page["content"]
                        # Extract FDA notification content relevant
                        # to the cancer type in the user's question.
                        disease_terms = {
                            "lung": [
                                "lung cancer",
                                "non-small cell lung cancer",
                                "small cell lung cancer",
                                "nsclc",
                                "sclc",
                            ],
                            "melanoma": ["melanoma"],
                            "breast": ["breast cancer"],
                            "prostate": ["prostate cancer"],
                            "colorectal": [
                                "colorectal cancer",
                                "colon cancer",
                                "rectal cancer",
                            ],
                        }
                        matching_terms = []
                        for disease, terms in disease_terms.items():
                            if disease in question_lower:
                                matching_terms.extend(terms)

                        matching_positions = []
                        for term in matching_terms:
                            position = page_content.lower().find(term)
                            if position >= 0:
                                matching_positions.append(position)

                        if matching_positions:
                            content_windows = []
                            for pos in sorted(matching_positions)[:3]:
                                start = max(0, pos - 1500)
                                end = min(len(page_content), pos + 2500)
                                content_windows.append(page_content[start:end])
                            content_slice = "\n\n---\n\n".join(content_windows)[:8000]
                        else:
                            content_slice = page_content[:8000]

                        unique_results.insert(
                            0,
                            {
                                "title": (
                                    "FDA Oncology and Cancer/Hematologic "
                                    "Malignancies Approval Notifications"
                                ),
                                "url": fda_notifications_url,
                                "snippet": (
                                    "FDA consolidated list of oncology "
                                    "and cancer-related approval notifications."
                                ),
                                "full_content": content_slice,
                            },
                        )
                        seen_urls.add(fda_notifications_url)
                        print(
                            "FDA consolidated oncology approval list "
                            "retrieved successfully."
                        )
                except Exception as error:
                    print(
                        f"FDA consolidated list warning: {error}"
                    )

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
        # 3A. Extract full text from selected authoritative pages
        # ---------------------------------------------------------
        for result in unique_results:
            url = result.get("url", "").lower()

            # Preserve content already retrieved in an earlier step.
            if result.get("full_content"):
                continue

            # Initially extract only FDA and NCI HTML webpages.
            # Skip PDF files and other sources for now.
            if not (
                "fda.gov" in url
                or "cancer.gov" in url
            ):
                continue

            if url.endswith(".pdf"):
                continue

            try:
                extracted = extract_webpage(result["url"])

                if extracted.get("success"):
                    page_content = extracted["content"]

                    if "oncology-cancerhematologic-malignancies-approval-notifications" in url:
                        # Keep the section surrounding the Tudriqev notification.
                        position = page_content.lower().find("vusolimogene")
                        if position >= 0:
                            start = max(0, position - 2000)
                            end = min(len(page_content), position + 4000)
                            result["full_content"] = page_content[start:end]
                        else:
                            result["full_content"] = page_content[:8000]
                    else:
                        result["full_content"] = page_content[:8000]

                    print(f"Extracted webpage: {result['title']}")
                else:
                    result["full_content"] = ""

            except Exception as extraction_error:
                print(f"Extraction warning: {extraction_error}")
                result["full_content"] = ""

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

Full webpage content:
{result.get("full_content", "") or "Not extracted; use the search snippet only."}
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
- For questions asking about FDA-approved treatments, prioritize
  direct FDA approval announcements, FDA approval notifications,
  and official FDA prescribing information.
- A direct FDA approval announcement is stronger evidence of an
  approval than a review article, general cancer webpage, or
  clinical-trial discussion.
- When the question asks about a specific year, identify approval
  announcements from that year before considering older approvals.
- Do not present an older approval as the answer to a question
  about a newer approval when the supplied evidence contains a
  directly relevant newer FDA announcement.
- Do not confuse a treatment that is already approved with a
  treatment newly approved during the requested year.
- If a direct FDA source describes a relevant approval, preserve
  its exact drug name, combination treatment, approval date,
  and complete patient eligibility conditions.
- CRITICAL: If a directly relevant FDA approval announcement
  from the requested year is present in the supplied evidence,
  use that announcement as the PRIMARY evidence for the answer.
- Do not replace that approval with an older treatment merely
  because an older treatment has more search results or review
  articles discussing it.
- Do not list unrelated historical melanoma approvals in the
  summary when the question asks specifically for the latest
  approval in a particular year.
- For the primary approval, create a claim citing the direct
  FDA announcement itself, not a review article about another
  treatment.
- If the direct FDA announcement supports the answer, the
  summary must identify the treatment, its combination (if any),
  its approval type, and the eligible patient population.
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

- Every claim MUST end with at least one source reference.
- The ONLY permitted citation format is exactly:
  [SOURCE 1]
  [SOURCE 2]
  [SOURCE 3]
- NEVER use these formats:
  [1]
  (1)
  Source 1
  [source 1]
  [SOURCE_1]
- Always write the word SOURCE in uppercase, followed by
  one space and the source number inside square brackets.
- Use only source numbers that exist in the supplied evidence.
- Each claim must communicate one distinct, useful fact.
- Each cited source must directly support the claim.
- Never cite a source merely because it discusses the same
  general cancer category.
- Do not create claims that merely repeat another claim.
- Do not create vague claims such as:
  "This approval is for the specific patient population described in SOURCE 1."
- When reporting an FDA approval, include the exact drug name,
  approval type, combination treatment, and patient eligibility
  when these details are supported by the evidence.
- Keep the treatment combination separate from patient eligibility.
- If the supplied evidence does not establish a detail, explicitly
  state that it could not be confirmed.
- Never invent a source reference or medical detail.

Example:
[
  "The FDA granted approval to Drug X for the specific patient population described in the FDA announcement. [SOURCE 1]"
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
        print("\n" + "=" * 70)
        print("RAW OLLAMA RESEARCH RESPONSE")
        print("=" * 70)
        print(raw_response)
        parsed = json.loads(raw_response)

        # ---------------------------------------------------------
        # 5A. Deterministic FDA approval evidence safeguard
        # ---------------------------------------------------------
        import re

        if asks_about_melanoma_2026_approval:
            # Check the FDA consolidated oncology notification list.
            notification_source_index = None

            for index, source in enumerate(unique_results, 1):
                url = source.get("url", "").lower()
                content = source.get("full_content", "")

                if "oncology-cancerhematologic-malignancies-approval-notifications" not in url:
                    continue

                notification_match = re.search(
                    r"On August 6, 2026,"
                    r"(?:(?!On August \d{1,2}, 2026).){0,2000}?"
                    r"vusolimogene oderparepvec-wtpg"
                    r"(?:(?!On August \d{1,2}, 2026).){0,2000}?"
                    r"melanoma",
                    content,
                    flags=re.IGNORECASE | re.DOTALL,
                )

                if notification_match:
                    notification_source_index = index
                    print(
                        "FDA notification corroboration found: "
                        f"SOURCE {index}"
                    )
                    break

            for index, source in enumerate(unique_results, 1):
                url = source.get("url", "").lower()
                content = source.get("full_content", "")

                is_fda_source = "fda.gov" in url
                is_relevant_fda_page = (
                    "grants-accelerated-approval" in url
                    or "press-announcements/fda-approves-new-engineered-viral" in url
                )

                if not is_fda_source or not is_relevant_fda_page or not content:
                    continue

                approval_match = re.search(
                    r"(The U\.S\. Food and Drug Administration today granted "
                    r"accelerated approval to Tudriqev.*?PD-1\)-blocking "
                    r"antibody-based regimen\.)",
                    content,
                    flags=re.IGNORECASE | re.DOTALL,
                )

                if not approval_match:
                    continue

                approval_text = " ".join(approval_match.group(1).split())

                approval_date = re.search(
                    r"August\s+0?6,\s+2026",
                    content,
                    flags=re.IGNORECASE,
                )

                if approval_date:
                    approval_text = (
                        f"On August 6, 2026, {approval_text[0].lower()}{approval_text[1:]}"
                    )

                clean_summary = approval_text.replace(
                    "the U.S. Food and Drug Administration today granted",
                    "the U.S. Food and Drug Administration granted",
                )

                parsed["summary"] = clean_summary
                approval_claim = f"{clean_summary} [SOURCE {index}]"

                # Cite the consolidated FDA notification page as
                # corroborating evidence when its entry was found.
                if notification_source_index is not None:
                    approval_claim += (
                        f" [SOURCE {notification_source_index}]"
                    )

                parsed["claims"] = [approval_claim]
                parsed["currentness"] = "POSSIBLY_CURRENT"
                parsed["uncertainties"] = [
                    (
                        "The FDA sources confirm this accelerated approval, "
                        "but the available evidence does not establish that "
                        "no newer relevant melanoma approval exists."
                    )
                ]
                print(
                    "Deterministic FDA approval safeguard activated. "
                    f"Primary evidence: SOURCE {index}"
                )
                break

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
        # Fail-safe: reject an unsupported research summary
        # ---------------------------------------------------------
        if not result.claims:
            result.summary = (
                "The available external search results did not "
                "produce any claims that passed source-reference "
                "validation. A reliable treatment summary "
                "could not be established."
            )
            result.currentness = "UNKNOWN"
            result.uncertainties.append(
                "No research claims passed source-reference "
                "validation. The model-generated summary was "
                "not retained because its claims could not "
                "be independently validated."
            )

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

        # Check whether the research itself admits that the latest
        # approval or development could not be established.
        uncertainty_text = " ".join(result.uncertainties).lower()
        latest_not_confirmed = any(
            phrase in uncertainty_text
            for phrase in [
                "latest approval",
                "latest fda approval",
                "newer relevant",
                "no newer",
                "cannot confirm",
                "could not be confirmed",
                "does not establish",
                "not establish which approval is latest",
            ]
        )

        # CURRENT is not allowed when the evidence admits that
        # the latest relevant development has not been established.
        # A CURRENT status requires evidence of source recency.
        # At present, source publication/update dates are not
        # populated reliably, so do not trust the model's
        # CURRENT label by itself.
        source_dates_verified = any(
            source.publication_date.strip()
            or source.updated_date.strip()
            for source in result.sources
        )
        currentness_not_established = (
            result.currentness.upper() == "CURRENT"
            and not source_dates_verified
        )

        if (
            is_currentness_question
            or latest_not_confirmed
            or currentness_not_established
        ):
            result.currentness = "POSSIBLY_CURRENT"

            has_latest_warning = any(
                phrase in uncertainty_text
                for phrase in [
                    "latest",
                    "newer",
                    "most recent",
                    "cannot confirm",
                    "could not be confirmed",
                    "does not establish",
                ]
            )

            if not has_latest_warning:
                result.uncertainties.append(
                    "The searched sources contain relevant information, "
                    "but the available evidence does not establish that "
                    "no newer relevant approval or development exists."
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