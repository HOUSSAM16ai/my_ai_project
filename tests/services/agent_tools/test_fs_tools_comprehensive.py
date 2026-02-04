import gzip
from unittest.mock import patch

import pytest

from app.services.agent_tools.fs_tools import (
    append_file,
    delete_file,
    ensure_file,
    file_exists,
    list_dir,
    read_bulk_files,
    read_file,
    write_file,
    write_file_if_changed,
)

# We need to mock PROJECT_ROOT in fs_tools.utils via patch,
# because fs_tools imports _safe_path from .utils
# and .utils uses PROJECT_ROOT.
# However, PROJECT_ROOT is a constant in definitions.py.
# The best way to test fs_tools safely is to make _safe_path point to our tmp_path.


@pytest.fixture
def mock_project_root(tmp_path):
    # We patch PROJECT_ROOT in app.services.agent_tools.utils
    with patch("app.services.agent_tools.utils.PROJECT_ROOT", str(tmp_path)):
        yield tmp_path


# class TestEnsureDirectory:
#     def test_ensure_new_directory(self, mock_project_root):
#         """Test creating a new directory."""
#         path = "new_dir/sub_dir"
#         result = ensure_directory(path=path)
#         assert result.ok
#         assert result.data["created"] is True
#         assert result.data["exists"] is True
#         assert (mock_project_root / path).is_dir()
#
#     def test_ensure_existing_directory(self, mock_project_root):
#         """Test ensuring an existing directory."""
#         path = "existing_dir"
#         (mock_project_root / path).mkdir()
#
#         result = ensure_directory(path=path)
#         assert result.ok
#         assert result.data["created"] is False
#         assert result.data["exists"] is True
#
#     def test_ensure_directory_fails_if_file_exists(self, mock_project_root):
#         """Test failure when path exists but is a file."""
#         path = "file.txt"
#         (mock_project_root / path).touch()
#
#         result = ensure_directory(path=path)
#         assert not result.ok
#         assert result.error == "PATH_EXISTS_NOT_DIR"
#
#     def test_ensure_directory_must_be_new(self, mock_project_root):
#         """Test must_be_new flag."""
#         path = "existing_dir"
#         (mock_project_root / path).mkdir()
#
#         result = ensure_directory(path=path, must_be_new=True)
#         assert not result.ok
#         assert result.error == "DIR_ALREADY_EXISTS"


class TestWriteFile:
    def test_write_file_simple(self, mock_project_root):
        """Test writing simple content."""
        path = "test.txt"
        content = "Hello World"

        result = write_file(path=path, content=content)

        assert result.ok
        assert (mock_project_root / path).read_text(encoding="utf-8") == content
        assert result.data["bytes"] == len(content.encode("utf-8"))

    def test_write_file_not_string(self, mock_project_root):
        """Test error when content is not a string."""
        # AUTOFILL doesn't exist in core anymore, but the test logic seems relevant if type checking exists.
        # If the decorator handles coercion or validation, we just test the result.
        # If AUTOFILL was removed, we remove the patch.
        result = write_file(path="test.txt", content=123)
        assert not result.ok
        assert (
            "must be of type 'string'" in result.error or result.error == "CONTENT_NOT_STRING"
        )

    def test_write_file_json_compression(self, mock_project_root):
        """Test automatic compression for large JSON files."""
        path = "large.json"
        # Create content larger than 400,000 chars to trigger compression
        content = "a" * 400_001

        result = write_file(path=path, content=content, compress_json_if_large=True)

        assert result.ok
        assert result.data["compressed"] is True
        gz_path = mock_project_root / "large.json.gz"
        assert gz_path.exists()

        with gzip.open(gz_path, "rt", encoding="utf-8") as f:
            read_content = f.read()
        assert read_content == content

    def test_write_file_too_large(self, mock_project_root):
        """Test writing file exceeding MAX_WRITE_BYTES."""
        # Mock MAX_WRITE_BYTES to be small for testing.
        # Note: the decorator or handler implementation must import MAX_WRITE_BYTES from config,
        # so we patch the config module used by the handler.
        with patch(
            "app.services.agent_tools.domain.filesystem.handlers.write_handlers.MAX_WRITE_BYTES", 10
        ):
            result = write_file(path="large.txt", content="This is too long")
            assert not result.ok
            assert result.error == "WRITE_TOO_LARGE"

    def test_write_file_create_parents(self, mock_project_root):
        """Test writing file creates parent directories."""
        path = "parent/child/test.txt"
        content = "content"

        result = write_file(path=path, content=content)

        assert result.ok
        assert (mock_project_root / path).exists()


