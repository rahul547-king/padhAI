from flask import Flask, render_template
from flask_cors import CORS

# Existing blueprints
from routes.auth_routes import auth_bp
from routes.upload_routes import upload_bp
from routes.chat_routes import chat_bp

# NEW: flashcards
from routes.flashcard_routes import flash_bp

app = Flask(__name__)
CORS(app)

# Existing (unchanged)
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(upload_bp, url_prefix="/upload")
app.register_blueprint(chat_bp, url_prefix="/chat")

# ✅ Flashcards (NO extra prefix here)
app.register_blueprint(flash_bp)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/quiz")
def quiz_dashboard():
    return render_template("quiz_dashboard.html")

@app.route("/cards")
def flashcards_dashboard():
    return render_template("flashcards_dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
