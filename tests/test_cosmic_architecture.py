# ======================================================================================
#  TESTS FOR COSMIC EXISTENTIAL ARCHITECTURE
# ======================================================================================
#  PURPOSE: Comprehensive tests for the Pragmatic Simplicity system
# ======================================================================================

from datetime import datetime

import pytest

from app.cosmic.automation import ExistentialAI
from app.cosmic.evolution import LearningType, SelfEvolvingConsciousnessEntity
from app.cosmic.evolution.sece import LearningInsight
from app.cosmic.primitives import (
    ConsciousnessType,
    ExistentialInterconnect,
    ExistentialProtocolPackage,
    GovernedConsciousnessUnit,
    InterconnectType,
    ProtocolFactory,
    ProtocolSeverity,
    ProtocolType,
    SecurityLevel,
)
from app.cosmic.rules import (
    AutonomousEvolutionRule,
    CosmicDesignEnforcer,
    DualConsciousnessRule,
    InfiniteScalabilityRule,
)


class TestGovernedConsciousnessUnit:
    """Tests for GCU - Governed Consciousness Unit"""

    def test_gcu_creation(self):
        """Test GCU can be created with proper initialization"""
        gcu = GovernedConsciousnessUnit(
            entity_type=ConsciousnessType.AI, entity_id="ai-001", name="Test AI Assistant"
        )

        assert gcu.entity_type == ConsciousnessType.AI
        assert gcu.entity_id == "ai-001"
        assert gcu.name == "Test AI Assistant"
        assert len(gcu.consciousness_id) > 0
        assert gcu.created_at is not None

    def test_gcu_protocol_subscription(self):
        """Test GCU can subscribe to protocols"""
        gcu = GovernedConsciousnessUnit(
            entity_type=ConsciousnessType.AI, entity_id="ai-002", name="Protocol Test AI"
        )

        result = gcu.subscribe_to_protocol("confidentiality_protocol")
        assert result is True
        assert "confidentiality_protocol" in gcu.subscribed_protocols

        # Test subscribing again returns False
        result = gcu.subscribe_to_protocol("confidentiality_protocol")
        assert result is False

    def test_gcu_process_information(self):
        """Test GCU can process information securely"""
        gcu = GovernedConsciousnessUnit(
            entity_type=ConsciousnessType.AI, entity_id="ai-003", name="Processing Test AI"
        )

        gcu.subscribe_to_protocol("integrity_protocol")

        result = gcu.process_information({"data": "test data", "checksum": "abc123"})

        assert result["success"] is True
        assert "data" in result
        assert result["consciousness_id"] == gcu.consciousness_id

    def test_gcu_performance_metrics(self):
        """Test GCU tracks performance metrics"""
        gcu = GovernedConsciousnessUnit(
            entity_type=ConsciousnessType.SYSTEM, entity_id="system-001", name="Metrics Test System"
        )

        # Process some data
        for _ in range(5):
            gcu.process_information({"data": "test"})

        report = gcu.get_performance_report()
        assert report["performance"]["total_operations"] == 5
        assert report["performance"]["successful_operations"] == 5
        assert float(report["performance"]["success_rate"].rstrip("%")) == 100.0


class TestExistentialInterconnect:
    """Tests for EI - Existential Interconnect"""

    def test_ei_creation(self):
        """Test EI can be created"""
        ei = ExistentialInterconnect(
            interconnect_type=InterconnectType.SYNCHRONOUS,
            security_level=SecurityLevel.CONFIDENTIAL,
        )

        assert ei.interconnect_type == InterconnectType.SYNCHRONOUS
        assert ei.security_level == SecurityLevel.CONFIDENTIAL
        assert len(ei.interconnect_id) > 0

    def test_ei_transfer_information(self):
        """Test EI can transfer information securely"""
        ei = ExistentialInterconnect(
            interconnect_type=InterconnectType.SYNCHRONOUS, security_level=SecurityLevel.INTERNAL
        )

        result = ei.transfer_information(
            source_gcu_id="gcu-001", target_gcu_id="gcu-002", data={"message": "secure transfer"}
        )

        assert result["success"] is True
        assert result["source_gcu_id"] == "gcu-001"
        assert result["target_gcu_id"] == "gcu-002"
        assert "transfer_id" in result
        assert "data_signature" in result

    def test_ei_provenance_tracking(self):
        """Test EI tracks data provenance"""
        ei = ExistentialInterconnect(enable_provenance_tracking=True)

        ei.transfer_information(
            source_gcu_id="gcu-source", target_gcu_id="gcu-target", data={"data": "tracked"}
        )

        chain = ei.get_provenance_chain("gcu-source")
        assert len(chain) > 0
        assert chain[0].source_consciousness_id == "gcu-source"

    def test_ei_health_report(self):
        """Test EI provides health reports"""
        ei = ExistentialInterconnect()

        # Perform some transfers
        for i in range(3):
            ei.transfer_information(
                source_gcu_id=f"gcu-{i}", target_gcu_id=f"gcu-{i+1}", data={"test": "data"}
            )

        health = ei.get_health_report()
        assert health["metrics"]["total_transfers"] == 3
        assert health["metrics"]["successful_transfers"] == 3


