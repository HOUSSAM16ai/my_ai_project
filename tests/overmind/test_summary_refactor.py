from app.overmind.planning.deep_indexer_v2.summary import summarize_for_prompt


class MockObject:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_summarize_for_prompt_dict_input():
    data = {
        "files_scanned": 100,
        "global_metrics": {
            "total_loc": 5000,
            "total_functions": 200,
            "avg_function_complexity": 5.5,
            "max_function_complexity": 25,
        },
        "file_metrics": [
            {"path": "a.py", "loc": 1000},
            {"path": "b.py", "loc": 500},
            {"path": "c.py", "loc": 100},
        ],
        "layers": {"core": ["a.py", "b.py"], "utils": ["c.py"]},
        "complexity_hotspots_top50": [
            {"file": "a.py", "name": "bad_func", "loc": 50, "complexity": 25},
            {"file": "b.py", "name": "complex_one", "loc": 40, "complexity": 15},
        ],
    }
    summary = summarize_for_prompt(data)
    assert "FILES_SCANNED=100" in summary
    assert "LOC=5000" in summary
    assert "avg=5.5" in summary
    assert "- a.py (loc=1000)" in summary
    assert "- Core: 2 files" in summary
    assert "- a.py::bad_func" in summary


def test_summarize_for_prompt_object_input():
    data = MockObject(
        files_scanned=100,
        global_metrics=MockObject(
            total_loc=5000,
            total_functions=200,
            avg_function_complexity=5.5,
            max_function_complexity=25,
        ),
        file_metrics=[
            MockObject(path="a.py", loc=1000),
            MockObject(path="b.py", loc=500),
            MockObject(path="c.py", loc=100),
        ],
        layers={"core": ["a.py", "b.py"], "utils": ["c.py"]},
        complexity_hotspots_top50=[
            MockObject(file="a.py", name="bad_func", loc=50, complexity=25),
            MockObject(file="b.py", name="complex_one", loc=40, complexity=15),
        ],
    )
    summary = summarize_for_prompt(data)
    assert "FILES_SCANNED=100" in summary
    assert "LOC=5000" in summary
    assert "avg=5.5" in summary
    assert "- a.py (loc=1000)" in summary
    assert "- Core: 2 files" in summary
    assert "- a.py::bad_func" in summary
