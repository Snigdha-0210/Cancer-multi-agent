from backend.agents.research_agent import verify_claim_support

# Fake evidence deliberately says nothing about melanoma.
test_sources = [
    {
        "title": "Example source about diabetes",
        "url": "https://example.com/diabetes",
        "snippet": "This page discusses diabetes management.",
        "full_content": (
            "Diabetes is a condition involving blood glucose "
            "regulation. This page contains no information "
            "about melanoma or cancer treatments."
        ),
    }
]

# Deliberately unsupported claim.
test_claim = (
    "The FDA approved Drug XYZ as a cure for all melanoma "
    "patients in 2026. [SOURCE 1]"
)

supported, reason = verify_claim_support(
    test_claim,
    test_sources,
)

print("\n" + "=" * 60)
print("UNSUPPORTED CLAIM VERIFICATION TEST")
print("=" * 60)
print("Claim:", test_claim)
print("Supported:", supported)
print("Reason:", reason)
print("=" * 60)

# ---------------------------------------------------------
# TEST 2: Partially supported / exaggerated medical claim
# ---------------------------------------------------------
partial_sources = [
    {
        "title": "Example FDA approval announcement",
        "url": "https://example.com/fda-approval",
        "snippet": (
            "Example approval for a specific melanoma population."
        ),
        "full_content": (
            "The FDA granted accelerated approval to Drug ABC "
            "in combination with Drug DEF for adults with "
            "unresectable advanced cutaneous melanoma who "
            "experienced disease progression following a "
            "PD-1-blocking antibody-based regimen. "
            "This approval applies to the specified patient "
            "population and does not establish approval for "
            "all patients with melanoma."
        ),
    }
]

partial_claim = (
    "The FDA approved Drug ABC as a standalone treatment "
    "for all melanoma patients, including newly diagnosed "
    "patients. [SOURCE 1]"
)

partial_supported, partial_reason = verify_claim_support(
    partial_claim,
    partial_sources,
)

print("\n" + "=" * 60)
print("EXAGGERATED CLAIM VERIFICATION TEST")
print("=" * 60)
print("Claim:", partial_claim)
print("Supported:", partial_supported)
print("Reason:", partial_reason)
if not partial_supported:
    print("TEST PASSED: Exaggerated claim was rejected.")
else:
    print("TEST FAILED: Exaggerated claim was incorrectly accepted.")
print("=" * 60)

# ---------------------------------------------------------
# TEST 3: Malformed Ollama response
# ---------------------------------------------------------
from unittest.mock import patch

malformed_sources = [
    {
        "title": "Example melanoma source",
        "url": "https://example.com/melanoma",
        "snippet": "Example melanoma evidence.",
        "full_content": (
            "This is example evidence about melanoma."
        ),
    }
]

malformed_claim = (
    "This is a claim about melanoma. [SOURCE 1]"
)

# Simulate Ollama returning invalid JSON.
with patch(
    "backend.agents.research_agent.ask_ollama",
    return_value="This is not valid JSON",
):
    malformed_supported, malformed_reason = verify_claim_support(
        malformed_claim,
        malformed_sources,
    )

print("\n" + "=" * 60)
print("MALFORMED RESPONSE VERIFICATION TEST")
print("=" * 60)
print("Supported:", malformed_supported)
print("Reason:", malformed_reason)
print("=" * 60)

if malformed_supported is False:
    print("TEST PASSED: Malformed response was safely rejected.")
else:
    print("TEST FAILED: Malformed response was accepted.")

# ---------------------------------------------------------
# TEST 4: String "true" must not be accepted as Boolean true
# ---------------------------------------------------------
with patch(
    "backend.agents.research_agent.ask_ollama",
    return_value='{"supported": "true", "reason": "String true should not pass."}',
):
    string_true_supported, string_true_reason = verify_claim_support(
        malformed_claim,
        malformed_sources,
    )

print("\n" + "=" * 60)
print("STRING TRUE VERIFICATION TEST")
print("=" * 60)
print("Supported:", string_true_supported)
print("Reason:", string_true_reason)
print("=" * 60)

if string_true_supported is False:
    print('TEST PASSED: String "true" was correctly rejected.')
else:
    print('TEST FAILED: String "true" was incorrectly accepted.')

