# LinkLens ✦

**A personal multi-agent LinkedIn feed intelligence system.**

LinkLens sits between you and your LinkedIn feed. It filters out hustle culture, anxiety posts, and career coach spam — so only the signal you actually care about reaches you.

**[→ Live Demo](https://shravya-rep.github.io/linkedin-manager-agent/)**

---

## What it does

Instead of asking "what do you want to follow?", LinkLens asks: **"What don't you want to see today?"**

You pick your block list once. LinkLens silently collapses everything that matches it, and highlights posts worth reading with a blue bar. At any time, request a daily digest — organized by topic, with a mental health stat line showing what was filtered.

---

## Architecture

Four agents, running locally:

| Agent | Model | Job |
|---|---|---|
| **JudgeAgent** | claude-sonnet-4-6 | Scores every post: topic, signal score, anxiety score → HIGHLIGHT / SHOW / HIDE |
| **SynthesizerAgent** | claude-sonnet-4-6 | Generates daily digest from today's posts |
| **MemoryAgent** | claude-haiku-4-5 | Detects pattern category when you manually block a post |
| **ScoutAgent** | Chrome extension | Watches the feed via MutationObserver, sends posts to the backend |

```
LinkedIn feed
     ↓
Chrome Extension (MutationObserver)
     ↓
FastAPI Backend (localhost:8000)
     ↓
JudgeAgent (Claude API)
     ↓
Overlay applied: HIGHLIGHT / SHOW / HIDE
     ↓
SQLite (posts, feedback, block_patterns)
     ↓
SynthesizerAgent → Daily digest
```

---

## Features

- **Block list paradigm** — shield yourself from hustle culture, AI doom posts, mass hiring blasts, career coaches, and more
- **Silent collapse** — blocked posts shrink to a 4px gray line, no text shown
- **Signal highlighting** — Agentic AI, RAG, MLOps, LLM Evals posts get a blue left bar
- **On-demand daily digest** — mental health stat line + signal posts organized by topic
- **Hover-to-block** — click ✕ on any post to block that pattern permanently
- **Memory** — MemoryAgent learns your preferences over time via feedback

---

## Stack

- **Backend:** Python, FastAPI, SQLite, Anthropic Claude API
- **Extension:** Chrome Manifest V3, MutationObserver, IntersectionObserver
- **Demo:** Vanilla JS, no dependencies, fully self-contained

---

## Run locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
uvicorn main:app --reload
```

**Extension:**
1. Open `chrome://extensions`
2. Enable Developer mode
3. Load unpacked → select the `extension/` folder
4. Go to LinkedIn — LinkLens activates automatically

---

## Demo

The [live demo](https://shravya-rep.github.io/linkedin-manager-agent/) is fully standalone — no backend or extension required. It shows two side-by-side feeds: raw LinkedIn on the left, LinkLens-filtered on the right.

---

Built by [Shravya Shashidhar](https://www.linkedin.com/in/shravya-shashidhar/) · AI Team Lead · USC MS CS
