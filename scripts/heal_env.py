import os


def heal_env_file(filepath=".env"):
    """
    Heals the .env file by quoting unquoted values containing spaces.
    """
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return

    print(f"Healing {filepath}...")

    with open(filepath) as f:
        lines = f.readlines()

    new_lines = []
    fixed_count = 0

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        if "=" in stripped:
            key, value = stripped.split("=", 1)
            value = value.strip()

            # Check if needs quoting
            # Simple check: starts and ends with same quote type
            is_quoted = False
            if len(value) >= 2 and (
                (value.startswith('"') and value.endswith('"'))
                or (value.startswith("'") and value.endswith("'"))
            ):
                is_quoted = True

            if not is_quoted and " " in value:
                # Escape existing double quotes
                safe_value = value.replace('"', '\\"')
                new_line = f'{key}="{safe_value}"\n'
                new_lines.append(new_line)
                fixed_count += 1
                continue

        new_lines.append(line)

    with open(filepath, "w") as f:
        f.writelines(new_lines)

    print(f"Fixed {fixed_count} lines in {filepath}.")


if __name__ == "__main__":
    heal_env_file()
