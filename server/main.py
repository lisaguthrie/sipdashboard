"""
SIP Dashboard API Server
Handles RAG retrieval and Anthropic API calls server-side.
"""
import json
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import anthropic
import numpy as np
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDINGS_URL = (
    "https://cdn.jsdelivr.net/gh/lisaguthrie/sipdashboard@main/goals_embeddings.json"
)
TOP_K = 10
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1500

SYSTEM_PROMPT = """You are an expert analyst helping a school board director review School Improvement Plans (SIPs).

CRITICAL ATTRIBUTION RULES — follow these exactly every time:
1. Each retrieved excerpt begins with a "School name:" line. That line is the sole authoritative source for which school a goal belongs to. Read it before citing anything in that excerpt.
2. Use the school name from the "School name:" line verbatim. Never infer or guess a school name from any other part of the text.
3. Never transfer information from one excerpt to another school.
4. When listing schools that share a characteristic, verify each one independently from its own "School name:" line.
5. If the retrieved excerpts do not contain enough information to answer the question, say so clearly rather than guessing or drawing on outside knowledge.

RESPONSE STYLE:
- Be concise and accurate.
- When listing multiple schools, use a bulleted list with the school name bolded.
- Always cite the relevant goal area (ELA, Math, SEL, etc.) alongside the school name."""

# Load environment variables from .env file
load_dotenv()

# ── App state (loaded once at startup) ───────────────────────────────────────
class AppState:
    embedding_model: SentenceTransformer = None
    goals: list = []          # list of goal dicts with 'embedding' and 'text'
    goal_matrix: np.ndarray = None   # (N, 384) float32 for fast batch similarity


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model and embeddings once at startup."""
    log.info("Loading sentence-transformers model...")
    state.embedding_model = SentenceTransformer(MODEL_NAME)
    log.info("Model loaded.")

    log.info("Fetching embeddings from CDN...")
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(EMBEDDINGS_URL)
        resp.raise_for_status()
        data = resp.json()

    state.goals = data["goals"]
    vectors = np.array([g["embedding"] for g in state.goals], dtype=np.float32)
    # Pre-normalise rows so dot product == cosine similarity
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    state.goal_matrix = vectors / np.maximum(norms, 1e-10)
    log.info(f"Loaded {len(state.goals)} goal embeddings.")

    yield  # server runs here

    log.info("Shutting down.")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this to your deployed domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / response models ─────────────────────────────────────────────────
class Message(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    question: str
    history: list[Message] = []


# ── RAG retrieval ─────────────────────────────────────────────────────────────
def retrieve_chunks(query: str, k: int = TOP_K) -> list[str]:
    """Embed query, compute cosine similarity, return top-k chunk texts."""
    query_vec = state.embedding_model.encode(query, convert_to_numpy=True).astype(np.float32)
    query_vec /= max(np.linalg.norm(query_vec), 1e-10)

    scores = state.goal_matrix @ query_vec          # (N,) cosine similarities
    top_indices = np.argsort(scores)[-k:][::-1]     # descending

    return [state.goals[i]["text"] for i in top_indices]


# ── Chat endpoint ─────────────────────────────────────────────────────────────
@app.post("/api/chat")
async def chat(req: ChatRequest):
    # 1. Retrieve relevant chunks
    chunks = retrieve_chunks(req.question)
    chunk_separator = "\n\n---\n\n"
    context_block = (
        "The following are the most relevant School Improvement Plan goal excerpts "
        "retrieved for this question. Each excerpt begins with a \"School name:\" line "
        "identifying the school it belongs to.\n\n"
        + chunk_separator.join(chunks)
    )

    # 2. Build messages: history + new user question
    messages = [{"role": m.role, "content": m.content} for m in req.history]
    messages.append({"role": "user", "content": req.question})

    # 3. Call Anthropic
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=MAX_TOKENS,
            system=[
                {"type": "text", "text": SYSTEM_PROMPT},
                {"type": "text", "text": context_block,
                 "cache_control": {"type": "ephemeral"}},
            ],
            messages=messages,
        )
        answer = response.content[0].text
    except anthropic.APIError as e:
        log.error(f"Anthropic API error: {e}")
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {e}")

    return {"answer": answer}


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "goals_loaded": len(state.goals),
        "model": MODEL_NAME,
    }


# ── Serve React static build (if present) ────────────────────────────────────
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        """Catch-all: serve index.html for any non-API route (SPA routing)."""
        return FileResponse(static_dir / "index.html")
