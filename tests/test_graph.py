from graph import build_graph, run


def test_graph_repairs_d2(scripted_llm, bad_unit_json, good_json):
    llm = scripted_llm([bad_unit_json, good_json])
    res = run(build_graph(llm, max_repairs=2), "<doc>")
    assert res.ok and res.repairs_used == 1
    assert res.document.quantity.unit == res.document.price.per_unit


def test_graph_exhausts(scripted_llm, bad_unit_json):
    llm = scripted_llm([bad_unit_json] * 3)
    res = run(build_graph(llm, max_repairs=2), "<doc>")
    assert not res.ok and res.repairs_used == 2


def test_graph_clean_first_try(scripted_llm, good_json):
    llm = scripted_llm([good_json])
    res = run(build_graph(llm, max_repairs=2), "<doc>")
    assert res.ok and res.repairs_used == 0
