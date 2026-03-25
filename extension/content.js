const API_URL = "http://localhost:8000/score";

// Track processed posts to avoid re-scoring
const processed = new WeakSet();

// ── Block list (mirrors demo-site logic) ──
let currentBlockList = [];

const CATEGORY_KEYWORDS = {
  hustle:           ["hustle", "morning routine", "grind", "bet on yourself", "5am", "entrepreneur", "side hustle"],
  job_doom:         ["job market", "layoff", "unemployed", "brutal", "no callbacks", "worst i've seen", "do not leave it"],
  ai_doom:          ["replace you", "ai will take", "unemployed in", "learn ai or", "ai replaced", "this is just the beginning"],
  mass_hiring:      ["500+", "open roles", "drop your resume", "we are hiring", "all levels", "all locations"],
  motivational:     ["habits of", "successful people", "mindset", "life lesson", "life advice", "like if you agree"],
  thought_leadership: ["recycled", "repost to remind", "this applies to every", "person using ai"],
  career_coach:     ["career coach", "dm me", "free guide", "job search challenge", "resume rewrite", "interview coaching", "comment", "coaching"],
  scams:            ["dm me for a job", "recruitment scam", "send your cv"],
};

function matchesBlockList(topic, reason) {
  if (currentBlockList.length === 0) return false;
  const text = (topic + " " + (reason || "")).toLowerCase();
  return currentBlockList.some(cat => {
    const keywords = CATEGORY_KEYWORDS[cat] || [];
    return keywords.some(kw => text.includes(kw));
  });
}

// Load block list once at startup, keep in sync
chrome.storage.local.get("blockList", ({ blockList = [] }) => {
  currentBlockList = blockList;
});
chrome.storage.onChanged.addListener((changes) => {
  if (changes.blockList) currentBlockList = changes.blockList.newValue || [];
});

function extractPostText(postEl) {
  // Demo page: grab the .post-text div directly
  const demoText = postEl.querySelector(".post-text");
  if (demoText && demoText.innerText.trim().length > 10) {
    return demoText.innerText.trim();
  }

  // LinkedIn selectors
  const selectors = [
    ".feed-shared-update-v2__description",
    ".feed-shared-text",
    ".update-components-text",
    ".feed-shared-text-view",
    ".attributed-text-segment-list__content",
    "[data-test-id='main-feed-activity-card__commentary']",
    "span[dir='ltr']",
  ];
  for (const sel of selectors) {
    try {
      const el = postEl.querySelector(sel);
      if (el && el.innerText && el.innerText.trim().length > 10) {
        return el.innerText.trim();
      }
    } catch (e) {
      // skip bad selector
    }
  }

  // Last resort: grab all text from the post
  const text = postEl.innerText ? postEl.innerText.trim() : null;
  if (text && text.length > 10) return text.slice(0, 1000);
  return null;
}

function getPostId(postEl) {
  // Demo page uses data-post-id attribute
  return postEl.getAttribute("data-post-id") || generatePostId(postEl.innerText || "");
}

function generatePostId(text) {
  // Simple hash for deduplication
  let hash = 0;
  for (let i = 0; i < Math.min(text.length, 200); i++) {
    hash = (hash << 5) - hash + text.charCodeAt(i);
    hash |= 0;
  }
  return String(hash);
}

async function scorePost(postEl) {
  if (processed.has(postEl)) return;
  processed.add(postEl);

  let text;
  try {
    text = extractPostText(postEl);
  } catch (e) {
    return;
  }
  if (!text) return;

  console.log("[LinkLens] Scoring post:", text.slice(0, 80));

  const postId = getPostId(postEl);

  // Mark as pending while we wait for the API
  postEl.setAttribute("data-linklens", "pending");

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, post_id: postId }),
    });

    if (!res.ok) return;

    const data = await res.json();
    console.log("[LinkLens] Result:", data.action, data.topic);
    applyOverlay(postEl, data);
  } catch (err) {
    // Backend not running — fail silently, don't break LinkedIn
    postEl.removeAttribute("data-linklens");
    processed.delete(postEl);
  }
}

function applyOverlay(postEl, data) {
  const { action, topic, reason } = data;

  // Respect user's block list — only hide if the topic matches a selected category
  let effectiveAction = action;
  if (action === "HIDE") {
    effectiveAction = matchesBlockList(topic, reason) ? "HIDE" : "SHOW";
  }

  postEl.style.position = "relative";
  postEl.setAttribute("data-linklens", effectiveAction.toLowerCase());
  postEl.setAttribute("data-linklens-topic", topic);

  if (effectiveAction === "HIGHLIGHT") {
    const badge = document.createElement("div");
    badge.className = "linklens-badge";
    badge.textContent = `✦ ${topic}`;
    badge.title = reason;
    postEl.prepend(badge);
  }

  // Add hover ✕ block button to all visible posts (HIGHLIGHT + SHOW)
  if (effectiveAction !== "HIDE") {
    addBlockButton(postEl, data.text || "");
  }
}

function addBlockButton(postEl, text) {
  const btn = document.createElement("button");
  btn.className = "linklens-block-btn";
  btn.textContent = "✕";
  btn.title = "Block posts like this";
  btn.addEventListener("click", async (e) => {
    e.stopPropagation();
    btn.textContent = "…";
    btn.disabled = true;
    try {
      const postText = extractPostText(postEl) || text;
      const res = await fetch(`${API_URL.replace("/score", "/block-pattern")}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: postText }),
      });
      const data = await res.json();

      // Add to chrome storage custom patterns
      chrome.storage.local.get("customPatterns", ({ customPatterns = [] }) => {
        if (!customPatterns.includes(data.pattern)) {
          chrome.storage.local.set({ customPatterns: [...customPatterns, data.pattern] });
        }
      });

      // Silently collapse this post
      postEl.setAttribute("data-linklens", "hide");
      btn.remove();
    } catch (e) {
      btn.textContent = "✕";
      btn.disabled = false;
    }
  });
  postEl.appendChild(btn);
}

// --- MutationObserver ---
function findPostElements(root) {
  return root.querySelectorAll(
    ".ll-post, .feed-shared-update-v2, .occludable-update, [data-urn]"
  );
}

function processPosts(root = document) {
  findPostElements(root).forEach(scorePost);
}

// Initial scan
processPosts();

// Watch for new posts as the user scrolls
const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (node.nodeType !== 1) continue;
      // Score the node itself if it's a post
      if (
        node.matches &&
        node.matches(".ll-post, .feed-shared-update-v2, .occludable-update, [data-urn]")
      ) {
        scorePost(node);
      }
      // Score any posts inside the added subtree
      processPosts(node);
    }
  }
});

observer.observe(document.body, { childList: true, subtree: true });
