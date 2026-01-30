import time

from app.core.logging import get_logger
from app.services.procedural_knowledge.domain import (
    AuditResult,
    AuditStatus,
    KnowledgeNode,
    LogicRuleProtocol,
    ProceduralGraph,
    RelationType,
)

logger = get_logger("procedural-engine")


class GraphAuditor:
    """
    المحرك المسؤول عن تنفيذ التدقيق الإجرائي على الرسم البياني المعرفي.
    يقوم هذا المحرك بتطبيق القواعد المنطقية لكشف الاحتيال أو الأخطاء الهيكلية.
    """

    def __init__(self, graph: ProceduralGraph) -> None:
        self.graph = graph
        self.rules: list[LogicRuleProtocol] = []
        logger.info("تم تهيئة محرك التدقيق الإجرائي بنجاح.")

    def register_rule(self, rule: LogicRuleProtocol) -> None:
        """
        تسجيل قاعدة منطقية جديدة ليتم فحصها أثناء عملية التدقيق.
        """
        self.rules.append(rule)

    def run_audit(self) -> list[AuditResult]:
        """
        تنفيذ عملية التدقيق الشاملة بتطبيق كافة القواعد المسجلة.

        Returns:
            list[AuditResult]: قائمة بنتائج التدقيق لكل قاعدة.
        """
        results: list[AuditResult] = []
        logger.info(
            f"بدء عملية التدقيق على {len(self.graph.nodes)} عقدة و {len(self.graph.relations)} علاقة."
        )

        for rule in self.rules:
            start_time = time.time()
            try:
                # نمرر العقد كقائمة والعلاقات كقائمة للقاعدة
                # يمكن تحسين هذا لتمرير الكائن الكامل، ولكن نلتزم بالبروتوكول الحالي
                result = rule(list(self.graph.nodes.values()), self.graph.relations)
                result.timestamp = time.time() - start_time
                results.append(result)

                log_msg = f"قاعدة '{result.rule_id}': {result.status.value}"
                if result.status == AuditStatus.FAIL:
                    logger.warning(f"فشل التدقيق: {log_msg} - {result.message}")
                else:
                    logger.info(f"نجاح التدقيق: {log_msg}")

            except Exception as e:
                logger.error(f"خطأ أثناء تنفيذ قاعدة منطقية: {e}")
                results.append(
                    AuditResult(
                        rule_id="unknown_error",
                        status=AuditStatus.FAIL,
                        message=f"حدث خطأ غير متوقع أثناء الفحص: {e!s}",
                        evidence=[],
                        timestamp=time.time() - start_time,
                    )
                )

        return results

    def get_neighbors(
        self, node_id: str, relation_type: RelationType | None = None
    ) -> list[KnowledgeNode]:
        """
        استرجاع العقد المجاورة (المتصلة بعلاقة موجهة) لعقدة معينة.
        """
        neighbors: list[KnowledgeNode] = []
        for rel in self.graph.relations:
            if rel.source_id == node_id and (relation_type is None or rel.type == relation_type):
                target_node = self.graph.get_node(rel.target_id)
                if target_node:
                    neighbors.append(target_node)
        return neighbors

    def find_nodes_by_type(self, type_val: str) -> list[KnowledgeNode]:
        """
        البحث عن جميع العقد التي تنتمي لنوع معين.
        """
        return [node for node in self.graph.nodes.values() if node.type == type_val]
