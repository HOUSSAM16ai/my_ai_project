import time
from collections import defaultdict

from app.core.logging import get_logger
from app.services.procedural_knowledge.domain import (
    AuditResult,
    AuditStatus,
    KnowledgeNode,
    LogicRuleProtocol,
    NodeType,
    ProceduralGraph,
    Relation,
    RelationType,
)

logger = get_logger("procedural-engine")


class GraphAuditor:
    """
    المحرك المسؤول عن تنفيذ التدقيق الإجرائي على الرسم البياني المعرفي.
    """

    def __init__(self, graph: ProceduralGraph) -> None:
        self.graph = graph
        self.rules: list[LogicRuleProtocol] = []
        logger.info("تم تهيئة محرك التدقيق الإجرائي بنجاح.")

    def register_rule(self, rule: LogicRuleProtocol) -> None:
        """تسجيل قاعدة منطقية جديدة."""
        self.rules.append(rule)

    def run_audit(self) -> list[AuditResult]:
        """تنفيذ عملية التدقيق الشاملة."""
        results: list[AuditResult] = []
        logger.info(
            f"بدء عملية التدقيق على {len(self.graph.nodes)} عقدة و {len(self.graph.relations)} علاقة."
        )

        for rule in self.rules:
            start_time = time.time()
            try:
                # Execute Rule
                result = rule(list(self.graph.nodes.values()), self.graph.relations)
                result.timestamp = time.time() - start_time
                results.append(result)

                log_msg = f"قاعدة '{result.rule_id}': {result.status.value}"
                if result.status == AuditStatus.FAIL:
                    logger.warning(f"فشل التدقيق: {log_msg} - {result.message}")
                else:
                    logger.info(f"نجاح التدقيق: {log_msg}")

            except Exception as e:
                logger.error(f"خطأ أثناء تنفيذ قاعدة منطقية: {e}", exc_info=True)
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


# --- قواعد الاحتيال المعقدة (Complex Fraud Rules) ---


class ConflictOfInterestRule:
    """
    قاعدة تعارض المصالح.
    تكتشف ما إذا كان هناك صلة قرابة أو علاقة خفية بين مسؤول حكومي أصدر مناقصة وبين مورد مشارك فيها.
    السيناريو: Tender -> issued_by -> Official -> related_to -> Supplier -> participated_in -> Tender
    """

    def __call__(self, nodes: list[KnowledgeNode], relations: list[Relation]) -> AuditResult:
        evidence = []
        # Build adjacency for fast lookup
        # Map: SourceID -> list of (TargetID, RelationType)
        adj = defaultdict(list)
        for rel in relations:
            adj[rel.source_id].append((rel.target_id, rel.type))

        # Find all Tenders
        tenders = [n for n in nodes if n.type == NodeType.TENDER]

        for tender in tenders:
            # 1. Who issued the tender?
            officials = [
                target
                for target, r_type in adj[tender.id]
                if r_type == RelationType.ISSUED_BY
            ]

            # 2. Who participated in the tender?
            # Note: Participation is usually Supplier -> participated_in -> Tender.
            # So we look for relations where target_id == tender.id
            suppliers = []
            for rel in relations:
                if (
                    rel.target_id == tender.id
                    and rel.type == RelationType.PARTICIPATED_IN
                ):
                    suppliers.append(rel.source_id)

            # 3. Check for relations between Officials and Suppliers
            for official_id in officials:
                # Check relations starting from Official
                related_targets = [
                    target
                    for target, r_type in adj[official_id]
                    if r_type == RelationType.RELATED_TO
                ]

                for supplier_id in suppliers:
                    if supplier_id in related_targets:
                        evidence.append(
                            f"تعارض مصالح: المناقصة {tender.label} أصدرها {official_id} الذي له علاقة بالمشارك {supplier_id}."
                        )

        if evidence:
            return AuditResult(
                rule_id="conflict_of_interest",
                status=AuditStatus.FAIL,
                message="تم اكتشاف تعارض مصالح محتمل بين المسؤولين والموردين.",
                evidence=evidence,
            )

        return AuditResult(
            rule_id="conflict_of_interest",
            status=AuditStatus.PASS,
            message="لم يتم العثور على تعارض مصالح ظاهر في الرسم البياني الحالي.",
            evidence=[],
        )


