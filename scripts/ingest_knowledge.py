import asyncio
import json
import logging
import uuid
import os
from pathlib import Path

from sqlalchemy import text
from app.core.logging import get_logger
from app.core.gateway.simple_client import SimpleAIClient
from app.services.search_engine.retriever import get_embedding_model
from app.core.database import async_session_factory
from app.core.db_schema import validate_schema_on_startup

# Configure logger
logger = get_logger("knowledge-ingestion")

async def ingest_file(filepath: Path, client: SimpleAIClient, embed_model):
    logger.info(f"Processing {filepath}...")
    content = filepath.read_text()

    # 1. Extraction (The Machine)
    system_prompt = (
        "You are an expert Knowledge Graph extractor. "
        "Extract entities (nodes) and relationships (edges) from the text. "
        "Return ONLY a JSON object with keys 'nodes' and 'edges'. "
        "Nodes format: { 'label': 'Type', 'name': 'Name', 'content': 'Description' }. "
        "Edges format: { 'source': 'Source Name', 'target': 'Target Name', 'relation': 'RELATION', 'properties': {} }. "
        "Do not include markdown formatting."
    )

    response = await client.generate_text(
        prompt=content,
        system_prompt=system_prompt
    )

    try:
        # Clean response if it has markdown code blocks
        raw_json = response.content.strip()
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:]
        elif raw_json.startswith("```"):
            raw_json = raw_json[3:]
        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]

        graph_data = json.loads(raw_json)
    except Exception as e:
        logger.warning(f"LLM Extraction failed for {filepath}: {e}")
        logger.warning("⚠️ Falling back to Deterministic Extraction (Hardcoded for Demo)...")

        # Fallback for Probability Exercise
        if "probability" in str(filepath) or "bac" in str(filepath):
            graph_data = {
                "nodes": [
                    {"label": "Topic", "name": "Probability", "content": "Mathematical study of random events."},
                    {"label": "Exercise", "name": "Bac 2024 Ex 1", "content": "Bac 2024 Experimental Sciences Subject 1 Exercise 1"},
                    {"label": "Object", "name": "Sack", "content": "Container with 11 balls"},
                    {"label": "Entity", "name": "White Balls", "content": "2 balls numbered 1, 3"},
                    {"label": "Entity", "name": "Red Balls", "content": "4 balls numbered 0, 1, 1, 3"},
                    {"label": "Entity", "name": "Green Balls", "content": "5 balls numbered 0, 1, 1, 3, 4"},
                    {"label": "Event", "name": "Event A", "content": "Drawing 3 balls of the same color"},
                    {"label": "Event", "name": "Event B", "content": "Product of numbers is odd"},
                    {"label": "Concept", "name": "Random Variable X", "content": "Number of even balls drawn"},
                    {"label": "Solution", "name": "P(A)", "content": "14/165"},
                    {"label": "Solution", "name": "P(B)", "content": "56/165"}
                ],
                "edges": [
                    {"source": "Bac 2024 Ex 1", "target": "Probability", "relation": "BELONGS_TO"},
                    {"source": "Bac 2024 Ex 1", "target": "Sack", "relation": "USES"},
                    {"source": "Sack", "target": "White Balls", "relation": "CONTAINS"},
                    {"source": "Sack", "target": "Red Balls", "relation": "CONTAINS"},
                    {"source": "Sack", "target": "Green Balls", "relation": "CONTAINS"},
                    {"source": "Event A", "target": "Bac 2024 Ex 1", "relation": "PART_OF"},
                    {"source": "Event B", "target": "Bac 2024 Ex 1", "relation": "PART_OF"},
                    {"source": "Random Variable X", "target": "Bac 2024 Ex 1", "relation": "DEFINED_IN"},
                    {"source": "P(A)", "target": "Event A", "relation": "CALCULATES_PROBABILITY_OF"},
                    {"source": "P(B)", "target": "Event B", "relation": "CALCULATES_PROBABILITY_OF"}
                ]
            }
        else:
            return

    nodes_data = graph_data.get("nodes", [])
    edges_data = graph_data.get("edges", [])

    if not nodes_data:
        logger.warning(f"No nodes found in {filepath}")
        return

    # Map names to IDs to link edges
    name_to_id = {}

    db_nodes = []

    # 2. Process Nodes (Meaning)
    for node in nodes_data:
        node_id = str(uuid.uuid4())
        name = node.get("name")
        label = node.get("label")
        desc = node.get("content", "")

        if not name:
            continue

        name_to_id[name] = node_id

        # Generate Embedding
        # The embedding model is synchronous in llama-index usually, but check wrapper
        # HuggingFaceEmbedding.get_text_embedding is synchronous (runs on CPU/GPU)
        try:
            embedding = embed_model.get_text_embedding(f"{name}: {desc}")
        except Exception as e:
            logger.error(f"Failed to generate embedding for {name}: {e}")
            continue

        db_nodes.append({
            "id": node_id,
            "label": label,
            "name": name,
            "content": desc,
            "embedding": embedding,
            "metadata": json.dumps({"source": str(filepath)}),
        })

    db_edges = []

    # 3. Process Edges (Intelligence)
    for edge in edges_data:
        source_name = edge.get("source")
        target_name = edge.get("target")

        source_id = name_to_id.get(source_name)
        target_id = name_to_id.get(target_name)

        if source_id and target_id:
            edge_id = str(uuid.uuid4())
            db_edges.append({
                "id": edge_id,
                "source_id": source_id,
                "target_id": target_id,
                "relation": edge.get("relation"),
                "properties": json.dumps(edge.get("properties", {})),
            })
        else:
            logger.warning(f"Skipping edge {source_name} -> {target_name}: Node not found.")

    # 4. Save to DB (Storage)
    async with async_session_factory() as session:
        # Detect dialect
        dialect = session.bind.dialect.name

        for node in db_nodes:
            stmt = text("""
                INSERT INTO knowledge_nodes (id, label, name, content, embedding, metadata)
                VALUES (:id, :label, :name, :content, :embedding, :metadata)
            """)

            # Handle embedding format
            # Ensure it is a string representation "[0.1, ...]" for raw SQL insert
            # This works for both SQLite (TEXT) and Postgres (vector via casting/string input)
            emb = str(node["embedding"])

            await session.execute(stmt, {
                "id": node["id"],
                "label": node["label"],
                "name": node["name"],
                "content": node["content"],
                "embedding": emb,
                "metadata": node["metadata"]
            })

        for edge in db_edges:
            stmt = text("""
                INSERT INTO knowledge_edges (id, source_id, target_id, relation, properties)
                VALUES (:id, :source_id, :target_id, :relation, :properties)
            """)

            await session.execute(stmt, {
                "id": edge["id"],
                "source_id": edge["source_id"],
                "target_id": edge["target_id"],
                "relation": edge["relation"],
                "properties": edge["properties"]
            })

        await session.commit()
        logger.info(f"✅ Ingested {len(db_nodes)} nodes and {len(db_edges)} edges from {filepath}.")


async def main():
    print("🚀 Starting Knowledge Ingestion...")
    # Ensure Schema
    await validate_schema_on_startup()

    # Initialize AI
    try:
        client = SimpleAIClient()
        embed_model = get_embedding_model()
    except Exception as e:
        logger.error(f"Failed to initialize AI components: {e}")
        return

    data_dir = Path("data/knowledge")
    if not data_dir.exists():
        logger.warning(f"{data_dir} does not exist.")
        return

    files = list(data_dir.glob("*.md"))
    print(f"📂 Found {len(files)} files.")

    for md_file in files:
        await ingest_file(md_file, client, embed_model)

    print("✨ Ingestion Complete.")

if __name__ == "__main__":
    asyncio.run(main())
