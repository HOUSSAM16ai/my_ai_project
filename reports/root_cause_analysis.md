# ROOT CAUSE REPORT

## 1. Stdout Pollution
- **Source:** `scripts/bootstrap_db.py` line 47: `print(f"export DATABASE_URL='{db_url}'")`
- **Mechanism:** The script explicitly prints a shell command string instead of the raw data.
- **Impact:** When captured by `$(...)` in shell, the variable becomes the literal string "export DATABASE_URL='...'" rather than the actual URL.

## 2. Invalid SQLAlchemy URL
- **Cause:** The `DATABASE_URL` environment variable is populated with "export DATABASE_URL='postgresql+asyncpg://...'" instead of just "postgresql+asyncpg://...".
- **Error:** SQLAlchemy's URL parser fails to recognize "export" as a valid protocol scheme, throwing `ArgumentError`.

## 3. Shell Parsing Break
- **Location:** `scripts/setup_dev.sh` line 12: `export DATABASE_URL=$(python3 scripts/bootstrap_db.py)`
- **Flaw:** The script assumes the python script outputs *only* the URL value. It does not validate the output before exporting it.

## 4. Database Engine Creation
- **Status:** The `engine_factory.py` logic appears correct regarding `statement_cache_size=0`, but it never gets a chance to work because the input URL is malformed due to the upstream bootstrap failure.

## Conclusion
The chain of failure starts at `bootstrap_db.py` treating its output as a shell command rather than a data pipe. Fixing this requires strict stdout hygiene (raw URL only) and stderr logging.
