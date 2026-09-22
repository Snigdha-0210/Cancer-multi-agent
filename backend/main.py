from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.dev_config import is_mock_mode
from backend.graph.mock_workflow import run_mock_workflow


app = FastAPI(
    title="Cancer Multi-Agent AI",
    description="Backend API for the cancer patient multi-agent assistant.",
    version="0.3.0",
)


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Cancer Multi-Agent AI backend is running.",
        "mode": "mock" if is_mock_mode() else "live",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "mode": "mock" if is_mock_mode() else "live",
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # ---------------------------------------------------------
    # DEVELOPMENT / MOCK MODE
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    # Do not import the real LangGraph workflow here.
    #
    # The real workflow imports sentence-transformers/PyTorch,
    # and Windows is currently blocking one of PyTorch's DLLs.
    #
    # Mock mode therefore stays completely independent of the
    # RAG/PyTorch stack.
    #
    if is_mock_mode():
        return {
            "question": question,
            **run_mock_workflow(question),
        }

    # ---------------------------------------------------------
    # LIVE MODE
    # ---------------------------------------------------------
    #
    # These imports are intentionally inside the live branch.
    # This prevents PyTorch/RAG dependencies from loading while
    # we are developing the frontend in mock mode.
    #
    from backend.graph.workflow import workflow
    from backend.graph.final_node import build_final_response

    initial_state = {
        "question": question,
        "verification_attempts": 0,
        "errors": [],
    }

    try:
        final_state = workflow.invoke(initial_state)

        response = build_final_response(final_state)

        return {
            "question": question,
            **response,
            "mode": "live",
        }

    except Exception as error:
        print(f"Workflow execution error: {error}")

        raise HTTPException(
            status_code=503,
            detail=(
                "The AI service is temporarily unavailable. "
                "Please try again later."
            ),
        )