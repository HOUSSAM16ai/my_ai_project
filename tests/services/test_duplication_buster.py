from app.services.system.duplication_buster import DuplicationBuster


class TestDuplicationBuster:
    def test_init(self):
        buster = DuplicationBuster(root="some/path")
        assert str(buster.root) == "some/path"
        assert len(buster.hashes) == 0

    def test_analyze_file_parses_functions(self, tmp_path):
        # Create a temporary python file with a function
        file_path = tmp_path / "test_file.py"
        content = """
def my_function():
    return 1 + 1
"""
        file_path.write_text(content, encoding="utf-8")

        buster = DuplicationBuster()
        buster._analyze_file(file_path)

        assert len(buster.hashes) == 1
        # Get the hash key
        hash_key = next(iter(buster.hashes.keys()))
        locations = buster.hashes[hash_key]
        assert len(locations) == 1
        assert locations[0][0] == str(file_path)
        assert locations[0][1] == "my_function"

    def test_analyze_file_detects_duplicates(self, tmp_path):
        # Create a file with two identical functions (structural match)
        file_path = tmp_path / "duplicates.py"
        content = """
def func_a():
    x = 1
    return x

def func_b():
    x = 1
    return x
"""
        file_path.write_text(content, encoding="utf-8")

        buster = DuplicationBuster()
        buster._analyze_file(file_path)

        # Now that we ignore function names, these should match
        assert len(buster.hashes) == 1
        hash_key = next(iter(buster.hashes.keys()))
        locations = buster.hashes[hash_key]
        assert len(locations) == 2
        names = sorted([loc[1] for loc in locations])
        assert names == ["func_a", "func_b"]

    def test_analyze_file_ignores_non_duplicates(self, tmp_path):
        file_path = tmp_path / "different.py"
        content = """
def func_a():
    return 1

def func_b():
    return 2
"""
        file_path.write_text(content, encoding="utf-8")

        buster = DuplicationBuster()
        buster._analyze_file(file_path)

        assert len(buster.hashes) == 2

    def test_scan_traverses_directories(self, tmp_path):
        # Create nested structure
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file1.py").write_text("def f(): pass", encoding="utf-8")
        (tmp_path / "subdir" / "file2.py").write_text("def f(): pass", encoding="utf-8")

        buster = DuplicationBuster(root=str(tmp_path))
        results = buster.scan()

        # Should find 1 pattern with 2 occurrences
        assert len(results) == 1
        assert results[0]["count"] == 2
        assert len(results[0]["locations"]) == 2

    def test_generate_report_format(self):
        buster = DuplicationBuster()
        # Manually inject hashes
        buster.hashes["hash1"] = [("file1.py", "func1"), ("file2.py", "func2")]
        buster.hashes["hash2"] = [("file3.py", "func3")]  # Not a duplicate

        report = buster._generate_report()

        assert len(report) == 1
        item = report[0]
        assert item["hash"] == "hash1"
        assert item["count"] == 2
        assert item["locations"] == [("file1.py", "func1"), ("file2.py", "func2")]
        # Check against actual implementation
        assert item["suggestion"] == "Refactor func1 into a shared utility."

    def test_analyze_file_handles_exceptions(self, tmp_path):
        # Create a file with syntax error
        file_path = tmp_path / "bad.py"
        file_path.write_text("def broken_func(", encoding="utf-8")

        buster = DuplicationBuster()
        # Should not raise exception
        buster._analyze_file(file_path)
        assert len(buster.hashes) == 0

    def test_async_functions(self, tmp_path):
        file_path = tmp_path / "async_test.py"
        content = """
async def async_func():
    await something()
"""
        file_path.write_text(content, encoding="utf-8")

        buster = DuplicationBuster()
        buster._analyze_file(file_path)

        assert len(buster.hashes) == 1
        hash_key = next(iter(buster.hashes.keys()))
        locations = buster.hashes[hash_key]
        assert locations[0][1] == "async_func"
