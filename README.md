# PaperLens AI

Understand research. Without the complexity.

A full-stack research-paper explainer built around PDF extraction, grounded analysis, RAG-style paper chat, quizzes, concepts, references, history, and a safe demo/mock mode.

## Stack
- Frontend: React + Vite + CSS
- Backend: FastAPI + SQLAlchemy + JWT
- Database: PostgreSQL (SQLite fallback for local demo)
- PDF: PyMuPDF
- AI: OpenAI-compatible API through a provider adapter; deterministic mock mode when no key is configured
- Vector search: optional pgvector; lexical retrieval fallback is included for easy setup

## Run
### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend expects `VITE_API_URL=http://localhost:8000/api`.

### PostgreSQL
For the fastest demo, leave `DATABASE_URL=sqlite:///./paperlens.db`. For production use PostgreSQL and optionally enable pgvector.

## AI configuration
Set `AI_API_KEY`, `AI_BASE_URL`, and `AI_MODEL` in `backend/.env`. If `AI_API_KEY` is blank, PaperLens runs in safe demo mode and clearly labels generated demo content.

## Features implemented
- Registration/login with hashed passwords and JWT
- PDF upload and text extraction
- Paper analysis with structured output
- Source-grounded chat with page references where available
- Summary modes, beginner explanation, methodology, results, concepts, quiz, flashcards, references
- Paper history and dashboard statistics
- Demo paper
- Dark/light mode
- Responsive UI
- Safe validation and ownership checks
- Export to TXT/Markdown from the UI

See the API docs at `http://localhost:8000/docs`.
