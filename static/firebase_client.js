"use strict";

(function () {
  try {
    if (typeof firebase === "undefined") {
      console.error("[Firebase] SDK not loaded");
      window.fbAuth = null;
      return;
    }

    if (!window.FIREBASE_CONFIG) {
      console.error("[Firebase] Config missing");
      window.fbAuth = null;
      return;
    }

    // Prevent double initialization
    if (!firebase.apps.length) {
      firebase.initializeApp(window.FIREBASE_CONFIG);
    }

    // Expose auth globally
    window.fbAuth = firebase.auth();

    console.log("[Firebase] initialized successfully");
  } catch (err) {
    console.error("[Firebase] init error:", err);
    window.fbAuth = null;
  }
})();
