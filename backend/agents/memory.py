import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

PATTERN_PROMPT = """You are analyzing a LinkedIn post that a user wants to block.
Identify the SHORT category label for the type of content this post represents.

Examples:
- "DM me for a job" → "recruitment scam"
- "Wake up at 5am" → "hustle culture"
- "AI will replace you in 6 months" → "AI doom anxiety"
- "We are hiring 500+ roles" → "mass hiring blast"
- "I turned down $500k to bet on myself" → "hustle brag"
- "The market is brutal, hold on for dear life" → "job market doom"

Respond with ONLY a JSON object:
{"pattern": "<short category label>", "description": "<one sentence describing what to block>"}"""


def detect_pattern(post_text: str) -> dict:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=PATTERN_PROMPT,
        messages=[{"role": "user", "content": post_text[:500]}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)
