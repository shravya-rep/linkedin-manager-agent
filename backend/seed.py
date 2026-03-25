"""
Seed script — feeds 20 realistic LinkedIn posts through the JudgeAgent.
Run with: python3 seed.py
Requires the backend to be running on localhost:8000.
"""

import urllib.request
import json
import time

POSTS = [
    # --- SIGNAL: Agentic AI ---
    {
        "id": "s1",
        "text": "LangGraph 0.3 just shipped persistent memory across sessions. Here's a breakdown of how checkpointers work under the hood and why this changes long-running agent workflows. The key insight: graph state is now serialized to durable storage at every node boundary, meaning your agent can resume exactly where it left off after a crash, interrupt, or human-in-the-loop pause.",
    },
    {
        "id": "s2",
        "text": "We ran a 72-hour autonomous agent experiment using CrewAI + GPT-4o. The agent completed 847 subtasks without human intervention. Here's what broke, what held, and what we'd architect differently. Spoiler: memory management and tool error recovery were the two biggest failure modes.",
    },
    {
        "id": "s3",
        "text": "Deep dive: how Anthropic's tool_use API differs from OpenAI function calling under the hood. We benchmarked both on 500 structured extraction tasks. Claude's tool_use had 12% fewer hallucinated field values. Here's the prompt structure that made the difference.",
    },
    {
        "id": "s4",
        "text": "Just open-sourced our multi-agent orchestration framework built on LangGraph. It handles dynamic agent spawning, inter-agent messaging, and shared memory pools. Star it if you're building production agentic systems: github.com/example/multiagent-orch",
    },
    {
        "id": "s5",
        "text": "AutoGen vs LangGraph vs CrewAI — which multi-agent framework actually scales? We ran all three on the same 50-task benchmark. LangGraph won on reliability, CrewAI on developer experience, AutoGen on flexibility. Full breakdown in the thread.",
    },

    # --- SIGNAL: RAG & Retrieval ---
    {
        "id": "s6",
        "text": "RAG is not dead — it's just being done wrong. Here's what we changed to go from 61% to 94% retrieval accuracy: (1) chunk overlap strategy, (2) hybrid BM25 + dense retrieval, (3) re-ranking with a cross-encoder. Each change and its impact explained with evals.",
    },
    {
        "id": "s7",
        "text": "We replaced ChromaDB with pgvector in production and cut our p99 retrieval latency from 340ms to 47ms. Here's the migration path, indexing strategy, and the one gotcha that cost us 3 hours of debugging.",
    },
    {
        "id": "s8",
        "text": "Contextual retrieval from Anthropic is genuinely good. We integrated it into our RAG pipeline last week. The trick is prepending chunk-level context summaries before embedding — relevance scores jumped 22%. Here's the exact implementation.",
    },

    # --- SIGNAL: MLOps / Infra ---
    {
        "id": "s9",
        "text": "How we serve 10M LLM requests/day on a $3k/month infra budget. Key decisions: vLLM for inference, speculative decoding for latency, aggressive KV cache tuning, and batching strategy. Full architecture diagram in the post.",
    },
    {
        "id": "s10",
        "text": "LLM evals are still broken in most teams. Here's the eval stack we built: unit evals for tool calls, integration evals for multi-turn flows, and a human preference eval pipeline for quality. All open source. The hardest part wasn't the tech — it was getting engineers to actually run evals in CI.",
    },

    # --- NOISE: Hustle culture ---
    {
        "id": "n1",
        "text": "5 habits of the most successful people I know:\n1. Wake up at 5am\n2. Never miss a Monday\n3. Read 30 books a year\n4. Cold showers\n5. Gratitude journal\n\nWhich one will you start today? 👇\n\n#Success #Mindset #GrowthMindset #Hustle",
    },
    {
        "id": "n2",
        "text": "I turned down a $500k offer to bet on myself.\n\nEveryone thought I was crazy.\n\nThat was 2 years ago.\n\nToday my company does $2M ARR.\n\nThe lesson: bet on yourself.\n\nLike if you agree 👍",
    },
    {
        "id": "n3",
        "text": "Your network is your net worth.\n\nI spent 10 years building mine.\n\nHere are 7 ways to network like a pro:\n\n1. Give before you take\n2. Follow up within 24 hours\n3. Remember people's names\n4. ...\n\nSave this for later! ♻️",
    },
    {
        "id": "n4",
        "text": "Nobody talks about this:\n\nWorking 80 hours a week isn't hustle.\n\nIt's poor planning.\n\nThe most productive people I know work 40 hours max.\n\nThoughts? Drop them below 👇\n\n#WorkLifeBalance #Productivity #Leadership",
    },

    # --- NOISE: Anxiety / job market doom ---
    {
        "id": "n5",
        "text": "AI replaced 200,000 software engineers last quarter.\n\nThis is just the beginning.\n\nIf you're not learning AI skills RIGHT NOW you will be unemployed in 18 months.\n\nThis is not fear mongering. This is reality.\n\nAre you prepared?",
    },
    {
        "id": "n6",
        "text": "The tech job market is the worst I've seen in 20 years.\n\nSenior engineers applying to 300 jobs with no callbacks.\n\nL5s at FAANG being let go with no warning.\n\nIf you have a job right now, do NOT leave it. Hold on for dear life.",
    },
    {
        "id": "n7",
        "text": "Just got laid off after 8 years at my company.\n\nApplied to 400 jobs in 3 months.\n\n12 interviews. 0 offers.\n\nThe market is brutal. If you're hiring or know someone who is, please help. 🙏\n\n#OpenToWork #Layoffs #TechJobs",
    },

    # --- NOISE: Mass hiring blasts ---
    {
        "id": "n8",
        "text": "🚨 WE ARE HIRING 🚨\n\nWe have 500+ open roles across Engineering, Product, Sales, Marketing, HR, Finance, and Operations!\n\nAll levels. All locations. Remote friendly.\n\nDrop your resume below or DM me!\n\nShare to help someone land their dream job! ♻️♻️♻️",
    },
    {
        "id": "n9",
        "text": "My company is hiring for the following roles:\n- 47 Software Engineers (all stacks)\n- 23 Product Managers\n- 15 Data Scientists\n- 31 Sales Representatives\n- 8 DevOps Engineers\n- 19 Customer Success\n\nLike and comment 'interested' and I'll reach out!",
    },

    # --- NOISE: Recycled thought leadership ---
    {
        "id": "n10",
        "text": "AI is not going to replace you.\n\nA person using AI will replace you.\n\nThis applies to every industry.\n\nEvery job.\n\nEvery role.\n\nStart learning AI today.\n\nRepost to remind your network ♻️\n\n#AI #FutureOfWork #ArtificialIntelligence",
    },
]


def score_post(post):
    data = json.dumps({"text": post["text"], "post_id": post["id"]}).encode()
    req = urllib.request.Request(
        "http://localhost:8000/score",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode())


def main():
    print(f"Seeding {len(POSTS)} posts...\n")
    results = {"HIGHLIGHT": [], "SHOW": [], "HIDE": []}

    for i, post in enumerate(POSTS):
        try:
            result = score_post(post)
            action = result["action"]
            results[action].append(result)
            icon = {"HIGHLIGHT": "✦", "SHOW": "·", "HIDE": "✗"}[action]
            print(f"[{i+1:02d}] {icon} {action:9s} | {result['topic'][:55]}")
            time.sleep(0.3)  # avoid rate limiting
        except Exception as e:
            print(f"[{i+1:02d}] ERROR: {e}")

    print(f"\n── Summary ──────────────────────────")
    print(f"  HIGHLIGHT : {len(results['HIGHLIGHT'])}")
    print(f"  SHOW      : {len(results['SHOW'])}")
    print(f"  HIDE      : {len(results['HIDE'])}")
    print(f"  Total     : {len(POSTS)}")
    print(f"\nRun test_brief.py to generate today's AI brief.")


if __name__ == "__main__":
    main()
