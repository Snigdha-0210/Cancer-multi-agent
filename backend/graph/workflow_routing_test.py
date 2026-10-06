from backend.graph.workflow import (
    route_after_verification,
    verification_node_with_counter,
    MAX_VERIFICATION_ATTEMPTS,
)


def test_pass():
    state = {
        "verification_status": "PASS",
        "verification_attempts": 1,
    }

    result = route_after_verification(state)

    print("TEST 1 — PASS")
    print("Expected: final")
    print("Actual:  ", result)
    print()


def test_fail_first_attempt():
    state = {
        "verification_status": "FAIL",
        "verification_attempts": 1,
    }

    result = route_after_verification(state)

    print("TEST 2 — FAIL, first attempt")
    print("Expected: retry_research")
    print("Actual:  ", result)
    print()


def test_fail_second_attempt():
    state = {
        "verification_status": "FAIL",
        "verification_attempts": MAX_VERIFICATION_ATTEMPTS,
    }

    result = route_after_verification(state)

    print("TEST 3 — FAIL, maximum attempts")
    print("Expected: verification_failed")
    print("Actual:  ", result)
    print()


def test_unknown():
    state = {
        "verification_status": "UNKNOWN",
        "verification_attempts": 1,
    }

    result = route_after_verification(state)

    print("TEST 4 — UNKNOWN")
    print("Expected: verification_failed")
    print("Actual:  ", result)
    print()


if __name__ == "__main__":
    print("=" * 70)
    print("VERIFICATION ROUTING TEST")
    print("=" * 70)
    print()

    test_pass()
    test_fail_first_attempt()
    test_fail_second_attempt()
    test_unknown()

    print("=" * 70)
    print("ROUTING TEST COMPLETE")
    print("=" * 70)