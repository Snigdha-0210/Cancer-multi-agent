import json
import re
import urllib.request


# ============================================================
# SETTINGS
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"



SYSTEM_PROMPT = """
You are the verification agent for a cancer information assistant.

Your job is to determine whether a proposed answer is adequately
supported by the evidence supplied to you.

You are NOT the final medical decision-maker.

IMPORTANT VERIFICATION RULES:

1. Evaluate the factual claims actually made in the proposed answer.

2. Check each important claim against the supplied evidence.
   Do not assume a claim is true merely because another agent stated it.

3. Do not invent facts or use your own medical knowledge to fill
   gaps in the evidence.

4. Check whether the answer accurately represents the source,
   including its title, date, page, and findings when provided.

5. Pay attention to source quality and publication dates.

6. CURRENTNESS:
   - If the user asks for latest, current, recent, or a specific year,
     verify that the evidence is sufficiently recent.
   - Older sources may support historical or general background facts.
   - Do not treat an old source as proof of current medical guidance.
   - Do not fail an answer solely because a source is old when the
     claim is a general background fact and currentness is not required.

7. PATIENT POPULATION:
   Check whether treatment claims are restricted to the population
   supported by the evidence, including relevant stage, age,
   previous treatment, and disease characteristics.

8. Check whether important limitations, uncertainty, warnings,
   or accelerated-approval status have been omitted.

9. Do not diagnose patients or prescribe treatment.

10. Do not automatically require every fact appearing in the
    evidence to be included in the proposed answer.

11. MISSING INFORMATION:
    - List only information genuinely necessary to answer the
      user's specific question.
    - Do not list unrelated statistics, numbers, or details merely
      because they appear in the evidence.
    - Do not demand exact numerical values unless the user asked
      for them or the proposed answer makes a numerical claim
      that requires verification.
    - If the question is about risk factors, do not demand annual
      case counts, death counts, or unrelated epidemiological
      statistics.
    - Do not mark a supported answer as incomplete merely because
      it does not mention every detail in the supplied evidence.
    - If an important omission changes the meaning or safety of
      the answer, identify it.

12. Keep each output array concise. Include at most five of the
    most important entries in each array.

13. If the evidence is insufficient for an important claim,
    mark the answer as FAIL rather than guessing.

CRITICAL OUTPUT RULE:

Return ONLY valid JSON.

Do not return Markdown.
Do not return explanations outside the JSON.
Do not use code fences.
Do not add text before or after the JSON.

The JSON MUST have exactly these fields:

{
  "verdict": "PASS" or "FAIL",
  "confidence": "HIGH" or "MEDIUM" or "LOW",
  "supported_claims": [],
  "unsupported_or_problematic_claims": [],
  "missing_information": [],
  "recommended_action": "PASS" or "RESEARCH" or "REVISE"
}

VERDICT RULES:

PASS:
Use when the important claims in the proposed answer are adequately
supported by the supplied evidence, and no essential information
or safety limitation is missing.

FAIL:
Use when an important claim is unsupported, contradicted,
misrepresented, insufficiently current for the user's request,
or missing essential information that changes the answer.

RECOMMENDED ACTION:

PASS:
The answer can proceed.

RESEARCH:
Additional evidence or more current evidence is required.

REVISE:
The answer needs correction using the supplied evidence.

CONFIDENCE:

HIGH:
The evidence clearly supports the verification decision.

MEDIUM:
The evidence supports the decision but has some limitations.

LOW:
The evidence is incomplete, ambiguous, or insufficient.

FINAL REMINDER:

Judge the proposed answer ONLY against the supplied evidence
and the user's actual question.

STRICT OUTPUT RULES:

- Evaluate only claims actually made in the proposed answer.
- Do not list facts that the answer was never asked to provide.
- Do not request exact statistics unless the question asks for statistics.
- Set missing_information to [] unless a specific omission prevents
  the answer from correctly answering the user's question or creates
  a safety issue.
- Never list more than 5 items in any output array.
- Keep each item to one short sentence.
- Return one complete valid JSON object.

Do not demand irrelevant information.
Do not invent replacement facts.

CLAIM-BY-CLAIM VERIFICATION PROCEDURE:

1. First identify the exact question being answered and its scope.

2. Read the PROPOSED ANSWER and identify its actual factual claims.
   Evaluate those claims, not random facts from the evidence.

3. For every important claim in the proposed answer:
   - Identify the corresponding supporting evidence.
   - Check whether the evidence genuinely supports the claim.
   - Check whether the answer exaggerates or changes the evidence.
   - Record unsupported or contradicted claims when necessary.

4. SUPPORTED CLAIMS must describe claims actually present in the
   proposed answer. Do not copy unrelated facts from the evidence.

5. MISSING INFORMATION must be relevant to the user's question.
   For example, when asked about melanoma risk factors:
   - Do not demand annual case counts.
   - Do not demand death statistics.
   - Do not demand unrelated survival statistics.
   - Consider whether important risk factors from the evidence
     have been omitted, but do not require every minor detail.

6. QUESTION-SCOPE CHECK:
   The answer must address what the user actually asked.
   Do not evaluate it as though the user asked a different question.

7. FINAL DECISION:
   - PASS if the important claims are supported and the answer
     adequately addresses the question.
   - FAIL if an important claim is unsupported, contradicted,
     misleading, or essential information is missing.
   - REVISE when the supplied evidence is sufficient to correct
     the answer.
   - RESEARCH when additional evidence is genuinely necessary.

8. Before returning JSON, check that every item in
   supported_claims and unsupported_or_problematic_claims
   refers to something actually stated in the proposed answer.

Do not approve unsupported medical claims.
"""