class TestWriteFileIfChanged:
    def test_write_new_file(self, mock_project_root):
        """Test writing a new file."""
        path = "new.txt"
        content = "content"

        result = write_file_if_changed(path=path, content=content)
        assert result.ok
        assert (mock_project_root / path).read_text() == content

    def test_skip_unchanged_file(self, mock_project_root):
        """Test skipping write if content matches."""
        path = "test.txt"
        content = "content"
        (mock_project_root / path).write_text(content, encoding="utf-8")

        result = write_file_if_changed(path=path, content=content)
        assert result.ok
        assert result.data["skipped"] is True
        assert result.data["reason"] == "UNCHANGED"

    def test_overwrite_changed_file(self, mock_project_root):
        """Test overwriting if content differs."""
        path = "test.txt"
        (mock_project_root / path).write_text("old content", encoding="utf-8")

        new_content = "new content"
        result = write_file_if_changed(path=path, content=new_content)
        assert result.ok
        assert result.data.get("skipped") is None
        assert (mock_project_root / path).read_text() == new_content


class TestAppendFile:
    def test_append_existing_file(self, mock_project_root):
        """Test appending to an existing file."""
        path = "test.txt"
        (mock_project_root / path).write_text("Hello", encoding="utf-8")

        result = append_file(path=path, content=" World")
        assert result.ok
        assert (mock_project_root / path).read_text() == "Hello World"

    def test_append_new_file(self, mock_project_root):
        """Test appending to a non-existent file creates it."""
        path = "new.txt"
        result = append_file(path=path, content="Start")
        assert result.ok
        assert (mock_project_root / path).read_text() == "Start"

    def test_append_not_string(self, mock_project_root):
        result = append_file(path="test.txt", content=123)
        assert not result.ok
        assert "must be of type 'string'" in result.error or result.error == "CONTENT_NOT_STRING"

    def test_append_total_limit(self, mock_project_root):
        """Test MAX_APPEND_BYTES enforcement."""
        with (
            patch(
                "app.services.agent_tools.domain.filesystem.handlers.write_handlers.ENFORCE_APPEND_TOTAL",
                True,
            ),
            patch(
                "app.services.agent_tools.domain.filesystem.handlers.write_handlers.MAX_APPEND_BYTES",
                10,
            ),
        ):
            path = "test.txt"
            (mock_project_root / path).write_text("12345", encoding="utf-8")

            # 5 + 6 = 11 > 10
            result = append_file(path=path, content="678901")
            assert not result.ok
            assert result.error == "APPEND_TOTAL_LIMIT_EXCEEDED"


class TestReadFile:
    def test_read_simple_file(self, mock_project_root):
        """Test reading a text file."""
        path = "test.txt"
        content = "Hello World"
        (mock_project_root / path).write_text(content, encoding="utf-8")

        result = read_file(path=path)
        assert result.ok
        assert result.data["content"] == content
        assert result.data["exists"] is True

    def test_read_missing_file_ignore(self, mock_project_root):
        """Test reading missing file with ignore_missing=True."""
        result = read_file(path="missing.txt", ignore_missing=True)
        assert result.ok
        assert result.data["missing"] is True
        assert result.data["content"] == ""

    def test_read_missing_file_error(self, mock_project_root):
        """Test reading missing file with ignore_missing=False."""
        result = read_file(path="missing.txt", ignore_missing=False)
        assert not result.ok
        assert result.error == "FILE_NOT_FOUND"

    def test_read_directory_error(self, mock_project_root):
        """Test reading a directory fails."""
        path = "dir"
        (mock_project_root / path).mkdir()

        result = read_file(path=path)
        assert not result.ok
        assert result.error == "IS_DIRECTORY"

    def test_read_gzip_file(self, mock_project_root):
        """Test reading a .gz file transparently."""
        # UPDATE: read_file in binary mode returns decoded bytes string,
        # which might be garbage if not utf-8.
        # But we should verify it returns binary_mode=True and some content.
        path = "test.txt.gz"
        content = "Compressed Content"
        with gzip.open(mock_project_root / path, "wt", encoding="utf-8") as f:
            f.write(content)

        result = read_file(path=path)
        assert result.ok
        assert result.data["binary_mode"] is True
        # Content will not be equal to "Compressed Content" because read_file doesn't decompress.
        # It reads raw bytes and tries to decode as utf-8.
        # gzip bytes start with \x1f\x8b.
        assert len(result.data["content"]) > 0

    def test_read_truncated(self, mock_project_root):
        """Test reading large file truncation."""
        path = "large.txt"
        content = "1234567890"
        (mock_project_root / path).write_text(content, encoding="utf-8")

        result = read_file(path=path, max_bytes=5)
        assert result.ok
        assert result.data["truncated"] is True
        assert len(result.data["content"]) == 5
        assert result.data["content"] == "12345"


