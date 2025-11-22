# InsightPilot – Autonomous Analytics Agent

InsightPilot is a production-style AI analyst that turns natural-language business questions into validated SQL, visualizations, insights, and executive-ready PDF reports. The stack combines LangGraph (deterministic agent workflow), FastAPI, SQLAlchemy, ReportLab, and a modern React dashboard.

## Highlights

- **Deterministic LangGraph workflow** – intent → schema discovery → NL2SQL → validation → execution → visualization → insights → PDF.
- **Groq Llama‑3 NL→SQL** – high-quality SQL for complex joins and aggregations.
- **Auto schema discovery & seed data** – SQLite demo DB is generated on boot so the agent always has tables to explore.
- **Insight-rich PDFs** – ReportLab/Platypus layout with SQL, insights, data preview, and embedded Matplotlib charts.
- **React analyst cockpit** – quick prompts, streaming conversation, scrollable “Latest Analysis” pane, instant PDF downloads.

## Architecture

| Layer | Tech | Notes |
| --- | --- | --- |
| API & Orchestration | FastAPI + LangGraph | Defines graph nodes for schema, NL2SQL, execution, viz, insight, and report building. |
| LLM | Groq `llama3-70b-8192` | Deterministic, low-latency NL2SQL + insight generation. |
| Data | SQLite via SQLAlchemy | Auto-generated `sales` dataset for local testing. |
| Visualization & Reports | Matplotlib, ReportLab/Platypus | Charts saved to `backend/static`, referenced in UI/PDF. |
| Frontend | React + Vite | Modern dashboard with prompt chips, chat, result stack, PDF download. |

## Prerequisites

- Python 3.9+
- Node.js 16+
- Groq API Key (for NL2SQL + insight generation)

## Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # add GROQ_API_KEY and optional DATABASE_URL
python create_db.py             # optional; startup also seeds the sales table
python -m app.main              # runs on http://localhost:8000
```

`DATABASE_URL` defaults to `sqlite:///./test.db`. Ensure the `.env` file includes your `GROQ_API_KEY` for Groq access.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

## Usage Flow

1. Start backend and frontend dev servers.
1. Upload your CSV via the “Dataset Control” card (or call `POST /api/upload-csv` with `file` + `table_name`). InsightPilot loads it into the configured database table (defaults to `sales`).
1. Open the React app, pick a quick prompt (e.g., “What were total sales by category?”) or type your own.
1. InsightPilot:

    - Reads DB schema & crafts SQL via Groq Llama‑3.
    - Executes SQL with SQLAlchemy/Pandas.
    - Generates Matplotlib charts and Groq insight summaries.
    - Streams insights to the chat, shows SQL/data preview, and produces a PDF.

1. Download the PDF to share with stakeholders.

## Project Structure

```text
backend/
  app/
    agents/graph.py          # LangGraph workflow
    api/routes.py            # FastAPI routes
    core/config.py           # Settings + env
    db/database.py           # Engine + auto seed
    services/pdf_generator.py# ReportLab report builder
  static/                    # Generated charts & PDFs
  create_db.py               # Manual seed script
  requirements.txt

frontend/
  src/App.jsx, App.css       # React dashboard
  package.json
```

## Future Ideas

- Intent-specific LangGraph branches (comparison vs. forecasting).
- Supabase/Postgres adapters with connection pooling.
- Auth + team workspaces for insights and PDF history.

Enjoy exploring data with InsightPilot! 🚀
