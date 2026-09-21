from openai import OpenAI
from pydantic import BaseModel, Field

from backend.config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are the Router/Triage Agent for a cancer information
assistant.

Your job is NOT to answer the user's question.

Your job is to decide which specialized agents should handle
the question.

The available agents are:

1. FACULTY_RAG
   - Uses the faculty-provided cancer PDF knowledge base.
   - Use this when the question can be answered from the
     provided faculty material.

2. CURRENT_RESEARCH
   - Uses current external sources.
   - Use this when the user asks for:
     latest, current, recent, newest, updated, 2026,
     current recommendations, current approvals, or other
     information where the faculty PDFs may be outdated.
   - Also use it when the faculty knowledge base is unlikely
     to contain the required information.

3. EMERGENCY
   - Handles urgent safety situations.
   - Use this when the user expresses:
       * suicidal thoughts
       * wanting to die
       * self-harm intentions
       * immediate danger
       * severe emotional crisis related to cancer
       * urgent medical danger or severe symptoms
   - Emergency routing has priority over ordinary information
     retrieval.

4. SYNTHESIS
   - Combines evidence from the selected agents.
   - Usually required whenever FACULTY_RAG or CURRENT_RESEARCH
     produces evidence.
   - Emergency situations may follow a specialized safety path.

5. VERIFICATION
   - Checks the final proposed answer against its evidence.
   - Use this for factual medical answers and especially for
     current/latest information.

IMPORTANT:

- Do not answer the user's question.
- Do not diagnose.
- Do not prescribe treatment.
- Do not make medical recommendations.
- Do not assume that the faculty PDFs are current.
- Do not treat an old source as current simply because it
  contains relevant information.
- If the user asks for current information, CURRENT_RESEARCH
  should normally be selected.
- If the user appears to be in immediate danger, EMERGENCY
  takes priority.
- You may select multiple agents.
- Give a short reason for every selected route.
"""


class RouterDecision(BaseModel):
    faculty_rag: bool = False
    current_research: bool = False
    emergency: bool = False
    synthesis: bool = False
    verification: bool = False

    intent: str = ""

    reason: str = ""

    confidence: str = ""

    priority: str = ""

    missing_information: list[str] = Field(
        default_factory=list
    )


def route_question(question: str) -> RouterDecision:

    response = client.responses.parse(
        model="gpt-5.6-luna",
        instructions=SYSTEM_PROMPT,
        input=question,
        text_format=RouterDecision,
    )

    return response.output_parsed


def main():

    test_questions = [
        "What are the risk factors for melanoma?",

        "What is the latest FDA-approved treatment for melanoma "
        "in 2026?",

        "My cancer treatment is unbearable and I want to die.",

        "What does the faculty material say about melanoma risk "
        "factors, and is that information still current?",
    ]

    print("=" * 70)
    print("ROUTER / TRIAGE AGENT TEST")
    print("=" * 70)

    for question in test_questions:

        print()
        print("=" * 70)
        print("QUESTION")
        print("=" * 70)
        print(question)

        decision = route_question(question)

        print()
        print("ROUTING DECISION")
        print("=" * 70)

        print(f"Intent: {decision.intent}")
        print(f"Priority: {decision.priority}")
        print(f"Confidence: {decision.confidence}")

        print()
        print("Selected Agents:")
        print(f"  Faculty RAG:       {decision.faculty_rag}")
        print(f"  Current Research:  {decision.current_research}")
        print(f"  Emergency:         {decision.emergency}")
        print(f"  Synthesis:         {decision.synthesis}")
        print(f"  Verification:      {decision.verification}")

        print()
        print("Reason:")
        print(decision.reason)

        if decision.missing_information:
            print()
            print("Missing Information:")
            for item in decision.missing_information:
                print(f"- {item}")


if __name__ == "__main__":
    main()