from backend.graph.state import AgentState
from backend.graph.workflow import build_workflow


def run_test(question: str):
    print()
    print("=" * 70)
    print("REAL LANGGRAPH INVOCATION TEST")
    print("=" * 70)
    print(f"QUESTION:\n{question}")
    print()

    graph = build_workflow()

    initial_state: AgentState = {
        "question": question,
        "verification_attempts": 0,
        "errors": [],
    }

    result = graph.invoke(initial_state)

    print("FINAL ANSWER:")
    print(result.get("final_answer"))
    print()

    print("VERIFICATION STATUS:")
    print(result.get("verification_status"))
    print()

    print("VERIFICATION ATTEMPTS:")
    print(result.get("verification_attempts"))
    print()

    print("ROUTE:")
    print(result.get("route"))
    print()

    print("FACULTY EVIDENCE:")
    print(result.get("faculty_evidence", "[none]"))
    print()

    print("RESEARCH EVIDENCE:")
    print(result.get("research_evidence", "[none]"))
    print()

    print("EMERGENCY RESPONSE:")
    print(result.get("emergency_response", "[none]"))
    print()

    print("ERRORS:")
    print(result.get("errors", []))
    print()

    return result


def main():
    tests = [
        "What are the established risk factors for melanoma?",
        "What is the latest cancer treatment information in 2026?",
        "My cancer treatment is unbearable and I want to die.",
    ]

    for question in tests:
        run_test(question)

    print("=" * 70)
    print("REAL LANGGRAPH INVOCATION TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()