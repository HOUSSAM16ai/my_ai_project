# setup_environment.py
import os

# A professional, robust script to ensure environment variables are always available.
# It bridges the gap between system-level secrets (like in GitHub Codespaces)
# and file-based configurations (like .env files).

print("🚀 Starting robust environment setup...")

# List of essential environment variables the application needs.
# Add any new required variables here in the future.
ESSENTIAL_VARS = [
    "OPENROUTER_API_KEY",
    "SQLALCHEMY_DATABASE_URI",
    "SECRET_KEY",
    "FLASK_ENV",
    "FLASK_APP"
]

env_content = ""
found_any = False

for var in ESSENTIAL_VARS:
    value = os.getenv(var)
    if value:
        print(f"✅ Found '{var}' in system environment.")
        env_content += f'{var}="{value}"\n'
        found_any = True
    else:
        print(f"⚠️  Could not find '{var}' in system environment. Skipping.")

if not os.path.exists(".env"):
    if found_any:
        print("\n📄 '.env' file not found. Creating it from system environment variables...")
        try:
            with open(".env", "w") as f:
                f.write(env_content)
            print("✅ Successfully created '.env' file.")
        except IOError as e:
            print(f"❌ Error: Could not write to '.env' file: {e}")
    else:
        print("\n- No essential variables found in system environment and no '.env' file exists.")
else:
    print("\n- '.env' file already exists. No action taken.")

print("\n🎉 Environment setup complete.")