class TestExistentialProtocolPackage:
    """Tests for EPP - Existential Protocol Package"""

    def test_epp_creation(self):
        """Test EPP can be created"""
        epp = ExistentialProtocolPackage(
            protocol_type=ProtocolType.CONFIDENTIALITY,
            name="Test Confidentiality Protocol",
            description="Test protocol for confidentiality",
        )

        assert epp.protocol_type == ProtocolType.CONFIDENTIALITY
        assert epp.name == "Test Confidentiality Protocol"
        assert len(epp.protocol_id) > 0

    def test_epp_default_rules_loaded(self):
        """Test EPP loads default rules based on type"""
        epp = ExistentialProtocolPackage(
            protocol_type=ProtocolType.INTEGRITY,
            name="Integrity Protocol",
            description="Data integrity protocol",
        )

        # Integrity protocol should have default rules
        assert len(epp.policy_rules) > 0
        rules_summary = epp.get_rules_summary()
        assert any("checksum" in rule["name"].lower() for rule in rules_summary)

    def test_epp_add_custom_rule(self):
        """Test EPP can add custom rules"""
        epp = ExistentialProtocolPackage(
            protocol_type=ProtocolType.AUDIT,
            name="Audit Protocol",
            description="Audit trail protocol",
        )

        initial_count = len(epp.policy_rules)

        epp.add_policy_rule(
            name="Custom Audit Rule",
            description="Custom rule for testing",
            severity=ProtocolSeverity.WARNING,
        )

        assert len(epp.policy_rules) == initial_count + 1

    def test_epp_validate_data(self):
        """Test EPP validates data against rules"""
        epp = ExistentialProtocolPackage(
            protocol_type=ProtocolType.CONFIDENTIALITY,
            name="Confidentiality Protocol",
            description="Test confidentiality",
        )

        result = epp.validate_data({"encrypted": True, "access_control": {"role": "admin"}})

        assert "valid" in result
        assert "violations" in result

    def test_protocol_factory(self):
        """Test ProtocolFactory creates protocols correctly"""
        high_security = ProtocolFactory.create_high_security_package()
        assert high_security.protocol_type == ProtocolType.CONFIDENTIALITY

        integrity = ProtocolFactory.create_data_integrity_package()
        assert integrity.protocol_type == ProtocolType.INTEGRITY

        audit = ProtocolFactory.create_audit_compliance_package()
        assert audit.protocol_type == ProtocolType.AUDIT


class TestCosmicDesignRules:
    """Tests for Cosmic Design Rules"""

    def test_dual_consciousness_rule(self):
        """Test Dual Consciousness Rule validation"""
        rule = DualConsciousnessRule()

        # Test compliant architecture
        compliant_arch = {
            "consciousness_units": 2,
            "independent_operation": True,
            "handles_sensitive_data": True,
        }
        result = rule.validate(compliant_arch)
        assert result["compliant"] is True

        # Test non-compliant architecture
        non_compliant_arch = {
            "consciousness_units": 1,
            "independent_operation": False,
            "handles_sensitive_data": True,
        }
        result = rule.validate(non_compliant_arch)
        assert result["compliant"] is False
        assert len(result["violations"]) > 0

    def test_infinite_scalability_rule(self):
        """Test Infinite Scalability Rule validation"""
        rule = InfiniteScalabilityRule()

        scalable_arch = {
            "horizontal_scaling": True,
            "stateless_design": True,
            "load_balancing": True,
            "partitionable": True,
        }
        result = rule.validate(scalable_arch)
        assert result["compliant"] is True

        non_scalable_arch = {"horizontal_scaling": False, "stateless_design": False}
        result = rule.validate(non_scalable_arch)
        assert result["compliant"] is False

    def test_autonomous_evolution_rule(self):
        """Test Autonomous Evolution Rule validation"""
        rule = AutonomousEvolutionRule()

        adaptive_arch = {
            "self_monitoring": True,
            "auto_optimization": True,
            "adaptive_configuration": True,
            "continuous_learning": True,
        }
        result = rule.validate(adaptive_arch)
        assert result["compliant"] is True

    def test_cosmic_design_enforcer(self):
        """Test Cosmic Design Enforcer validates architectures"""
        enforcer = CosmicDesignEnforcer()

        perfect_arch = {
            # Dual Consciousness
            "consciousness_units": 3,
            "independent_operation": True,
            "handles_sensitive_data": True,
            # Infinite Scalability
            "horizontal_scaling": True,
            "stateless_design": True,
            "load_balancing": True,
            "partitionable": True,
            # Autonomous Evolution
            "self_monitoring": True,
            "auto_optimization": True,
            "adaptive_configuration": True,
            "continuous_learning": True,
        }

        report = enforcer.validate_architecture(perfect_arch)
        assert report["architecture_compliant"] is True
        assert report["total_violations"] == 0

        # Test compliance score
        score = enforcer.get_compliance_score(perfect_arch)
        assert score == 100.0


