document.getElementById("date").textContent = new Date().toLocaleDateString("en-US", {
  weekday: "long", year: "numeric", month: "long", day: "numeric",
});

async function loadBrief() {
  const content = document.getElementById("content");
  content.textContent = "Generating your digest...";

  try {
    const res = await fetch("http://localhost:8000/brief");
    const data = await res.json();
    const brief = data.brief || "";
    const lines = brief.split("\n");

    content.innerHTML = "";

    const statLine = lines.find(l => l.startsWith("✦"));
    if (statLine) {
      const stat = document.createElement("div");
      stat.className = "stat-line";
      stat.textContent = statLine;
      content.appendChild(stat);
    }

    const briefText = lines.filter(l => !l.startsWith("✦")).join("\n").trim();

    // Simple markdown render: **bold**, ## headers, --- dividers, - bullets
    const rendered = briefText
      .replace(/^---$/gm, "<hr>")
      .replace(/^\*\*(.+?)\*\*$/gm, "<h2>$1</h2>")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/^- (.+)$/gm, "<li>$1</li>")
      .replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
      .replace(/\n{2,}/g, "<br><br>")
      .replace(/\n/g, "<br>");

    const div = document.createElement("div");
    div.className = "brief";
    div.innerHTML = rendered;
    content.appendChild(div);

  } catch (e) {
    content.textContent = "Could not load digest. Make sure the backend is running on localhost:8000.";
  }
}

loadBrief();
