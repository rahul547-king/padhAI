"""
firebase_init.py

Centralized Firebase Admin initialization for PadhAI.

Env (.env)
---------
FIREBASE_CREDENTIALS=path/to/serviceAccount.json
FIREBASE_STORAGE_BUCKET=your-project.appspot.com

Firestore works without FIREBASE_STORAGE_BUCKET, but Storage uploads require it.
"""

from __future__ import annotations

import os
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore, storage

from config import Config

_APP: Optional[firebase_admin.App] = None


def ensure_firebase() -> firebase_admin.App:
    """
    Initialize Firebase Admin exactly once (per process) and return the app.

    Safe to call multiple times from anywhere (routes, auth guard, services).
    """
    global _APP

    # If we already cached it, return it
    if _APP is not None:
        return _APP

    # If firebase_admin already has an app (e.g., initialized elsewhere), use it
    if firebase_admin._apps:  # type: ignore[attr-defined]
        _APP = firebase_admin.get_app()
        return _APP

    cred_path = (Config.FIREBASE_CREDENTIALS or "").strip()
    if not cred_path:
        raise RuntimeError(
            "FIREBASE_CREDENTIALS is missing. Set it in .env, e.g.\n"
            "FIREBASE_CREDENTIALS=firebase_key.json"
        )

    cred = credentials.Certificate(cred_path)

    bucket_name = (os.getenv("FIREBASE_STORAGE_BUCKET") or "").strip()
    options = {"storageBucket": bucket_name} if bucket_name else None

    _APP = firebase_admin.initialize_app(cred, options)
    return _APP


# Backwards compatible alias (if other files call init_firebase)
def init_firebase() -> firebase_admin.App:
    return ensure_firebase()


def get_db():
    """Return Firestore client (initializes Firebase if needed)."""
    ensure_firebase()
    return firestore.client()


def get_bucket():
    """
    Return Storage bucket; raises if FIREBASE_STORAGE_BUCKET is not set.
    """
    ensure_firebase()

    bucket_name = (os.getenv("FIREBASE_STORAGE_BUCKET") or "").strip()
    if not bucket_name:
        raise RuntimeError(
            "FIREBASE_STORAGE_BUCKET is not set. Add it to .env, e.g.\n"
            "FIREBASE_STORAGE_BUCKET=your-project.appspot.com"
        )
    return storage.bucket()
