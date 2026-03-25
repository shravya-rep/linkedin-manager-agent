import os
import anthropic
from db import get_highlights_today, get_recent_posts

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are SynthesizerAgent, a daily intelligence briefing writer for Shravya — an Agentic AI / ML engineer.

You will receive:
1. A mental health stat line — copy it exactly as the first line
2. SIGNAL POSTS — summarize each as a bullet under the right bucket (TECH, JOBS, PEOPLE, NEWS)
3. FILTERED COUNTS — pre-counted blocked posts per category, include each as a single line like "· 6 hustle posts blocked" under the right bucket

Format:
**TECH**
- [insight from signal post]
- [insight from signal post]
· N hustle posts blocked
· N anxiety posts blocked

**JOBS**
- [insight from signal job post if any]
· N hiring blasts blocked

**WORTH ACTING ON**
- [1-2 signal posts worth engaging with]

Rules:
- Only show buckets that have content
- NEVER include post numbers
- One line per bullet
- Tone: direct, no fluff"""


def generate_brief() -> str:
    all_posts = get_recent_posts(limit=200)

    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_posts = [p for p in all_posts if p.get("created_at", "").startswith(today)]

    if not today_posts:
        return "No posts captured today. Open the demo feed or LinkedIn with LinkLens active."

    total = len(today_posts)
    hidden_posts = [p for p in today_posts if p["action"] == "HIDE"]
    hidden = len(hidden_posts)

    # Categorize hidden posts by topic pattern
    CATEGORY_LABELS = {
        "hustle": ("hustle", "motivational", "morning routine", "habits", "successful"),
        "anxiety": ("doom", "anxiety", "layoff", "brutal", "replace", "unemployed", "market"),
        "hiring": ("hiring", "mass hiring", "recruitment", "roles", "open to work"),
        "career coach": ("career coach", "coaching", "dm me", "free guide", "resume rewrite", "job search challenge"),
        "scam": ("scam", "recruitment bait"),
        "thought leadership": ("thought leadership", "recycled", "repost"),
    }

    category_counts = {k: 0 for k in CATEGORY_LABELS}
    for p in hidden_posts:
        topic = p.get("topic", "").lower()
        matched = False
        for cat, keywords in CATEGORY_LABELS.items():
            if any(kw in topic for kw in keywords):
                category_counts[cat] += 1
                matched = True
                break
        if not matched:
            category_counts.setdefault("other", 0)
            category_counts["other"] = category_counts.get("other", 0) + 1

    # Build the breakdown string
    breakdown_parts = []
    label_map = {
        "hustle": "hustle posts",
        "anxiety": "anxiety posts",
        "hiring": "hiring blasts",
        "scam": "recruitment scams",
        "thought leadership": "recycled thought leadership",
        "other": "other noise",
    }
    for cat, count in category_counts.items():
        if count > 0:
            breakdown_parts.append(f"{count} {label_map.get(cat, cat)}")

    breakdown = ", ".join(breakdown_parts) if breakdown_parts else f"{hidden} noisy posts"
    stat_line = f"✦ LinkLens had your back today. {breakdown} filtered — you didn't have to see any of it."

    # Signal posts for AI to summarize
    signal_posts = [p for p in today_posts if p["action"] in ("HIGHLIGHT", "SHOW")]
    signal_lines = "\n\n".join(
        f"Topic: {p['topic']}\n{p['text'][:300]}"
        for p in signal_posts
    ) or "None today."

    # Pre-count filtered posts by category so AI doesn't have to guess
    TOPIC_BUCKET = [
        ("hustle", ("hustle", "motivational", "morning routine", "habits")),
        ("anxiety", ("doom", "anxiety", "layoff", "replace", "unemployed", "brutal")),
        ("hiring blasts", ("mass hiring", "hiring blast", "hiring")),
        ("career coach pitches", ("career coach", "coaching", "free guide", "resume rewrite", "job search challenge")),
        ("recruitment scams", ("scam", "recruitment bait")),
        ("recycled thought leadership", ("thought leadership", "recycled")),
    ]

    filtered_counts = {}
    for p in hidden_posts:
        topic = p.get("topic", "").lower()
        matched = False
        for label, keywords in TOPIC_BUCKET:
            if any(kw in topic for kw in keywords):
                filtered_counts[label] = filtered_counts.get(label, 0) + 1
                matched = True
                break
        if not matched:
            filtered_counts["other noise"] = filtered_counts.get("other noise", 0) + 1

    filtered_lines = "\n".join(
        f"· {count} {label} blocked"
        for label, count in filtered_counts.items()
        if count > 0
    ) or "None."

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Mental health stat (copy exactly as first line):\n{stat_line}\n\n"
                    f"SIGNAL POSTS (summarize these):\n{signal_lines}\n\n"
                    f"FILTERED COUNTS (include these as-is in the right bucket):\n{filtered_lines}\n\n"
                    f"Generate the digest."
                ),
            }
        ],
    )

    return response.content[0].text.strip()
