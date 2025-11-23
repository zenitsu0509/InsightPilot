---
title: InsightPilot - Autonomous Analytics Agent
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.16.0
app_file: app.py
pinned: false
license: mit
python_version: 3.10
---

# InsightPilot – Autonomous Analytics Agent

<div align="center">

[![Powered by LangGraph](https://img.shields.io/badge/Powered%20by-LangGraph-blue)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green)](https://fastapi.tiangolo.com/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama--3-orange)](https://groq.com/)

</div>

InsightPilot is a production-ready AI analyst that transforms natural language questions into validated SQL queries, interactive visualizations, comprehensive insights, and executive-ready PDF reports.

## 🌟 Features

- **🤖 Agentic LangGraph Pipeline** – Deterministic tool-calling workflow (intent → schema → NL2SQL → execution → diagnostics → visualization → PDF)
- **📊 Advanced Analytics** – Automated trend detection and anomaly analysis with statistical insights
- **📄 PDF Report Generation** – Executive-ready reports with branded title pages, charts, and SQL appendix
- **📁 Multi-table Support** – Easy CSV upload and dataset catalog management
- **⚡ Real-time Streaming** – Live insights streamed to the UI as they're generated
- **🔍 Groq Llama-3 Powered** – Low-latency NL→SQL and narrative insight generation

## 🚀 Quick Start on Hugging Face Spaces

1. **Set Environment Variables** (Required)
   - Go to Settings → Repository Secrets
   - Add `GROQ_API_KEY` with your Groq API key ([Get one here](https://console.groq.com/))

2. **Upload Your Data** (Optional)
   - Use the "Upload Dataset" tab to add your CSV files
   - Or work with the pre-loaded sample sales dataset

3. **Ask Questions**
   - Use the Analytics Dashboard to ask natural language questions
   - Example: "What were the total sales by category last quarter?"
   - Get SQL, visualizations, insights, and downloadable PDF reports

## 🏗️ Architecture

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM Orchestration** | LangGraph + Groq Llama-3 70B | Deterministic agent workflow with tool calling |
| **API & Backend** | FastAPI + SQLAlchemy | RESTful API, database management |
| **Analytics** | Pandas, NumPy, SciPy | Trend detection, anomaly analysis |
| **Visualization** | Matplotlib, ReportLab | Charts and PDF report generation |
| **Database** | SQLite | Lightweight, persistent data storage |
| **Frontend** | React + Vite (optional) | Modern interactive dashboard |
| **Interface** | Gradio | HF Spaces integration |

## 📊 Advanced Analytics Modules

- **Trend Detection**: Time series regression analysis with slope quantification and % change metrics
- **Anomaly Detection**: Z-score based statistical outlier identification
- **Insight Generation**: Context-aware narrative summaries powered by Groq LLM

## 🛠️ Tech Stack

```
Backend:  FastAPI + LangGraph + LangChain + Groq
Data:     SQLite + SQLAlchemy + Pandas
Viz:      Matplotlib + ReportLab/Platypus
Frontend: React + Vite (embedded in Gradio)
Deploy:   Hugging Face Spaces (Gradio SDK)
```

## 📁 Project Structure

```
.
├── app.py                      # Gradio wrapper for HF Spaces
├── requirements.txt            # Python dependencies
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── agents/graph.py    # LangGraph workflow
│   │   ├── api/routes.py      # API endpoints
│   │   ├── core/config.py     # Settings & environment
│   │   ├── db/database.py     # Database engine & seeding
│   │   └── services/          # Analytics, PDF, CSV modules
│   ├── static/                # Generated charts & PDFs
│   └── requirements.txt       # Backend-specific deps
├── frontend/                  # React dashboard (optional)
└── data/                      # Sample datasets

```

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM access | ✅ Yes |
| `DATABASE_URL` | Database connection string | ⚪ Optional (defaults to SQLite) |

## 📖 Usage Examples

**Question:** "What were the top 5 products by revenue last year?"

**InsightPilot will:**
1. ✅ Analyze your database schema
2. ✅ Generate optimized SQL query
3. ✅ Execute query and validate results
4. ✅ Create visualizations (bar charts, trends)
5. ✅ Perform trend & anomaly analysis
6. ✅ Generate narrative insights
7. ✅ Build downloadable PDF report

## 🎯 Use Cases

- **Business Analytics**: Ad-hoc reporting without SQL knowledge
- **Executive Briefings**: Automated PDF reports with insights
- **Data Exploration**: Quick analysis of uploaded CSV datasets
- **Trend Analysis**: Automated time-series analytics
- **Anomaly Detection**: Statistical outlier identification

## 🚧 Limitations & Notes

- **Free HF Spaces**: CPU-only tier; suitable for moderate traffic
- **Database**: SQLite with persistent storage (50GB limit)
- **File Cleanup**: Old PDFs/charts should be periodically removed
- **Concurrent Users**: May need rate limiting for production use

## 🔮 Future Enhancements

- Multi-tenant workspaces with authentication
- Postgres/Supabase adapter for production databases
- Real-time collaborative dashboards
- Forecast & prediction modules
- Custom visualization templates

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.

## 🔗 Links

- **Repository**: [GitHub](https://github.com/zenitsu0509/InsightPilot)
- **Documentation**: See original README in repo
- **Groq Platform**: [Get API Key](https://console.groq.com/)

---

**Built with ❤️ using LangGraph, FastAPI, and Groq**
