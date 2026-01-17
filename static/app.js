"use strict";

/* -------------------------
   Element Registry
-------------------------- */
const elements = {
  messagesContainer: document.getElementById("messagesContainer"),
  welcomeScreen: document.getElementById("welcomeScreen"),
  userMessage: document.getElementById("userMessage"),
  sendBtn: document.getElementById("sendMessageBtn"),
  chatHistory: document.getElementById("chatHistory"),

  uploadTrigger: document.getElementById("uploadTrigger"),
  pdfUpload: document.getElementById("pdfUpload"),
  quizTrigger: document.getElementById("quizTrigger"),

  newChatBtn: document.getElementById("newChatBtn"),
  collapseToggle: document.getElementById("collapseToggle"),
  sidebar: document.getElementById("sidebar"),
  historySearch: document.getElementById("historySearch"),
  themeToggle: document.getElementById("themeToggle"),

  currentChatTitle: document.getElementById("currentChatTitle"),
  currentDocBadge: document.getElementById("currentDocBadge"),
  docNameDisplay: document.getElementById("docNameDisplay"),

  toastContainer: document.getElementById("toastContainer"),

  // Auth
  openAuthBtn: document.getElementById("openAuthBtn"),
  logoutBtn: document.getElementById("logoutBtn"),
  authModal: document.getElementById("authModal"),
  closeAuthBtn: document.getElementById("closeAuthBtn"),
  googleLoginBtn: document.getElementById("googleLoginBtn"),

  authEmail: document.getElementById("authEmail"),
  authPass: document.getElementById("authPass"),

  authName: document.getElementById("authName"),
  authPhone: document.getElementById("authPhone"),
  registerOnlyFields: document.getElementById("registerOnlyFields"),
  passwordRow: document.getElementById("passwordRow"),

  loginBtn: document.getElementById("loginBtn"),
  registerBtn: document.getElementById("registerBtn"),

  toggleAuthModeBtn: document.getElementById("toggleAuthModeBtn"),
  authModeHint: document.getElementById("authModeHint"),

  authMini: document.getElementById("authMini"),
  authMiniName: document.getElementById("authMiniName"),
  authMiniEmail: document.getElementById("authMiniEmail"),
};

/* -------------------------
   State
-------------------------- */
let typingIndicator = null;
let currentChatId = null;
let currentChatIndex = -1;

let currentDocId = localStorage.getItem("currentDocId") || null;
let currentDocName = localStorage.getItem("currentDocName") || null;

// Firebase Auth state
let fbAuth = null;

let authBusy = false;
function setAuthBusy(isBusy) {
  authBusy = !!isBusy;
  if (elements.googleLoginBtn) elements.googleLoginBtn.disabled = authBusy;
  if (elements.loginBtn) elements.loginBtn.disabled = authBusy;
  if (elements.registerBtn) elements.registerBtn.disabled = authBusy;
  if (elements.toggleAuthModeBtn) elements.toggleAuthModeBtn.disabled = authBusy;
}

/* -------------------------
   Safe event helper
-------------------------- */
function on(el, event, handler, opts) {
  if (!el) return;
  el.addEventListener(event, handler, opts);
}

