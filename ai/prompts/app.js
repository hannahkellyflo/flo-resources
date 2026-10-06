import { PROMPTS, CATEGORIES, THEMES, JOBS, CATEGORY_NOTES } from "./prompt-data-v4.js";

/* ------------------------------------------------------------------ *
 * Constants
 * ------------------------------------------------------------------ */

const COLORS = {
  "Lateral non-partner and partner hiring": "#C74500",
  "Entry-level hiring":                     "#12655C",
  "Reviews and development":    "#1F4E8C",
  "Firm-wide talent strategy":  "#6B2A63"
};

const COPIED_MS = 1600;

/* ------------------------------------------------------------------ *
 * Data prep
 * ------------------------------------------------------------------ */

const DATA = PROMPTS.map(p => ({
  ...p,
  hay: [p.title, p.prompt, p.category, p.theme].concat(p.jobs).join(" ").toLowerCase()
}));

const TOTAL = DATA.length;

/* ------------------------------------------------------------------ *
 * State
 * ------------------------------------------------------------------ */

const state = {
  q: "",
  collapsed: window.innerWidth < 820,
  copied: null,
  active: null                   // anchor id of the section the reader is in
};

/* The rail is a table of contents, not a filter. Clicking a row scrolls to that
 * section and leaves the rest of the page rendered, so the reader can keep
 * scrolling through the category they landed in. Search is the only thing that
 * removes prompts from the page. */
const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
/* Keyed by category as well as name: two categories may carry the same
 * subheading, and an anchor must stay unique if that ever happens again. */
const catId   = c      => "s-" + slug(c);
const themeId = (c, t) => "s-" + slug(c) + "--" + slug(t);

let copyTimer = null;

/* ------------------------------------------------------------------ *
 * Matching
 * ------------------------------------------------------------------ */

function stem(t) {
  if (t.length > 4 && /ies$/.test(t)) return t.slice(0, -3);
  if (t.length > 4 && /y$/.test(t))   return t.slice(0, -1);
  if (t.length > 3 && /s$/.test(t) && !/ss$/.test(t)) return t.slice(0, -1);
  return t;
}

/* Matches one prompt against the active filters.
 * `skip` names dimensions to ignore, so a dimension can compute its own
 * counts without counting itself. */
function matches(d) {
  const q = state.q.trim().toLowerCase();
  if (!q) return true;
  for (const t of q.split(/\s+/).filter(Boolean)) {
    if (d.hay.indexOf(stem(t)) === -1) return false;
  }
  return true;
}

/* ------------------------------------------------------------------ *
 * Mutations
 * ------------------------------------------------------------------ */

function clearSearch() {
  state.q = "";
  searchInput.value = "";
  render();
}

/* Repaints just the affected copy buttons. A full re-render would rebuild
 * every card and throw away focus on the button the user just pressed. */
function paintCopied(n, on) {
  for (const btn of document.querySelectorAll(`.card__copy[data-copy="${n}"]`)) {
    btn.classList.toggle("is-copied", on);
    btn.querySelector("span:last-child").textContent = on ? "Copied" : "Copy";
  }
}

function copyPrompt(p) {
  const done = () => {
    if (state.copied !== null) paintCopied(state.copied, false);
    state.copied = p.n;
    paintCopied(p.n, true);
    clearTimeout(copyTimer);
    copyTimer = setTimeout(() => {
      paintCopied(p.n, false);
      state.copied = null;
    }, COPIED_MS);
  };

  /* Hidden-textarea fallback for browsers without the async clipboard API,
   * and for embedded views that reject it at runtime. */
  const fallback = () => {
    const ta = document.createElement("textarea");
    ta.value = p.prompt;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) { /* no-op */ }
    document.body.removeChild(ta);
  };

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(p.prompt).then(done, () => { fallback(); done(); });
  } else {
    fallback();
    done();
  }
}

/* ------------------------------------------------------------------ *
 * Rendering helpers
 * ------------------------------------------------------------------ */

const esc = s => String(s).replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* Bracket highlighting is generated here, never stored per prompt. */
function promptHTML(text) {
  let out = "", last = 0, m;
  const re = /\[[^\]]+\]/g;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out += esc(text.slice(last, m.index));
    out += `<span class="bracket">${esc(m[0])}</span>`;
    last = m.index + m[0].length;
  }
  if (last < text.length) out += esc(text.slice(last));
  return out;
}

const ICON_COPY = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`;
const ICON_INFO = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>`;

/* ------------------------------------------------------------------ *
 * Counts
 * ------------------------------------------------------------------ */

/* Counts follow the search, which is now the only filter. */
const catCount   = c      => DATA.filter(d => d.category === c && matches(d)).length;
const themeCount = (c, t) => DATA.filter(d => d.category === c && d.theme === t && matches(d)).length;

