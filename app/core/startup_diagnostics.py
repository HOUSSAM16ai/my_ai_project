import os
import sys
from app.config.settings import get_settings

def run_diagnostics():
    """
    Executes the Superhuman Configuration Diagnostics at startup.
    Verifies that secrets are loaded and environment is correctly detected.
    """
    settings = get_settings()

    print("\n" + "="*60)
    print("   COGNIFORGE REALITY KERNEL V3 - SUPERHUMAN BOOT SEQUENCE")
    print("="*60)

    # 1. Environment Detection
    env_source = "GitHub Codespaces" if settings.CODESPACES else "Standard Container/Local"
    print(f"[*] Environment Logic:    {settings.ENVIRONMENT.upper()}")
    print(f"[*] Deployment Context:   {env_source}")

    # 2. Secret Integrity Check (Masked)
    def check_secret(name, value):
        status = "ACTIVE" if value else "MISSING"
        if value and len(str(value)) > 8:
            masked = str(value)[:4] + "..." + str(value)[-4:]
        else:
            masked = "N/A"
        print(f"[*] Secret Audit [{name}]: {status}")

    check_secret("DATABASE_URL", settings.DATABASE_URL)
    check_secret("SECRET_KEY", settings.SECRET_KEY)
    check_secret("OPENROUTER_API_KEY", settings.OPENROUTER_API_KEY)
    check_secret("OPENAI_API_KEY", settings.OPENAI_API_KEY)

    # 3. Connection Heuristics
    db_mode = "AsyncPG (High-Performance)" if "asyncpg" in settings.DATABASE_URL else "Standard"
    print(f"[*] Database Protocol:    {db_mode}")

    print("="*60 + "\n")

    # Warn if critical secrets are missing in non-test env
    if settings.ENVIRONMENT != "test" and settings.DATABASE_URL.startswith("sqlite"):
        print("!! WARNING: Running with SQLite fallback in non-test environment. !!")
        print("!! Check GitHub Secrets injection if this is production/staging. !!\n")
