"""
خدمات الذاكرة المهيكلة للوكيل (GraphRAG & LongMemEval).

تطبق هذه الوحدة طبقة تطبيقية خفيفة تحفظ الذاكرة في حدود واضحة،
وتوفر واجهات مطابقة لبروتوكولات النواة دون خلط مع تفاصيل التنفيذ.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.protocols import GraphMemoryProtocol, LongMemoryEvaluatorProtocol
from app.services.project_context.domain.graph_rag import (
    GraphEntity,
    GraphRAGIndex,
    GraphRelation,
    build_graph_index,
    query_graph,
)
from app.services.project_context.domain.long_memory_eval import (
    LongMemoryScore,
    MemoryEvent,
    MemoryQuery,
    evaluate_long_memory,
)


@dataclass
class InMemoryGraphMemory(GraphMemoryProtocol):
    """ذاكرة GraphRAG داخلية لتجميع الكيانات والعلاقات."""

    _entities: dict[str, GraphEntity] = field(default_factory=dict)
    _relations: list[GraphRelation] = field(default_factory=list)

    def upsert_entities(self, entities: list[dict[str, object]]) -> None:
        """تسجيل أو تحديث الكيانات داخل الذاكرة المهيكلة."""

        for payload in entities:
            entity_id = str(payload.get("entity_id", ""))
            if not entity_id:
                continue
            entity = GraphEntity(
                entity_id=entity_id,
                entity_type=str(payload.get("entity_type", "unknown")),
                attributes=payload.get("attributes", {}),
            )
            self._entities[entity.entity_id] = entity

    def upsert_relations(self, relations: list[dict[str, object]]) -> None:
        """تسجيل أو تحديث العلاقات بين الكيانات."""

        for payload in relations:
            source_id = str(payload.get("source_id", ""))
            target_id = str(payload.get("target_id", ""))
            if not source_id or not target_id:
                continue
            relation = GraphRelation(
                source_id=source_id,
                target_id=target_id,
                relation_type=str(payload.get("relation_type", "related")),
                metadata=payload.get("metadata", {}),
            )
            self._relations.append(relation)

    def query(self, seed_ids: list[str], max_hops: int = 2) -> dict[str, object]:
        """استرجاع السياق عبر الرسم البياني وفق عدد القفزات."""

        index = build_graph_index(list(self._entities.values()), self._relations)
        result = query_graph(index, seed_ids=seed_ids, max_hops=max_hops)
        return {
            "nodes": [node.__dict__ for node in result.nodes],
            "relations": [relation.__dict__ for relation in result.relations],
            "hops": result.hops,
        }

    def snapshot(self) -> GraphRAGIndex:
        """إرجاع لقطة ثابتة لفهرس GraphRAG الحالي."""

        return build_graph_index(list(self._entities.values()), self._relations)


@dataclass
class LongMemoryEvaluator(LongMemoryEvaluatorProtocol):
    """مقيم الذاكرة طويلة المدى وفق LongMemEval."""

    def evaluate(
        self, events: list[dict[str, object]], queries: list[dict[str, object]]
    ) -> dict[str, object]:
        """تنفيذ تقييم شامل لقدرات الذاكرة طويلة المدى."""

        normalized_events = [
            MemoryEvent(
                session_id=str(item["session_id"]),
                timestamp=item["timestamp"],
                key=str(item["key"]),
                value=item["value"],
                is_update=bool(item.get("is_update", False)),
            )
            for item in events
        ]
        normalized_queries = [
            MemoryQuery(
                session_id=str(item["session_id"]),
                key=str(item["key"]),
                expected_value=item.get("expected_value"),
                query_type=str(item.get("query_type", "recall")),
            )
            for item in queries
        ]
        score = evaluate_long_memory(normalized_events, normalized_queries)
        return _score_to_dict(score)


def _score_to_dict(score: LongMemoryScore) -> dict[str, object]:
    """تحويل نتيجة التقييم إلى تمثيل معجمي قابل للإرسال عبر الحدود."""

    return {
        "accuracy": score.accuracy,
        "abstention_rate": score.abstention_rate,
        "temporal_order_score": score.temporal_order_score,
        "update_consistency": score.update_consistency,
        "notes": score.notes,
    }
