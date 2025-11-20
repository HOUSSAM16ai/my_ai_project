# migration/auto_loop/auto_patch_builder.py
import re


class AutoPatchBuilder:
    @staticmethod
    def generate_patch(original_content: str) -> str:
        """
        Generates a patched version of the file content by intelligently
        rewriting Flask imports.
        """
        print("Generating intelligent migration patch...")
        lines = original_content.split("\n")
        new_lines = []
        modified = False

        # All possible objects we can replace from our compat layer
        compat_objects = {"current_app", "g", "request", "jsonify", "current_user"}

        # --- Find all objects imported from Flask ---
        flask_imports_found = set()
        lines_to_remove = []

        for i, line in enumerate(lines):
            # Match lines like "from flask import obj1, obj2"
            match = re.search(r"^\s*from\s+flask\s+import\s+(.*)", line)
            if match:
                imports_str = match.group(1)
                # Handle imports with parentheses
                imports_str = imports_str.replace("(", "").replace(")", "")
                # Find all imported objects on that line
                imported_objects = {s.strip() for s in imports_str.split(",")}

                # Check which of these are ones we can replace
                replaceable_objects = imported_objects.intersection(compat_objects)
                if replaceable_objects:
                    flask_imports_found.update(replaceable_objects)
                    lines_to_remove.append(i)
                    modified = True

            # Also handle flask_login imports
            match_login = re.search(r"^\s*from\s+flask_login\s+import\s+(.*)", line)
            if match_login and "current_user" in match_login.group(1):
                flask_imports_found.add("current_user")
                lines_to_remove.append(i)
                modified = True

        if not modified:
            print("No replaceable Flask imports found.")
            return original_content

        # --- Construct the new file content ---
        # 1. Create the new compat import line
        sorted_imports = sorted(flask_imports_found)
        compat_import_line = (
            f"from app.core.kernel_v2.compat_collapse import {', '.join(sorted_imports)}"
        )
        print(f"+ Generated new import: {compat_import_line}")

        # 2. Add the new line at the top (or a suitable position)
        # For simplicity, we'll add it after the first block of imports
        import_insertion_point = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                import_insertion_point = i + 1
            elif line.strip() == "" and import_insertion_point > 0:
                break  # First blank line after imports

        # 3. Rebuild the file
        new_lines.append(compat_import_line)
        for i, line in enumerate(lines):
            if i not in lines_to_remove:
                new_lines.append(line)

        # A cleaner way is to insert the line and remove the old ones
        final_lines = []
        import_added = False
        for i, line in enumerate(lines):
            if i in lines_to_remove:
                if not import_added:
                    final_lines.append(compat_import_line)
                    import_added = True
                print(f"- Removed: {line.strip()}")
            else:
                final_lines.append(line)

        print("+ Refactoring complete.")
        return "\n".join(final_lines)
