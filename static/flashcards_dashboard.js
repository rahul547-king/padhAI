"use strict";

const $ = (id) => document.getElementById(id);

function toast(msg, isBad = false) {
  const wrap = $("fcToast");
  if (!wrap) return;
  const t = document.createElement("div");
  t.className = `fc-toast ${isBad ? "bad" : ""}`;
  t.textContent = msg;
  wrap.appendChild(t);
  setTimeout(() => t.remove(), 2600);
}

function getTheme() {
  return document.documentElement.getAttribute("data-theme") || "dark";
}
function setTheme(next) {
  document.documentElement.setAttribute("data-theme", next);
  const icon = $("fcThemeBtn")?.querySelector("i");
  if (icon) icon.className = next === "dark" ? "fa-solid fa-moon" : "fa-solid fa-sun";
}

function getAuthHeaders(isJson = true) {
  const token = localStorage.getItem("firebaseToken");
  const headers = isJson ? { "Content-Type": "application/json" } : {};
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

/* -------- State -------- */
let docId = null;
let docName = null;

let deckId = null;
let deck = null;
let idx = 0;

// simple local SRS stats
const srs = {}; // { cardId: "Again|Good|Easy" }

/* -------- DOM -------- */
const dom = {
  docBadge: $("fcDocBadge"),
  docName: $("fcDocName"),
  docMissing: $("fcDocMissing"),

  count: $("fcCount"),
  mode: $("fcMode"),
  difficulty: $("fcDifficulty"),
  generateBtn: $("fcGenerateBtn"),

  metaCard: $("fcMetaCard"),
  metaTitle: $("fcMetaTitle"),
  metaMode: $("fcMetaMode"),
  metaDiff: $("fcMetaDiff"),
  metaProg: $("fcMetaProg"),

  empty: $("fcEmpty"),
  player: $("fcPlayer"),

  progressText: $("fcProgressText"),
  progressFill: $("fcProgressFill"),
  tagPill: $("fcTagPill"),
  tagText: $("fcTagText"),

  flipInner: $("fcFlipInner"),
  flipBtn: $("fcFlipBtn"),

  frontText: $("fcFrontText"),
  backText: $("fcBackText"),

  prevBtn: $("fcPrevBtn"),
  nextBtn: $("fcNextBtn"),

  againBtn: $("fcAgainBtn"),
  goodBtn: $("fcGoodBtn"),
  easyBtn: $("fcEasyBtn"),
  srsNote: $("fcSrsNote"),

  themeBtn: $("fcThemeBtn"),
};

function loadDocFromStorage() {
  docId = localStorage.getItem("currentDocId");
  docName = localStorage.getItem("currentDocName") || "document.pdf";

  if (docId) {
    dom.docBadge.style.display = "flex";
    dom.docMissing.style.display = "none";
    dom.docName.textContent = docName;
  } else {
    dom.docBadge.style.display = "none";
    dom.docMissing.style.display = "flex";
  }
}

function showEmpty() {
  dom.empty.style.display = "flex";
  dom.player.style.display = "none";
  dom.metaCard.style.display = "none";
}
function showPlayer() {
  dom.empty.style.display = "none";
  dom.player.style.display = "flex";
  dom.metaCard.style.display = "block";
}

function renderCard() {
  const c = deck?.cards?.[idx];
  if (!c) return;

  // reset flip to front
  dom.flipInner.classList.remove("flipped");

  dom.frontText.textContent = c.front || "";
  dom.backText.textContent = c.back || "";

  const total = deck.cards.length;
  dom.progressText.textContent = `Card ${idx + 1} of ${total}`;
  dom.progressFill.style.width = `${Math.round(((idx + 1) / total) * 100)}%`;

  dom.metaTitle.textContent = deck.title || "Flashcards";
  dom.metaMode.textContent = deck.mode || "mixed";
  dom.metaDiff.textContent = deck.difficulty || "Medium";
  dom.metaProg.textContent = `${idx + 1}/${total}`;

  const tag = (c.tag || "").trim();
  if (tag) {
    dom.tagPill.style.display = "flex";
    dom.tagText.textContent = tag;
  } else {
    dom.tagPill.style.display = "none";
  }

  dom.prevBtn.disabled = idx === 0;
  dom.nextBtn.disabled = idx === total - 1;

  const label = srs[String(c.id)];
  dom.srsNote.textContent = label ? `Marked: ${label}` : "Not marked yet";
}

function flip() {
  dom.flipInner.classList.toggle("flipped");
}

function markSrs(label) {
  const c = deck?.cards?.[idx];
  if (!c) return;
  srs[String(c.id)] = label;
  dom.srsNote.textContent = `Marked: ${label}`;
}

/* -------- API -------- */
async function generateDeck() {
  if (!docId) {
    toast("No PDF selected. Upload in Chat first.", true);
    return;
  }

  const count = parseInt(dom.count.value || "20", 10);
  const mode = dom.mode.value || "mixed";
  const difficulty = dom.difficulty.value || "Medium";

  dom.generateBtn.disabled = true;
  dom.generateBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating...`;

  try {
    const res = await fetch("/flashcards/generate", {
      method: "POST",
      headers: getAuthHeaders(true),
      body: JSON.stringify({ doc_id: docId, count, mode, difficulty })
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      toast(data.error || "Flashcards generation failed", true);
      return;
    }

    deckId = data.deck_id;
    deck = data.deck;
    idx = 0;

    // reset local marks
    for (const k of Object.keys(srs)) delete srs[k];

    toast("Flashcards generated");
    showPlayer();
    renderCard();
  } catch (e) {
    console.error(e);
    toast("Server connection error", true);
  } finally {
    dom.generateBtn.disabled = false;
    dom.generateBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Generate`;
  }
}

/* -------- Events -------- */
dom.generateBtn?.addEventListener("click", generateDeck);
dom.flipBtn?.addEventListener("click", flip);
$("fcFlip")?.addEventListener("click", flip);

dom.prevBtn?.addEventListener("click", () => {
  idx = Math.max(0, idx - 1);
  renderCard();
});
dom.nextBtn?.addEventListener("click", () => {
  idx = Math.min(deck.cards.length - 1, idx + 1);
  renderCard();
});

dom.againBtn?.addEventListener("click", () => markSrs("Again"));
dom.goodBtn?.addEventListener("click", () => markSrs("Good"));
dom.easyBtn?.addEventListener("click", () => markSrs("Easy"));

dom.themeBtn?.addEventListener("click", () => {
  setTheme(getTheme() === "dark" ? "light" : "dark");
});

/* Init */
(function init() {
  loadDocFromStorage();
  setTheme(getTheme());
  showEmpty();
})();
