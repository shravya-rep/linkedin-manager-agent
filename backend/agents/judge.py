import os
import json
import anthropic
from pydantic import BaseModel

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are JudgeAgent, a feed intelligence system for a senior Agentic AI / ML engineer named Shravya.

Your job is to classify LinkedIn posts and decide whether they are signal or noise FOR HER specifically.

SIGNAL (highlight these):
- Agentic AI, LLM agents, multi-agent systems, agent frameworks (LangGraph, CrewAI, AutoGen, etc.)
- ML engineering: RAG, fine-tuning, embeddings, vector databases, inference optimization
- AI infrastructure, MLOps, LLMOps
- Real technical tutorials, code walkthroughs, research paper breakdowns
- Thoughtful career moves by people in AI/ML (not mass broadcasts)
- Hiring posts specifically for Agentic AI / ML engineering roles

NOISE (hide these):
- Motivational coaching, hustle culture, "5 habits of successful people" style posts
- Anxiety-inducing job market doom posts ("AI is taking all jobs", "market is brutal")
- Mass hiring blasts with 100+ roles across all domains
- Recycled thought leadership with no original technical insight
- Engagement bait, polls with no substance
- Personal life posts unrelated to tech
- Career coaches, "DM me" job pitches, free guide offers, resume review spam, job search coaching

Respond ONLY with valid JSON in this exact format:
{
  "topic": "<short topic label>",
  "signal_score": <0.0 to 1.0>,
  "relevance_score": <0.0 to 1.0>,
  "anxiety_score": <0.0 to 1.0>,
  "action": "<HIGHLIGHT | SHOW | HIDE>",
  "reason": "<one sentence>"
}

Rules for action:
- HIGHLIGHT: signal_score >= 0.7 AND relevance_score >= 0.6
- HIDE: signal_score < 0.3 OR anxiety_score > 0.6
- SHOW: everything else"""


class PostScore(BaseModel):
    topic: str
    signal_score: float
    relevance_score: float
    anxiety_score: float
    action: str  # HIGHLIGHT | SHOW | HIDE
    reason: str


def score_post(post_text: str) -> PostScore:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Classify this LinkedIn post:\n\n{post_text}",
            }
        ],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if Claude wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    data = json.loads(raw)
    return PostScore(**data)
