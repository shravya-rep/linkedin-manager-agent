from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agents.judge import score_post, PostScore
from agents.synthesizer import generate_brief
from agents.memory import detect_pattern
from db import init_db, save_post, get_recent_posts, save_feedback, get_topic_weights, save_block_pattern, get_block_patterns
import os

app = FastAPI(title="LinkLens API", version="1.0.0")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/demo")
def demo():
    return FileResponse(os.path.join(STATIC_DIR, "demo.html"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ScoreRequest(BaseModel):
    text: str
    post_id: str | None = None  # optional, for deduplication later


class ScoreResponse(BaseModel):
    post_id: str | None
    topic: str
    signal_score: float
    relevance_score: float
    anxiety_score: float
    action: str
    reason: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest):
    if not req.text or len(req.text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Post text too short to classify.")

    result: PostScore = score_post(req.text)

    save_post(
        post_id=req.post_id,
        text=req.text,
        topic=result.topic,
        signal_score=result.signal_score,
        relevance_score=result.relevance_score,
        anxiety_score=result.anxiety_score,
        action=result.action,
        reason=result.reason,
    )

    return ScoreResponse(
        post_id=req.post_id,
        topic=result.topic,
        signal_score=result.signal_score,
        relevance_score=result.relevance_score,
        anxiety_score=result.anxiety_score,
        action=result.action,
        reason=result.reason,
    )


@app.get("/posts")
def recent_posts(limit: int = 50):
    return get_recent_posts(limit)


@app.get("/brief")
def daily_brief():
    return {"brief": generate_brief()}


class FeedbackRequest(BaseModel):
    post_id: str
    feedback: str  # "like" or "dislike"


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    if req.feedback not in ("like", "dislike"):
        raise HTTPException(status_code=400, detail="feedback must be 'like' or 'dislike'")
    save_feedback(req.post_id, req.feedback)
    return {"status": "ok", "post_id": req.post_id, "feedback": req.feedback}


@app.get("/memory")
def memory():
    return {"topic_weights": get_topic_weights()}


class BlockPatternRequest(BaseModel):
    text: str


@app.post("/block-pattern")
def block_pattern(req: BlockPatternRequest):
    result = detect_pattern(req.text)
    save_block_pattern(result["pattern"], result.get("description", ""))
    return result


@app.get("/block-patterns")
def list_block_patterns():
    return get_block_patterns()


class BlockListRequest(BaseModel):
    categories: list[str]


@app.post("/block-list")
def save_block_list(req: BlockListRequest):
    # Store the user's category block list (from popup checkboxes)
    # Map category ids to human-readable patterns and save
    CATEGORY_MAP = {
        "hustle": ("hustle culture", "Motivational hustle and morning routine posts"),
        "job_doom": ("job market doom", "Anxiety-inducing posts about layoffs and job market"),
        "ai_doom": ("AI doom anxiety", '"AI will replace you" fear posts'),
        "mass_hiring": ("mass hiring blast", "Mass hiring posts with hundreds of roles"),
        "motivational": ("motivational fluff", "Generic life advice and motivational content"),
        "thought_leadership": ("recycled thought leadership", "Recycled insights with no original value"),
        "career_coach": ("career coach pitch", '"DM me" career coaching and job search pitches'),
        "scams": ("recruitment scam", '"DM me for a job" and similar recruitment bait'),
    }
    for cat in req.categories:
        if cat in CATEGORY_MAP:
            pattern, desc = CATEGORY_MAP[cat]
            save_block_pattern(pattern, desc)
    return {"status": "ok", "saved": len(req.categories)}
