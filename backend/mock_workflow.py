from backend.graph.final_node import build_final_response


def run_mock_workflow(question: str) -> dict:
    """
    Simulates the multi-agent workflow without making
    any external API calls.

    This is intended for development and frontend testing.
    """

    question_lower = question.lower()

    # ---------------------------------------------------------
    # ROUTER
    # ---------------------------------------------------------

    if (
        "die" in question_lower
        or "suicide" in question_lower
        or "kill myself" in question_lower
    ):
        route = {
            "faculty_rag": False,
            "current_research": False,
            "emergency": True,
            "synthesis": True,
            "verification": True,
            "intent": "emergency",
        }

        emergency_response = (
            "This sounds like an emergency. "
            "Please seek immediate human support and emergency assistance."
        )

        proposed_answer = emergency_response

        agents_used = [
            "router",
            "emergency",
            "synthesis",
            "verification",
        ]

        verification_status = "PASS"

        sources = []

    elif (
        "latest" in question_lower
        or "current" in question_lower
        or "2026" in question_lower
    ):
        route = {
            "faculty_rag": False,
            "current_research": True,
            "emergency": False,
            "synthesis": True,
            "verification": True,
            "intent": "current_research",
        }

        proposed_answer = (
            "This is a development-mode response. "
            "The question would normally be sent to the "
            "current research agent for up-to-date external evidence."
        )

        agents_used = [
            "router",
            "research",
            "synthesis",
            "verification",
        ]

        verification_status = "PASS"

        sources = [
            {
                "title": "Development Mock Source",
                "source_category": "current_external_research",
            }
        ]

    else:
        route = {
            "faculty_rag": True,
            "current_research": False,
            "emergency": False,
            "synthesis": True,
            "verification": True,
            "intent": "faculty_knowledge",
        }

        proposed_answer = (
            "This is a development-mode response. "
            "The question would normally be sent to the "
            "faculty PDF RAG agent for grounded evidence."
        )

        agents_used = [
            "router",
            "faculty_rag",
            "synthesis",
            "verification",
        ]

        verification_status = "PASS"

        sources = [
            {
                "title": "Faculty Knowledge Base",
                "source_category": "faculty_knowledge",
            }
        ]

    # ---------------------------------------------------------
    # FINAL RESPONSE
    # ---------------------------------------------------------

    return {
        "answer": proposed_answer,
        "verification_status": verification_status,
        "sources": sources,
        "agents_used": agents_used,
        "verification_attempts": 1,
        "mode": "mock",
        "route": route,
    }