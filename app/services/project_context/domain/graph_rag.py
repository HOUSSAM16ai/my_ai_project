"""
نماذج GraphRAG للذاكرة المهيكلة واسترجاع المعرفة.

يوفر هذا الملف تمثيلاً وظيفياً للرسم البياني المعرفي مع عمليات بناء واستعلام
تسمح بتتبع العلاقات عبر قفزات متعددة دون آثار جانبية.
"""

from __future__ import annotations

from dataclasses import dataclass

ScalarValue = str | int | float | bool
Attributes = dict[str, ScalarValue]


@dataclass(frozen=True)
class GraphEntity:
    """يمثل كياناً معرفياً داخل الرسم البياني."""

    entity_id: str
    entity_type: str
    attributes: Attributes


@dataclass(frozen=True)
class GraphRelation:
    """يمثل علاقة موجهة بين كيانين داخل الرسم البياني."""

    source_id: str
    target_id: str
    relation_type: str
    metadata: Attributes


@dataclass(frozen=True)
class GraphRAGIndex:
    """فهرس GraphRAG الذي يحتوي على الكيانات وعلاقاتها ضمن بنية قابلة للاستعلام."""

    nodes: dict[str, GraphEntity]
    adjacency: dict[str, list[GraphRelation]]


@dataclass(frozen=True)
class GraphRAGResult:
    """نتيجة استعلام GraphRAG مع الكيانات والعلاقات ضمن نطاق القفزات."""

    nodes: list[GraphEntity]
    relations: list[GraphRelation]
    hops: int


def build_graph_index(
    entities: list[GraphEntity], relations: list[GraphRelation]
) -> GraphRAGIndex:
    """يبني فهرساً معرفياً خالصاً من الكيانات والعلاقات."""

    node_map = {entity.entity_id: entity for entity in entities}
    adjacency: dict[str, list[GraphRelation]] = {}
    for relation in relations:
        adjacency.setdefault(relation.source_id, []).append(relation)
    return GraphRAGIndex(nodes=node_map, adjacency=adjacency)


def query_graph(
    index: GraphRAGIndex, seed_ids: list[str], max_hops: int = 2
) -> GraphRAGResult:
    """يسترجع عقداً وعلاقات ضمن عدد محدد من القفزات بدءاً من بذور المعرفة."""

    visited: set[str] = set(seed_ids)
    frontier: set[str] = set(seed_ids)
    collected_relations: list[GraphRelation] = []

    for _ in range(max_hops):
        next_frontier: set[str] = set()
        for node_id in frontier:
            for relation in index.adjacency.get(node_id, []):
                collected_relations.append(relation)
                if relation.target_id not in visited:
                    visited.add(relation.target_id)
                    next_frontier.add(relation.target_id)
        frontier = next_frontier
        if not frontier:
            break

    collected_nodes = [node for node_id, node in index.nodes.items() if node_id in visited]
    return GraphRAGResult(nodes=collected_nodes, relations=collected_relations, hops=max_hops)