class SuspiciousLocationRule:
    """
    قاعدة الموقع المشبوه.
    تكتشف ما إذا كان هناك موردون متعددون يتشاركون نفس العنوان الفعلي (مؤشر على شركات وهمية).
    """

    def __call__(self, nodes: list[KnowledgeNode], relations: list[Relation]) -> AuditResult:
        # Map AddressID -> list of CompanyIDs
        address_map = defaultdict(list)

        # Build lookup
        for rel in relations:
            if rel.type == RelationType.LOCATED_AT:
                address_map[rel.target_id].append(rel.source_id)

        suspicious_addresses = []
        for addr_id, companies in address_map.items():
            if len(set(companies)) > 1:
                # Check if these companies are Suppliers (optional strictness)
                suspicious_addresses.append(
                    f"العنوان {addr_id} مشترك بين الشركات: {', '.join(companies)}"
                )

        if suspicious_addresses:
            return AuditResult(
                rule_id="suspicious_location",
                status=AuditStatus.WARNING,  # Warning not Fail, as co-working spaces exist
                message="تم العثور على عناوين مشتركة لشركات متعددة (مؤشر خطر).",
                evidence=suspicious_addresses,
            )

        return AuditResult(
            rule_id="suspicious_location",
            status=AuditStatus.PASS,
            message="جميع الشركات تقع في عناوين منفصلة.",
            evidence=[],
        )


class CycleDetectionRule:
    """
    قاعدة كشف الحلقات المالية (Shell Companies).
    تكتشف حلقات الملكية: A owns B -> B owns C -> C owns A.
    """

    def __call__(self, nodes: list[KnowledgeNode], relations: list[Relation]) -> AuditResult:
        # Build graph for 'OWNS' relations only
        adj = defaultdict(list)
        for rel in relations:
            if rel.type == RelationType.OWNS:
                adj[rel.source_id].append(rel.target_id)

        visited = set()
        recursion_stack = set()
        cycles = []

        def dfs(node_id, path):
            visited.add(node_id)
            recursion_stack.add(node_id)
            path.append(node_id)

            for neighbor in adj[node_id]:
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in recursion_stack:
                    # Cycle found
                    cycle_slice = path[path.index(neighbor) :]
                    cycles.append(" -> ".join(cycle_slice) + f" -> {neighbor}")

            recursion_stack.remove(node_id)
            path.pop()

        for node in nodes:
            if node.id not in visited:
                dfs(node.id, [])

        if cycles:
            return AuditResult(
                rule_id="shell_company_cycle",
                status=AuditStatus.FAIL,
                message="تم اكتشاف حلقات ملكية دائرية (شركات وهمية).",
                evidence=cycles,
            )

        return AuditResult(
            rule_id="shell_company_cycle",
            status=AuditStatus.PASS,
            message="هيكل الملكية سليم ولا توجد حلقات دائرية.",
            evidence=[],
        )


class GraphBuilder:
    """
    مساعد لبناء الرسم البياني من بيانات مهيكلة.
    """

    @staticmethod
    def from_structure(data: dict) -> ProceduralGraph:
        """
        تحويل هيكل بيانات (JSON) إلى كائن ProceduralGraph.
        """
        graph = ProceduralGraph()

        # Parse Nodes
        for n in data.get("nodes", []):
            try:
                node = KnowledgeNode(**n)
                graph.add_node(node)
            except Exception as e:
                logger.warning(f"Failed to parse node: {n} - {e}")

        # Parse Relations
        for r in data.get("relations", []):
            try:
                relation = Relation(**r)
                graph.add_relation(relation)
            except Exception as e:
                logger.warning(f"Failed to parse relation: {r} - {e}")

        return graph