/* ------------------------------------------------------------------ *
 * Render
 * ------------------------------------------------------------------ */

const catBlocks     = document.getElementById("catBlocks");
const railRows      = document.getElementById("railRows");
const results       = document.getElementById("results");
const searchInput   = document.getElementById("search");
const clearQueryBtn = document.getElementById("clearQuery");
const collapseBtn   = document.getElementById("collapseToggle");
const liveCount     = document.getElementById("liveCount");

function renderCatBlocks() {
  catBlocks.innerHTML = CATEGORIES.map(c => `
      <button class="cat-block" type="button" data-jump="${catId(c)}"
              aria-current="${state.active === catId(c)}" style="--cat:${COLORS[c]}">
        <span class="cat-block__count">${catCount(c)}</span>
        <span class="cat-block__name">${esc(c)}</span>
        <span class="cat-block__note">${esc(CATEGORY_NOTES[c] || "")}</span>
        <span class="cat-block__pill">View these prompts</span>
      </button>`).join("");
}

function renderRail() {
  const shown = DATA.filter(matches).length;

  const rows = [`
    <button class="rail-row" type="button" data-jump="top">
      <span class="rail-row__label">All prompts</span>
      <span class="rail-row__num">${shown}</span>
    </button>`];

  for (const c of CATEGORIES) {
    const count = catCount(c);
    const own   = THEMES[c] || [];
    /* Every category's subheadings are listed at once: the rail indexes the
     * whole page now, rather than drilling into one selected category. */
    const showSubs = own.length > 0 && !state.collapsed;

    let subs = "";
    if (showSubs) {
      subs = `<div class="rail__subs" style="--cat-faint:${COLORS[c]}33">` + own.map(t => {
        const id   = themeId(c, t);
        const tCnt = themeCount(c, t);
        /* A search can empty a subheading. Disable rather than hide, so the
         * index keeps its shape and nothing jumps around as you type. */
        return `
          <button class="sub-row${tCnt === 0 ? " is-empty" : ""}" type="button"
                  data-jump="${id}"${tCnt === 0 ? " disabled" : ""}
                  aria-current="${state.active === id}" style="--cat:${COLORS[c]}">
            <span>${esc(t)}</span>
            <span class="sub-row__num">${tCnt}</span>
          </button>`;
      }).join("") + `</div>`;
    }

    rows.push(`
      <div>
        <button class="rail-row${count === 0 ? " is-empty" : ""}" type="button"
                data-jump="${catId(c)}"${count === 0 ? " disabled" : ""}
                aria-current="${state.active === catId(c)}">
          <span class="rail-row__label"><span class="swatch" style="--cat:${COLORS[c]}"></span>${esc(c)}</span>
          <span class="rail-row__num">${count}</span>
        </button>
        ${subs}
      </div>`);
  }

  railRows.innerHTML = rows.join("");
  collapseBtn.textContent = state.collapsed ? "Show subheadings" : "Hide subheadings";
  collapseBtn.setAttribute("aria-expanded", String(!state.collapsed));
}

function cardHTML(p) {
  const isCopied = state.copied === p.n;
  return `
    <article class="card" style="--cat:${COLORS[p.category] || "#C74500"}">
      <div class="card__head">
        <h4 class="card__title">${esc(p.title)}</h4>
        <button class="card__copy${isCopied ? " is-copied" : ""}" type="button" data-copy="${p.n}"
                data-print-hide aria-label="Copy prompt: ${esc(p.title)}">
          ${ICON_COPY}<span>${isCopied ? "Copied" : "Copy"}</span>
        </button>
      </div>
      <button class="card__prompt" type="button" data-copy="${p.n}" title="Click to copy"
              aria-label="Copy prompt: ${esc(p.title)}">${promptHTML(p.prompt)}</button>
      ${p.req ? `<div class="card__req">${ICON_INFO}<span>${esc(p.req)}</span></div>` : ""}
    </article>`;
}

