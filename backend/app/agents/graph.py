import json
from typing import TypedDict, Annotated, List, Union, Any

import matplotlib
import matplotlib.pyplot as plt
import os
import pandas as pd
import uuid
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.db.database import get_db_schema, engine
from app.services.pdf_generator import generate_pdf_report

matplotlib.use('Agg') # Use non-interactive backend

# Define State
class AgentState(TypedDict, total=False):
    query: str
    history: List[dict]
    schema: str
    sql_query: str
    data: Any # Pandas DataFrame as dict or list
    visualization_path: str
    visualization_summary: str
    insights: str
    report_path: str
    error: str
def _format_history(history: List[dict]) -> str:
    if not history:
        return "None"
    rendered = []
    for turn in history[-5:]:
        question = turn.get("question", "")
        answer = turn.get("insights", "")
        rendered.append(f"User: {question}\nAgent: {answer}")
    return "\n---\n".join(rendered)


# LLM Setup
def get_llm():
    if not settings.GROQ_API_KEY:
        # Fallback or mock if needed, but for now assume key is present or will fail
        return None
    return ChatGroq(
        temperature=0,
        model_name="openai/gpt-oss-120b",
        api_key=settings.GROQ_API_KEY,
    )


def _summarize_dataframe(df: pd.DataFrame) -> List[dict]:
    summary = []
    for col in df.columns:
        series = df[col]
        summary.append(
            {
                "name": col,
                "dtype": str(series.dtype),
                "numeric": pd.api.types.is_numeric_dtype(series),
                "unique_count": int(series.nunique()),
                "sample_values": series.dropna().astype(str).unique().tolist()[:3],
            }
        )
    return summary


def _fallback_chart_plan(df: pd.DataFrame) -> dict:
    numeric_cols = list(df.select_dtypes(include=["number", "bool"]).columns)
    categorical_cols = list(df.select_dtypes(include=["object", "category"]).columns)

    if categorical_cols and numeric_cols:
        return {
            "chart_type": "bar",
            "x_field": categorical_cols[0],
            "y_field": numeric_cols[0],
            "aggregation": "sum",
            "top_n": 10,
            "explanation": f"Bar chart of {numeric_cols[0]} by {categorical_cols[0]}"
        }

    if len(numeric_cols) >= 2:
        return {
            "chart_type": "line",
            "x_field": numeric_cols[0],
            "y_field": numeric_cols[1],
            "aggregation": "none",
            "top_n": 50,
            "explanation": f"Line plot of {numeric_cols[1]} vs {numeric_cols[0]}"
        }

    return {
        "chart_type": "table",
        "x_field": None,
        "y_field": None,
        "aggregation": "none",
        "top_n": 0,
        "explanation": "No suitable numeric/categorical combination for chart"
    }


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        candidate = text[start:end + 1]
        return json.loads(candidate)
    return json.loads(text)


def _suggest_chart_plan(df: pd.DataFrame, query: str) -> dict:
    plan = _fallback_chart_plan(df)
    llm = get_llm()
    if not llm:
        return plan

    columns_meta = _summarize_dataframe(df)
    sample_rows = df.head(5).to_dict(orient="records")

    template = """
    You are an analytics visualization planner. Based on the user's question, the column metadata, and sample rows, choose the most appropriate chart to highlight the insight.

    Allowed chart_type values: bar, line, area, scatter, pie, table.
    aggregation can be sum, mean, avg, average, count, or none. Use count when only frequency matters.
    Return ONLY valid JSON with keys: chart_type, x_field, y_field (nullable), aggregation, top_n (int), explanation.
    Make sure fields exist in the dataset and chart type matches their dtypes (categorical for x axis on bar/pie, numeric for y).
    Pick at most top 12 categories when using bar/pie.

    Columns: {columns}
    Sample rows: {sample}
    User question: {query}
    """

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()

    try:
        response = chain.invoke({
            "columns": json.dumps(columns_meta, ensure_ascii=False),
            "sample": json.dumps(sample_rows, ensure_ascii=False),
            "query": query,
        })
        plan = _parse_json_response(response)
    except Exception:
        # keep fallback plan
        plan.setdefault("explanation", "Heuristic visualization applied")
    return plan


def _aggregate_for_chart(df: pd.DataFrame, x_field: str, y_field: str, aggregation: str) -> pd.DataFrame:
    if not x_field or x_field not in df.columns:
        return pd.DataFrame()

    agg = (aggregation or "sum").lower()

    if agg in ("sum", "total", "mean", "avg", "average"):
        target_col = y_field if y_field in df.columns else None
        if not target_col:
            numeric_cols = df.select_dtypes(include=["number", "bool"]).columns
            target_col = numeric_cols[0] if len(numeric_cols) else None
        if not target_col or not pd.api.types.is_numeric_dtype(df[target_col]):
            return pd.DataFrame()
        agg_fn = "mean" if agg in ("mean", "avg", "average") else "sum"
        grouped = df.groupby(x_field)[target_col].agg(agg_fn).reset_index()
        return grouped.rename(columns={target_col: "value"})

    if agg == "count":
        grouped = df.groupby(x_field).size().reset_index(name="value")
        return grouped

    if y_field and y_field in df.columns and pd.api.types.is_numeric_dtype(df[y_field]):
        subset = df[[x_field, y_field]].copy()
        subset = subset.rename(columns={y_field: "value"})
        return subset

    return pd.DataFrame()


