from src.monitoring.prediction_monitor import prediction_distribution


def test_prediction_distribution():
    predictions = [0, 0, 0, 1, 1]

    result = prediction_distribution(predictions)

    assert result[0] == 0.6
    assert result[1] == 0.4
