from __future__ import annotations

from pathlib import Path

from app.tooling.repository_map import build_repository_map, emit_repository_map, summarize


def test_build_repository_map_walks_directories(tmp_path: Path) -> None:
    root_dir = tmp_path / "project"
    src_dir = root_dir / "src"
    hidden_dir = root_dir / ".cache"
    src_dir.mkdir(parents=True)
    hidden_dir.mkdir(parents=True)
    file_a = src_dir / "a.py"
    file_a.write_text("print('a')\n")
    file_b = hidden_dir / "b.py"
    file_b.write_text("print('b')\n")

    node = build_repository_map(root_dir, include_hidden=False)

    assert node.kind == "directory"
    assert any(child.path == "src" for child in node.children)
    assert all(".cache" not in child.path for child in node.children)

    node_with_hidden = build_repository_map(root_dir, include_hidden=True)
    assert any(child.path == ".cache" for child in node_with_hidden.children)


def test_build_repository_map_respects_depth(tmp_path: Path) -> None:
    root_dir = tmp_path / "project"
    deep_dir = root_dir / "level1" / "level2"
    deep_dir.mkdir(parents=True)
    (deep_dir / "target.txt").write_text("depth\n")

    shallow_map = build_repository_map(root_dir, max_depth=1)
    assert shallow_map.children[0].children == []


def test_emit_repository_map_outputs_json(tmp_path: Path) -> None:
    root_dir = tmp_path / "project"
    (root_dir / "data").mkdir(parents=True)
    (root_dir / "data" / "info.txt").write_text("value")

    output = emit_repository_map(root_dir)
    assert "data/info.txt" in output
    assert "size_bytes" in output


def test_summarize_filters_by_predicate(tmp_path: Path) -> None:
    root_dir = tmp_path / "project"
    (root_dir / "keep").mkdir(parents=True)
    (root_dir / "skip").mkdir(parents=True)

    repo_map = build_repository_map(root_dir)
    matches = summarize(repo_map, lambda node: node.path == "keep")

    assert [node.path for node in matches] == ["keep"]
