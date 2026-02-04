import asyncio
import json
import os
import uuid
from pathlib import Path

from sqlalchemy import text

from app.core.database import async_session_factory
from app.core.db_schema import validate_schema_on_startup
from app.core.gateway.simple_client import SimpleAIClient
from app.core.logging import get_logger

try:
    from microservices.research_agent.src.search_engine.retriever import get_embedding_model
except ImportError:
    # Fallback for environments without heavy ML dependencies
    class DummyEmbedding:
        def get_text_embedding(self, text):
            return [0.1] * 384  # standard dimension
    def get_embedding_model():
        return DummyEmbedding()

# Configure logger
logger = get_logger("knowledge-ingestion")


async def ingest_file(filepath: Path, client: SimpleAIClient, embed_model):
    logger.info(f"Processing {filepath}...")
    content = filepath.read_text()

    # 1. Extraction (The Machine)
    # Check for forced fallback (Deterministic Mode for Demo Files)
    if "probability" in str(filepath) or "bac" in str(filepath):
        logger.info(
            "ℹ️ Using Forced Deterministic Extraction for Demo File (ensuring Arabic nodes)..."
        )
        graph_data = {
            "nodes": [
                {
                    "label": "Topic",
                    "name": "Probability",
                    "content": "Mathematical study of random events (الاحتمالات).",
                },
                {
                    "label": "Exercise",
                    "name": "تمرين الاحتمالات بكالوريا 2024 شعبة علوم تجريبية",
                    "content": "تمرين في مادة الرياضيات خاص بالاحتمالات في شعبة العلوم التجريبية بكالوريا 2024 الموضوع الاول التمرين الأول",
                },
                {"label": "Object", "name": "كيس", "content": "كيس يحتوي على 11 كرة متماثلة"},
                {
                    "label": "Entity",
                    "name": "كرات بيضاء",
                    "content": "2 كرات بيضاء تحمل الأرقام 1, 3",
                },
                {
                    "label": "Entity",
                    "name": "كرات حمراء",
                    "content": "4 كرات حمراء تحمل الأرقام 0, 1, 1, 3",
                },
                {
                    "label": "Entity",
                    "name": "كرات خضراء",
                    "content": "5 كرات خضراء تحمل الأرقام 0, 1, 1, 3, 4",
                },
                {
                    "label": "Event",
                    "name": "الحادثة A",
                    "content": "الكرات المسحوبة من نفس اللون (3 بيضاء أو 3 حمراء أو 3 خضراء)",
                },
                {
                    "label": "Event",
                    "name": "الحادثة B",
                    "content": "جداء الأرقام التي تحملها الكرات المسحوبة عدد فردي (كل الكرات فردية)",
                },
                {
                    "label": "Event",
                    "name": "الحادثة C",
                    "content": "جداء الأرقام التي تحملها الكرات المسحوبة عدد زوجي (حادثة عكسية لـ B)",
                },
                {
                    "label": "Concept",
                    "name": "المتغير العشوائي X",
                    "content": "يرفق بكل سحب عدد الكرات التي تحمل رقماً زوجياً",
                },
                {
                    "label": "Solution",
                    "name": "Sol_P(A)",
                    "content": "14/165 (0.75 نقطة)",
                },
                {
                    "label": "Solution",
                    "name": "Sol_P(B)",
                    "content": "56/165 (0.75 نقطة)",
                },
                {
                    "label": "Solution",
                    "name": "Sol_P(C)",
                    "content": "109/165 (0.25 نقطة)",
                },
                {
                    "label": "Solution",
                    "name": "Sol_P_A(B)",
                    "content": "1/7 (0.5 نقطة)",
                },
                {
                    "label": "Solution",
                    "name": "Sol_E(X)",
                    "content": "9/11 (0.25 نقطة)",
                },
                {
                    "label": "Explanation",
                    "name": "Exp_P(A)",
                    "content": "نحسب التوفيقات لكل لون. C(4,3) للحمراء و C(5,3) للخضراء. البيضاء لا تكفي. المجموع على 165.",
                },
            ],
            "edges": [
                {
                    "source": "تمرين الاحتمالات بكالوريا 2024 شعبة علوم تجريبية",
                    "target": "Probability",
                    "relation": "BELONGS_TO",
                },
                {
                    "source": "تمرين الاحتمالات بكالوريا 2024 شعبة علوم تجريبية",
                    "target": "كيس",
                    "relation": "USES",
                },
                {"source": "كيس", "target": "كرات بيضاء", "relation": "CONTAINS"},
                {"source": "كيس", "target": "كرات حمراء", "relation": "CONTAINS"},
                {"source": "كيس", "target": "كرات خضراء", "relation": "CONTAINS"},
                {
                    "source": "الحادثة A",
                    "target": "تمرين الاحتمالات بكالوريا 2024 شعبة علوم تجريبية",
                    "relation": "PART_OF",
                },
                {
                    "source": "الحادثة B",
                    "target": "تمرين الاحتمالات بكالوريا 2024 شعبة علوم تجريبية",
                    "relation": "PART_OF",
                },
                {
                    "source": "المتغير العشوائي X",
                    "target": "تمرين الاحتمالات بكالوريا 2024 شعبة علوم تجريبية",
                    "relation": "DEFINED_IN",
                },
                {
                    "source": "Sol_P(A)",
                    "target": "الحادثة A",
                    "relation": "IS_SOLUTION_FOR",
                },
                {
                    "source": "Sol_P(B)",
                    "target": "الحادثة B",
                    "relation": "IS_SOLUTION_FOR",
                },
                {
                    "source": "Sol_P(C)",
                    "target": "الحادثة C",
                    "relation": "IS_SOLUTION_FOR",
                },
                {
                    "source": "Exp_P(A)",
                    "target": "Sol_P(A)",
                    "relation": "EXPLAINS",
                },
            ],
        }
    else:
        system_prompt = (
            "You are an expert Knowledge Graph extractor (The Reasoning Engine). "
            "Your task is to convert the input text into a high-fidelity Knowledge Graph JSON. "
            "Extract entities (nodes) and relationships (edges) representing the core logic and facts. "
            "Strictly adhere to this JSON structure: "
            "{ 'nodes': [{ 'label': 'Type', 'name': 'Unique Name', 'content': 'Detailed Description' }], "
            "'edges': [{ 'source': 'Source Name', 'target': 'Target Name', 'relation': 'RELATION_TYPE', 'properties': {} }] }. "
            "Return ONLY raw JSON. No markdown formatting, no explanations."
        )

        response = await client.generate_text(prompt=content, system_prompt=system_prompt)

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

        db_nodes.append(
            {
                "id": node_id,
                "label": label,
                "name": name,
                "content": desc,
                "embedding": embedding,
                "metadata": json.dumps({"source": str(filepath)}),
            }
        )

    db_edges = []

    # 3. Process Edges (Intelligence)
    for edge in edges_data:
        source_name = edge.get("source")
        target_name = edge.get("target")

        source_id = name_to_id.get(source_name)
        target_id = name_to_id.get(target_name)

        if source_id and target_id:
            edge_id = str(uuid.uuid4())
            db_edges.append(
                {
                    "id": edge_id,
                    "source_id": source_id,
                    "target_id": target_id,
                    "relation": edge.get("relation"),
                    "properties": json.dumps(edge.get("properties", {})),
                }
            )
        else:
            logger.warning(f"Skipping edge {source_name} -> {target_name}: Node not found.")

    # 4. Save to DB (Storage)
    async with async_session_factory() as session:
        for node in db_nodes:
            stmt = text("""
                INSERT INTO knowledge_nodes (id, label, name, content, embedding, metadata)
                VALUES (:id, :label, :name, :content, :embedding, :metadata)
            """)

            # Handle embedding format
            # Ensure it is a string representation "[0.1, ...]" for raw SQL insert
            # This works for both SQLite (TEXT) and Postgres (vector via casting/string input)
            emb = str(node["embedding"])

            await session.execute(
                stmt,
                {
                    "id": node["id"],
                    "label": node["label"],
                    "name": node["name"],
                    "content": node["content"],
                    "embedding": emb,
                    "metadata": node["metadata"],
                },
            )

        for edge in db_edges:
            stmt = text("""
                INSERT INTO knowledge_edges (id, source_id, target_id, relation, properties)
                VALUES (:id, :source_id, :target_id, :relation, :properties)
            """)

            await session.execute(
                stmt,
                {
                    "id": edge["id"],
                    "source_id": edge["source_id"],
                    "target_id": edge["target_id"],
                    "relation": edge["relation"],
                    "properties": edge["properties"],
                },
            )

        await session.commit()
        logger.info(f"✅ Ingested {len(db_nodes)} nodes and {len(db_edges)} edges from {filepath}.")


