from src.monitoring.performance import calculate_performance


def test_performance_metrics():
    y_true = [0, 1, 1, 0]
    y_pred = [0, 1, 0, 0]

    result = calculate_performance(y_true, y_pred)

    assert result["accuracy"] == 0.75
    assert 0 <= result["precision"] <= 1
    assert 0 <= result["recall"] <= 1
    assert 0 <= result["f1"] <= 1
