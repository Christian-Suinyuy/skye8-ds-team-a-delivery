from __future__ import annotations
from typing import Any
import pandas as pd

def check_data_quality(df: pd.DataFrame) -> dict[str, Any]:
  """Return basic data-quality statistics for a dataset."""
  return{
     "rows": len(df),
     "columns": len(df.columns),
     "missing_values": df.isna().sum().to_dict(),
     "duplicate_rows": int(df.duplicated().sum()),
     "dtypes": {
        column: str(dtype)
        for coulumn, dtype in df.dtypes.items()
     },
   }