def _render_chart(path: str, df: pd.DataFrame, plan: dict) -> str:
    chart_type = (plan.get("chart_type") or "bar").lower()
    x_field = plan.get("x_field")
    y_field = plan.get("y_field")
    agg = plan.get("aggregation")
    top_n = int(plan.get("top_n") or 12)

    plt.figure(figsize=(10, 6))

    if chart_type == "scatter" and x_field and y_field:
        if x_field in df.columns and y_field in df.columns and \
                pd.api.types.is_numeric_dtype(df[x_field]) and pd.api.types.is_numeric_dtype(df[y_field]):
            plot_df = df[[x_field, y_field]].dropna().head(top_n)
            if plot_df.empty:
                return ""
            plt.scatter(plot_df[x_field], plot_df[y_field], color="#5cd4f4")
            plt.xlabel(x_field)
            plt.ylabel(y_field)
            plt.title(plan.get("explanation", f"{y_field} vs {x_field}"))
            plt.tight_layout()
            plt.savefig(path, bbox_inches="tight")
            plt.close()
            return path
        return ""

    if not x_field:
        return ""

    plot_df = _aggregate_for_chart(df, x_field, y_field, agg)
    if plot_df.empty:
        return ""

    plot_df = plot_df.sort_values("value", ascending=False)
    if top_n > 0:
        plot_df = plot_df.head(top_n)

    if chart_type == "pie":
        plot_df.set_index(x_field)["value"].plot(kind="pie", autopct="%1.1f%%")
        plt.ylabel("")
    elif chart_type == "line":
        plt.plot(plot_df[x_field], plot_df["value"], marker="o")
    elif chart_type == "area":
        plt.fill_between(plot_df[x_field], plot_df["value"], alpha=0.4)
        plt.plot(plot_df[x_field], plot_df["value"], color="#7a83ff")
    else:
        plt.bar(plot_df[x_field], plot_df["value"], color="#7a83ff")

    plt.xticks(rotation=45, ha="right")
    plt.xlabel(x_field)
    plt.ylabel(plan.get("y_field") or "Value")
    plt.title(plan.get("explanation", "Visualization"))
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path

# Nodes
def get_schema_node(state: AgentState):
    schema = get_db_schema()
    return {"schema": schema}

def generate_sql_node(state: AgentState):
    llm = get_llm()
    if not llm:
        return {"error": "LLM not configured"}
    
    template = """
    You are a SQL expert. Convert the following natural language query into a SQL query for SQLite.
    
    Schema:
    {schema}
    
    Recent conversation:
    {history}

    Current Query: {query}
    
    Return ONLY the SQL query, nothing else. Do not wrap in markdown code blocks.
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    try:
        sql_query = chain.invoke({
            "schema": state["schema"],
            "history": _format_history(state.get("history", [])),
            "query": state["query"],
        })
        # Clean up sql if needed
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        return {"sql_query": sql_query}
    except Exception as e:
        return {"error": str(e)}

def execute_sql_node(state: AgentState):
    if state.get("error"):
        return state
    
    try:
        df = pd.read_sql(state["sql_query"], engine)
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        return {"error": f"SQL Execution failed: {str(e)}"}

def generate_visualization_node(state: AgentState):
    if state.get("error") or not state.get("data"):
        return state
    
    df = pd.DataFrame(state["data"])
    if df.empty:
        return {"visualization_path": None, "visualization_summary": "No data to visualize."}

    plan = _suggest_chart_plan(df, state.get("query", ""))

    filename = f"chart_{uuid.uuid4()}.png"
    path = os.path.join("backend", "static", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    image_path = _render_chart(path, df, plan)

    if not image_path:
        return {"visualization_path": None, "visualization_summary": plan.get("explanation")}

    return {"visualization_path": image_path, "visualization_summary": plan.get("explanation")}

def generate_insights_node(state: AgentState):
    if state.get("error"):
        return state
    
    llm = get_llm()
    if not llm:
        return {"insights": "LLM not configured"}
    
    data_summary = str(state["data"])[:2000] # Truncate if too long
    
    template = """
    You are an analytics copilot. Use the latest query, the conversation history, and data sample to provide incremental insights. If the question repeats, avoid repetition by referencing earlier answers.

    History:
    {history}

    Current Query: {query}
    Data Sample: {data}

    Provide 3-5 concise bullet insights plus a short summary paragraph.
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    try:
        insights = chain.invoke({
            "query": state["query"],
            "history": _format_history(state.get("history", [])),
            "data": data_summary,
        })
        return {"insights": insights}
    except Exception as e:
        return {"insights": f"Failed to generate insights: {str(e)}"}

def build_report_node(state: AgentState):
    if state.get("error"):
        return state
    
    filename = f"report_{uuid.uuid4()}.pdf"
    path = os.path.join("backend", "static", filename)
    
    try:
        generate_pdf_report(
            report_path=path,
            title="Autonomous Data Analyst Report",
            query=state.get("query", ""),
            sql_query=state.get("sql_query", ""),
            insights=state.get("insights", "No insights generated."),
            chart_image_path=state.get("visualization_path"),
            chart_summary=state.get("visualization_summary"),
            data_sample=state.get("data"),
        )
        return {"report_path": path}
    except Exception as e:
        return {"error": f"Report generation failed: {str(e)}"}

def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("get_schema", get_schema_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("visualize", generate_visualization_node)
    workflow.add_node("generate_insights", generate_insights_node)
    workflow.add_node("build_report", build_report_node)
    
    # Define edges
    workflow.set_entry_point("get_schema")
    workflow.add_edge("get_schema", "generate_sql")
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("execute_sql", "visualize")
    workflow.add_edge("visualize", "generate_insights")
    workflow.add_edge("generate_insights", "build_report")
    workflow.add_edge("build_report", END)
    
    return workflow.compile()
