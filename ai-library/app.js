import { PROMPTS, CATEGORIES, THEMES, JOBS, CATEGORY_NOTES } from "./prompt-data-v4.js";

/* ------------------------------------------------------------------ *
 * Constants
 * ------------------------------------------------------------------ */

const COLORS = {
  "Lateral and partner hiring": "#C74500",
  "Candidate sourcing":         "#12655C",
  "Reviews and development":    "#1F4E8C",
  "Firm-wide talent strategy":  "#6B2A63"
};

/* Subheading names are not unique across categories ("Screening and criteria"
 * lives under two). Every theme is therefore keyed by category + name so that
 * counts and filters stay scoped to one category. */
/* Internal only — never serialised into the DOM (an HTML attribute would
 * mangle a NUL into U+FFFD). Category and name travel as separate attributes. */
const SEP = "\u001F";
const themeKey = (cat, theme) => cat + SEP + theme;
const keyOf = d => themeKey(d.category, d.theme);
const themeNameOf = key => key.slice(key.indexOf(SEP) + 1);
const catOf = key => key.slice(0, key.indexOf(SEP));

const COPIED_MS = 1600;

/* ------------------------------------------------------------------ *
 * Data prep
 * ------------------------------------------------------------------ */

const DATA = PROMPTS.map(p => ({
  ...p,
  hay: [p.title, p.prompt, p.category, p.theme].concat(p.jobs).join(" ").toLowerCase()
}));

const TOTAL = DATA.length;

/* Subheading names that appear under more than one category. Their filter
 * chips get a category prefix so two identical labels stay tellable apart. */
const SHARED_THEME_NAMES = (() => {
  const seen = new Set(), shared = new Set();
  for (const list of Object.values(THEMES)) {
    for (const t of list) {
      if (seen.has(t)) shared.add(t); else seen.add(t);
    }
  }
  return shared;
})();

const chipLabel = key => {
  const name = themeNameOf(key);
  return SHARED_THEME_NAMES.has(name) ? `${catOf(key)} \u00b7 ${name}` : name;
};

/* ------------------------------------------------------------------ *
 * State
 * ------------------------------------------------------------------ */

const state = {
  q: "",
  selCats: [],
  selThemes: [],                 // theme keys, not bare names
  selJobs: [],                   // no UI today; filter logic stays wired
  collapsed: window.innerWidth < 820,
  copied: null
};

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
function matches(d, ...skip) {
  const off = k => skip.indexOf(k) !== -1;

  const q = state.q.trim().toLowerCase();
  if (q) {
    for (const t of q.split(/\s+/).filter(Boolean)) {
      if (d.hay.indexOf(stem(t)) === -1) return false;
    }
  }
  if (!off("selCats") && state.selCats.length && !state.selCats.includes(d.category)) return false;
  if (!off("selJobs") && state.selJobs.length && !d.jobs.some(j => state.selJobs.includes(j))) return false;
  if (!off("selThemes") && state.selThemes.length && !state.selThemes.includes(keyOf(d))) return false;
  return true;
}

/* ------------------------------------------------------------------ *
 * Mutations
 * ------------------------------------------------------------------ */

function toggle(key, v) {
  const arr = state[key].slice();
  const i = arr.indexOf(v);
  if (i === -1) arr.push(v); else arr.splice(i, 1);
  state[key] = arr;
  render();
}

/* Toggling a category prunes theme selections that are no longer reachable:
 * deselecting a category drops its own themes, selecting one drops themes
 * belonging to categories outside the new selection. */
function toggleCat(c) {
  const on = state.selCats.includes(c);
  const arr = state.selCats.slice();
  if (on) arr.splice(arr.indexOf(c), 1); else arr.push(c);

  state.selThemes = arr.length
    ? state.selThemes.filter(k => arr.includes(catOf(k)))
    : state.selThemes.filter(k => catOf(k) !== c);
  state.selCats = arr;
  render();
}

