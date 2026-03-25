const API = "http://localhost:8000";

const BLOCK_OPTIONS = [
  { id: "hustle", emoji: "💪", label: "Hustle culture & morning routines" },
  { id: "job_doom", emoji: "😰", label: "Job market doom & layoff anxiety" },
  { id: "ai_doom", emoji: "🤖", label: '"AI will replace you" posts' },
  { id: "mass_hiring", emoji: "📢", label: "Mass hiring blasts (500+ roles)" },
  { id: "motivational", emoji: "✨", label: "Motivational fluff & life advice" },
  { id: "thought_leadership", emoji: "♻️", label: "Recycled thought leadership" },
  { id: "career_coach", emoji: "🎯", label: 'Career coaches & "DM me" job pitches' },
  { id: "scams", emoji: "🚨", label: 'Recruitment scams ("DM me for a job")' },
];

async function loadStats() {
  try {
    const res = await fetch(`${API}/posts?limit=200`);
    const posts = await res.json();
    const today = new Date().toISOString().slice(0, 10);
    const todayPosts = posts.filter(p => p.created_at?.startsWith(today));
    const hidden = todayPosts.filter(p => p.action === "HIDE").length;
    const signal = todayPosts.filter(p => p.action === "HIGHLIGHT").length;
    const total = todayPosts.length;

    document.getElementById("stat-total").textContent = total;
    document.getElementById("stat-hidden").textContent = hidden;
    document.getElementById("stat-signal").textContent = signal;

    if (total > 0) {
      const pct = Math.round((hidden / total) * 100);
      const stat = document.getElementById("mh-stat");
      stat.textContent = `✦ ${hidden} noisy posts blocked. Feed ${pct}% cleaner today.`;
      stat.style.display = "block";
    }
  } catch (e) {
    document.getElementById("mh-stat").textContent = "Backend not running.";
    document.getElementById("mh-stat").style.display = "block";
  }
}

function renderBlockList(selected) {
  const container = document.getElementById("block-list");
  container.innerHTML = "";
  BLOCK_OPTIONS.forEach(opt => {
    const item = document.createElement("div");
    item.className = "block-item";
    item.innerHTML = `
      <span class="emoji">${opt.emoji}</span>
      <input type="checkbox" id="bl-${opt.id}" ${selected.includes(opt.id) ? "checked" : ""} />
      <label for="bl-${opt.id}">${opt.label}</label>
    `;
    container.appendChild(item);
  });
}

function getSelected() {
  return BLOCK_OPTIONS.filter(opt =>
    document.getElementById(`bl-${opt.id}`)?.checked
  ).map(opt => opt.id);
}

function renderCurrentFilters(blockList, customPatterns) {
  const container = document.getElementById("current-filters");
  container.innerHTML = "";

  const activeOptions = BLOCK_OPTIONS.filter(o => blockList.includes(o.id));

  if (activeOptions.length === 0 && customPatterns.length === 0) {
    container.innerHTML = `<div style="font-size:12px;color:#aaa">No filters set yet.</div>`;
    return;
  }

  activeOptions.forEach(opt => {
    const tag = document.createElement("span");
    tag.className = "filter-tag";
    tag.textContent = `${opt.emoji} ${opt.label}`;
    container.appendChild(tag);
  });

  customPatterns.forEach(p => {
    const tag = document.createElement("span");
    tag.className = "filter-tag custom";
    tag.textContent = `🚫 ${p}`;
    container.appendChild(tag);
  });
}

function showOnboarding(selected = []) {
  renderBlockList(selected);
  document.getElementById("onboarding-section").classList.remove("hidden");
  document.getElementById("return-section").classList.add("hidden");
}

function showReturn(blockList, customPatterns) {
  document.getElementById("onboarding-section").classList.add("hidden");
  document.getElementById("return-section").classList.remove("hidden");
  renderCurrentFilters(blockList, customPatterns);
}

// Save block list
document.getElementById("save-btn").addEventListener("click", () => {
  const selected = getSelected();
  chrome.storage.local.set({ blockList: selected, onboarded: true }, () => {
    chrome.storage.local.get("customPatterns", ({ customPatterns = [] }) => {
      showReturn(selected, customPatterns);
    });
    fetch(`${API}/block-list`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ categories: selected }),
    }).catch(() => {});
  });
});

// Edit filters
document.getElementById("edit-btn").addEventListener("click", () => {
  chrome.storage.local.get("blockList", ({ blockList = [] }) => {
    showOnboarding(blockList);
  });
});

// Digest — open as new tab, digest.html fetches from backend directly
document.getElementById("digest-btn").addEventListener("click", () => {
  chrome.tabs.create({ url: chrome.runtime.getURL("digest.html") });
});

// Init
chrome.storage.local.get(["onboarded", "blockList", "customPatterns"], ({ onboarded, blockList = [], customPatterns = [] }) => {
  if (onboarded) {
    showReturn(blockList, customPatterns);
  } else {
    showOnboarding([]);
  }
  loadStats();
});
