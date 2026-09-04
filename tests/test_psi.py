import pandas as pd

from src.monitoring.psi import calculate_psi

def test_psi_is_zero_for_identical_data():
  data = pd.Series([10,20, 30, 40, 50])

  result= calculate_psi(data, data)

  assert result == 0.0

def test_psi_increases_when_distribution_changes():
  reference = pd.Series([10, 20, 30, 40, 50])
  current = pd.Series([100, 110, 120, 130, 140])

  result = calculate_psi(reference, current)

  assert result > 0