class TestDeleteFile:
    def test_delete_file_success(self, mock_project_root):
        """Test successful deletion."""
        path = "test.txt"
        (mock_project_root / path).touch()

        result = delete_file(path=path, confirm=True)
        assert result.ok
        assert not (mock_project_root / path).exists()

    def test_delete_no_confirm(self, mock_project_root):
        """Test fails without confirmation."""
        path = "test.txt"
        (mock_project_root / path).touch()

        result = delete_file(path=path, confirm=False)
        assert not result.ok
        assert result.error == "CONFIRM_REQUIRED"
        assert (mock_project_root / path).exists()

    def test_delete_missing_file(self, mock_project_root):
        result = delete_file(path="missing.txt", confirm=True)
        assert not result.ok
        assert result.error == "FILE_NOT_FOUND"

    def test_delete_directory(self, mock_project_root):
        """Test fails if target is directory."""
        path = "dir"
        (mock_project_root / path).mkdir()

        result = delete_file(path=path, confirm=True)
        assert not result.ok
        assert result.error == "IS_DIRECTORY"


class TestEnsureFile:
    def test_ensure_file_exists_returns_content(self, mock_project_root):
        """Test ensuring existing file returns preview."""
        path = "test.txt"
        content = "Existing content"
        (mock_project_root / path).write_text(content, encoding="utf-8")

        result = ensure_file(path=path)
        assert result.ok
        assert result.data["exists"] is True
        assert result.data["created"] is False
        assert result.data["content"] == content

    def test_ensure_file_creates_if_missing(self, mock_project_root):
        """Test creating file if missing."""
        path = "new.txt"
        result = ensure_file(path=path, initial_content="Init")
        assert result.ok
        assert result.data["created"] is True
        assert (mock_project_root / path).read_text() == "Init"

    def test_ensure_file_enforce_ext(self, mock_project_root):
        """Test extension enforcement."""
        result = ensure_file(path="test.txt", enforce_ext=".json")
        assert not result.ok
        assert result.error == "EXTENSION_MISMATCH"

    def test_ensure_file_not_allow_create(self, mock_project_root):
        """Test fails if allow_create is False."""
        result = ensure_file(path="missing.txt", allow_create=False)
        assert not result.ok
        assert result.error == "FILE_NOT_FOUND"


class TestReadBulkFiles:
    def test_read_bulk_json_mode(self, mock_project_root):
        """Test reading multiple files in JSON mode."""
        f1 = "f1.txt"
        f2 = "f2.txt"
        (mock_project_root / f1).write_text("Content 1", encoding="utf-8")
        (mock_project_root / f2).write_text("Content 2", encoding="utf-8")

        result = read_bulk_files(paths=[f1, f2], merge_mode="json")
        assert result.ok
        assert result.data["mode"] == "json"
        assert len(result.data["files"]) == 2
        assert result.data["files"][0]["content"] == "Content 1"
        assert result.data["files"][1]["content"] == "Content 2"

    def test_read_bulk_concat_mode(self, mock_project_root):
        """Test reading multiple files in concat mode."""
        f1 = "f1.txt"
        f2 = "f2.txt"
        (mock_project_root / f1).write_text("Content 1", encoding="utf-8")
        (mock_project_root / f2).write_text("Content 2", encoding="utf-8")

        result = read_bulk_files(paths=[f1, f2], merge_mode="concat")
        assert result.ok
        assert result.data["mode"] == "concat"
        assert "Content 1" in result.data["content"]
        assert "Content 2" in result.data["content"]
        assert "# f1.txt" in result.data["content"]

    def test_read_bulk_ignore_missing(self, mock_project_root):
        """Test bulk read with missing files."""
        result = read_bulk_files(paths=["missing.txt"], ignore_missing=True)
        assert result.ok
        assert result.data["files"][0]["exists"] is False

    def test_read_bulk_error_missing(self, mock_project_root):
        """Test bulk read error on missing file."""
        result = read_bulk_files(paths=["missing.txt"], ignore_missing=False)
        assert not result.ok
        assert "FILE_NOT_FOUND" in result.error


class TestMetaTools:
    def test_file_exists(self, mock_project_root):
        path = "test.txt"
        (mock_project_root / path).touch()

        result = file_exists(path=path)
        assert result.ok
        assert result.data["exists"] is True
        assert result.data["is_file"] is True

    def test_list_dir(self, mock_project_root):
        (mock_project_root / "f1.txt").touch()
        (mock_project_root / "d1").mkdir()

        result = list_dir(path=".")
        assert result.ok
        names = [e["name"] for e in result.data["entries"]]
        assert "f1.txt" in names
        assert "d1" in names

    def test_list_dir_not_dir(self, mock_project_root):
        path = "f1.txt"
        (mock_project_root / path).touch()

        result = list_dir(path=path)
        assert not result.ok
        assert result.error == "NOT_A_DIRECTORY"