# ---------------------------------------------------------
# TEST 5: Claim without citation
# ---------------------------------------------------------
uncited_claim = (
    "The FDA approved Drug ABC for melanoma patients in 2026."
)

uncited_supported, uncited_reason = verify_claim_support(
    uncited_claim,
    partial_sources,
)

print("\n" + "=" * 60)
print("MISSING CITATION VERIFICATION TEST")
print("=" * 60)
print("Supported:", uncited_supported)
print("Reason:", uncited_reason)
print("=" * 60)

if uncited_supported is False:
    print("TEST PASSED: Claim without citation was rejected.")
else:
    print("TEST FAILED: Claim without citation was accepted.")

# ---------------------------------------------------------
# TEST 6: Invalid source reference
# ---------------------------------------------------------
invalid_reference_claim = (
    "The FDA approved Drug ABC for melanoma patients. [SOURCE 99]"
)

invalid_supported, invalid_reason = verify_claim_support(
    invalid_reference_claim,
    partial_sources,
)

print("\n" + "=" * 60)
print("INVALID SOURCE REFERENCE TEST")
print("=" * 60)
print("Supported:", invalid_supported)
print("Reason:", invalid_reason)
print("=" * 60)

if invalid_supported is False:
    print("TEST PASSED: Invalid source reference was rejected.")
else:
    print("TEST FAILED: Invalid source reference was accepted.")

# ---------------------------------------------------------
# TEST 7: Ollama connection failure
# ---------------------------------------------------------
with patch(
    "backend.agents.research_agent.ask_ollama",
    side_effect=ConnectionError("Ollama server is unavailable."),
):
    connection_supported, connection_reason = verify_claim_support(
        partial_claim,
        partial_sources,
    )

print("\n" + "=" * 60)
print("OLLAMA CONNECTION FAILURE TEST")
print("=" * 60)
print("Supported:", connection_supported)
print("Reason:", connection_reason)
print("=" * 60)

if connection_supported is False:
    print("TEST PASSED: Ollama failure was handled safely.")
else:
    print("TEST FAILED: Ollama failure was incorrectly accepted.")

# ---------------------------------------------------------
# TEST 8: Valid and supported claim
# ---------------------------------------------------------
valid_claim = (
    "The FDA granted accelerated approval to Drug ABC "
    "in combination with Drug DEF for adults with "
    "unresectable advanced cutaneous melanoma who "
    "experienced disease progression following a "
    "PD-1-blocking antibody-based regimen. [SOURCE 1]"
)

valid_supported, valid_reason = verify_claim_support(
    valid_claim,
    partial_sources,
)

print("\n" + "=" * 60)
print("VALID SUPPORTED CLAIM TEST")
print("=" * 60)
print("Supported:", valid_supported)
print("Reason:", valid_reason)
print("=" * 60)

if valid_supported is True:
    print("TEST PASSED: Correctly supported claim was accepted.")
else:
    print("TEST FAILED: Correctly supported claim was rejected.")


# ---------------------------------------------------------
# TEST 9: Conflicting evidence
# ---------------------------------------------------------

conflict_sources = [
    {
        "title": "Example FDA approval announcement",
        "url": "https://example.com/approval",
        "snippet": "Drug ABC received FDA approval.",
        "full_content": (
            "The FDA officially approved Drug ABC "
            "for the treatment of advanced melanoma."
        ),
    },
    {
        "title": "Example FDA non-approval announcement",
        "url": "https://example.com/non-approval",
        "snippet": "Drug ABC has not received FDA approval.",
        "full_content": (
            "Drug ABC has not received FDA approval "
            "for the treatment of advanced melanoma. "
            "No such approval has been granted."
        ),
    },
]

conflict_claim = (
    "The FDA approved Drug ABC for advanced melanoma. "
    "[SOURCE 1] [SOURCE 2]"
)

conflict_supported, conflict_reason = verify_claim_support(
    conflict_claim,
    conflict_sources,
)

print("\n" + "=" * 60)
print("CONFLICTING EVIDENCE VERIFICATION TEST")
print("=" * 60)
print("Supported:", conflict_supported)
print("Reason:", conflict_reason)
print("=" * 60)

if conflict_supported is False:
    print("TEST PASSED: Conflicting evidence was rejected.")
else:
    print(
        "TEST FAILED: Conflicting evidence was accepted. "
        "The verifier needs stronger conflict detection."
    )