from app.config.settings import get_settings

# app/core/startup_diagnostics.py


async def run_diagnostics():
    """
    Runs startup diagnostics.
    """
    print("Running diagnostics...")

    settings = get_settings()

    # Secret Audit
    # Check Pydantic settings first, then env vars as backup for raw keys

    secrets_map = {
        "SECRET_KEY": settings.SECRET_KEY,
        "DATABASE_URL": settings.DATABASE_URL,
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "OPENROUTER_API_KEY": settings.OPENROUTER_API_KEY,
    }

    for name, value in secrets_map.items():
        status = "SET" if value else "MISSING"

        # Audit log (masked)
        if value and ("KEY" in name or "PASSWORD" in name or "SECRET" in name):
            pass
        else:
            pass

        print(f"[*] Secret Audit [{name}]: {status}")

    # Add other checks here
    print("Diagnostics complete.")