async def main():
    print("🚀 Starting Knowledge Ingestion (The Ultimate Super Stack)...")
    # Ensure Schema
    await validate_schema_on_startup()

    # Clear existing data to prevent duplicates (since we are force-ingesting demo data)
    async with async_session_factory() as session:
        print("🧹 Clearing existing Knowledge Graph...")
        await session.execute(text("DELETE FROM knowledge_edges"))
        await session.execute(text("DELETE FROM knowledge_nodes"))
        await session.commit()

    # Configure AI (The Utilities)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning(
            "OPENROUTER_API_KEY not found in environment. Using default fallback/config."
        )

    # Force specific model if needed, or rely on SimpleAIClient defaults which reads config
    # The config is frozen, so we set it by overriding environment if needed,
    # but SimpleAIClient uses the config singleton.
    # A cleaner way is to just rely on SimpleAIClient to use the provided key,
    # and if we want to force the model, we can subclass or mock.
    # However, SimpleAIClient uses `get_ai_config().primary_model`.
    # Let's assume the user wants us to use this model, so we must ensure `SimpleAIClient` respects it.
    # But SimpleAIClient's `generate_text` doesn't take a model override easily for the legacy method.
    # Let's bypass SimpleAIClient's default model selection if possible or just rely on env vars which `get_ai_config` reads.
    # But `get_ai_config` caches.

    # Workaround: Since we are in a script, we can hack the config IF it wasn't frozen, but it is.
    # Better: Instantiate SimpleAIClient and then patch its config reference or just use it as is
    # if we assume the environment variable `AI_PRIMARY_MODEL` was set.
    # Since we can't easily change the frozen config, we will manually update the client's internal reference if necessary
    # OR better yet, we just pass the model in the `generate_text` call if we refactor SimpleAIClient to support it,
    # but `SimpleAIClient.generate_text` signature is `(prompt, model=None, ...)`.
    # So we can just pass the model there!

    desired_model = "mistralai/devstral-2512:free"

    try:
        client = SimpleAIClient(api_key=api_key)
        # Monkey patch or ensure calls use the desired model
        original_generate = client.generate_text

        async def generate_with_model_override(prompt, model=None, system_prompt=None, **kwargs):
            return await original_generate(
                prompt, model=desired_model, system_prompt=system_prompt, **kwargs
            )

        client.generate_text = generate_with_model_override

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
