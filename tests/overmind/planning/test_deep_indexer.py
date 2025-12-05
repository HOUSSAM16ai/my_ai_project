import os
import json
from app.overmind.planning import deep_indexer

def test_deep_indexer_build_index_structure(tmp_path):
    # Setup: Create a dummy python project structure
    d = tmp_path / "project"
    d.mkdir()

    # File 1: Simple function
    p1 = d / "simple.py"
    p1.write_text("""
def hello():
    print("world")
    return True
""")

    # File 2: Class with complexity
    p2 = d / "complex.py"
    p2.write_text("""
import os

class Processor:
    def process(self, items):
        results = []
        for i in items:
            if i > 10:
                results.append(i * 2)
            else:
                results.append(i)
        return results
""")

    # Act: Build the index
    index = deep_indexer.build_index(root=str(d))

    # Assert: Basic Structure
    assert "files_scanned" in index
    assert index["files_scanned"] == 2
    assert "modules" in index
    assert len(index["modules"]) == 2

    # Verify module contents
    modules = {m["path"]: m for m in index["modules"]}

    # Check simple.py
    # Note: deep_indexer uses absolute paths or relative depending on implementation.
    # The current implementation in deep_indexer.py uses _collect_python_files which calls os.path.abspath(root).
    # So the keys in modules will be absolute paths.

    p1_abs = str(p1.resolve())
    assert p1_abs in modules
    m1 = modules[p1_abs]
    assert len(m1["functions"]) == 1
    assert m1["functions"][0]["name"] == "hello"

    # Check complex.py
    p2_abs = str(p2.resolve())
    assert p2_abs in modules
    m2 = modules[p2_abs]
    assert len(m2["classes"]) == 1
    assert m2["classes"][0]["name"] == "Processor"
    assert len(m2["functions"]) == 1
    assert m2["functions"][0]["name"] == "process"
    # Complexity check (For loop + If + basic)
    # _DeepIndexVisitor counts:
    # FunctionDef (+1)
    # For (+1)
    # If (+1)
    # So complexity should be roughly 3.
    assert m2["functions"][0]["complexity"] >= 3

def test_summarize_for_prompt(tmp_path):
    # Setup dummy index
    index = {
        "files_scanned": 10,
        "global_metrics": {
            "total_functions": 50,
            "avg_function_complexity": 5.5,
            "std_function_complexity": 2.1,
            "max_function_complexity": 20,
            "max_function_complexity_ref": "foo.py::bar",
            "total_loc": 1000
        },
        "complexity_hotspots_top50": [
            {"file": "bad.py", "name": "do_bad", "loc": 100, "complexity": 50}
        ],
        "duplicate_function_bodies": {},
        "function_call_frequency_top50": [],
        "dependencies": {},
        "layers": {},
        "service_candidates": [],
        "entrypoints": [],
        "call_graph_edges_sample": []
    }

    # Act
    summary = deep_indexer.summarize_for_prompt(index)

    # Assert
    assert "FILES_SCANNED=10" in summary
    assert "GLOBAL: funcs=50" in summary
    assert "bad.py::do_bad" in summary
