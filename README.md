# 📘 PadhAI – AI Study Assistant

**PadhAI** is an AI-powered personalized study assistant built to help students **learn from their own study materials** instead of generic internet answers.
It uses **Retrieval-Augmented Generation (RAG)** to let users chat with PDFs, generate quizzes, flashcards, summaries, and structured study plans — all inside one platform.

🔗 **GitHub Repository**
[https://github.com/rahul547-king/padhAI](https://github.com/rahul547-king/padhAI)

---

## 🚀 Features

### 🔍 Chat With Your Notes (RAG-Based)

* Upload PDFs (notes, books, syllabus)
* Ask questions in natural language
* Answers are **strictly grounded in the selected PDF**
* Prevents mixing content across multiple documents

### 🧠 AI Study Tools

* **Smart Question Answering**
* **Quiz Generator**

  * MCQ, True/False, Short answers
  * Auto-grading with explanations
* **Flashcard Generator**

  * AI-generated revision cards
  * Stored per user in Firestore
* **Exam-Oriented Summaries**
* **Socratic Tutor Mode** (guided learning approach)

### 📅 Study Planner

* Generates structured weekly study plans
* Based on syllabus text, available hours, and goals
* Saved per user in Firestore

### 🔐 Authentication & User Data

* Firebase Authentication (Email/Password + Google)
* User-specific:

  * PDFs
  * Chats
  * Quizzes
  * Flashcards
  * Study plans

### ⚡ Performance Optimized

* Local embeddings supported (`SentenceTransformer`)
* ChromaDB vector store
* Minimal Gemini API usage to reduce quota issues

---

## 🏗️ System Architecture (RAG Pipeline)

1. User uploads a PDF
2. Text extracted using **PyMuPDF**
3. Text is chunked intelligently
4. Chunks converted to embeddings
5. Stored in **ChromaDB (per user)**
6. User asks a question
7. Relevant chunks retrieved (MMR-based)
8. Gemini generates a **context-grounded answer**

✅ Accurate
✅ PDF-scoped
✅ Hallucination-resistant

---

## 🧰 Tech Stack

### Frontend

* HTML5
* CSS3
* Vanilla JavaScript

### Backend

* Python (Flask)
* Gemini API (LLM)
* Sentence Transformers (local embeddings)
* PyMuPDF

### Database & Storage

* Firebase Authentication
* Firebase Firestore
* Firebase Storage
* ChromaDB (Vector Database)

---

## 📁 Updated Project Structure

```
padhAI/
│
├── routes/
│   ├── auth_routes.py
│   ├── chat_routes.py
│   ├── flashcard_routes.py
│   ├── pages_routes.py
│   ├── planner_routes.py
│   └── upload_routes.py
│
├── services/
│   ├── chat_history.py
│   ├── firestore_chat.py
│   ├── firestore_flashcards.py
│   ├── flashcard_generator.py
│   ├── gemini_client.py
│   ├── local_embeddings.py
│   ├── pdf_loader.py
│   ├── quiz_generator.py
│   ├── rag_pipeline.py
│   ├── text_chunker.py
│   └── vector_store.py
│
├── static/
│   ├── app.js
│   ├── firebase_client.js
│   ├── firebase_config.js
│   ├── flashcards_dashboard.css
│   ├── flashcards_dashboard.js
│   ├── quiz_dashboard.css
│   ├── quiz_dashboard.js
│   └── styles.css
│
├── templates/
│   ├── index.html
│   └── flashcards_dashboard.html
│
├── utils/
│   └── auth_guard.py
│
├── data/                 # ChromaDB storage
├── venv/
├── .env
├── .gitignore
├── app.py
├── config.py
├── firebase_init.py
├── firebase_key.json
├── requirements.txt
├── test_rag.py
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/rahul547-king/padhAI.git
cd padhAI
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# or
source venv/bin/activate   # Linux / macOS
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
FIREBASE_CREDENTIALS=firebase_key.json
CHROMA_PATH=data/chroma
```

(Optional but recommended)

```env
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

---

### 5️⃣ Run the Application

```bash
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

---

## 🎯 Academic Outcomes

* Demonstrates **RAG-based AI system**
* Secure authentication and user-scoped data
* Practical application of NLP + Vector Databases
* Scalable full-stack AI project suitable for:

  * Semester project
  * Final year project
  * AI portfolio showcase

---

## 🚧 Future Improvements

* Flashcard spaced repetition
* Performance analytics dashboard
* Mobile-responsive PWA
* Offline PDF indexing
* Teacher / Admin dashboards

---

## 📄 License

This project is developed for **academic and learning purposes**.
License can be added in future releases.

---

⭐ **If you find this project helpful, please star the repository!**

