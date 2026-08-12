const state = { payload: null, file: "source", running: false };

const codeElement = document.querySelector("#input-code");
const runButton = document.querySelector("#run-analysis");
const progress = document.querySelector("#progress");
const results = document.querySelector("#results");

function escapeHtml(value) {
  return value.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function highlightJava(value) {
  const highlightCode = (code) => escapeHtml(code).replace(
    /\b(package|import|public|class|static|void)\b|\b(Logger|LoggerFactory|LoggingEventBuilder|String)\b|(&quot;.*?&quot;)/g,
    (match, keyword, type, string) => {
      if (keyword) return `<span class="token-keyword">${match}</span>`;
      if (type) return `<span class="token-type">${match}</span>`;
      if (string) return `<span class="token-string">${match}</span>`;
      return match;
    },
  );

  return value.split("\n").map((line) => {
    const commentAt = line.indexOf("//");
    if (commentAt === -1) return highlightCode(line);
    return `${highlightCode(line.slice(0, commentAt))}<span class="token-comment">${escapeHtml(line.slice(commentAt))}</span>`;
  }).join("\n");
}

function highlightXml(value) {
  return escapeHtml(value)
    .replace(/(&lt;\/?)([\w.-]+)/g, '$1<span class="token-type">$2</span>')
    .replace(/(&lt;!--.*?--&gt;)/g, '<span class="token-comment">$1</span>')
    .replace(/(&gt;)([^<&\n]+)(&lt;)/g, '$1<span class="token-string">$2</span>$3');
}

function showInput() {
  if (!state.payload) return;
  const value = state.payload.input[state.file];
  codeElement.innerHTML = state.file === "source" ? highlightJava(value) : highlightXml(value);
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    state.file = tab.dataset.file;
    document.querySelectorAll(".tab").forEach((item) => {
      const active = item === tab;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-selected", String(active));
    });
    showInput();
  });
});

function renderDiff(value) {
  return value.split("\n").map((line) => {
    let className = "";
    if (line.startsWith("+") && !line.startsWith("+++")) className = "diff-add";
    if (line.startsWith("-") && !line.startsWith("---")) className = "diff-remove";
    return `<span class="${className}">${escapeHtml(line)}</span>`;
  }).join("\n");
}

function renderResult() {
  const result = state.payload.result;
  document.querySelector("#confidence").textContent = `${result.confidence} confidence`;
  document.querySelector("#result-headline").textContent = result.headline;
  document.querySelector("#result-summary").textContent = result.summary;
  document.querySelector("#fix-summary").textContent = result.suggestion.summary;
  document.querySelector("#diff").innerHTML = renderDiff(result.suggestion.diff);
  document.querySelector("#verification").textContent = result.verification;
  document.querySelector("#evidence").innerHTML = result.evidence.map((item) => `
    <article class="evidence-card">
      <span>${escapeHtml(item.source)}</span>
      <code>${escapeHtml(item.value)}</code>
      <p>${escapeHtml(item.detail)}</p>
    </article>
  `).join("");
}

const wait = (duration) => new Promise((resolve) => window.setTimeout(resolve, duration));

runButton.addEventListener("click", async () => {
  if (state.running || !state.payload) return;
  state.running = true;
  runButton.disabled = true;
  runButton.querySelector("span:first-child").textContent = "Analysing…";
  results.hidden = true;
  progress.hidden = false;

  const steps = [...document.querySelectorAll(".progress-steps li")];
  for (const step of steps) {
    steps.forEach((item) => item.classList.remove("is-active"));
    step.classList.add("is-active");
    await wait(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 80 : 550);
    step.classList.add("is-done");
  }

  renderResult();
  progress.hidden = true;
  results.hidden = false;
  runButton.disabled = false;
  runButton.querySelector("span:first-child").textContent = "Run again";
  state.running = false;
  results.scrollIntoView({ behavior: "smooth", block: "start" });
});

document.querySelector("#copy-diff").addEventListener("click", async (event) => {
  await navigator.clipboard.writeText(state.payload.result.suggestion.diff);
  event.currentTarget.textContent = "Copied";
  window.setTimeout(() => { event.currentTarget.textContent = "Copy diff"; }, 1400);
});

fetch("/api/demo")
  .then((response) => {
    if (!response.ok) throw new Error("Demo unavailable");
    return response.json();
  })
  .then((payload) => { state.payload = payload; showInput(); })
  .catch(() => {
    codeElement.textContent = "The demo fixture could not be loaded. Please refresh the page.";
    runButton.disabled = true;
  });
