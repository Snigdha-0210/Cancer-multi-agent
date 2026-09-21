from openai import OpenAI

from backend.config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are the verification agent for a cancer information
assistant.

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

Return the result in this exact structure:

VERDICT: PASS or FAIL

CONFIDENCE: HIGH, MEDIUM, or LOW

SUPPORTED CLAIMS:
- ...

UNSUPPORTED OR PROBLEMATIC CLAIMS:
- ...

MISSING INFORMATION:
- ...

RECOMMENDED ACTION:
- PASS: answer can proceed
- RESEARCH: obtain additional/current evidence
- REVISE: modify the answer using the supplied evidence
"""


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

Return your verification using the exact structure requested
in the system instructions.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
    )

    return response.output_text


def main():

    question = (
        "What is the latest FDA-approved treatment for melanoma "
        "in 2026?"
    )

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