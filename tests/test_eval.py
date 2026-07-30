from eval.run_eval import flatten, score


def test_flatten_nested_and_skips_underscore():
    flat = flatten({"a": 1, "b": {"c": 2}, "_comment": "x"})
    assert flat == {"a": 1, "b.c": 2}


def test_score_numeric_aware():
    gold = {"notional": "85420.00", "quantity": {"value": "1000"}}
    pred = {"notional": 85420, "quantity": {"value": "1000.0"}}
    correct, total, misses = score(pred, gold)
    assert (correct, total) == (2, 2) and misses == []


def test_score_reports_misses():
    gold = {"price": {"currency": "USD"}}
    pred = {"price": {"currency": "EUR"}}
    correct, total, misses = score(pred, gold)
    assert correct == 0 and total == 1 and "price.currency" in misses[0]
