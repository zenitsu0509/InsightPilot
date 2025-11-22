import io
from typing import Any, Dict

import pandas as pd
from fastapi import UploadFile

from app.db.database import engine

SUPPORTED_ENCODINGS = ("utf-8", "latin1", "cp1252")

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

    safe_table_name = table_name.strip() or "sales"
    dataframe.to_sql(safe_table_name, engine, if_exists="replace", index=False)

    return {
        "table": safe_table_name,
        "rows": len(dataframe),
        "columns": list(dataframe.columns),
        "encoding": chosen_encoding,
    }
