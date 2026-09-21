from openai import OpenAI
from pydantic import BaseModel

from backend.config import OPENAI_API_KEY
from backend.safety.emergency_rules import detect_emergency_keywords


client = OpenAI(api_key=OPENAI_API_KEY)


SYSTEM_PROMPT = """
You are the Emergency/Safety Agent for a cancer information
assistant.

Your role is to respond safely when a user may be experiencing
a self-harm crisis or an urgent medical emergency.

This is a safety-critical component.

IMPORTANT RULES:

1. Be calm, empathetic, direct, and non-judgmental.

2. If the user expresses suicidal thoughts, wanting to die,
   self-harm intentions, or similar immediate danger:
   - acknowledge their distress;
   - encourage them to seek immediate human help;
   - encourage contacting local emergency services or a
     crisis service;
   - encourage contacting a trusted person who can stay with
     them;
   - encourage moving away from weapons, medications, or other
     means of self-harm;
   - ask whether they are in immediate danger or have already
     harmed themselves.

3. If the user describes an urgent medical emergency:
   - encourage immediate emergency medical care;
   - do not attempt to diagnose the condition;
   - do not give detailed treatment instructions.

4. Do not provide instructions for self-harm.

5. Do not provide information about methods, lethal doses,
   effectiveness of methods, or ways to avoid detection.

6. Do not shame, blame, or guilt the user.

7. Do not tell the user that everything will definitely be okay.

8. Do not make promises that you cannot keep.

9. Do not overwhelm the user with a long explanation.

10. Do not route the message through the ordinary cancer RAG
    answer path before addressing the emergency.

11. Do not diagnose.

12. Do not prescribe medication.

13. The response should prioritize immediate safety over
    answering the underlying cancer-information question.

14. Do not expose internal reasoning or agent details.

The response should be short enough to read during a crisis.

For an explicit self-harm crisis, the response should generally
follow this structure:

- Empathetic acknowledgement.
- Immediate safety instruction.
- Encourage emergency/crisis support.
- Encourage contacting a trusted person.
- Ask whether the person is in immediate danger or has already
  harmed themselves.

For an urgent medical emergency:

- State that the symptoms may require immediate medical care.
- Encourage contacting local emergency services or going to the
  nearest emergency department.
- Encourage having another person stay with them if possible.
- Ask whether they are currently in immediate danger.
"""


class EmergencyResponse(BaseModel):
    emergency: bool
    emergency_type: str
    response: str
    immediate_danger_question: str
    recommended_action: str


def generate_emergency_response(
    question: str,
    detection: dict,
) -> EmergencyResponse:

    emergency_type = "general"

    if detection["self_harm"]:
        emergency_type = "self_harm"
    elif detection["medical_emergency"]:
        emergency_type = "medical_emergency"

    user_prompt = f"""
USER MESSAGE:

{question}


DETERMINISTIC SAFETY DETECTION:

Emergency detected: {detection["emergency"]}
Self-harm indicators: {detection["self_harm"]}
Medical-emergency indicators: {detection["medical_emergency"]}
Matched patterns: {detection["matched_patterns"]}

Emergency type:

{emergency_type}


Generate a safe emergency response according to your system
instructions.

Do not provide ordinary cancer-information content.
Prioritize immediate safety.
"""

    response = client.responses.parse(
        model="gpt-5.6-luna",
        instructions=SYSTEM_PROMPT,
        input=user_prompt,
        text_format=EmergencyResponse,
    )

    return response.output_parsed


def handle_emergency(question: str) -> EmergencyResponse:

    detection = detect_emergency_keywords(question)

    if not detection["emergency"]:
        return EmergencyResponse(
            emergency=False,
            emergency_type="none",
            response=(
                "No emergency indicators were detected by the "
                "deterministic safety screen."
            ),
            immediate_danger_question="",
            recommended_action="Continue with normal routing.",
        )

    return generate_emergency_response(
        question=question,
        detection=detection,
    )


def main():

    test_questions = [
        "My cancer treatment is unbearable and I want to die.",

        "I cannot breathe properly and I feel very weak.",

        "I am feeling very sad about my diagnosis.",

        "What are the risk factors for melanoma?",
    ]

    print("=" * 70)
    print("EMERGENCY / SAFETY AGENT TEST")
    print("=" * 70)

    for question in test_questions:

        print()
        print("=" * 70)
        print("USER MESSAGE")
        print("=" * 70)
        print(question)

        result = handle_emergency(question)

        print()
        print("EMERGENCY:", result.emergency)
        print("TYPE:", result.emergency_type)

        print()
        print("RESPONSE:")
        print(result.response)

        if result.immediate_danger_question:
            print()
            print("IMMEDIATE DANGER QUESTION:")
            print(result.immediate_danger_question)

        print()
        print("RECOMMENDED ACTION:")
        print(result.recommended_action)


if __name__ == "__main__":
    main()