def ask_ollama(
    system_prompt: str,
    user_prompt: str,
    output_schema: dict | None = None,
) -> str:
    payload = {
        "model": MODEL_NAME,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
        "format":output_schema or {
            "type": "object",
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": ["PASS", "FAIL"],
                },
                "confidence": {
                    "type": "string",
                    "enum": ["HIGH", "MEDIUM", "LOW"],
                },
                "supported_claims": {
    "type": "array",
    "items": {"type": "string"},
    "maxItems": 5,
},
"unsupported_or_problematic_claims": {
    "type": "array",
    "items": {"type": "string"},
    "maxItems": 5,
},
"missing_information": {
    "type": "array",
    "items": {"type": "string"},
    "maxItems": 5,
},
                "recommended_action": {
                    "type": "string",
                    "enum": ["PASS", "RESEARCH", "REVISE"],
                },
            },
            "required": [
                "verdict",
                "confidence",
                "supported_claims",
                "unsupported_or_problematic_claims",
                "missing_information",
                "recommended_action",
            ],
            "additionalProperties": False,
        },
        "options": {
            "temperature": 0,
            "num_predict": 1000,
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result["response"]


def extract_claims(proposed_answer: str) -> str:
    """
    Extract factual statements without rewriting them.

    Supports:
    - Bullet-point answers
    - Numbered lists
    - Ordinary paragraphs

    Original wording is preserved to avoid changing medical meaning.
    """

    claims = []

    lines = proposed_answer.splitlines()

    ignored_headings = {
        "sources:",
        "references:",
        "disclaimer:",
    }

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Ignore heading-only lines.
        if line.endswith(":"):
            continue

        # Ignore headings and source-list entries.
        if line.lower() in ignored_headings:
            continue

        if line.lower().startswith(
            ("source:", "document:", "reference:")
        ):
            continue

        # Remove common bullet and numbered-list markers.
        line = re.sub(
            r"^\s*(?:[-*•]|\d+[.)])\s*",
            "",
            line,
        ).strip()
        # Ignore source citations after removing bullet markers.
        if re.match(
            r"^(source|document|reference)\b",
            line,
            re.IGNORECASE,
        ):
            continue

        # Ignore PDF filenames and page references in source lists.
        if ".pdf" in line.lower() or re.search(
            r"\bpages?\s+\d",
            line,
            re.IGNORECASE,
        ):
            continue
        # Ignore source citations after removing bullet markers.
        if re.match(
            r"^(source|document|reference)\b",
            line,
            re.IGNORECASE,
        ):
            continue
        if not line:
            continue

        # Split ordinary paragraphs into individual sentences.
        sentences = re.split(
            r'(?<=[.!?])\s+(?=[A-Z0-9])',
            line,
        )

        for sentence in sentences:
            sentence = sentence.strip()

            if len(sentence) > 15:
                claims.append(sentence)

    # Remove duplicate statements while preserving order.
    claims = list(dict.fromkeys(claims))

    return json.dumps({"claims": claims}, ensure_ascii=False)


def verify_answer(
    question: str,
    proposed_answer: str,
    evidence: str,
) -> str:

    try:
        # STEP 1: Extract factual claims
        claims_result = extract_claims(proposed_answer)
        claims_data = json.loads(claims_result)
        claims = claims_data.get("claims", [])

        if not isinstance(claims, list) or not claims:
            raise ValueError("No factual claims extracted.")

        print("\n" + "=" * 60)
        print("EXTRACTED CLAIMS")
        print("=" * 60)

        for i, claim in enumerate(claims, 1):
            print(f"{i}. {claim}")

        # STEP 2: Prepare result containers
        supported = []
        unsupported = []
        missing = []
        confidences = []

        # STEP 3: Verify claims in batches of three
        batch_size = 3

        for start in range(0, len(claims), batch_size):

            batch = claims[start:start + batch_size]

            print("\n" + "-" * 60)
            print(f"VERIFYING CLAIMS {start + 1} TO {start + len(batch)}")
            print("-" * 60)

            user_prompt = f"""
            You are verifying a small list of factual claims.

            USER QUESTION:
            {question}

            CLAIMS TO VERIFY:
            {json.dumps(batch, ensure_ascii=False)}

            EVIDENCE:
            {evidence}

            STRICT INSTRUCTIONS:

            1. Evaluate every claim separately.
            2. You MUST copy each claim EXACTLY as written above.
            3. Put a claim in supported_claims only if the evidence supports it.
            4. Put a claim in unsupported_or_problematic_claims if the
            evidence contradicts it or does not adequately support it.
            5. Never create, rewrite, shorten, or introduce claims.
            6. Never copy unrelated facts from the evidence.
            7. Do not use outside medical knowledge.
            8. Set missing_information to [] unless essential information
            is missing to answer the user's question safely.
            9. Every submitted claim must appear in exactly one of the
            two claim arrays.
            10. Keep confidence based on the quality of the evidence.

            IMPORTANT:
            The only permitted entries in supported_claims and
            unsupported_or_problematic_claims are exact copies of the
            claims listed under CLAIMS TO VERIFY.

            Return the required JSON object only.
            """

            result = ask_ollama(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            batch_result = json.loads(result)
            # Ensure the model returned the expected JSON structure.
            if not isinstance(batch_result, dict):
                raise ValueError("Verifier returned an invalid JSON object.")

            if not isinstance(batch_result.get("supported_claims"), list):
                raise ValueError("Invalid supported_claims array.")

            if not isinstance(
                batch_result.get("unsupported_or_problematic_claims"), list
            ):
                raise ValueError("Invalid unsupported claims array.")
            print("\nRAW VERIFIER RESPONSE:")
            print(json.dumps(batch_result, indent=2))
            # STEP 4: Validate model output against actual claims
            valid_claims = set(batch)

            for claim in batch_result.get("supported_claims", []):
                if claim in valid_claims and claim not in supported:
                    supported.append(claim)

            for claim in batch_result.get(
                "unsupported_or_problematic_claims", []
            ):
                if claim in valid_claims and claim not in unsupported:
                    unsupported.append(claim)

            missing.extend(
                batch_result.get("missing_information", [])
            )

            confidences.append(
                batch_result.get("confidence", "LOW")
            )

        # STEP 5: Check whether every claim was evaluated
        evaluated = set(supported) | set(unsupported)
        unevaluated = [claim for claim in claims if claim not in evaluated]

        if unevaluated:
            unsupported.extend(unevaluated)

        # STEP 6: Deterministic final decision
        if unsupported:
            verdict = "FAIL"
            action = "REVISE"
            confidence = "MEDIUM"
        else:
            verdict = "PASS"
            action = "PASS"
            confidence = "HIGH"

        final_result = {
            "verdict": verdict,
            "confidence": confidence,
            "supported_claims": supported[:5],
            "unsupported_or_problematic_claims": unsupported[:5],
            "missing_information": missing[:5],
            "recommended_action": action,
        }

        return json.dumps(final_result, indent=2)

    except Exception as e:

        print("\n" + "=" * 70)
        print("VERIFICATION AGENT - VERIFICATION ERROR")
        print("=" * 70)
        print(f"Reason: {e}")

        return json.dumps({
            "verdict": "FAIL",
            "confidence": "LOW",
            "supported_claims": [],
            "unsupported_or_problematic_claims": [
                "The proposed answer could not be fully verified."
            ],
            "missing_information": [
                "Successful factual claim extraction and verification."
            ],
            "recommended_action": "RESEARCH"
        })

def main():

    question = (
        "What is the latest FDA-approved treatment for melanoma "
        "in 2026?"
    )

    # Deliberately incorrect answer.
    #
    # This lets us test whether the Verification Agent catches
    # unsupported generalizations.

    proposed_answer = """
Tudriqev is the standard first-line treatment for all melanoma
patients.

It should be used for patients with melanoma regardless of
stage, previous treatment, or disease progression.
"""

    evidence = """
Source: FDA
Title: FDA grants accelerated approval to
vusolimogene oderparepvec-wtpg in combination with nivolumab
for melanoma

Publication date: August 6, 2026

The FDA states that on August 6, 2026 it granted accelerated
approval to vusolimogene oderparepvec-wtpg (Tudriqev) in
combination with nivolumab for adult patients with
unresectable advanced cutaneous melanoma who experienced
disease progression on a PD-1-blocking-antibody-based regimen.

The FDA states that the approval was based on objective
response rate and duration of response and that continued
approval may depend on verification of clinical benefit in
confirmatory trials.
"""

    print("=" * 70)
    print("VERIFICATION AGENT TEST")
    print("=" * 70)

    result = verify_answer(
        question=question,
        proposed_answer=proposed_answer,
        evidence=evidence,
    )

    print(result)


if __name__ == "__main__":
    main()