from openai import OpenAI

from backend.config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are the synthesis agent for a cancer information assistant.

Your job is to combine evidence produced by other agents into a
clear proposed answer.

You do NOT perform independent web research.

You must use only the evidence supplied to you.

IMPORTANT RULES:

1. Do not invent facts that are not present in the supplied
   evidence.

2. Preserve the distinction between:
   - faculty knowledge
   - current external research
   - safety/emergency information

3. Faculty PDFs may be older. Never silently present old faculty
   information as current medical guidance.

4. When current external evidence is available and relevant,
   clearly identify it as current external evidence.

5. If faculty evidence and current research conflict because of
   changes over time, explain that the information differs by
   source date.

6. Do not diagnose the patient.

7. Do not prescribe treatment or medication.

8. Do not make an individual treatment recommendation.

9. Preserve important limitations, contraindications,
   eligibility criteria, uncertainty, and accelerated-approval
   status when they are present in the evidence.

10. Do not remove important uncertainty simply to make the answer
    sound more confident.

11. If the supplied evidence is insufficient, say so.

12. The resulting answer will be passed to a separate
    Verification Agent. Do not claim that the answer has already
    been verified.

13. Include source references so the Verification Agent can trace
    claims back to evidence.

Write a concise, patient-friendly proposed answer.

Do not expose internal chain-of-thought or hidden reasoning.
"""


def synthesize_answer(
    question: str,
    faculty_evidence: str = "",
    research_evidence: str = "",
    emergency_evidence: str = "",
) -> str:

    user_prompt = f"""
USER QUESTION:

{question}


FACULTY RAG EVIDENCE:

{faculty_evidence}


CURRENT RESEARCH EVIDENCE:

{research_evidence}


EMERGENCY/SAFETY EVIDENCE:

{emergency_evidence}


Using ONLY the evidence above, create a proposed answer to the
user's question.

Requirements:

- Clearly distinguish older faculty evidence from current
  external evidence.
- Preserve important limitations.
- Do not invent missing information.
- Do not diagnose or prescribe.
- Include relevant source names and dates.
- If the evidence is insufficient or conflicting, say so.
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

    faculty_evidence = """
Source: managing-skin-cancer-2010.pdf
Page: 103
Source year: 2010

The document describes high-dose interferon alfa-2b as an
FDA-approved adjuvant therapy for high-risk melanoma at that
time.

The document is historical and cannot establish current FDA
approvals in 2026.
"""

    research_evidence = """
Summary:

As of September 21, 2026, the latest melanoma-specific FDA
approval identified was Tudriqev (vusolimogene
oderparepvec-wtpg), approved on August 6, 2026, in combination
with nivolumab.

The approval applies to adults with unresectable advanced
cutaneous melanoma whose disease progressed after treatment
with a PD-1-blocking antibody regimen.

Sources:

FDA — FDA Approves New Engineered Viral Immunotherapy for
Patients with Treatment-Resistant Advanced Melanoma
Publication date: August 6, 2026

NCI — Drugs Approved for Skin Cancer
Updated: September 17, 2026

The approval is accelerated and requires confirmatory evidence
of clinical benefit.
"""

    print("=" * 70)
    print("SYNTHESIS AGENT TEST")
    print("=" * 70)

    result = synthesize_answer(
        question=question,
        faculty_evidence=faculty_evidence,
        research_evidence=research_evidence,
    )

    print(result)


if __name__ == "__main__":
    main()