# app/services/refactoring_tool.py - The Supercharged, Safe Refactoring Engine (v1.2 - Final & Complete)

from __future__ import annotations

import contextlib
import difflib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RefactorResult:
    file_path: str
    changed: bool
    wrote: bool
    backup_path: str | None
    diff: str
    message: str


class RefactorTool:
    def __init__(
        self,
        llm_client,  # This is an instance of openai.OpenAI
        formatter_cmds: list[list[str]] | None = None,
        max_chars: int = 200_000,
    ):
        self.llm_client = llm_client
        self.formatter_cmds = formatter_cmds or []
        self.max_chars = max_chars

    def _read_text_safely(self, path: Path) -> tuple[str, str]:
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return path.read_text(encoding=enc), enc
            except UnicodeDecodeError:
                continue
        data = path.read_bytes()
        return data.decode(errors="replace"), "unknown"

    def _write_atomic(
        self, path: Path, text: str, preserve_meta_from: Path | None = None
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tf:
            tmp_name = tf.name
            tf.write(text)
        try:
            if preserve_meta_from and preserve_meta_from.exists():
                st = preserve_meta_from.stat()
                os.chmod(tmp_name, st.st_mode)
            os.replace(tmp_name, path)
            if preserve_meta_from and preserve_meta_from.exists():
                shutil.copystat(preserve_meta_from, path, follow_symlinks=True)
        except Exception:
            with contextlib.suppress(Exception):
                os.remove(tmp_name)
            raise

    def _make_backup(self, path: Path) -> Path:
        backup = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup)
        return backup

    def _build_diff(self, old: str, new: str, file_path: str) -> str:
        a = old.splitlines(keepends=True)
        b = new.splitlines(keepends=True)
        diff_lines = difflib.unified_diff(
            a, b, fromfile=f"{file_path} (original)", tofile=f"{file_path} (refactored)"
        )
        return "".join(diff_lines)

    def _run_formatters(self, file_path: Path) -> None:
        for cmd in self.formatter_cmds:
            cmd_expanded = [p.replace("{file}", str(file_path)) for p in cmd]
            try:
                subprocess.run(
                    cmd_expanded, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue

    def apply_code_refactoring(
        self,
        file_path: str,
        requested_changes: str,
        dry_run: bool = True,
        create_backup: bool = True,
    ) -> RefactorResult:
        p = Path(file_path)
        if not p.exists():
            return RefactorResult(file_path, False, False, None, "", f"File not found: {file_path}")

        try:
            original, enc = self._read_text_safely(p)
        except Exception as e:
            return RefactorResult(file_path, False, False, None, "", f"Read error: {e}")

        if len(original) > self.max_chars:
            return RefactorResult(
                file_path, False, False, None, "", "File is too large to process."
            )

        try:
            refactor_prompt = f"""
            You are a world-class software architect. Your task is to refactor the
            following code based on the user's request.
            Preserve all existing functionality. Your response must be ONLY the
            raw, complete, and refactored code for the entire file. Do not add
            any explanations, comments, or markdown formatting like ```python.

            ### USER'S REFACTORING REQUEST:
            ---
            {requested_changes}
            ---

            ### ORIGINAL CODE from file '{file_path}':
            ---
            {original} 
            ---
            """

            completion = self.llm_client.chat.completions.create(
                model="openai/gpt-4o",
                messages=[{"role": "user", "content": refactor_prompt}],
                temperature=0.1,
            )
            refactored = completion.choices.message.content

        except Exception as e:
            return RefactorResult(file_path, False, False, None, "", f"LLM call failed: {e}")

        if not isinstance(refactored, str) or not refactored.strip():
            return RefactorResult(
                file_path, False, False, None, "", "Refactoring result from AI was empty."
            )

        diff_text = self._build_diff(original, refactored, file_path)
        if not diff_text:
            return RefactorResult(
                file_path, False, False, None, "", "No changes were generated by the AI."
            )

        if dry_run:
            return RefactorResult(
                file_path, True, False, None, diff_text, "Dry-run: changes preview only."
            )

        backup_path = None
        try:
            if create_backup:
                backup = self._make_backup(p)
                backup_path = str(backup)
            self._write_atomic(p, refactored, preserve_meta_from=p)
        except Exception as e:
            return RefactorResult(
                file_path, True, False, backup_path, diff_text, f"Write error: {e}"
            )

        self._run_formatters(p)

        return RefactorResult(
            file_path, True, True, backup_path, diff_text, "Refactoring applied successfully."
        )
