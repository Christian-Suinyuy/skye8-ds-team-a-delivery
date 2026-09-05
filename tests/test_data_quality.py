import pandas as pd

from src.monitoring.data_quality import check_data_quality

def test_check_data_quality():
  df = pd.DataFrame(
    {
      "age": [20, 30, 30],
      "income": [100000, 200000, 200000]

    }
  )

  result = check_data_quality(df)

  assert result["rows"] == 3
  assert result["columns"] == 2
  assert result["duplicate_rows"] == 1
  assert result["missing_values"]["age"] == 0