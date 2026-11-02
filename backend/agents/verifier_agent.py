import json
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
Do not approve unsupported medical claims.
"""



def ask_ollama(system_prompt: str, user_prompt: str) -> str:

    payload = {
        "model": MODEL_NAME,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
        "format": {
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
                },
                "unsupported_or_problematic_claims": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "missing_information": {
                    "type": "array",
                    "items": {"type": "string"},
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