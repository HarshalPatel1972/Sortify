# Question Bank Sorter

A robust tool to split, deduplicate, and cluster PDF question banks into per-topic PDFs.

## Architecture
- **Backend:** FastAPI, SQLite (via SQLAlchemy), RQ/Redis
- **Frontend:** React, Vite, TailwindCSS
- **ML:** `sentence-transformers` for local embeddings, `scikit-learn` for clustering
- **LLM Integration:** Minimal generative AI calls for cluster labeling via Gemini and Groq.

## Getting Started

1. Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
2. Start the application stack:
   ```bash
   docker-compose up -d --build
   ```
3. Open http://localhost:5173 to access the frontend.
