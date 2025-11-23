import io
import re
from typing import Any, Dict, List

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import inspect, text

from app.db.database import engine

SUPPORTED_ENCODINGS = ("utf-8", "latin1", "cp1252")

SAFE_TABLE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_table_name(name: str) -> str:
    if not SAFE_TABLE_PATTERN.match(name):
        raise ValueError("Table name must start with a letter/underscore and contain only alphanumerics or underscores.")
    return name


def ingest_csv_dataset(
    upload_file: UploadFile,
    table_name: str = "sales",
) -> Dict[str, Any]:
    """Load an uploaded CSV file into the configured database table."""
    raw_bytes = upload_file.file.read()
    upload_file.file.seek(0)

    dataframe = None
    chosen_encoding = None
    errors = []

    for encoding in SUPPORTED_ENCODINGS:
        buffer = io.BytesIO(raw_bytes)
        try:
            dataframe = pd.read_csv(buffer, encoding=encoding)
            chosen_encoding = encoding
            break
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
            continue
        except Exception as exc:
            raise ValueError(f"Unable to parse CSV: {exc}")

    if dataframe is None:
        raise ValueError(
            "Unable to decode CSV. Please upload UTF-8 or Latin-1 encoded files." +
            (f" Details: {'; '.join(errors)}" if errors else "")
        )

    if dataframe.empty:
        raise ValueError("Uploaded CSV is empty.")

    safe_table_name = _validate_table_name(table_name.strip() or "sales")
    dataframe.to_sql(safe_table_name, engine, if_exists="replace", index=False)

    # Convert first 5 rows to dict for preview
    preview_rows = dataframe.head(5).to_dict(orient="records")

    return {
        "table": safe_table_name,
        "rows": len(dataframe),
        "columns": list(dataframe.columns),
        "encoding": chosen_encoding,
        "preview": preview_rows
    }


def list_dataset_tables(limit: int = 15) -> List[Dict[str, Any]]:
    inspector = inspect(engine)
    tables = [t for t in inspector.get_table_names() if not t.startswith("sqlite_")][:limit]
    catalog: List[Dict[str, Any]] = []

    with engine.connect() as conn:
        for table_name in tables:
            column_info = inspector.get_columns(table_name)
            try:
                result = conn.execute(text(f"SELECT COUNT(*) as cnt FROM {table_name}"))
                row_count = result.scalar() or 0
            except Exception:
                row_count = None

            catalog.append(
                {
                    "table": table_name,
                    "rows": int(row_count) if row_count is not None else None,
                    "columns": [col.get("name") for col in column_info],
                }
            )
    return catalog
