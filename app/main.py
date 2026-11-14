from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.generate import answer
from app.retrieval import retrieve

import logging

logger= logging.getLogger("uvicorn.error")

app = FastAPI(title="RAG Assistant")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class Source(BaseModel):
    number: int
    source: str
    page: int | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    try:
        chunks = retrieve(req.question)
        text = answer(req.question, chunks)
    except Exception as exc:
        logger.exception("ask failed")
        raise HTTPException(status_code=502, detail="Upstream service error") from exc

    sources = [
        Source(number=i, source=c["source"], page=c["page"])
        for i, c in enumerate(chunks, start=1)
    ]
    return AskResponse(answer=text, sources=sources)