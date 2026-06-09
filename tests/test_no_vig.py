from src.strategy.value_detector import calculate_ev


def test_ev_calculation():
    ev = calculate_ev(model_probability=0.58, odds=1.95)

    assert ev > 0
    assert round(ev, 3) == 0.131
