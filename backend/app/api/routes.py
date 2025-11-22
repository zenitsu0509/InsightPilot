from collections import defaultdict
from typing import Optional, List, Dict

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.agents.graph import create_agent_graph
from app.services.csv_loader import ingest_csv_dataset

router = APIRouter()
agent_graph = create_agent_graph()
session_histories: Dict[str, List[dict]] = defaultdict(list)

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"


class SessionResetRequest(BaseModel):
    session_id: str

@router.post("/analyze")
async def analyze_data(request: QueryRequest):
    try:
        history = list(session_histories.get(request.session_id, []))
        initial_state = {"query": request.query, "history": history}
        result = agent_graph.invoke(initial_state)
        
        # Construct response
        response = {
            "status": "success",
            "query": result.get("query"),
            "sql_query": result.get("sql_query"),
            "data": result.get("data"),
            "insights": result.get("insights"),
            "visualization_url": None,
            "visualization_summary": result.get("visualization_summary"),
            "report_url": None,
            "error": result.get("error")
        }
        
        if result.get("visualization_path"):
            # Convert path to URL (assuming static mount)
            filename = result["visualization_path"].split("\\")[-1].split("/")[-1]
            response["visualization_url"] = f"/static/{filename}"
            
        if result.get("report_path"):
            filename = result["report_path"].split("\\")[-1].split("/")[-1]
            response["report_url"] = f"/static/{filename}"

        if not result.get("error"):
            session_histories[request.session_id].append(
                {
                    "question": request.query,
                    "insights": result.get("insights", ""),
                    "sql": result.get("sql_query", ""),
                }
            )
            # limit memory
            session_histories[request.session_id] = session_histories[request.session_id][-10:]
            
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.post("/upload-csv")
async def upload_csv_dataset(
    file: UploadFile = File(...),
    table_name: str = Form("sales")
):
    try:
        payload = ingest_csv_dataset(file, table_name)
        return {"status": "success", **payload}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/session/reset")
async def reset_session(req: SessionResetRequest):
    session_histories.pop(req.session_id, None)
    return {"status": "cleared", "session_id": req.session_id}