class TestExistentialAI:
    """Tests for E-AI - Existential AI Automation"""

    def test_eai_creation(self):
        """Test E-AI can be created"""
        e_ai = ExistentialAI(name="Test E-AI")

        assert e_ai.name == "Test E-AI"
        assert len(e_ai.e_ai_id) > 0
        assert e_ai.enable_auto_healing is True

    def test_eai_auto_deploy_protocol(self):
        """Test E-AI can auto-deploy protocols"""
        e_ai = ExistentialAI(name="Protocol Deployer")

        result = e_ai.auto_deploy_protocol(
            workspace_id="ws-test-001", protocol_type=ProtocolType.CONFIDENTIALITY
        )

        assert result["success"] is True
        assert "protocol_id" in result
        assert len(e_ai.deployed_protocols) == 1

    def test_eai_monitor_interconnects(self):
        """Test E-AI can monitor interconnects"""
        e_ai = ExistentialAI(name="Monitor E-AI")

        # Add test interconnect
        ei = ExistentialInterconnect()
        e_ai.register_interconnect(ei)

        result = e_ai.monitor_interconnects()
        assert result["success"] is True
        assert result["monitored_count"] == 1

    def test_eai_manage_access(self):
        """Test E-AI manages access dynamically"""
        e_ai = ExistentialAI(name="Access Manager")

        # Create and register a GCU
        gcu = GovernedConsciousnessUnit(
            entity_type=ConsciousnessType.AI, entity_id="ai-access-test", name="Access Test AI"
        )
        gcu.subscribe_to_protocol("confidentiality_protocol")
        e_ai.register_gcu(gcu)

        # Test access management
        result = e_ai.manage_access_dynamically(
            gcu_id="ai-access-test", resource_id="resource-001", requested_action="read_sensitive"
        )

        assert result["success"] is True
        assert "access_granted" in result


class TestSelfEvolvingConsciousnessEntity:
    """Tests for SECE - Self-Evolving Consciousness Entity"""

    def test_sece_creation(self):
        """Test SECE can be created"""
        sece = SelfEvolvingConsciousnessEntity(name="Test SECE")

        assert sece.name == "Test SECE"
        assert len(sece.sece_id) > 0
        assert sece.auto_evolution_enabled is True

    def test_sece_observe_components(self):
        """Test SECE can observe components"""
        sece = SelfEvolvingConsciousnessEntity(name="Observer SECE")

        # Create components
        gcu = GovernedConsciousnessUnit(
            entity_type=ConsciousnessType.AI, entity_id="ai-observe", name="Observed AI"
        )
        ei = ExistentialInterconnect()
        epp = ProtocolFactory.create_high_security_package()

        # Register for observation
        sece.observe_gcu(gcu)
        sece.observe_interconnect(ei)
        sece.observe_protocol(epp)

        assert len(sece.observed_gcus) == 1
        assert len(sece.observed_interconnects) == 1
        assert len(sece.observed_protocols) == 1

    def test_sece_analyze_patterns(self):
        """Test SECE analyzes behavior patterns"""
        sece = SelfEvolvingConsciousnessEntity(
            name="Pattern Analyzer",
            learning_threshold=0.5,  # Lower threshold for testing
        )

        # Create components with patterns to detect
        gcu = GovernedConsciousnessUnit(
            entity_type=ConsciousnessType.AI, entity_id="ai-pattern", name="Pattern Test AI"
        )

        # Subscribe to many protocols to trigger complexity insight
        for i in range(7):
            gcu.subscribe_to_protocol(f"protocol_{i}")

        sece.observe_gcu(gcu)

        insights = sece.analyze_behavior_patterns()
        # Should detect complexity issue
        assert len(insights) > 0

    def test_sece_generate_recommendations(self):
        """Test SECE generates recommendations"""
        sece = SelfEvolvingConsciousnessEntity(name="Recommender SECE", learning_threshold=0.7)

        # Add some mock insights
        for i in range(4):
            insight = LearningInsight(
                insight_id=f"insight-{i}",
                learning_type=LearningType.COMPLEXITY_REDUCTION,
                description=f"Complexity issue {i}",
                confidence_score=0.9,
                evidence=["test evidence"],
                timestamp=datetime.now(),
            )
            sece.insights.append(insight)

        recommendations = sece.generate_recommendations()
        assert len(recommendations) > 0

    def test_sece_evolution_report(self):
        """Test SECE provides evolution report"""
        sece = SelfEvolvingConsciousnessEntity(name="Report SECE")

        report = sece.get_evolution_report()
        assert "sece_id" in report
        assert "statistics" in report
        assert "observed_components" in report
        assert "capabilities" in report


