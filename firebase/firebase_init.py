import firebase_admin
from firebase_admin import credentials, firestore
from config import Config

_app = None
_db = None

def init_firebase():
    global _app, _db
    if _app is None:
        cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS)
        _app = firebase_admin.initialize_app(cred)
        _db = firestore.client()
    return _app, _db

def get_db():
    if _db is None:
        init_firebase()
    return _db
