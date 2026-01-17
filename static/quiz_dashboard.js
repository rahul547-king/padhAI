"use strict";

const $ = (id) => document.getElementById(id);

/* -------- Toast -------- */
function toast(msg, isBad = false) {
  const wrap = $("qdToast");
  if (!wrap) return;
  const t = document.createElement("div");
  t.className = `qd-toast ${isBad ? "bad" : ""}`;
  t.textContent = msg;
  wrap.appendChild(t);
  setTimeout(() => t.remove(), 2800);
}

/* -------- Theme -------- */
function getTheme() {
  return document.documentElement.getAttribute("data-theme") || "dark";
}
function setTheme(next) {
  document.documentElement.setAttribute("data-theme", next);
  const icon = $("qdThemeBtn")?.querySelector("i");
  if (icon) icon.className = next === "dark" ? "fa-solid fa-moon" : "fa-solid fa-sun";
}

/* -------- Auth headers (matches your chat app.js) -------- */
function getAuthHeaders(isJson = true) {
  const token = localStorage.getItem("firebaseToken");
  const headers = isJson ? { "Content-Type": "application/json" } : {};
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

/* -------- State -------- */
let docId = null;
let docName = null;

let quizId = null;
let quiz = null;
let idx = 0;

const answers = {};     // { "1": "B" | "True" | "some text" }
const marked = new Set();

let timerInterval = null;
let secondsLeft = 0;

/* -------- DOM -------- */
const dom = {
  docBadge: $("qdDocBadge"),
  docName: $("qdDocName"),
  docMissing: $("qdDocMissing"),

  count: $("qdCount"),
  difficulty: $("qdDifficulty"),
  generateBtn: $("qdGenerateBtn"),

  metaCard: $("qdMetaCard"),
  metaTitle: $("qdMetaTitle"),
  metaDiff: $("qdMetaDiff"),
  metaTime: $("qdMetaTime"),

  navCard: $("qdNavCard"),
  navGrid: $("qdNavGrid"),

  empty: $("qdEmpty"),
  player: $("qdPlayer"),
  results: $("qdResults"),

  progressText: $("qdProgressText"),
  progressFill: $("qdProgressFill"),
  timerBox: $("qdTimer"),
  timerText: $("qdTimerText"),

  typeChip: $("qdTypeChip"),
  markBtn: $("qdMarkBtn"),

  questionText: $("qdQuestionText"),
  options: $("qdOptions"),
  shortWrap: $("qdShortWrap"),
  shortInput: $("qdShortInput"),

  prevBtn: $("qdPrevBtn"),
  nextBtn: $("qdNextBtn"),
  saveBtn: $("qdSaveBtn"),
  submitBtn: $("qdSubmitBtn"),

  scoreBig: $("qdScoreBig"),
  scoreSub: $("qdScoreSub"),
  correct: $("qdCorrect"),
  incorrect: $("qdIncorrect"),
  total: $("qdTotal"),
  review: $("qdReview"),
  newQuizBtn: $("qdNewQuizBtn"),
  scrollReviewBtn: $("qdScrollReviewBtn"),

  themeBtn: $("qdThemeBtn"),
};

/* -------- Doc from localStorage --------
   We expect chat upload to store:
     localStorage.setItem("currentDocId", doc_id)
     localStorage.setItem("currentDocName", filename)
---------------------------------------- */
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

/* -------- Views -------- */
function showEmpty() {
  dom.empty.style.display = "flex";
  dom.player.style.display = "none";
  dom.results.style.display = "none";
}
function showPlayer() {
  dom.empty.style.display = "none";
  dom.player.style.display = "flex";
  dom.results.style.display = "none";
}
function showResults() {
  dom.empty.style.display = "none";
  dom.player.style.display = "none";
  dom.results.style.display = "flex";
}

/* -------- Render nav -------- */
function renderNav() {
  dom.navGrid.innerHTML = "";
  quiz.questions.forEach((q, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "qd-nav-btn";
    b.textContent = String(i + 1);

    const qid = String(q.id);
    if (answers[qid] != null && String(answers[qid]).trim() !== "") b.classList.add("answered");
    if (marked.has(qid)) b.classList.add("marked");
    if (i === idx) b.classList.add("current");

    b.addEventListener("click", () => {
      saveCurrentDraft();
      idx = i;
      renderQuestion();
    });

    dom.navGrid.appendChild(b);
  });
}

/* -------- Render question -------- */
function renderQuestion() {
  const q = quiz.questions[idx];
  if (!q) return;

  // Progress UI
  dom.progressText.textContent = `Question ${idx + 1} of ${quiz.questions.length}`;
  dom.progressFill.style.width = `${Math.round(((idx + 1) / quiz.questions.length) * 100)}%`;

  const t = (q.type || "").toLowerCase();
  dom.typeChip.textContent = t === "mcq" ? "MCQ" : (t === "tf" ? "TRUE/FALSE" : "SHORT");

  const qid = String(q.id);

  // Mark button UI
  dom.markBtn.innerHTML = marked.has(qid)
    ? `<i class="fa-solid fa-flag"></i> Marked`
    : `<i class="fa-regular fa-flag"></i> Mark`;

  // Question text
  dom.questionText.textContent = q.question || "";

  // Reset answer area
  dom.options.innerHTML = "";
  dom.shortWrap.style.display = "none";

  // Existing saved answer (if any)
  const existing = answers[qid];

  // ----- SHORT ANSWER -----
  if (t === "short") {
    dom.shortWrap.style.display = "block";
    dom.shortInput.value = typeof existing === "string" ? existing : "";

    // ✅ Auto-save while typing (current question only)
    dom.shortInput.oninput = () => {
      answers[qid] = (dom.shortInput.value || "").trim();
      renderNav();
    };

  // ----- MCQ / TRUE-FALSE -----
  } else {
    // For MCQ, your backend sends q.options = ["A","B","C","D"] text.
    // For TF, q.options = ["True", "False"].
    const opts = Array.isArray(q.options) ? q.options : [];
    const letters = ["A", "B", "C", "D"];

    opts.forEach((opt, i) => {
      // Value to send back:
      // MCQ -> "A"/"B"/"C"/"D"
      // TF  -> "True"/"False"
      const val = t === "mcq" ? letters[i] : String(opt);

      const row = document.createElement("label");
      row.className = "qd-opt";
      row.innerHTML = `
        <input type="radio" name="qd_${qid}" value="${escapeHtml(val)}">
        <div class="k">${t === "mcq" ? letters[i] : (i === 0 ? "T" : "F")}</div>
        <div class="txt">${escapeHtml(opt)}</div>
      `;

      const input = row.querySelector("input");

      // Restore existing selection
      if (
        existing != null &&
        String(existing).trim().toLowerCase() === String(val).trim().toLowerCase()
      ) {
        input.checked = true;
      }

      // ✅ Auto-save on click (most important)
      row.addEventListener("click", () => {
        input.checked = true;
        answers[qid] = input.value;
        renderNav();
      });

      // ✅ Auto-save on change (keyboard / direct radio click)
      input.addEventListener("change", () => {
        answers[qid] = input.value;
        renderNav();
      });

      dom.options.appendChild(row);
    });

    // Prevent leaking old short handler
    if (dom.shortInput) dom.shortInput.oninput = null;
  }

  // Prev/Next state
  dom.prevBtn.disabled = idx === 0;
  dom.nextBtn.disabled = idx === quiz.questions.length - 1;

  // Nav update
  renderNav();
}


/* -------- Save current answer -------- */
function saveCurrentDraft() {
  if (!quiz) return;
  const q = quiz.questions[idx];
  if (!q) return;

  const qid = String(q.id);
  const t = (q.type || "").toLowerCase();

  if (t === "short") {
    answers[qid] = (dom.shortInput.value || "").trim();
  } else {
    const checked = document.querySelector(`input[name="qd_${qid}"]:checked`);
    if (checked) answers[qid] = checked.value;
  }
}

/* -------- Timer -------- */
function formatTime(sec) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function startTimer(minutes) {
  if (!minutes || minutes <= 0) {
    dom.timerBox.style.display = "none";
    return;
  }
  secondsLeft = Math.max(60, Math.floor(minutes * 60));
  dom.timerBox.style.display = "flex";
  dom.timerText.textContent = formatTime(secondsLeft);

  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    secondsLeft--;
    dom.timerText.textContent = formatTime(Math.max(0, secondsLeft));
    if (secondsLeft <= 0) {
      clearInterval(timerInterval);
      toast("Time’s up! Submitting…", true);
      submitQuiz().catch(() => {});
    }
  }, 1000);
}

