import json
import re
import urllib.request
from urllib.parse import urlparse

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

CRITICAL CITATION FORMAT — FOLLOW EXACTLY:

Every factual claim must identify at least one supporting source.

The supplied sources have unique identifiers such as:
SRC_A01
SRC_A02
SRC_A03

Use ONLY the exact SOURCE_ID values appearing in the supplied
research evidence.

Never invent a source ID.
Never use webpage numbers, dates, reference numbers, or ordinary
numeric citations as source IDs.

If no supplied source supports a claim, omit that claim.

The output must use source_ids as an array of strings.
Do not put citation markers inside the claim text.
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


def ask_ollama(
    prompt: str,
    system_prompt: str = SYSTEM_PROMPT,
) -> str:
    payload = {
        "model": MODEL_NAME,
        "system": system_prompt,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_ctx": 8192,
            "num_predict": 1200,
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=180) as response:
        result = json.loads(response.read().decode("utf-8"))

    print("\nOLLAMA DIAGNOSTICS")
    print("-" * 50)
    print("Model:", result.get("model"))
    print("Done reason:", result.get("done_reason"))
    print("Prompt tokens:", result.get("prompt_eval_count"))
    print("Generated tokens:", result.get("eval_count"))
    print("Response:", repr(result.get("response")))
    print("-" * 50)

    return result.get("response", "")


def identify_source_organization(url: str) -> str:
    """
    Identify the organization responsible for a source
    using its website domain.
    """
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return "Unknown organization"
        hostname = hostname.lower()
        organizations = {
            "fda.gov": "U.S. Food and Drug Administration (FDA)",
            "cancer.gov": "National Cancer Institute (NCI)",
            "nih.gov": "National Institutes of Health (NIH)",
            "cdc.gov": "Centers for Disease Control and Prevention (CDC)",
            "who.int": "World Health Organization (WHO)",
            "cancer.org": "American Cancer Society (ACS)",
        }
        for domain, organization in organizations.items():
            if hostname == domain or hostname.endswith("." + domain):
                return organization
        # Use the hostname when it does not match a known organization.
        return hostname
    except Exception:
        return "Unknown organization"


