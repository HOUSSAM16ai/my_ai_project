"""
مكونات تقييم الذاكرة طويلة المدى وفق معيار LongMemEval.

تركز هذه النماذج على الاسترجاع الدقيق، التحديث، التسلسل الزمني،
ومعايير الامتناع عند غياب المعرفة.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

ScalarValue = str | int | float | bool


@dataclass(frozen=True)
class MemoryEvent:
    """يمثل حدثاً معرفياً تم تخزينه عبر جلسة أو أكثر."""

    session_id: str
    timestamp: datetime
    key: str
    value: ScalarValue
    is_update: bool = False


@dataclass(frozen=True)
class MemoryQuery:
    """يمثل استعلاماً لاختبار قدرات الاسترجاع عبر جلسات متعددة."""

    session_id: str
    key: str
    expected_value: ScalarValue | None
    query_type: str


@dataclass(frozen=True)
class LongMemoryScore:
    """نتيجة معيارية لتقييم الذاكرة طويلة المدى."""

    accuracy: float
    abstention_rate: float
    temporal_order_score: float
    update_consistency: float
    notes: list[str]


def evaluate_long_memory(
    events: list[MemoryEvent], queries: list[MemoryQuery]
) -> LongMemoryScore:
    """
    ينفذ تقييماً بسيطاً لنتائج الذاكرة وفق LongMemEval بشكل وظيفي.
    """

    if not queries:
        return LongMemoryScore(
            accuracy=1.0,
            abstention_rate=0.0,
            temporal_order_score=1.0,
            update_consistency=1.0,
            notes=["لا توجد استعلامات للاختبار."],
        )

    latest_values: dict[str, ScalarValue] = {}
    last_timestamps: dict[str, datetime] = {}
    update_hits = 0
    update_total = 0

    for event in sorted(events, key=lambda item: item.timestamp):
        if event.key in last_timestamps:
            if event.timestamp < last_timestamps[event.key]:
                continue
        last_timestamps[event.key] = event.timestamp
        latest_values[event.key] = event.value
        if event.is_update:
            update_total += 1

    correct = 0
    abstained = 0
    temporal_hits = 0

    for query in queries:
        if query.expected_value is None:
            abstained += 1
            continue
        actual_value = latest_values.get(query.key)
        if actual_value == query.expected_value:
            correct += 1
        if query.key in last_timestamps:
            temporal_hits += 1
        if query.query_type == "update" and actual_value == query.expected_value:
            update_hits += 1

    total_queries = len(queries)
    accuracy = correct / total_queries if total_queries else 0.0
    abstention_rate = abstained / total_queries if total_queries else 0.0
    temporal_order_score = temporal_hits / total_queries if total_queries else 0.0
    update_consistency = update_hits / update_total if update_total else 1.0

    notes = []
    if update_total == 0:
        notes.append("لا توجد أحداث تحديث لاختبار الاتساق.")
    if abstained:
        notes.append("تم تسجيل امتناع في بعض الاستعلامات لغياب المعرفة.")

    return LongMemoryScore(
        accuracy=accuracy,
        abstention_rate=abstention_rate,
        temporal_order_score=temporal_order_score,
        update_consistency=update_consistency,
        notes=notes,
    )