/* -------- API: Generate (YOUR route: /chat/quiz) -------- */
async function generateQuiz() {
  if (!docId) {
    toast("No PDF selected. Upload in Chat first.", true);
    return;
  }

  const num_questions = parseInt(dom.count.value || "20", 10);
  const difficulty = dom.difficulty.value || "Medium";

  dom.generateBtn.disabled = true;
  dom.generateBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Generating...`;

  try {
    const res = await fetch("/chat/quiz", {
      method: "POST",
      headers: getAuthHeaders(true),
      body: JSON.stringify({ doc_id: docId, num_questions, difficulty })
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      toast(data.error || "Quiz generation failed", true);
      return;
    }

    quizId = data.quiz_id;
    quiz = data.quiz;

    idx = 0;
    for (const k of Object.keys(answers)) delete answers[k];
    marked.clear();

    dom.metaCard.style.display = "block";
    dom.navCard.style.display = "block";
    dom.metaTitle.textContent = quiz.title || "Practice Quiz";
    dom.metaDiff.textContent = quiz.difficulty || difficulty;
    dom.metaTime.textContent = `${quiz.estimated_time_minutes || 0} mins`;

    toast("Quiz generated");
    showPlayer();

    startTimer(quiz.estimated_time_minutes || 0);
    renderQuestion();

  } catch (e) {
    console.error(e);
    toast("Server connection error", true);
  } finally {
    dom.generateBtn.disabled = false;
    dom.generateBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Generate`;
  }
}