class TestIntegration:
    """Integration tests for the complete Cosmic Architecture"""

    def test_complete_workflow(self):
        """Test complete workflow: GCU -> EI -> EPP -> E-AI -> SECE"""
        # 1. Create GCUs
        gcu1 = GovernedConsciousnessUnit(
            entity_type=ConsciousnessType.AI, entity_id="ai-integration-1", name="AI System 1"
        )
        gcu2 = GovernedConsciousnessUnit(
            entity_type=ConsciousnessType.AI, entity_id="ai-integration-2", name="AI System 2"
        )

        # 2. Create and configure protocols
        protocol = ProtocolFactory.create_high_security_package()
        gcu1.subscribe_to_protocol(protocol.name)
        gcu2.subscribe_to_protocol(protocol.name)

        # 3. Create interconnect and transfer data
        ei = ExistentialInterconnect(security_level=SecurityLevel.CONFIDENTIAL)

        transfer_result = ei.transfer_information(
            source_gcu_id=gcu1.entity_id,
            target_gcu_id=gcu2.entity_id,
            data={
                "sensitive": "information",
                "encrypted": True,
                "access_control": {"role": "admin"},
            },
        )
        assert transfer_result["success"] is True

        # 4. Deploy E-AI automation
        e_ai = ExistentialAI(name="Integration E-AI")
        e_ai.register_gcu(gcu1)
        e_ai.register_gcu(gcu2)
        e_ai.register_interconnect(ei)

        # Auto-deploy protocol
        deploy_result = e_ai.auto_deploy_protocol(
            workspace_id="ws-integration", protocol_type=ProtocolType.INTEGRITY
        )
        assert deploy_result["success"] is True

        # 5. Deploy SECE for continuous learning
        sece = SelfEvolvingConsciousnessEntity(name="Integration SECE", learning_threshold=0.6)
        sece.observe_gcu(gcu1)
        sece.observe_gcu(gcu2)
        sece.observe_interconnect(ei)
        sece.observe_protocol(protocol)

        # Analyze patterns
        sece.analyze_behavior_patterns()

        # 6. Validate architecture with Cosmic Design Rules
        enforcer = CosmicDesignEnforcer()
        architecture = {
            "consciousness_units": 2,
            "independent_operation": True,
            "handles_sensitive_data": True,
            "horizontal_scaling": True,
            "stateless_design": True,
            "load_balancing": True,
            "self_monitoring": True,
            "auto_optimization": True,
        }

        validation = enforcer.validate_architecture(architecture)

        # Verify everything works together
        assert len(sece.observed_gcus) == 2
        assert len(e_ai.managed_gcus) == 2
        assert validation["total_rules_checked"] == 3

        # Get comprehensive reports
        gcu_report = gcu1.get_performance_report()
        ei_health = ei.get_health_report()
        e_ai_report = e_ai.get_performance_report()
        sece_report = sece.get_evolution_report()

        assert gcu_report["entity_type"] == "ai"
        assert ei_health["status"] == "active"
        assert e_ai_report["managed_resources"]["gcus"] == 2
        assert sece_report["observed_components"]["gcus"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