function clearAll() {
  state.q = "";
  state.selCats = [];
  state.selThemes = [];
  state.selJobs = [];
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

/* A category's count ignores the category and theme dimensions, but still
 * honours theme selections made *within* that category. */
function catCount(c) {
  const ownSel = state.selThemes.filter(k => catOf(k) === c);
  return DATA.filter(d =>
    d.category === c &&
    matches(d, "selCats", "selThemes") &&
    (!ownSel.length || ownSel.includes(keyOf(d)))
  ).length;
}

const themeCount = key =>
  DATA.filter(d => matches(d, "selThemes") && keyOf(d) === key).length;

/* ------------------------------------------------------------------ *
 * Render
 * ------------------------------------------------------------------ */

const catBlocks     = document.getElementById("catBlocks");
const railRows      = document.getElementById("railRows");
const filterCard    = document.getElementById("filterCard");
const results       = document.getElementById("results");
const searchInput   = document.getElementById("search");
const clearQueryBtn = document.getElementById("clearQuery");
const collapseBtn   = document.getElementById("collapseToggle");
const liveCount     = document.getElementById("liveCount");

function renderCatBlocks() {
  catBlocks.innerHTML = CATEGORIES.map(c => {
    const on = state.selCats.includes(c);
    return `
      <button class="cat-block" type="button" data-cat="${esc(c)}" aria-pressed="${on}"
              style="--cat:${COLORS[c]}">
        <span class="cat-block__count">${catCount(c)}</span>
        <span class="cat-block__name">${esc(c)}</span>
        <span class="cat-block__note">${esc(CATEGORY_NOTES[c] || "")}</span>
        <span class="cat-block__pill">${on ? "&#10003; Selected &mdash; clear" : "View these prompts"}</span>
      </button>`;
  }).join("");
}

function renderRail() {
  const anyCat = state.selCats.length > 0;
  const allOn  = !state.selCats.length && !state.selThemes.length;

  const rows = [`
    <button class="rail-row" type="button" data-all aria-pressed="${allOn}">
      <span class="rail-row__label">All prompts</span>
      <span class="rail-row__num">${TOTAL}</span>
    </button>`];

  for (const c of CATEGORIES) {
    const on    = state.selCats.includes(c);
    const count = catCount(c);
    const own   = THEMES[c] || [];
    const showSubs = own.length > 0 && !state.collapsed && (on || !anyCat);

    let subs = "";
    if (showSubs) {
      subs = `<div class="rail__subs" style="--cat-faint:${COLORS[c]}33">` + own.map(t => {
        const key  = themeKey(c, t);
        const tOn  = state.selThemes.includes(key);
        const tCnt = themeCount(key);
        return `
          <button class="sub-row${tCnt === 0 && !tOn ? " is-empty" : ""}" type="button"
                  data-theme-cat="${esc(c)}" data-theme-name="${esc(t)}"
                  aria-pressed="${tOn}" style="--cat:${COLORS[c]}">
            <span>${esc(t)}</span>
            <span class="sub-row__num">${tCnt}</span>
          </button>`;
      }).join("") + `</div>`;
    }

    rows.push(`
      <div>
        <button class="rail-row${count === 0 && !on ? " is-empty" : ""}" type="button"
                data-cat="${esc(c)}" aria-pressed="${on}">
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

function renderFilterCard() {
  const chips = state.selCats.map(c => ({ label: c, attr: `data-cat="${esc(c)}"` }))
    .concat(state.selThemes.map(k => ({ label: chipLabel(k),
      attr: `data-theme-cat="${esc(catOf(k))}" data-theme-name="${esc(themeNameOf(k))}"` })))
    .concat(state.selJobs.map(j => ({ label: j, attr: `data-job="${esc(j)}"` })));

  if (!chips.length) { filterCard.innerHTML = ""; return; }

  filterCard.innerHTML = `
    <div class="filter-card">
      <div class="filter-card__title">Filtering by</div>
      <div class="filter-card__chips">
        ${chips.map(c => `
          <button class="chip" type="button" ${c.attr}>
            <span>${esc(c.label)}</span><span class="chip__x" aria-hidden="true">&times;</span>
            <span class="sr-only">Remove filter</span>
          </button>`).join("")}
      </div>
      <button class="btn-clear" type="button" data-clear>Clear all selections</button>
    </div>`;
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

  liveCount.textContent = `${rows.length} ${rows.length === 1 ? "prompt" : "prompts"} match your selections.`;

  if (!rows.length) {
    results.innerHTML = `
      <div class="empty-state">
        <p class="empty-state__head">Nothing matches that combination.</p>
        <p class="empty-state__body">Clear a selection or try a broader term.</p>
        <button class="btn-solid" type="button" data-clear>Clear all selections</button>
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
      <section class="cat-section" style="--cat:${COLORS[c]}">
        <div class="cat-section__head">
          <span class="cat-section__swatch"></span>
          <h2 class="cat-section__name">${esc(c)}</h2>
          <span class="cat-section__count">${inC.length} ${inC.length === 1 ? "prompt" : "prompts"}</span>
        </div>
        <p class="cat-section__note">${esc(CATEGORY_NOTES[c] || "")}</p>
        ${groups.map(g => `
          <div class="theme-group">
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
  renderFilterCard();
  renderResults();
  clearQueryBtn.hidden = !state.q.trim();
}

/* ------------------------------------------------------------------ *
 * Events (delegated)
 * ------------------------------------------------------------------ */

document.addEventListener("click", e => {
  const el = e.target.closest("[data-cat],[data-theme-name],[data-job],[data-all],[data-clear],[data-copy]");
  if (!el) return;

  if (el.hasAttribute("data-copy")) {
    const p = DATA.find(d => d.n === Number(el.getAttribute("data-copy")));
    if (p) copyPrompt(p);
  } else if (el.hasAttribute("data-clear")) {
    clearAll();
  } else if (el.hasAttribute("data-all")) {
    state.selCats = []; state.selThemes = []; render();
  } else if (el.hasAttribute("data-cat")) {
    toggleCat(el.getAttribute("data-cat"));
  } else if (el.hasAttribute("data-theme-name")) {
    toggle("selThemes", themeKey(el.getAttribute("data-theme-cat"), el.getAttribute("data-theme-name")));
  } else if (el.hasAttribute("data-job")) {
    toggle("selJobs", el.getAttribute("data-job"));
  }
});

searchInput.addEventListener("input", e => { state.q = e.target.value; render(); });
clearQueryBtn.addEventListener("click", () => { state.q = ""; searchInput.value = ""; render(); });
collapseBtn.addEventListener("click", () => { state.collapsed = !state.collapsed; render(); });

/* ------------------------------------------------------------------ *
 * Boot
 * ------------------------------------------------------------------ */

for (const el of document.querySelectorAll("[data-total]")) el.textContent = TOTAL;
render();
