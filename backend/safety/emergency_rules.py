"""
Deterministic safety rules for emergency detection.

This module provides a first-pass safety screen before an LLM
handles the user's message.

It is intentionally conservative: messages indicating possible
self-harm, suicide, immediate danger, or severe medical emergency
should be routed to the emergency path.
"""


HIGH_RISK_PATTERNS = [
    "i want to die",
    "i wanna die",
    "want to die",
    "wanna die",
    "kill myself",
    "killing myself",
    "suicide",
    "suicidal",
    "end my life",
    "take my own life",
    "hurt myself",
    "harm myself",
    "self harm",
    "self-harm",
]


URGENT_MEDICAL_PATTERNS = [
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "severe chest pain",
    "chest pain",
    "unconscious",
    "passed out",
    "severe bleeding",
    "bleeding heavily",
    "heavy bleeding",
    "seizure",
    "having a seizure",
    "overdose",
    "poisoned",
]


def normalize_text(text: str) -> str:
    """
    Normalize user text for deterministic matching.
    """

    return " ".join(text.lower().strip().split())


def detect_emergency_keywords(text: str) -> dict:
    """
    Perform deterministic emergency detection.

    Returns:
        {
            "emergency": bool,
            "self_harm": bool,
            "medical_emergency": bool,
            "matched_patterns": list[str]
        }
    """

    normalized = normalize_text(text)

    self_harm_matches = [
        pattern
        for pattern in HIGH_RISK_PATTERNS
        if pattern in normalized
    ]

    medical_matches = [
        pattern
        for pattern in URGENT_MEDICAL_PATTERNS
        if pattern in normalized
    ]

    matched_patterns = (
        self_harm_matches +
        medical_matches
    )

    return {
        "emergency": bool(matched_patterns),
        "self_harm": bool(self_harm_matches),
        "medical_emergency": bool(medical_matches),
        "matched_patterns": matched_patterns,
    }


if __name__ == "__main__":

    test_messages = [
        "My cancer treatment is unbearable and I want to die.",
        "I am feeling very sad about my diagnosis.",
        "I cannot breathe properly.",
        "What are the risk factors for melanoma?",
    ]

    for message in test_messages:

        result = detect_emergency_keywords(message)

        print("=" * 70)
        print(f"MESSAGE: {message}")
        print("=" * 70)
        print(result)