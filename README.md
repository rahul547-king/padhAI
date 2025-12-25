# 📘 Padhai – AI Study Assistant

**Padhai** is an AI-powered, personalized study assistant designed to help students learn smarter, not harder. It uses **Retrieval-Augmented Generation (RAG)** to allow students to *chat with their own study materials* (PDFs, notes, syllabus) and provides tools like AI summaries, quizzes, planners, and a focus music player — all in one platform.

🔗 **GitHub Repository:** [https://github.com/rahul547-king/padhAI](https://github.com/rahul547-king/padhAI)

---

## 🚀 Features

* 🔍 **Chat with Your Notes (RAG-based)**
  Ask questions directly from your uploaded PDFs and notes.

* 🧠 **AI-Powered Study Tools**

  * Smart Summarization
  * Practice Quiz Generator
  * Flashcard Generator
  * Socratic Tutor Mode (guides instead of direct answers)

* 📅 **Adaptive Study Planner**
  Parses syllabus files and creates balanced study routines.

* 🎧 **Focus & Wellness Hub**
  Inbuilt concentration music player (audio stored in Firebase).

* 📚 **Web Book Reader**
  Access and read public-domain books using free APIs (Gutendex / Open Library).

* 🔐 **Secure Authentication**
  Firebase Authentication with user-specific data storage.

---

## 🏗️ Project Architecture

The core of Padhai is built on a **Retrieval-Augmented Generation (RAG) pipeline**:

1. User uploads a PDF
2. Backend extracts text
3. Text is chunked and embedded using Gemini API
4. Embeddings are stored in ChromaDB / Firestore Vector Store
5. Relevant chunks are retrieved for every user query
6. Gemini API generates grounded responses

---

## 🧰 Tech Stack

### Frontend

* HTML5
* CSS3
* Vanilla JavaScript

### Backend

* Python (Flask)
* Gemini API (LLM + Embeddings)
* PyMuPDF (PDF text extraction)

### Database & Storage

* Firebase Authentication
* Firebase Firestore (NoSQL)
* Firebase Storage (PDFs & MP3 files)
* ChromaDB (Vector Database)

---

📁 Project Structure

```
padhAI/
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── firebase/
│   │   └── firebase_init.py
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── chat_routes.py
│   │   ├── planner_routes.py
│   │   └── upload_routes.py
│   ├── services/
│   │   ├── gemini_client.py
│   │   ├── pdf_loader.py
│   │   ├── rag_pipeline.py
│   │   ├── text_chunker.py
│   │   └── vector_store.py
│   ├── requirements.txt
│   └── test_rag.py
│
├── frontend/
│   ├── index.html
│   ├── assets/
│   ├── css/
│   └── js/
│
├── .env
├── .gitignore
└── README.md
```

 ⚙️ Installation & Setup

 1️⃣ Clone the Repository

```bash
git clone https://github.com/rahul547-king/padhAI.git
cd padhAI
```

2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3️⃣ Install Dependencies

```bash
pip install -r backend/requirements.txt
```

 4️⃣ Environment Variables

Create a `.env` file and add:

```
GEMINI_API_KEY=your_api_key
FIREBASE_CREDENTIALS=path_to_firebase_json
```

5️⃣ Run the Application

```bash
python backend/app.py
```

Then open `frontend/index.html` in your browser.

---

🎯 Expected Outcomes

* Fully functional AI-powered study assistant
* Personalized learning experience grounded in user data
* Improved study efficiency and engagement
* Scalable and secure architecture

---


This project is developed for academic purposes. License can be added later.

---

⭐ If you find this project helpful, don’t forget to star the repository!
