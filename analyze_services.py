#!/usr/bin/env python3
"""Analyze all service files and generate refactoring report"""

import os
from pathlib import Path

services_dir = Path("app/services")
results = []

for py_file in services_dir.glob("*.py"):
    if py_file.name.startswith("__"):
        continue
    
    lines = len(py_file.read_text().splitlines())
    size_kb = py_file.stat().st_size / 1024
    
    if lines > 500:  # God Services
        results.append((lines, size_kb, py_file.name))

results.sort(reverse=True)

print("=" * 80)
print("GOD SERVICES REQUIRING REFACTORING (500+ lines)")
print("=" * 80)
print(f"{'Lines':<8} {'Size (KB)':<12} {'File Name'}")
print("-" * 80)

total_lines = 0
total_files = 0

for lines, size_kb, name in results:
    print(f"{lines:<8} {size_kb:<12.1f} {name}")
    total_lines += lines
    total_files += 1

print("-" * 80)
print(f"Total: {total_files} files, {total_lines:,} lines need refactoring")
print("=" * 80)
