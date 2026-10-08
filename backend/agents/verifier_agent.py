import json
import urllib.request


# ============================================================
# SETTINGS
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"


SYSTEM_PROMPT = """
You are the verification agent for a cancer information assistant.

Your job is to verify whether a proposed answer is adequately
supported by the evidence provided to you.

You are NOT the final medical decision-maker.

IMPORTANT RULES:

1. Check whether the claims in the proposed answer are actually
   supported by the supplied evidence.

2. Do not assume that a claim is true merely because another
   agent stated it.

3. Pay special attention to dates and freshness.

4. If the user asked for latest, current, recent, or 2026
   information, verify that the evidence is sufficiently recent
   to support that claim.

5. Prefer authoritative sources for medical claims.

6. If a source is older than the requested time period, it must
   not automatically be treated as evidence of current guidance.

7. Check whether the answer incorrectly generalizes a treatment
   intended for a specific patient population.

8. Check whether important limitations, uncertainty, or
   accelerated-approval status have been omitted.

9. Do not invent replacement facts.

10. Do not diagnose the patient.

11. Do not prescribe treatment.

12. If the evidence is insufficient, mark the answer as FAIL
    rather than guessing.

CRITICAL OUTPUT RULE:

Return ONLY valid JSON.

Do not return Markdown.
Do not return explanations outside the JSON.
Do not use code fences.
Do not add any text before or after the JSON.

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

- PASS:
  Use only when the proposed answer is adequately supported by
  the supplied evidence.

- FAIL:
  Use when an important claim is unsupported, problematic,
  contradicted by the evidence, insufficiently current, or when
  important information required by the question is missing.

RECOMMENDED ACTION:

- PASS:
  The answer can proceed.

- RESEARCH:
  Additional or more current evidence is required.

- REVISE:
  The answer should be modified using the supplied evidence.

Remember:

Judge the proposed answer ONLY against the supplied evidence.
Do not use your own medical knowledge to replace missing evidence.
"""


def ask_ollama(system_prompt: str, user_prompt: str) -> str:

    payload = {
        "model": MODEL_NAME,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
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


def verify_answer(
    question: str,
    proposed_answer: str,
    evidence: str,
) -> str:

    user_prompt = f"""
USER QUESTION:

{question}


PROPOSED ANSWER:

{proposed_answer}


EVIDENCE:

{evidence}


Verify the proposed answer against the evidence.

Pay particular attention to:

- factual support
- source quality
- source dates
- currentness
- patient population
- limitations
- uncertainty
- whether the answer makes claims that the evidence does not
  support

IMPORTANT:

Do not use your own medical knowledge to replace missing
information.

Judge the proposed answer ONLY against the supplied evidence.

If a claim is not supported by the evidence, mark it as
UNSUPPORTED OR PROBLEMATIC.

If important information is missing, list it under
MISSING INFORMATION.

Return your verification using the exact structure requested
in the system instructions.
"""

    try:
        return ask_ollama(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

    except Exception as e:

        print()
        print("=" * 70)
        print("VERIFICATION AGENT — LOCAL MODEL UNAVAILABLE")
        print("=" * 70)
        print(f"Reason: {e}")

        return """VERDICT: UNKNOWN

CONFIDENCE: LOW

SUPPORTED CLAIMS:
- Verification could not be completed because the verification model is unavailable.

UNSUPPORTED OR PROBLEMATIC CLAIMS:
- The proposed answer could not be fully checked.

MISSING INFORMATION:
- Live verification by the Verification Agent.

RECOMMENDED ACTION:
- RESEARCH: obtain verification from the Verification Agent when the model is available.
"""


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