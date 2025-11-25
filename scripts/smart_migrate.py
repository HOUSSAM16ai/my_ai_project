import asyncio
import logging
import sys

logger = logging.getLogger(__name__)


async def run_migrations(args):
    """
    Runs alembic migrations in a subprocess to avoid
    asyncio loop conflicts or driver cleanup hangs.
    """
    cmd = [sys.executable, "-m", "alembic", *args]
    logger.info(f"Executing command: {' '.join(cmd)}")

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if stdout:
        print(stdout.decode())
    if stderr:
        print(stderr.decode(), file=sys.stderr)

    if process.returncode != 0:
        raise RuntimeError(f"Alembic command failed with exit code {process.returncode}")


if __name__ == "__main__":
    # Simple wrapper to run migrations
    if len(sys.argv) > 1:
        asyncio.run(run_migrations(sys.argv[1:]))
    else:
        print("Usage: smart_migrate.py [alembic args]")
