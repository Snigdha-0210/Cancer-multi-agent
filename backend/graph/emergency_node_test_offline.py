from backend.safety.emergency_rules import detect_emergency_keywords


def main():
    question = "My cancer treatment is unbearable and I want to die."

    detection = detect_emergency_keywords(question)

    print("=" * 70)
    print("EMERGENCY NODE OFFLINE SAFETY TEST")
    print("=" * 70)

    print("Question:")
    print(question)

    print()
    print("Emergency detected:")
    print(detection["emergency"])

    print()
    print("Self-harm detected:")
    print(detection["self_harm"])

    print()
    print("Medical emergency detected:")
    print(detection["medical_emergency"])

    print()
    print("Matched patterns:")
    for pattern in detection["matched_patterns"]:
        print(f"- {pattern}")

    print()
    print("Offline emergency detection test completed.")


if __name__ == "__main__":
    main()