/* -------------------------
   Auth headers
-------------------------- */
function getAuthHeaders(isJson = true) {
  const token = localStorage.getItem("firebaseToken");
  const headers = isJson ? { "Content-Type": "application/json" } : {};
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

/* -------------------------
   UI helpers
-------------------------- */
function autoGrowTextarea() {
  if (!elements.userMessage) return;
  elements.userMessage.style.height = "auto";
  elements.userMessage.style.height = `${Math.min(elements.userMessage.scrollHeight, 160)}px`;
}

function updateSendButtonState() {
  if (!elements.userMessage || !elements.sendBtn) return;
  const hasContent = elements.userMessage.value.trim().length > 0;
  elements.sendBtn.disabled = !hasContent;
  elements.sendBtn.classList.toggle("disabled", !hasContent);
}

function showToast(message, type = "success") {
  const container = elements.toastContainer;
  if (!container) return;

  const existing = [...container.querySelectorAll(".toast")].some(
    (t) => t.textContent === message
  );
  if (existing) return;

  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

function setDocBadge() {
  if (!elements.currentDocBadge || !elements.docNameDisplay) return;

  if (currentDocId) {
    elements.currentDocBadge.style.display = "flex";
    elements.docNameDisplay.textContent = currentDocName || "document.pdf";
  } else {
    elements.currentDocBadge.style.display = "none";
    elements.docNameDisplay.textContent = "document.pdf";
  }
}

/* -------------------------
   Formatting
-------------------------- */
function escapeHtml(unsafe = "") {
  return String(unsafe)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatBotResponse(text) {
  let t = escapeHtml(text);
  t = t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/`([^`]+)`/g, "<code class='inline-code'>$1</code>");

  const lines = t.split("\n");
  let html = "";
  let inList = false;

  for (const line of lines) {
    const trimmed = line.trim();

    if (/^[-•*]\s+/.test(trimmed)) {
      if (!inList) {
        html += "<ul class='bot-list'>";
        inList = true;
      }
      html += `<li>${trimmed.replace(/^[-•*]\s+/, "")}</li>`;
      continue;
    }

    if (inList) {
      html += "</ul>";
      inList = false;
    }

    if (/^[A-Za-z0-9 ()\/\-]+:\s*$/.test(trimmed)) {
      html += `<div class="bot-section">${trimmed}</div>`;
      continue;
    }

    if (trimmed) html += `<div class="bot-line">${trimmed}</div>`;
    else html += `<div class="bot-gap"></div>`;
  }

  if (inList) html += "</ul>";
  return html;
}

/* -------------------------
   Messages
-------------------------- */
function renderMessage(content, role) {
  if (!content || !elements.messagesContainer) return;

  if (elements.welcomeScreen) elements.welcomeScreen.style.display = "none";

  const msg = document.createElement("div");
  msg.className = `message ${role}`;

  if (role === "bot") msg.innerHTML = formatBotResponse(content);
  else msg.textContent = content;

  const actions = document.createElement("div");
  actions.className = "message-actions";

  const copyBtn = document.createElement("button");
  copyBtn.className = "action-icon";
  copyBtn.type = "button";
  copyBtn.title = "Copy";
  copyBtn.innerHTML = `<i class="fa-solid fa-copy"></i>`;
  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(content);
      showToast("Copied to clipboard", "success");
    } catch {
      showToast("Copy failed", "error");
    }
  });

  actions.appendChild(copyBtn);
  msg.appendChild(actions);

  elements.messagesContainer.appendChild(msg);
  elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

/* -------------------------
   Typing indicator
-------------------------- */
function showTyping() {
  if (typingIndicator || !elements.messagesContainer) return;

  typingIndicator = document.createElement("div");
  typingIndicator.className = "typing-message";
  typingIndicator.innerHTML = `
    <span class="thinking-text">PadhAI is thinking</span>
    <div class="typing-dots"><span></span><span></span><span></span></div>
  `;

  elements.messagesContainer.appendChild(typingIndicator);
  elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

function hideTyping() {
  if (typingIndicator) {
    typingIndicator.remove();
    typingIndicator = null;
  }
}

/* -------------------------
   Send message
-------------------------- */
async function sendMessage() {
  const text = elements.userMessage?.value?.trim();
  if (!text) return;

  if (!currentDocId) {
    renderMessage("Please upload and select a PDF first.", "bot");
    showToast("No document selected", "error");
    return;
  }

  renderMessage(text, "user");

  elements.userMessage.value = "";
  autoGrowTextarea();
  updateSendButtonState();

  if (elements.sendBtn) elements.sendBtn.disabled = true;
  showTyping();

  try {
    const res = await fetch("/chat/", {
      method: "POST",
      headers: getAuthHeaders(true),
      body: JSON.stringify({
        question: text,
        chat_id: currentChatId,
        doc_id: currentDocId,
      }),
    });

    const data = await res.json();
    hideTyping();

    if (!res.ok) {
      renderMessage(data.error || "Server error occurred", "bot");
      showToast("Failed to get response", "error");
      return;
    }

    renderMessage(data.answer || "No response received", "bot");

    if (data.chat_id) currentChatId = data.chat_id;
    if (data.title && elements.currentChatTitle)
      elements.currentChatTitle.textContent = data.title;

    loadChatHistory(elements.historySearch?.value || "");
  } catch (err) {
    hideTyping();
    renderMessage("Could not connect to server", "bot");
    showToast("Connection error", "error");
    console.error("[sendMessage]", err);
  } finally {
    if (elements.sendBtn) elements.sendBtn.disabled = false;
    elements.userMessage?.focus();
    updateSendButtonState();
  }
}

/* -------------------------
   Upload PDF
-------------------------- */
async function uploadPDF() {
  if (!elements.pdfUpload?.files?.length) return;

  const file = elements.pdfUpload.files[0];
  renderMessage(`Uploading "${file.name}"...`, "bot");

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/upload/pdf", {
      method: "POST",
      headers: getAuthHeaders(false),
      body: formData,
    });

    const data = await res.json();

    if (!res.ok) {
      renderMessage(data.error || "Upload failed", "bot");
      showToast("Upload failed", "error");
      return;
    }

    currentDocId = data.doc_id;
    currentDocName = data.filename || file.name;

    localStorage.setItem("currentDocId", currentDocId);
    localStorage.setItem("currentDocName", currentDocName);

    setDocBadge();

    renderMessage(`✓ "${currentDocName}" uploaded and selected`, "bot");
    showToast("PDF uploaded", "success");
  } catch (err) {
    renderMessage("Failed to upload PDF", "bot");
    showToast("Upload error", "error");
    console.error("[uploadPDF]", err);
  } finally {
    elements.pdfUpload.value = "";
  }
}

/* -------------------------
   Quiz
-------------------------- */
function goToQuizDashboard() {
  if (!currentDocId) {
    renderMessage("Please upload and select a PDF first.", "bot");
    showToast("No document selected", "error");
    return;
  }

  localStorage.setItem("currentDocId", currentDocId);
  localStorage.setItem("currentDocName", currentDocName || "document.pdf");

  window.location.href = "/quiz";
}

/* -------------------------
   Chat History
-------------------------- */
function normalizeHistoryPayload(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload && Array.isArray(payload.chats)) return payload.chats;
  if (payload && Array.isArray(payload.history)) return payload.history;
  return [];
}

async function loadChatHistory(searchTerm = "") {
  if (!elements.chatHistory) return;

  try {
    const res = await fetch("/chat/history", { headers: getAuthHeaders(false) });
    if (!res.ok) throw new Error(`History fetch failed: ${res.status}`);

    const raw = await res.json();
    let history = normalizeHistoryPayload(raw);

    const term = (searchTerm || "").trim().toLowerCase();
    if (term) {
      history = history.filter((c) =>
        (c.title || c.id || "").toLowerCase().includes(term)
      );
    }

    history.sort((a, b) => {
      const ta = new Date(a.updated_at || a.created_at || 0).getTime();
      const tb = new Date(b.updated_at || b.created_at || 0).getTime();
      return tb - ta;
    });

    elements.chatHistory.innerHTML = "";

    if (!history.length) {
      elements.chatHistory.innerHTML = `<div class="group-title">${
        term ? "No matching chats" : "No chats yet"
      }</div>`;
      return;
    }

    history.forEach((chat, index) => {
      const item = document.createElement("div");
      item.className = `history-item ${chat.id === currentChatId ? "active" : ""}`;

      const displayTitle =
        chat.title || `Chat ${String(chat.id || "").slice(0, 8) || index + 1}`;
      item.innerHTML = `
        <i class="fa-solid fa-file-lines"></i>
        <span class="title">${escapeHtml(displayTitle)}</span>
      `;

      item.addEventListener("click", () => loadSpecificChat(chat.id, index));
      elements.chatHistory.appendChild(item);
    });
  } catch (err) {
    console.error("[loadChatHistory]", err);
    elements.chatHistory.innerHTML =
      `<div class="group-title" style="color:#f87171;">Failed to load history</div>`;
  }
}

async function loadSpecificChat(chatId, index) {
  try {
    if (!elements.messagesContainer) return;

    elements.messagesContainer.innerHTML = "";
    if (elements.welcomeScreen) elements.welcomeScreen.style.display = "none";

    const res = await fetch(`/chat/${encodeURIComponent(chatId)}`, {
      headers: getAuthHeaders(false),
    });
    const data = await res.json();

    if (!res.ok || data?.error) {
      showToast(data.error || "Failed to load chat", "error");
      return;
    }

    currentChatId = chatId;
    currentChatIndex = index;

    if (elements.currentChatTitle) {
      elements.currentChatTitle.textContent =
        data.title || data?.chat?.title || "Conversation";
    }

    const messages = data.messages || data?.chat?.messages || [];
    messages.forEach((m) => {
      const role = m.role === "assistant" ? "bot" : m.role || "user";
      renderMessage(m.content || "", role);
    });

    loadChatHistory(elements.historySearch?.value || "");
  } catch (err) {
    console.error("[loadSpecificChat]", err);
    showToast("Failed to load chat", "error");
  }
}

/* -------------------------
   New Chat
-------------------------- */
function startNewChat() {
  if (elements.messagesContainer) elements.messagesContainer.innerHTML = "";
  if (elements.welcomeScreen) elements.welcomeScreen.style.display = "flex";

  if (elements.currentChatTitle)
    elements.currentChatTitle.textContent = "New Conversation";

  currentChatId = null;
  currentChatIndex = -1;

  loadChatHistory(elements.historySearch?.value || "");

  if (elements.userMessage) {
    elements.userMessage.value = "";
    autoGrowTextarea();
    updateSendButtonState();
    elements.userMessage.focus();
  }
}

/* -------------------------
   Sidebar / Theme
-------------------------- */
function toggleSidebar() {
  if (!elements.sidebar) return;
  elements.sidebar.classList.toggle("collapsed");
}

function toggleTheme() {
  const root = document.documentElement;
  const current = root.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  root.setAttribute("data-theme", next);

  const icon = elements.themeToggle?.querySelector("i");
  if (icon) icon.className = next === "dark" ? "fa-solid fa-moon" : "fa-solid fa-sun";
}

/* -------------------------
   Firebase Auth
-------------------------- */
function initFirebaseAuth() {
  if (typeof firebase === "undefined") return false;
  if (!window.FIREBASE_CONFIG || !window.FIREBASE_CONFIG.apiKey) return false;

  try {
    if (!firebase.apps || !firebase.apps.length) {
      firebase.initializeApp(window.FIREBASE_CONFIG);
    }
    fbAuth = firebase.auth();
    return true;
  } catch (e) {
    console.error("[initFirebaseAuth]", e);
    return false;
  }
}

function openAuthModal() {
  if (!elements.authModal) return;
  setAuthMode("login");
  elements.authModal.style.display = "flex";
  setTimeout(() => elements.authEmail?.focus(), 50);
}

function closeAuthModal() {
  if (!elements.authModal) return;
  elements.authModal.style.display = "none";
}

function setAuthUI(user) {
  if (elements.authMini && elements.authMiniName && elements.authMiniEmail) {
    if (user) {
      elements.authMini.style.display = "flex";
      elements.authMiniName.textContent = user.displayName || "Logged in";
      elements.authMiniEmail.textContent = user.email || "";
    } else {
      elements.authMini.style.display = "none";
      elements.authMiniName.textContent = "";
      elements.authMiniEmail.textContent = "";
    }
  }

  if (elements.openAuthBtn) elements.openAuthBtn.style.display = user ? "none" : "flex";
  if (elements.logoutBtn) elements.logoutBtn.style.display = user ? "flex" : "none";
}

async function refreshToken(user) {
  if (!user) {
    localStorage.removeItem("firebaseToken");
    return null;
  }
  try {
    const token = await user.getIdToken(true);
    localStorage.setItem("firebaseToken", token);
    return token;
  } catch (e) {
    console.error("[refreshToken]", e);
    return null;
  }
}

/* -------------------------
   Auth Mode
-------------------------- */
let authMode = "login"; // "login" | "register"

function setAuthMode(mode) {
  authMode = mode === "register" ? "register" : "login";

  if (elements.registerOnlyFields) {
    elements.registerOnlyFields.style.display = authMode === "register" ? "flex" : "none";
  }

  if (elements.authModeHint) {
    elements.authModeHint.textContent = authMode === "register" ? "Register mode" : "Login mode";
  }

  if (elements.toggleAuthModeBtn) {
    elements.toggleAuthModeBtn.textContent =
      authMode === "register" ? "Already have account?" : "Create account";
  }
}

/* -------------------------
   Login Email/Password
-------------------------- */
async function loginEmail() {
  if (!fbAuth) return showToast("Firebase not initialized", "error");
  if (authBusy) return;

  const email = (elements.authEmail?.value || "").trim();
  const pass = (elements.authPass?.value || "").trim();
  if (!email || !pass) return showToast("Enter email & password", "error");

  try {
    setAuthBusy(true);
    const cred = await fbAuth.signInWithEmailAndPassword(email, pass);
    await refreshToken(cred.user);
    showToast("Logged in", "success");
    closeAuthModal();
    loadChatHistory(elements.historySearch?.value || "");
  } catch (e) {
    console.error("[loginEmail]", e);
    showToast(e?.message || "Login failed", "error");
  } finally {
    setAuthBusy(false);
  }
}

/* -------------------------
   Register (name + phone + email + pass)
-------------------------- */
async function registerEmail() {
  if (!fbAuth) return showToast("Firebase not initialized", "error");
  if (authBusy) return;

  const name = (elements.authName?.value || "").trim();
  const phone = (elements.authPhone?.value || "").trim();
  const email = (elements.authEmail?.value || "").trim();
  const pass = (elements.authPass?.value || "").trim();

  if (!name) return showToast("Enter your name", "error");
  if (!phone) return showToast("Enter your phone number", "error");
  if (!email || !pass) return showToast("Enter email & password", "error");

  try {
    setAuthBusy(true);

    // Create user
    const cred = await fbAuth.createUserWithEmailAndPassword(email, pass);

    // Set displayName so sidebar shows name
    await cred.user.updateProfile({ displayName: name });

    // Save profile in Firestore: users/{uid}
    if (!firebase.firestore) {
      throw new Error("Firestore not loaded. Ensure firebase-firestore-compat.js is included.");
    }
    const db = firebase.firestore();
    await db.collection("users").doc(cred.user.uid).set(
      {
        name,
        phone,
        email,
        createdAt: firebase.firestore.FieldValue.serverTimestamp(),
      },
      { merge: true }
    );

    await refreshToken(cred.user);

    showToast("Registered & logged in", "success");
    closeAuthModal();
    loadChatHistory(elements.historySearch?.value || "");
  } catch (e) {
    console.error("[registerEmail]", e);
    showToast(e?.message || "Registration failed", "error");
  } finally {
    setAuthBusy(false);
  }
}

/* -------------------------
   Google login
-------------------------- */
async function loginGoogle() {
  if (!fbAuth) return showToast("Firebase not initialized", "error");
  if (authBusy) return;

  try {
    setAuthBusy(true);
    const provider = new firebase.auth.GoogleAuthProvider();
    const cred = await fbAuth.signInWithPopup(provider);
    await refreshToken(cred.user);

    showToast("Logged in with Google", "success");
    closeAuthModal();
    loadChatHistory(elements.historySearch?.value || "");
  } catch (e) {
    console.error("[loginGoogle]", e);

    if (e?.code === "auth/cancelled-popup-request") {
      showToast("Popup already open. Complete the Google login window.", "error");
    } else if (e?.code === "auth/popup-closed-by-user") {
      showToast("Popup closed. Try again.", "error");
    } else if (e?.code === "auth/popup-blocked") {
      showToast("Popup blocked. Allow popups and try again.", "error");
    } else if (e?.code === "auth/unauthorized-domain") {
      showToast("Unauthorized domain. Add your domain in Firebase Auth → Authorized domains.", "error");
    } else {
      showToast(e?.message || "Google login failed", "error");
    }
  } finally {
    setAuthBusy(false);
  }
}

async function logout() {
  try {
    if (fbAuth) await fbAuth.signOut();
  } catch (e) {
    console.error("[logout]", e);
  } finally {
    localStorage.removeItem("firebaseToken");
    setAuthUI(null);
    showToast("Logged out", "success");
    loadChatHistory(elements.historySearch?.value || "");
  }
}

/* -------------------------
   Events
-------------------------- */
on(elements.userMessage, "input", () => {
  autoGrowTextarea();
  updateSendButtonState();
});

on(elements.userMessage, "keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (!elements.sendBtn?.disabled) sendMessage();
  }
});

on(elements.sendBtn, "click", sendMessage);

on(elements.uploadTrigger, "click", () => elements.pdfUpload?.click());
on(elements.pdfUpload, "change", uploadPDF);

on(elements.quizTrigger, "click", goToQuizDashboard);

on(elements.newChatBtn, "click", startNewChat);
on(elements.collapseToggle, "click", toggleSidebar);
on(elements.historySearch, "input", (e) => loadChatHistory(e.target.value));
on(elements.themeToggle, "click", toggleTheme);

/* Auth events */
on(elements.openAuthBtn, "click", openAuthModal);
on(elements.closeAuthBtn, "click", closeAuthModal);
on(elements.authModal, "click", (e) => {
  if (e.target === elements.authModal) closeAuthModal();
});

on(elements.loginBtn, "click", loginEmail);
on(elements.registerBtn, "click", registerEmail);
on(elements.googleLoginBtn, "click", loginGoogle);
on(elements.logoutBtn, "click", logout);

on(elements.toggleAuthModeBtn, "click", () => {
  setAuthMode(authMode === "login" ? "register" : "login");
});

/* Keyboard shortcuts */
document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key.toLowerCase() === "k") {
    e.preventDefault();
    startNewChat();
  }

  if (e.key === "/" && document.activeElement !== elements.historySearch) {
    e.preventDefault();
    elements.historySearch?.focus();
  }

  if (e.key === "Escape") {
    if (elements.authModal && elements.authModal.style.display === "flex") {
      closeAuthModal();
      return;
    }
    if (elements.userMessage) {
      elements.userMessage.value = "";
      autoGrowTextarea();
      updateSendButtonState();
    }
  }
});

/* -------------------------
   Init
-------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  setDocBadge();

  loadChatHistory();
  autoGrowTextarea();
  updateSendButtonState();
  elements.userMessage?.focus();

  if (elements.welcomeScreen) elements.welcomeScreen.style.display = "flex";

  const ok = initFirebaseAuth();

  if (ok && fbAuth) {
    setAuthBusy(false);

    fbAuth.onAuthStateChanged(async (user) => {
      setAuthUI(user);
      await refreshToken(user);
      loadChatHistory(elements.historySearch?.value || "");
    });
  } else {
    setAuthUI(null);
  }

  console.log("[PadhAI] Frontend initialized (auth + register profile)");
});
