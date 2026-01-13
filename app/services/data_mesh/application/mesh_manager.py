from __future__ import annotations

import logging
import threading
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import UTC, datetime

from app.services.data_mesh.domain.models import (
    BoundedContext,
    DataContract,
    DataDomainType,
    DataProduct,
    DataProductStatus,
    DataQualityMetrics,
    GovernanceLevel,
    GovernancePolicy,
    SchemaCompatibility,
    SchemaEvolution,
)


class DataMeshManager:
    """
    Application Layer for Data Mesh.
    Manages the lifecycle of data products, contracts, and governance.
    """

    def __init__(self) -> None:
        self.bounded_contexts: dict[str, BoundedContext] = {}
        self.data_contracts: dict[str, DataContract] = {}
        self.data_products: dict[str, DataProduct] = {}
        self.governance_policies: dict[str, GovernancePolicy] = {}
        self.quality_metrics: dict[str, deque[DataQualityMetrics]] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.schema_evolutions: dict[str, list[SchemaEvolution]] = defaultdict(list)
        self.event_streams: dict[str, deque[dict[str, object]]] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        self.lock = threading.RLock()

        self._initialize_governance()

    def _initialize_governance(self) -> None:
        """Initialize default governance policies"""
        self._create_quality_standard_policy()
        self._create_schema_compatibility_policy()

    def _create_quality_standard_policy(self) -> None:
        self.add_governance_policy(
            GovernancePolicy(
                policy_id="quality-standard",
                name="Data Quality Standard",
                description="Minimum data quality requirements",
                level=GovernanceLevel.MANDATORY,
                rules=[
                    {"type": "completeness", "threshold": 0.95},
                    {"type": "accuracy", "threshold": 0.98},
                    {"type": "freshness_max_seconds", "threshold": 3600},
                ],
                applicable_domains=list(DataDomainType),
                enforcement_actions=["alert", "block_consumption"],
            )
        )

    def _create_schema_compatibility_policy(self) -> None:
        self.add_governance_policy(
            GovernancePolicy(
                policy_id="schema-compatibility",
                name="Schema Compatibility Policy",
                description="Ensure backward compatibility for all schema changes",
                level=GovernanceLevel.MANDATORY,
                rules=[
                    {"type": "compatibility_mode", "allowed": ["backward", "full"]},
                    {"type": "breaking_changes", "allowed": False},
                ],
                applicable_domains=list(DataDomainType),
                enforcement_actions=["reject_deployment"],
            )
        )

    def register_bounded_context(self, context: BoundedContext) -> bool:
        with self.lock:
            if context.context_id in self.bounded_contexts:
                logging.getLogger(__name__).warning(
                    f"Bounded context already exists: {context.context_id}"
                )
                return False

            self.bounded_contexts[context.context_id] = context
            logging.getLogger(__name__).info(f"Registered bounded context: {context.name}")
            return True

    def get_bounded_context(self, context_id: str) -> BoundedContext | None:
        return self.bounded_contexts.get(context_id)

    def create_data_contract(self, contract: DataContract) -> bool:
        with self.lock:
            if not self._validate_schema_compatibility(contract):
                logging.getLogger(__name__).error(
                    f"Schema compatibility validation failed: {contract.name}"
                )
                return False

            if not self._check_governance_compliance(contract):
                logging.getLogger(__name__).error(
                    f"Governance compliance check failed: {contract.name}"
                )
                return False

            self.data_contracts[contract.contract_id] = contract
            logging.getLogger(__name__).info(f"Created data contract: {contract.name}")

            self._publish_event(
                "data.contract.created",
                {
                    "contract_id": contract.contract_id,
                    "domain": contract.domain.value,
                    "name": contract.name,
                    "version": contract.schema_version,
                },
            )

            return True

    def register_product(self, product_def: dict[str, object], owner_id: str) -> DataProduct:
        """
        تسجيل منتج بيانات جديد.
        """
        self._validate_product_ownership(owner_id)
        product = self._create_product_entity(product_def, owner_id)

        if not self.register_data_product(product):
            raise ValueError(f"Product {product.product_id} already exists")

        return product

    def _validate_product_ownership(self, owner_id: str) -> None:
        # In a real system, this would check against an identity service
        if not owner_id:
            raise ValueError("Owner ID is required")

    def _create_product_entity(self, product_def: dict[str, object], owner_id: str) -> DataProduct:
        return DataProduct(
            product_id=product_def["product_id"],
            name=product_def["name"],
            domain=DataDomainType(product_def["domain"]),
            description=product_def.get("description", ""),
            owner_team=owner_id,
            contracts=[],
            quality_metrics={},
            access_patterns=[],
            lineage={},
            status=DataProductStatus.ACTIVE,
        )

    def evolve_contract_schema(
        self,
        contract_id: str,
        new_schema: dict[str, object],
        new_version: str,
        changes: list[dict[str, object]],
    ) -> SchemaEvolution | None:
        """
        تطور مخطط العقد وتتحقق من التوافق.
        Evolves the contract schema and checks for compatibility.
        """
        contract = self.data_contracts.get(contract_id)
        if not contract:
            return None

        compatibility = self._check_schema_compatibility(
            contract.schema_definition, new_schema, changes
        )
        if not compatibility:
            return None

        evolution = self._create_schema_evolution(
            contract_id=contract_id,
            contract_version=contract.schema_version,
            new_version=new_version,
            changes=changes,
            compatibility=compatibility,
        )

        self._apply_schema_evolution(contract, evolution, new_schema, new_version)
        return evolution

    def _check_schema_compatibility(
        self,
        old_schema: dict[str, object],
        new_schema: dict[str, object],
        changes: list[dict[str, object]],
    ) -> SchemaCompatibility | None:
        """
        التحقق من توافق المخطط مع السياسات.
        Checks schema compatibility against governance policies.
        """
        compatibility = self._detect_schema_compatibility(old_schema, new_schema, changes)

        if compatibility == SchemaCompatibility.BREAKING:
            policy = self.governance_policies.get("schema-compatibility")
            if policy and policy.enabled:
                logging.getLogger(__name__).error("Breaking schema changes not allowed")
                return None

        return compatibility

    def _create_schema_evolution(
        self,
        contract_id: str,
        contract_version: str,
        new_version: str,
        changes: list[dict[str, object]],
        compatibility: SchemaCompatibility,
    ) -> SchemaEvolution:
        """
        إنشاء كائن تطور المخطط.
        Creates the SchemaEvolution object.
        """
        return SchemaEvolution(
            evolution_id=str(uuid.uuid4()),
            contract_id=contract_id,
            from_version=contract_version,
            to_version=new_version,
            changes=changes,
            compatibility=compatibility,
            migration_scripts=[],
            validated_at=datetime.now(UTC),
        )

    def _apply_schema_evolution(
        self,
        contract: DataContract,
        evolution: SchemaEvolution,
        new_schema: dict[str, object],
        new_version: str,
    ) -> None:
        """
        تطبيق تطور المخطط على العقد وتحديث الحالة.
        Applies the evolution to the contract and updates state safely.
        """
        with self.lock:
            self.schema_evolutions[contract.contract_id].append(evolution)
            contract.schema_definition = new_schema
            contract.schema_version = new_version
            contract.updated_at = datetime.now(UTC)

            logging.getLogger(__name__).info(
                f"Schema evolved: {contract.name} v{new_version} ({evolution.compatibility.value})"
            )

    def _validate_schema_compatibility(self, contract: DataContract) -> bool:
        required_fields = ["type", "properties"]
        schema = contract.schema_definition
        return all(field in schema for field in required_fields)

    def _detect_schema_compatibility(
        self,
        old_schema: dict[str, object],
        new_schema: dict[str, object],
        changes: list[dict[str, object]],
    ) -> SchemaCompatibility:
        breaking_change_types = ["field_removed", "field_type_changed", "constraint_added"]

        for change in changes:
            if change.get("type") in breaking_change_types:
                return SchemaCompatibility.BREAKING

        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))

        if not old_required.issubset(new_required):
            return SchemaCompatibility.FORWARD

        if not new_required.issubset(old_required):
            return SchemaCompatibility.BACKWARD

        return SchemaCompatibility.FULL

    def register_data_product(self, product: DataProduct) -> bool:
        with self.lock:
            if product.product_id in self.data_products:
                return False

            self.data_products[product.product_id] = product
            logging.getLogger(__name__).info(f"Registered data product: {product.name}")

            self._publish_event(
                "data.product.registered",
                {
                    "product_id": product.product_id,
                    "name": product.name,
                    "domain": product.domain.value,
                },
            )

            return True

    def get_data_products_by_domain(self, domain: DataDomainType) -> list[DataProduct]:
        return [p for p in self.data_products.values() if p.domain == domain]

    def add_governance_policy(self, policy: GovernancePolicy) -> bool:
        with self.lock:
            self.governance_policies[policy.policy_id] = policy
            logging.getLogger(__name__).info(f"Added governance policy: {policy.name}")
            return True

    def _check_governance_compliance(self, contract: DataContract) -> bool:
        for policy in self.governance_policies.values():
            if not policy.enabled:
                continue

            if contract.domain not in policy.applicable_domains:
                continue

            if policy.level == GovernanceLevel.MANDATORY:
                for rule in policy.rules:
                    if not self._evaluate_governance_rule(contract, rule):
                        logging.getLogger(__name__).error(
                            f"Governance violation: {policy.name} - {rule}"
                        )
                        return False

        return True

    def _evaluate_governance_rule(self, contract: DataContract, rule: dict[str, object]) -> bool:
        rule_type = rule.get("type")
        if rule_type == "compatibility_mode":
            allowed_modes = rule.get("allowed", [])
            return contract.compatibility_mode.value in allowed_modes
        return True

    def record_quality_metrics(self, metrics: DataQualityMetrics) -> None:
        with self.lock:
            self.quality_metrics[metrics.product_id].append(metrics)
            self._check_quality_thresholds(metrics)

    def _check_quality_thresholds(self, metrics: DataQualityMetrics) -> None:
        policy = self.governance_policies.get("quality-standard")
        if not policy or not policy.enabled:
            return

        for rule in policy.rules:
            rule_type = rule.get("type")
            threshold = rule.get("threshold")

            if threshold is None:
                continue

            if rule_type == "completeness" and metrics.completeness < float(threshold):
                self._trigger_governance_action(
                    policy, f"Completeness below threshold: {metrics.completeness:.2%}"
                )
            elif rule_type == "accuracy" and metrics.accuracy < float(threshold):
                self._trigger_governance_action(
                    policy, f"Accuracy below threshold: {metrics.accuracy:.2%}"
                )
            elif rule_type == "freshness_max_seconds" and metrics.freshness_seconds > float(
                threshold
            ):
                self._trigger_governance_action(
                    policy, f"Data freshness exceeded: {metrics.freshness_seconds}s"
                )

    def _trigger_governance_action(self, policy: GovernancePolicy, reason: str) -> None:
        logging.getLogger(__name__).warning(f"Governance action: {policy.name} - {reason}")
        # In future: implement specific actions like blocking consumption

    def get_quality_summary(self, product_id: str) -> dict[str, object] | None:
        metrics_list = list(self.quality_metrics.get(product_id, []))
        if not metrics_list:
            return None

        recent_metrics = metrics_list[-10:]

        return {
            "product_id": product_id,
            "avg_completeness": sum(m.completeness for m in recent_metrics) / len(recent_metrics),
            "avg_accuracy": sum(m.accuracy for m in recent_metrics) / len(recent_metrics),
            "avg_consistency": sum(m.consistency for m in recent_metrics) / len(recent_metrics),
            "avg_timeliness": sum(m.timeliness for m in recent_metrics) / len(recent_metrics),
            "avg_freshness_seconds": sum(m.freshness_seconds for m in recent_metrics)
            / len(recent_metrics),
            "total_volume": sum(m.volume for m in recent_metrics),
            "avg_error_rate": sum(m.error_rate for m in recent_metrics) / len(recent_metrics),
            "sample_count": len(recent_metrics),
        }

    def _publish_event(self, event_type: str, payload: dict[str, object]) -> None:
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        with self.lock:
            self.event_streams[event_type].append(event)

    def subscribe_to_events(
        self, event_type: str, callback: Callable[[dict[str, object]], None]
    ) -> str:
        subscription_id = str(uuid.uuid4())
        logging.getLogger(__name__).info(f"Subscribed to {event_type}: {subscription_id}")
        return subscription_id

    def get_event_stream(self, event_type: str, limit: int = 100) -> list[dict[str, object]]:
        events = list(self.event_streams.get(event_type, []))
        return events[-limit:]

    def get_mesh_metrics(self) -> dict[str, object]:
        return {
            "bounded_contexts": len(self.bounded_contexts),
            "data_contracts": len(self.data_contracts),
            "data_products": len(self.data_products),
            "governance_policies": len(self.governance_policies),
            "active_policies": len([p for p in self.governance_policies.values() if p.enabled]),
            "schema_evolutions": sum(len(evs) for evs in self.schema_evolutions.values()),
            "domains": {
                domain.value: len([p for p in self.data_products.values() if p.domain == domain])
                for domain in DataDomainType
            },
        }