/* -------- API: Submit (YOUR route: /chat/quiz/submit) -------- */
async function submitQuiz() {
  if (!quizId || !quiz) {
    toast("No active quiz", true);
    return;
  }

  saveCurrentDraft();

  dom.submitBtn.disabled = true;
  dom.submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Submitting...`;

  try {
    const res = await fetch("/chat/quiz/submit", {
      method: "POST",
      headers: getAuthHeaders(true),
      body: JSON.stringify({ quiz_id: quizId, answers })
    });

    const data = await res.json();

    if (!res.ok || data.error) {
      toast(data.error || "Grading failed", true);
      return;
    }

    clearInterval(timerInterval);

    dom.scoreBig.textContent = `${data.score_percent}%`;
    dom.scoreSub.textContent = `${data.correct} correct • ${data.incorrect} incorrect`;
    dom.correct.textContent = data.correct;
    dom.incorrect.textContent = data.incorrect;
    dom.total.textContent = data.total_questions;

    renderReview(data.review || []);
    showResults();
    toast("Graded");

  } catch (e) {
    console.error(e);
    toast("Server connection error", true);
  } finally {
    dom.submitBtn.disabled = false;
    dom.submitBtn.innerHTML = `Submit <i class="fa-solid fa-check"></i>`;
  }
}

function renderReview(items) {
  dom.review.innerHTML = "";
  if (!items.length) {
    dom.review.textContent = "No review available.";
    return;
  }

  items.forEach((r) => {
    const ok = !!r.is_correct;
    const div = document.createElement("div");
    div.className = "qd-rev-item";
    div.innerHTML = `
      <div class="qd-rev-head">
        <div class="qd-rev-q">${escapeHtml(`${r.id}) ${r.question || ""}`)}</div>
        <div class="qd-tag ${ok ? "ok" : "bad"}">${ok ? "Correct" : "Incorrect"}</div>
      </div>

      <div class="qd-rev-meta">
        <div><b>Your:</b> ${escapeHtml(String(r.your_answer ?? "—"))}</div>
        <div><b>Correct:</b> ${escapeHtml(String(r.correct_answer ?? "—"))}</div>
      </div>

      <div class="qd-rev-exp">${escapeHtml(String(r.explanation || ""))}</div>
    `;
    dom.review.appendChild(div);
  });
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g,"&amp;")
    .replace(/</g,"&lt;")
    .replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;")
    .replace(/'/g,"&#039;");
}

/* -------- Events -------- */
dom.generateBtn?.addEventListener("click", generateQuiz);

dom.prevBtn?.addEventListener("click", () => {
  saveCurrentDraft();
  idx = Math.max(0, idx - 1);
  renderQuestion();
});

dom.nextBtn?.addEventListener("click", () => {
  saveCurrentDraft();
  idx = Math.min(quiz.questions.length - 1, idx + 1);
  renderQuestion();
});

dom.saveBtn?.addEventListener("click", () => {
  saveCurrentDraft();
  toast("Saved");
  renderNav();
});

dom.markBtn?.addEventListener("click", () => {
  if (!quiz) return;
  const qid = String(quiz.questions[idx].id);
  if (marked.has(qid)) marked.delete(qid);
  else marked.add(qid);
  renderQuestion();
});

dom.submitBtn?.addEventListener("click", submitQuiz);

dom.newQuizBtn?.addEventListener("click", () => {
  quizId = null;
  quiz = null;
  idx = 0;
  for (const k of Object.keys(answers)) delete answers[k];
  marked.clear();
  clearInterval(timerInterval);

  dom.metaCard.style.display = "none";
  dom.navCard.style.display = "none";
  showEmpty();
});

dom.scrollReviewBtn?.addEventListener("click", () => {
  dom.review.scrollIntoView({ behavior: "smooth" });
});

dom.themeBtn?.addEventListener("click", () => {
  setTheme(getTheme() === "dark" ? "light" : "dark");
});

/* Init */
(function init() {
  loadDocFromStorage();
  setTheme(getTheme());
  showEmpty();
})();
