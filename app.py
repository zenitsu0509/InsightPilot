import gradio as gr
import os
import sys
import uvicorn
from threading import Thread
import time
import shutil

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.main import app as fastapi_app

# Set up paths for HF Spaces
STATIC_DIR = "backend/static"
FRONTEND_BUILD_DIR = "frontend/dist"
DB_PATH = "test.db"

os.makedirs(STATIC_DIR, exist_ok=True)

def start_fastapi():
    """Start FastAPI server in background thread"""
    uvicorn.run(fastapi_app, host="0.0.0.0", port=7860, log_level="info")

# Start FastAPI in a separate thread
fastapi_thread = Thread(target=start_fastapi, daemon=True)
fastapi_thread.start()

# Give FastAPI time to start
time.sleep(2)

# Create Gradio interface
with gr.Blocks(title="InsightPilot - Autonomous Analytics Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🚀 InsightPilot – Autonomous Analytics Agent
    
    An AI-powered analyst that turns natural language questions into SQL queries, visualizations, and executive-ready PDF reports.
    
    **Powered by:** LangGraph + FastAPI + Groq Llama-3
    """)
    
    with gr.Tab("📊 Analytics Dashboard"):
        gr.Markdown("""
        ### Access the full React dashboard below
        
        The dashboard provides:
        - Natural language query interface
        - Real-time SQL generation and execution
        - Interactive visualizations
        - PDF report generation
        - Dataset management and CSV upload
        """)
        
        # Embed the React app if built, otherwise show API info
        if os.path.exists(FRONTEND_BUILD_DIR):
            gr.HTML(f"""
            <iframe src="/frontend" width="100%" height="800px" frameborder="0"></iframe>
            """)
        else:
            gr.Markdown("""
            ⚠️ **Frontend not built yet.** 
            
            To build the frontend:
            ```bash
            cd frontend
            npm install
            npm run build
            ```
            
            For now, you can interact with the API directly at the endpoints below.
            """)
    
    with gr.Tab("🔧 API Access"):
        gr.Markdown("""
        ### Direct API Endpoints
        
        - **Base URL:** `http://localhost:7860/api`
        - **Query Analysis:** `POST /api/analyze` - Send natural language questions
        - **Upload CSV:** `POST /api/upload-csv` - Upload datasets
        - **List Datasets:** `GET /api/datasets` - View available tables
        - **API Docs:** [Interactive Swagger UI](http://localhost:7860/docs)
        
        ### Quick Test
        """)
        
        with gr.Row():
            question_input = gr.Textbox(
                label="Ask a Question",
                placeholder="What were the total sales by category?",
                lines=2
            )
            submit_btn = gr.Button("Analyze", variant="primary")
        
        result_output = gr.JSON(label="Analysis Result")
        
        def analyze_question(question):
            """Call the FastAPI analyze endpoint"""
            import requests
            try:
                response = requests.post(
                    "http://localhost:7860/api/analyze",
                    json={"question": question},
                    timeout=60
                )
                return response.json()
            except Exception as e:
                return {"error": str(e)}
        
        submit_btn.click(
            fn=analyze_question,
            inputs=[question_input],
            outputs=[result_output]
        )
    
    with gr.Tab("📤 Upload Dataset"):
        gr.Markdown("""
        ### Upload CSV Dataset
        
        Upload your own CSV files to analyze custom data.
        """)
        
        with gr.Row():
            csv_file = gr.File(label="Select CSV File", file_types=[".csv"])
            table_name = gr.Textbox(
                label="Table Name",
                placeholder="sales_data",
                value="uploaded_data"
            )
        
        upload_btn = gr.Button("Upload", variant="primary")
        upload_result = gr.Textbox(label="Upload Status", lines=3)
        
        def upload_csv(file, table):
            """Upload CSV to the database"""
            import requests
            try:
                if file is None:
                    return "Please select a CSV file"
                
                with open(file.name, 'rb') as f:
                    files = {'file': (os.path.basename(file.name), f, 'text/csv')}
                    data = {'table_name': table}
                    response = requests.post(
                        "http://localhost:7860/api/upload-csv",
                        files=files,
                        data=data,
                        timeout=30
                    )
                    if response.status_code == 200:
                        result = response.json()
                        return f"✅ Success! Uploaded {result.get('rows', 0)} rows to table '{table}'"
                    else:
                        return f"❌ Error: {response.text}"
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        upload_btn.click(
            fn=upload_csv,
            inputs=[csv_file, table_name],
            outputs=[upload_result]
        )
    
    with gr.Tab("ℹ️ About"):
        gr.Markdown("""
        ## About InsightPilot
        
        InsightPilot is a production-style AI analyst that combines:
        
        - **Agentic LangGraph Pipeline:** Deterministic tool-calling workflow
        - **Advanced Analytics:** Automated trend detection and anomaly analysis
        - **PDF Reports:** Executive-ready reports with visualizations
        - **Multi-table Support:** Easy CSV upload and dataset management
        
        ### Tech Stack
        - **Backend:** FastAPI + LangGraph + SQLAlchemy
        - **LLM:** Groq Llama-3 (70B)
        - **Frontend:** React + Vite
        - **Database:** SQLite
        - **Visualization:** Matplotlib + ReportLab
        
        ### Environment Variables
        Make sure to set your `GROQ_API_KEY` in the Hugging Face Space secrets!
        
        ### Repository
        [View on GitHub](https://github.com/zenitsu0509/InsightPilot)
        """)

# Mount frontend if built
if os.path.exists(FRONTEND_BUILD_DIR):
    from fastapi.staticfiles import StaticFiles
    fastapi_app.mount("/frontend", StaticFiles(directory=FRONTEND_BUILD_DIR, html=True), name="frontend")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
