import asyncio
import hashlib
import logging
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

import yaml
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Import the engine and factory from the core database module
from app.core.settings.base import get_settings
# Bypass the app.core.database factory to ensure we have full control over the engine creation for this script
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Direct Engine Creation for Script (Bypassing potential factory issues)
settings = get_settings()
db_url = settings.DATABASE_URL
connect_args = {}

if "postgresql" in db_url or "asyncpg" in db_url:
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }

engine = create_async_engine(
    db_url,
    echo=False,
    connect_args=connect_args
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

CONTENT_ROOT = Path("content")
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"
embedding_model = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return embedding_model

def parse_pack(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("\n\n", 1)
    if len(parts) < 2:
        logger.error(f"Invalid pack format (missing header/body split): {file_path}")
        return None

    yaml_header = parts[0]
    body = parts[1]

    try:
        metadata = yaml.safe_load(yaml_header)
    except yaml.YAMLError as e:
        logger.error(f"YAML Error in {file_path}: {e}")
        return None

    exercises = []
    # Regex to find [ex: ID] blocks
    # Logic: Match [ex: ID] -> Capture ID -> Capture everything until next [ex: or End of String
    pattern = re.compile(r"\[ex:\s*([\w-]+)\](.*?)(?=\n\[ex:|\Z)", re.DOTALL)

    matches = pattern.finditer(body)

    for match in matches:
        ex_id = match.group(1)
        raw_content_block = match.group(2).strip()

        # Heuristic: First line is title, rest is content
        lines = raw_content_block.split('\n', 1)
        if not lines:
            continue

        title = lines[0].strip()
        md_content = lines[1].strip() if len(lines) > 1 else ""

        # Reconstruct full markdown for display
        full_md = f"# {title}\n\n{md_content}"

        exercises.append({
            "id": ex_id,
            "title": title,
            "md_content": full_md,
            "metadata": metadata
        })

    # Regex to find [sol: ID] blocks
    sol_pattern = re.compile(r"\[sol:\s*([\w-]+)\](.*?)(?=\n\[sol:|\Z)", re.DOTALL)
    sol_matches = sol_pattern.finditer(body)

    solutions = {}
    for match in sol_matches:
        ex_id = match.group(1)
        content = match.group(2).strip()
        solutions[ex_id] = content

    # Merge solutions into exercises
    for ex in exercises:
        if ex["id"] in solutions:
            ex["solution_md"] = solutions[ex["id"]]

    return exercises

async def ingest_pack(file_path: Path, session: AsyncSession):
    logger.info(f"Processing pack: {file_path}")
    items = parse_pack(file_path)
    if not items:
        logger.warning(f"No items found in {file_path}")
        return

    # Determine dialect safely
    settings = get_settings()
    is_postgres = "postgres" in str(settings.DATABASE_URL)

    for item in items:
        ex_id = item["id"]
        metadata = item["metadata"]
        md_content = item["md_content"]

        sha256 = hashlib.sha256(md_content.encode('utf-8')).hexdigest()
        content_type = metadata.get('type', 'exercise')

        # Upsert into content_items
        query_items = text("""
            INSERT INTO content_items (
                id, type, title, level, subject, branch, set_name, year, lang, md_content, source_path, sha256, updated_at
            ) VALUES (
                :id, :type, :title, :level, :subject, :branch, :set_name, :year, :lang, :md_content, :source_path, :sha256, CURRENT_TIMESTAMP
            )
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                level = EXCLUDED.level,
                subject = EXCLUDED.subject,
                branch = EXCLUDED.branch,
                set_name = EXCLUDED.set_name,
                year = EXCLUDED.year,
                lang = EXCLUDED.lang,
                md_content = EXCLUDED.md_content,
                sha256 = EXCLUDED.sha256,
                updated_at = CURRENT_TIMESTAMP
        """)

        await session.execute(query_items, {
            "id": ex_id,
            "type": content_type,
            "title": item["title"],
            "level": metadata.get("level"),
            "subject": metadata.get("subject"),
            "branch": metadata.get("branch"),
            "set_name": str(metadata.get("set")),
            "year": metadata.get("year"),
            "lang": metadata.get("lang"),
            "md_content": md_content,
            "source_path": str(file_path),
            "sha256": sha256
        })

        # Upsert into content_search
        plain_text = md_content  # In a real app, we'd strip markdown syntax

        # Generate embedding
        model = get_embedding_model()
        # e5 models expect "query: " or "passage: " prefix usually, but for content we just embed.
        # Actually e5-small docs say: "Each input text should start with "query: " or "passage: ".
        # For symmetric tasks usually passage: is fine.
        loop = asyncio.get_running_loop()
        embedding = await loop.run_in_executor(None, lambda: model.encode(f"passage: {plain_text}").tolist())

        if is_postgres:
            # Upsert with vector (explicit cast for pgvector)
            query_search = text("""
                INSERT INTO content_search (content_id, plain_text, tsvector, embedding)
                VALUES (:id, :plain_text, to_tsvector('arabic', :plain_text), :embedding::vector)
                ON CONFLICT (content_id) DO UPDATE SET
                    plain_text = EXCLUDED.plain_text,
                    tsvector = to_tsvector('arabic', EXCLUDED.plain_text),
                    embedding = EXCLUDED.embedding
            """)
            # Note: We pass the embedding as a list of floats. SQLAlchemy/AsyncPG usually handles array binding.
            # However, pgvector often requires the input to be cast to vector explicitly in the SQL
            # if the driver doesn't support the type natively in bind params.
            # Passing list + ::vector cast works for list->vector conversion.
            await session.execute(query_search, {
                "id": ex_id,
                "plain_text": plain_text,
                "embedding": embedding
            })
        else:
            # Fallback for SQLite (no vector)
             query_search = text("""
                INSERT INTO content_search (content_id, plain_text)
                VALUES (:id, :plain_text)
                ON CONFLICT (content_id) DO UPDATE SET
                    plain_text = EXCLUDED.plain_text
            """)
             await session.execute(query_search, {
                "id": ex_id,
                "plain_text": plain_text
            })

        # Upsert into content_solutions if present
        if "solution_md" in item:
            # Check if updated_at column exists in schema or just skip it for now.
            # Based on the error, content_solutions doesn't have updated_at.
            # We will remove it from the query.

            # Use sha256 for solution as well
            sol_sha256 = hashlib.sha256(item["solution_md"].encode('utf-8')).hexdigest()

            query_solution = text("""
                INSERT INTO content_solutions (content_id, solution_md, sha256)
                VALUES (:id, :solution_md, :sha256)
                ON CONFLICT (content_id) DO UPDATE SET
                    solution_md = EXCLUDED.solution_md,
                    sha256 = EXCLUDED.sha256
            """)
            await session.execute(query_solution, {
                "id": ex_id,
                "solution_md": item["solution_md"],
                "sha256": sol_sha256
            })
            logger.info(f"Ingested solution for: {ex_id}")

        logger.info(f"Ingested item: {ex_id}")

    await session.commit()

async def main():
    files = list(CONTENT_ROOT.rglob("*.md"))
    if not files:
        logger.warning("No packs found in content directory.")
        return

    logger.info(f"Found {len(files)} packs to ingest.")

    try:
        async with async_session_factory() as session:
            for file_path in files:
                try:
                    await ingest_pack(file_path, session)
                except Exception as e:
                    logger.error(f"Failed to ingest {file_path}: {e}")
                    await session.rollback()
    finally:
        # Crucial: Close the engine to release connections and allow script to exit
        logger.info("Disposing database engine...")
        await engine.dispose()
        logger.info("Done.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())
