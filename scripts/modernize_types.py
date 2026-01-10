#!/usr/bin/env python3
"""
أداة تحويل Type Hints من typing القديمة إلى Python 3.12+
Tool to convert old typing to Python 3.12+ style
"""

import re
import sys
from pathlib import Path


def modernize_type_hints(content: str) -> str:
    """
    Convert old typing syntax to modern Python 3.12+ syntax.

    Conversions:
    - Optional[X] → X | None
    - Union[X, Y] → X | Y
    - List[X] → list[X]
    - Dict[X, Y] → dict[X, Y]
    - Tuple[X, Y] → tuple[X, Y]
    - Set[X] → set[X]
    """

    # Track if we need to keep any typing imports

    # Step 1: Convert Optional[X] to X | None
    content = re.sub(
        r'Optional\[([^\]]+)\]',
        r'\1 | None',
        content
    )

    # Step 2: Convert Union[X, Y, ...] to X | Y | ...
    def replace_union(match):
        types = match.group(1)
        # Split by comma but respect nested brackets
        return ' | '.join([t.strip() for t in split_types(types)])

    content = re.sub(
        r'Union\[([^\]]+(?:\[[^\]]*\])*[^\]]*)\]',
        replace_union,
        content
    )

    # Step 3: Convert List[X] to list[X]
    content = re.sub(r'\bList\[', 'list[', content)

    # Step 4: Convert Dict[X, Y] to dict[X, Y]
    content = re.sub(r'\bDict\[', 'dict[', content)

    # Step 5: Convert Tuple[X, Y] to tuple[X, Y]
    content = re.sub(r'\bTuple\[', 'tuple[', content)

    # Step 6: Convert Set[X] to set[X]
    content = re.sub(r'\bSet\[', 'set[', content)

    # Step 7: Update imports
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        # Remove unused typing imports
        if 'from typing import' in line:
            imports = re.search(r'from typing import (.+)', line)
            if imports:
                import_list = [i.strip() for i in imports.group(1).split(',')]
                # Keep only necessary imports (Protocol, Generic, etc.)
                keep_imports = []
                for imp in import_list:
                    if imp not in ['Optional', 'Union', 'List', 'Dict', 'Tuple', 'Set']:
                        keep_imports.append(imp)

                if keep_imports:
                    new_lines.append(f"from typing import {', '.join(keep_imports)}")
                # Skip the original line
                continue

        new_lines.append(line)

    return '\n'.join(new_lines)


def split_types(types_str: str) -> list[str]:
    """Split type string by comma, respecting brackets."""
    result = []
    current = ""
    depth = 0

    for char in types_str:
        if char == '[':
            depth += 1
            current += char
        elif char == ']':
            depth -= 1
            current += char
        elif char == ',' and depth == 0:
            result.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        result.append(current.strip())

    return result


def process_file(file_path: Path) -> tuple[bool, str]:
    """
    Process a single Python file.

    Returns:
        (changed, message) tuple
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        new_content = modernize_type_hints(content)

        if content != new_content:
            file_path.write_text(new_content, encoding='utf-8')
            return True, f"✅ Updated: {file_path}"
        return False, f"⏭️  No changes: {file_path}"

    except Exception as e:
        return False, f"❌ Error in {file_path}: {e}"


def main():
    """Main function to process all Python files."""
    app_dir = Path("app")

    if not app_dir.exists():
        print("❌ app/ directory not found!")
        sys.exit(1)

    python_files = list(app_dir.rglob("*.py"))
    print(f"📁 Found {len(python_files)} Python files")
    print("🔄 Processing...\n")

    updated = 0
    skipped = 0
    errors = 0

    for file_path in python_files:
        changed, message = process_file(file_path)
        print(message)

        if "Error" in message:
            errors += 1
        elif changed:
            updated += 1
        else:
            skipped += 1

    print(f"\n{'='*60}")
    print("📊 Summary:")
    print(f"   ✅ Updated: {updated} files")
    print(f"   ⏭️  Skipped: {skipped} files")
    print(f"   ❌ Errors: {errors} files")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
