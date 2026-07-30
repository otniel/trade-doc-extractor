from extract import extract


def test_repairs_unit_bug(scripted_llm, bad_unit_json, good_json):
    llm = scripted_llm([bad_unit_json, good_json])
    res = extract("<doc>", llm)
    assert res.ok and res.repairs_used == 1 and llm.calls == 2


def test_exhausts_budget_and_reports(scripted_llm, bad_unit_json):
    llm = scripted_llm([bad_unit_json, bad_unit_json, bad_unit_json])
    res = extract("<doc>", llm, max_repairs=2)
    assert not res.ok
    assert res.repairs_used == 2 and llm.calls == 3
    assert any("unit mismatch" in e for e in res.errors)


def test_recovers_from_nonjson(scripted_llm, good_json):
    llm = scripted_llm(["Sure! here it is: (not json)", good_json])
    res = extract("<doc>", llm)
    assert res.ok and res.repairs_used == 1


def test_clean_first_try(scripted_llm, good_json):
    llm = scripted_llm([good_json])
    res = extract("<doc>", llm)
    assert res.ok and res.repairs_used == 0 and llm.calls == 1
