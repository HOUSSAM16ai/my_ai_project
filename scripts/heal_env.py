import os
import re
import sys

def heal_env_file(filepath=".env"):
    """
    Scans the .env file for syntax errors (specifically unquoted values with spaces)
    and fixes them by wrapping the values in double quotes.
    """
    if not os.path.exists(filepath):
        print(f"ℹ️  {filepath} not found. Skipping healing.")
        return

    print(f"🚑 Healing {filepath} syntax...")

    with open(filepath, "r") as f:
        lines = f.readlines()

    new_lines = []
    fixed_count = 0

    for line in lines:
        original_line = line.strip()
        if not original_line or original_line.startswith("#"):
            new_lines.append(line)
            continue

        # Simple parse: Key=Value
        match = re.match(r"^([A-Z_a-z0-9]+)=(.*)$", original_line)
        if match:
            key = match.group(1)
            value = match.group(2)

            # Check if value needs quoting
            # Condition: Contains space AND (not quoted OR badly quoted)

            # If it's already properly quoted, leave it.
            # Simple check: starts and ends with same quote type
            is_quoted = False
            if len(value) >= 2:
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    is_quoted = True

            if not is_quoted:
                # If it contains spaces, it MUST be quoted for bash 'source' to work safely
                if " " in value:
                    # Escape existing double quotes
                    safe_value = value.replace('"', '\\"')
                    new_line = f'{key}="{safe_value}"\n'
                    new_lines.append(new_line)
                    fixed_count += 1
                    print(f"   FIXED: {key}='{value}' -> {key}=\"{safe_value}\"")
                    continue

            # Even if no spaces, ensure we don't have dangling stuff or shell meta chars
            # But for now, focus on the reported bug (spaces)

        new_lines.append(line)

    if fixed_count > 0:
        with open(filepath, "w") as f:
            f.writelines(new_lines)
        print(f"✅ Healed {fixed_count} issues in {filepath}.")
    else:
        print(f"✅ {filepath} syntax appears healthy.")

if __name__ == "__main__":
    heal_env_file()