function renderResults() {
  const rows = DATA.filter(d => matches(d));

  liveCount.textContent = state.q.trim()
    ? `${rows.length} ${rows.length === 1 ? "prompt" : "prompts"} match your search.`
    : `Showing all ${rows.length} prompts.`;

  if (!rows.length) {
    results.innerHTML = `
      <div class="empty-state">
        <p class="empty-state__head">Nothing matches that search.</p>
        <p class="empty-state__body">Try a broader term.</p>
        <button class="btn-solid" type="button" data-clear>Clear search</button>
      </div>`;
    return;
  }

  const sections = CATEGORIES.map(c => {
    const inC = rows.filter(d => d.category === c);
    if (!inC.length) return "";

    const order = THEMES[c] || [];
    const groups = [];

    for (const t of order) {
      const inT = inC.filter(d => d.theme === t);
      if (inT.length) groups.push({ name: t, show: true, prompts: inT });
    }
    const loose = inC.filter(d => !d.theme || !order.includes(d.theme));
    if (loose.length) groups.push({ name: "", show: false, prompts: loose });

    return `
      <section class="cat-section" id="${catId(c)}" style="--cat:${COLORS[c]}">
        <div class="cat-section__head">
          <span class="cat-section__swatch"></span>
          <h2 class="cat-section__name">${esc(c)}</h2>
          <span class="cat-section__count">${inC.length} ${inC.length === 1 ? "prompt" : "prompts"}</span>
        </div>
        <p class="cat-section__note">${esc(CATEGORY_NOTES[c] || "")}</p>
        ${groups.map(g => `
          <div class="theme-group"${g.show ? ` id="${themeId(c, g.name)}"` : ""}>
            ${g.show ? `
              <div class="theme-group__head">
                <h3 class="theme-group__name">${esc(g.name)}</h3>
                <span class="theme-group__rule"></span>
                <span class="theme-group__count">${g.prompts.length}</span>
              </div>` : ""}
            <div class="card-grid">${g.prompts.map(cardHTML).join("")}</div>
          </div>`).join("")}
      </section>`;
  }).join("");

  results.innerHTML = sections;
}

function render() {
  renderCatBlocks();
  renderRail();
  renderResults();
  clearQueryBtn.hidden = !state.q.trim();
}

/* ------------------------------------------------------------------ *
 * Events (delegated)
 * ------------------------------------------------------------------ */

/* Jumping ------------------------------------------------------------- *
 * The spy is muted while a click-driven scroll is in flight: a smooth scroll
 * crosses every section on the way, and letting it repaint would flicker the
 * rail through each one before settling. */
let spyMuted = false;
let spyTimer = null;

function sectionAnchors() {
  return Array.prototype.slice.call(results.querySelectorAll(".cat-section, .theme-group[id]"))
    .filter(el => el.id);
}

/* Paints the rail in place. A full render() here would rebuild every card on
 * each scroll frame and drop focus. */
function paintActive() {
  for (const el of document.querySelectorAll("[data-jump]")) {
    el.setAttribute("aria-current", String(el.getAttribute("data-jump") === state.active));
  }
}

function updateActive() {
  if (spyMuted) return;
  /* The current section is the last one whose top has passed the reading line. */
  const line = 120;
  let id = null;
  for (const el of sectionAnchors()) {
    if (el.getBoundingClientRect().top <= line) id = el.id; else break;
  }
  if (window.scrollY < 40) id = null;
  if (id !== state.active) { state.active = id; paintActive(); }
}

function jumpTo(id) {
  if (id === "top") {
    spyMuted = true; state.active = null; paintActive();
    window.scrollTo({ top: 0, behavior: scrollBehavior() });
  } else {
    const el = document.getElementById(id);
    if (!el) return;
    spyMuted = true; state.active = id; paintActive();
    el.scrollIntoView({ behavior: scrollBehavior(), block: "start" });
  }
  clearTimeout(spyTimer);
  spyTimer = setTimeout(() => { spyMuted = false; updateActive(); }, 700);
}

const scrollBehavior = () =>
  (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)
    ? "auto" : "smooth";

/* ------------------------------------------------------------------ *
 * Events (delegated)
 * ------------------------------------------------------------------ */

document.addEventListener("click", e => {
  const el = e.target.closest("[data-jump],[data-clear],[data-copy]");
  if (!el) return;

  if (el.hasAttribute("data-copy")) {
    const p = DATA.find(d => d.n === Number(el.getAttribute("data-copy")));
    if (p) copyPrompt(p);
  } else if (el.hasAttribute("data-clear")) {
    clearSearch();
  } else if (el.hasAttribute("data-jump")) {
    jumpTo(el.getAttribute("data-jump"));
  }
});

let spyFrame = null;
window.addEventListener("scroll", () => {
  if (spyFrame) return;
  spyFrame = requestAnimationFrame(() => { spyFrame = null; updateActive(); });
}, { passive: true });

searchInput.addEventListener("input", e => { state.q = e.target.value; render(); });
clearQueryBtn.addEventListener("click", () => { state.q = ""; searchInput.value = ""; render(); });
collapseBtn.addEventListener("click", () => { state.collapsed = !state.collapsed; render(); });

/* ------------------------------------------------------------------ *
 * Boot
 * ------------------------------------------------------------------ */

for (const el of document.querySelectorAll("[data-total]")) el.textContent = TOTAL;
render();
