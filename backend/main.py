from fastapi import FastAPI
from pydantic import BaseModel

from backend.ai_service import ask_ai


app = FastAPI(
    title="Cancer Multi-Agent AI",
    description="Backend API for the cancer patient multi-agent assistant.",
    version="0.1.0",
)


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Cancer Multi-Agent AI backend is running.",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):
    answer = ask_ai(request.question)

    return {
        "question": request.question,
        "answer": answer,
    }