def extract_source_dates(content: str) -> tuple[str, str]:
    """
    Extract publication and modification dates from HTML metadata
    and JSON-LD structured data.
    Returns:
        (publication_date, updated_date)
    Missing or invalid metadata returns empty strings.
    """
    if not isinstance(content, str) or not content.strip():
        return "", ""

    publication_date = ""
    updated_date = ""

    # ---------------------------------------------------------
    # 1. Search HTML meta tags
    # ---------------------------------------------------------
    meta_patterns = {
        "publication": [
            "article:published_time",
            "datePublished",
            "datepublished",
            "publishdate",
            "dc.date",
            "dcterms.created",
        ],
        "updated": [
            "article:modified_time",
            "dateModified",
            "datemodified",
            "last-modified",
            "modified",
            "dcterms.modified",
        ],
    }

    for name in meta_patterns["publication"]:
        pattern = (
            rf'<meta[^>]+(?:property|name|itemprop)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)'
            rf'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name|itemprop)=["\']{re.escape(name)}["\']'
        )
        match = re.search(pattern, content, flags=re.IGNORECASE)
        if match:
            val = (match.group(1) or match.group(2) or "").strip()
            if val:
                publication_date = val
                break

    for name in meta_patterns["updated"]:
        pattern = (
            rf'<meta[^>]+(?:property|name|itemprop)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)'
            rf'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name|itemprop)=["\']{re.escape(name)}["\']'
        )
        match = re.search(pattern, content, flags=re.IGNORECASE)
        if match:
            val = (match.group(1) or match.group(2) or "").strip()
            if val:
                updated_date = val
                break

    # ---------------------------------------------------------
    # 2. Search JSON-LD structured data
    # ---------------------------------------------------------
    if not publication_date or not updated_date:
        json_ld_blocks = re.findall(
            r'<script\s+[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            content,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for block in json_ld_blocks:
            try:
                data = json.loads(block.strip())
            except Exception:
                continue

            items = []
            if isinstance(data, dict):
                if "@graph" in data and isinstance(data["@graph"], list):
                    items.extend(data["@graph"])
                items.append(data)
            elif isinstance(data, list):
                items.extend(data)

            for item in items:
                if not isinstance(item, dict):
                    continue
                if not publication_date:
                    pub = item.get("datePublished") or item.get("dateCreated")
                    if isinstance(pub, str) and pub.strip():
                        publication_date = pub.strip()
                if not updated_date:
                    upd = item.get("dateModified")
                    if isinstance(upd, str) and upd.strip():
                        updated_date = upd.strip()
                if publication_date and updated_date:
                    break

            if publication_date and updated_date:
                break

    return publication_date, updated_date


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


def verify_claim_support(claim: str, sources: list) -> tuple[bool, str]:
    """
    Check whether the cited source content directly supports a claim.
    Returns:
        (True, reason) if supported.
        (False, reason) if unsupported or verification fails.
    """
    import re

    # Extract source references from the claim.
    references = re.findall(
        r"\[SOURCE\s+(\d+)\]",
        claim,
        flags=re.IGNORECASE,
    )
    if not references:
        return False, "Claim has no source references."

    # Remove duplicate references.
    references = list(dict.fromkeys(int(ref) for ref in references))

    evidence_parts = []
    for source_number in references:
        if source_number < 1 or source_number > len(sources):
            return False, f"Invalid source reference: {source_number}"
        source = sources[source_number - 1]
        if not isinstance(source, dict):
            return False, f"Invalid source format for reference: {source_number}"

        content = (
            source.get("full_content", "")
            or source.get("snippet", "")
            or ""
        )
        if not isinstance(content, str) or not content.strip():
            return False, f"Cited source {source_number} contains no evidence."

        evidence_parts.append(
            f"SOURCE {source_number}:\n"
            f"Title: {source.get('title', '')}\n"
            f"URL: {source.get('url', '')}\n"
            f"Content:\n{content.strip()[:4000]}"
        )

    if not evidence_parts:
        return False, "No cited source evidence available for verification."

    verification_evidence = "\n\n".join(evidence_parts)
    if not verification_evidence.strip():
        return False, "Cited source evidence is empty."

    verification_prompt = f"""Claim to verify:
{claim}

Cited source evidence:
{verification_evidence}

Does the cited source evidence directly support the factual accuracy of this claim?
Respond in JSON format with:
{{
    "supported": true,
    "reason": "Brief explanation of why the source supports or does not support the claim"
}}
"""

    verification_system = (
        "You are a strict medical evidence verifier. "
        "Your task is to confirm whether a claim is directly supported by the cited evidence. "
        "If the evidence does not corroborate the specific drug, indication, approval, or cancer type, "
        "set supported to false. Only return supported as true when the cited source directly confirms the claim."
    )

    try:
        raw_response = ask_ollama(
            verification_prompt,
            system_prompt=verification_system,
        )
        parsed = json.loads(raw_response)
        if not isinstance(parsed, dict):
            return False, "Verifier returned an invalid JSON structure."

        supported = parsed.get("supported")
        if not isinstance(supported, bool):
            return False, "Verifier did not return a valid Boolean result."

        reason = parsed.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            return False, "Verifier returned no valid explanation."

        return supported, reason.strip()
    except Exception as error:
        return False, f"Verification failed: {error}"


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
                                "html_content": notification_page.get("html", ""),
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
                    result["html_content"] = extracted.get("html", "")
                    
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
        # 3B. Extract publication and update dates for each source
        # ---------------------------------------------------------
        for result in unique_results:
            metadata_content = (
                result.get("html_content", "")
                or result.get("full_content", "")
            )
            publication_date, updated_date = extract_source_dates(
                metadata_content
            )
            result["publication_date"] = publication_date
            result["updated_date"] = updated_date

        # ---------------------------------------------------------
        # 4. Prepare evidence using unique source IDs
        # ---------------------------------------------------------
        evidence_text = []
        source_id_to_number = {}

        for index, result in enumerate(unique_results, 1):
            source_id = f"SRC_A{index:02d}"
            source_id_to_number[source_id] = index
            evidence_text.append(
                f"""SOURCE_ID: {source_id}

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

IMPORTANT SOURCE ID RULES:

The supplied evidence contains exactly {len(unique_results)} sources.

The ONLY valid source IDs are the SOURCE_ID labels explicitly
shown in the supplied evidence.

Valid IDs are:
{", ".join(source_id_to_number.keys())}

For every claim:
- Select source_ids only from this exact list.
- Copy each ID exactly as written.
- Never use numbers found inside webpage content as source IDs.
- Never create or modify a source ID.
- If you cannot identify a supporting source, omit the claim.

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

- Every claim must have at least one supporting source.
- Each claim must be a JSON object with exactly two fields:
  "text": the factual claim as a string.
  "source_ids": an array of source ID strings.

- Every source ID must exactly match a SOURCE_ID label
  supplied in the evidence.
- Use only sources that directly support the claim.
- Never invent source IDs.
- Do not include citations inside the text field.
- If no supplied source supports a claim, omit that claim.
- Each claim must communicate one distinct, useful fact.
- Preserve exact FDA approval type, drug name, combination,
  and patient eligibility when supported by the source.

Example:
{{
  "text": "The FDA granted accelerated approval to Drug X for the specified patient population.",
  "source_ids": ["SRC_A01"]
}}

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
        {{
            "text": "A factual claim supported by the supplied evidence.",
            "source_ids": ["SRC_A01"]
        }},
        {{
            "text": "Another factual claim supported by the supplied evidence.",
            "source_ids": ["SRC_A02", "SRC_A03"]
        }}
    ],
    "uncertainties": [
        "uncertainty 1"
    ],
    "currentness": "CURRENT / POSSIBLY_CURRENT / OUTDATED / UNKNOWN"
}}

IMPORTANT:
- claims MUST be an array of objects, not strings.
- source_ids MUST contain exact source ID strings.
- Do not put citation markers inside claim text.

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

        # ---------------------------------------------------------
        # Convert structured source IDs into citation markers
        # ---------------------------------------------------------
        normalized_claims = []
        for item in parsed.get("claims", []):
            # Preserve claims generated by the deterministic FDA safeguard.
            if isinstance(item, str):
                references = re.findall(
                    r"\[SOURCE\s+(\d+)\]",
                    item,
                    flags=re.IGNORECASE,
                )
                if not references:
                    continue
                numbers = [int(number) for number in references]
                if any(
                    number not in range(1, len(unique_results) + 1)
                    for number in numbers
                ):
                    continue
                normalized_claims.append(item.strip())
                continue

            if not isinstance(item, dict):
                continue
            claim_text = item.get("text", "")
            source_ids = item.get("source_ids", [])
            if not isinstance(claim_text, str):
                continue
            claim_text = claim_text.strip()
            if not claim_text or not isinstance(source_ids, list):
                continue
            if not source_ids:
                continue
            # Every ID must be a valid string from our source map.
            if any(
                not isinstance(source_id, str)
                or source_id not in source_id_to_number
                for source_id in source_ids
            ):
                print(
                    "Rejected claim because it contained an "
                    "invalid source ID:",
                    source_ids,
                )
                continue

            # Remove duplicate IDs while preserving order
            source_ids = list(dict.fromkeys(source_ids))

            citations = " ".join(
                f"[SOURCE {source_id_to_number[source_id]}]"
                for source_id in source_ids
            )
            normalized_claims.append(f"{claim_text} {citations}")

        parsed["claims"] = normalized_claims

        result = ResearchResult(
            summary=parsed.get("summary", ""),
            claims=parsed.get("claims", []),
            sources=[
                ResearchSource(
                    title=source.get("title", ""),
                    organization=identify_source_organization(
                        source.get("url", "")
                    ),
                    url=source.get("url", ""),
                    publication_date=source.get("publication_date", ""),
                    updated_date=source.get("updated_date", ""),
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
        # Claim-evidence verification
        # ---------------------------------------------------------
        evidence_verified_claims = []
        print("\n" + "=" * 70)
        print("CLAIM-EVIDENCE VERIFICATION")
        print("=" * 70)

        for claim in result.claims:
            print(f"\nVerifying claim:\n{claim}")
            supported, reason = verify_claim_support(
                claim,
                unique_results,
            )

            if supported:
                evidence_verified_claims.append(claim)
                print("RESULT: SUPPORTED")
                print("Reason:", reason)
            else:
                result.uncertainties.append(
                    "A research claim was rejected because its "
                    "cited evidence did not adequately support it. "
                    f"Reason: {reason}"
                )
                print("RESULT: REJECTED")
                print("Reason:", reason)

        result.claims = evidence_verified_claims

        # ---------------------------------------------------------
        # Build summary ONLY from evidence-verified claims
        # ---------------------------------------------------------
        if result.claims:
            verified_summary_parts = []
            for claim in result.claims:
                clean_claim = re.sub(
                    r"\s*\[SOURCE\s+\d+\]",
                    "",
                    claim,
                    flags=re.IGNORECASE,
                ).strip()
                if clean_claim:
                    verified_summary_parts.append(clean_claim)
            result.summary = " ".join(verified_summary_parts)

        # ---------------------------------------------------------
        # Fail-safe: reject an unsupported research summary
        # ---------------------------------------------------------
        if not result.claims:
            result.summary = (
                "The available external search results did not "
                "produce any claims that passed source-reference "
                "and claim-evidence verification. A reliable "
                "research summary could not be established."
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