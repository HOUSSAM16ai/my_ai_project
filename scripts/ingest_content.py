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

from app.core.database import async_session_factory
from app.core.settings.base import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONTENT_ROOT = Path("content")

def parse_pack(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("\n\n", 1)
    if len(parts) < 2:
        logger.error(f"Invalid pack format: {file_path}")
        return None

    yaml_header = parts[0]
    body = parts[1]

    try:
        metadata = yaml.safe_load(yaml_header)
    except yaml.YAMLError as e:
        logger.error(f"YAML Error in {file_path}: {e}")
        return None

    exercises = []
    pattern = re.compile(r"\[ex:\s*([\w-]+)\]\s*(.*?)(?=\n\[ex:|\Z)", re.DOTALL)

    matches = pattern.finditer(body)

    for match in matches:
        ex_id = match.group(1)
        raw_content_block = match.group(2).strip()
        lines = raw_content_block.split('\n', 1)
        title = lines[0].strip()
        md_content = lines[1].strip() if len(lines) > 1 else ""
        full_md = f"# {title}\n\n{md_content}"

        exercises.append({
            "id": ex_id,
            "title": title,
            "md_content": full_md,
            "metadata": metadata
        })

    return exercises

async def ingest_pack(file_path: Path, session: AsyncSession):
    logger.info(f"Ingesting {file_path}")
    items = parse_pack(file_path)
    if not items:
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

        query_items = text("""
            INSERT INTO content_items (
                id, type, title, level, subject, set_name, year, lang, md_content, source_path, sha256, updated_at
            ) VALUES (
                :id, :type, :title, :level, :subject, :set_name, :year, :lang, :md_content, :source_path, :sha256, CURRENT_TIMESTAMP
            )
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
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
            "set_name": str(metadata.get("set")),
            "year": metadata.get("year"),
            "lang": metadata.get("lang"),
            "md_content": md_content,
            "source_path": str(file_path),
            "sha256": sha256
        })

        plain_text = md_content

        if is_postgres:
            query_search = text("""
                INSERT INTO content_search (content_id, plain_text, tsvector)
                VALUES (:id, :plain_text, to_tsvector('simple', :plain_text))
                ON CONFLICT (content_id) DO UPDATE SET
                    plain_text = EXCLUDED.plain_text,
                    tsvector = to_tsvector('simple', EXCLUDED.plain_text)
            """)
        else:
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

    await session.commit()
    logger.info(f"Ingested {len(items)} items from {file_path}")

async def main():
    files = list(CONTENT_ROOT.rglob("*.md"))
    if not files:
        logger.warning("No packs found.")
        return

    logger.info(f"Found {len(files)} packs to ingest.")

    async with async_session_factory() as session:
        for file_path in files:
            await ingest_pack(file_path, session)

if __name__ == "__main__":
    asyncio.run(main())
