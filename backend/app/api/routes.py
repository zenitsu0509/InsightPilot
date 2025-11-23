from collections import defaultdict
from decimal import Decimal
import math
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.agents.graph import create_agent_graph
from app.services.csv_loader import ingest_csv_dataset, list_dataset_tables

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - numpy optional at runtime
    np = None

router = APIRouter()
agent_graph = create_agent_graph()
session_histories: Dict[str, List[dict]] = defaultdict(list)


def _sanitize_for_json(value: Any):
    """Recursively coerce values so FastAPI's JSON encoding never sees NaN/Inf."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Decimal):
        as_float = float(value)
        return as_float if math.isfinite(as_float) else None
    if np is not None:
        if isinstance(value, (np.floating, np.integer)):
            coerced = value.item()
            if isinstance(coerced, float) and not math.isfinite(coerced):
                return None
            return coerced
        if isinstance(value, np.ndarray):
            return [_sanitize_for_json(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {key: _sanitize_for_json(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_sanitize_for_json(item) for item in value]
    # Fallback to string representation for unsupported objects (e.g., Timestamp)
    return str(value)


def _safe_json(payload: Any) -> JSONResponse:
    sanitized = _sanitize_for_json(payload)
    encoded = jsonable_encoder(
        sanitized,
        custom_encoder={
            float: lambda v: v if math.isfinite(v) else None,
            Decimal: lambda v: float(v) if math.isfinite(float(v)) else None,
        },
    )
    return JSONResponse(content=encoded)

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
            "trend_analysis": result.get("trend_analysis"),
            "anomaly_analysis": result.get("anomaly_analysis"),
            "forecast_analysis": result.get("forecast_analysis"),
            "statistical_tests": result.get("statistical_tests"),
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
            
        return _safe_json(response)
        
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
        return _safe_json({"status": "success", **payload})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/datasets")
async def get_dataset_catalog():
    try:
        catalog = list_dataset_tables()
        return _safe_json({"tables": catalog})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/session/reset")
async def reset_session(req: SessionResetRequest):
    session_histories.pop(req.session_id, None)
    return _safe_json({"status": "cleared", "session_id": req.session_id})
