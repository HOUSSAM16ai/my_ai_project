# ======================================================================================
#  STANDALONE TESTS FOR COSMIC EXISTENTIAL ARCHITECTURE
# ======================================================================================
#  PURPOSE: Standalone tests that don't require Flask app context
# ======================================================================================

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


from app.cosmic.automation.existential_ai import ExistentialAI  # noqa: E402
from app.cosmic.evolution.sece import (  # noqa: E402
    SelfEvolvingConsciousnessEntity,
)
from app.cosmic.primitives.consciousness_unit import (  # noqa: E402
    ConsciousnessType,
    GovernedConsciousnessUnit,
)
from app.cosmic.primitives.existential_interconnect import (  # noqa: E402
    ExistentialInterconnect,
    InterconnectType,
    SecurityLevel,
)
from app.cosmic.primitives.protocol_package import (  # noqa: E402
    ExistentialProtocolPackage,
    ProtocolFactory,
    ProtocolType,
)
from app.cosmic.rules.design_rules import (  # noqa: E402
    CosmicDesignEnforcer,
    DualConsciousnessRule,
    InfiniteScalabilityRule,
)


def test_gcu_creation():
    """Test GCU creation"""
    print("Testing GCU creation...")
    gcu = GovernedConsciousnessUnit(
        entity_type=ConsciousnessType.AI, entity_id="ai-001", name="Test AI"
    )
    assert gcu.entity_type == ConsciousnessType.AI
    assert gcu.entity_id == "ai-001"
    print("✅ GCU creation test passed")


def test_gcu_protocol_subscription():
    """Test GCU protocol subscription"""
    print("Testing GCU protocol subscription...")
    gcu = GovernedConsciousnessUnit(
        entity_type=ConsciousnessType.AI, entity_id="ai-002", name="Protocol Test AI"
    )
    result = gcu.subscribe_to_protocol("confidentiality_protocol")
    assert result is True
    assert "confidentiality_protocol" in gcu.subscribed_protocols
    print("✅ GCU protocol subscription test passed")


def test_ei_transfer():
    """Test EI information transfer"""
    print("Testing EI information transfer...")
    ei = ExistentialInterconnect(
        interconnect_type=InterconnectType.SYNCHRONOUS, security_level=SecurityLevel.INTERNAL
    )
    result = ei.transfer_information(
        source_gcu_id="gcu-001", target_gcu_id="gcu-002", data={"message": "test"}
    )
    assert result["success"] is True
    print("✅ EI transfer test passed")


def test_epp_validation():
    """Test EPP validation"""
    print("Testing EPP validation...")
    epp = ExistentialProtocolPackage(
        protocol_type=ProtocolType.CONFIDENTIALITY, name="Test Protocol", description="Test"
    )
    result = epp.validate_data({"encrypted": True, "access_control": {"role": "admin"}})
    assert "valid" in result
    print("✅ EPP validation test passed")


def test_protocol_factory():
    """Test Protocol Factory"""
    print("Testing Protocol Factory...")
    high_security = ProtocolFactory.create_high_security_package()
    assert high_security.protocol_type == ProtocolType.CONFIDENTIALITY
    integrity = ProtocolFactory.create_data_integrity_package()
    assert integrity.protocol_type == ProtocolType.INTEGRITY
    print("✅ Protocol Factory test passed")


def test_dual_consciousness_rule():
    """Test Dual Consciousness Rule"""
    print("Testing Dual Consciousness Rule...")
    rule = DualConsciousnessRule()
    compliant_arch = {
        "consciousness_units": 2,
        "independent_operation": True,
        "handles_sensitive_data": True,
    }
    result = rule.validate(compliant_arch)
    assert result["compliant"] is True
    print("✅ Dual Consciousness Rule test passed")


def test_infinite_scalability_rule():
    """Test Infinite Scalability Rule"""
    print("Testing Infinite Scalability Rule...")
    rule = InfiniteScalabilityRule()
    scalable_arch = {
        "horizontal_scaling": True,
        "stateless_design": True,
        "load_balancing": True,
        "partitionable": True,
    }
    result = rule.validate(scalable_arch)
    assert result["compliant"] is True
    print("✅ Infinite Scalability Rule test passed")


def test_cosmic_design_enforcer():
    """Test Cosmic Design Enforcer"""
    print("Testing Cosmic Design Enforcer...")
    enforcer = CosmicDesignEnforcer()
    perfect_arch = {
        "consciousness_units": 3,
        "independent_operation": True,
        "handles_sensitive_data": True,
        "horizontal_scaling": True,
        "stateless_design": True,
        "load_balancing": True,
        "partitionable": True,
        "self_monitoring": True,
        "auto_optimization": True,
        "adaptive_configuration": True,
        "continuous_learning": True,
    }
    report = enforcer.validate_architecture(perfect_arch)
    assert report["architecture_compliant"] is True
    score = enforcer.get_compliance_score(perfect_arch)
    assert score == 100.0
    print("✅ Cosmic Design Enforcer test passed")


def test_existential_ai():
    """Test Existential AI"""
    print("Testing Existential AI...")
    e_ai = ExistentialAI(name="Test E-AI")
    result = e_ai.auto_deploy_protocol(
        workspace_id="ws-test", protocol_type=ProtocolType.CONFIDENTIALITY
    )
    assert result["success"] is True
    print("✅ Existential AI test passed")


def test_sece():
    """Test Self-Evolving Consciousness Entity"""
    print("Testing SECE...")
    sece = SelfEvolvingConsciousnessEntity(name="Test SECE", learning_threshold=0.5)

    # Create and observe a GCU
    gcu = GovernedConsciousnessUnit(
        entity_type=ConsciousnessType.AI, entity_id="ai-sece-test", name="SECE Test AI"
    )
    for i in range(7):  # Subscribe to many protocols
        gcu.subscribe_to_protocol(f"protocol_{i}")

    sece.observe_gcu(gcu)
    sece.analyze_behavior_patterns()

    report = sece.get_evolution_report()
    assert "sece_id" in report
    print("✅ SECE test passed")


def test_complete_integration():
    """Test complete integration workflow"""
    print("Testing complete integration...")

    # 1. Create GCUs
    gcu1 = GovernedConsciousnessUnit(
        entity_type=ConsciousnessType.AI, entity_id="ai-int-1", name="AI System 1"
    )
    gcu2 = GovernedConsciousnessUnit(
        entity_type=ConsciousnessType.AI, entity_id="ai-int-2", name="AI System 2"
    )

    # 2. Create protocol
    protocol = ProtocolFactory.create_high_security_package()
    gcu1.subscribe_to_protocol(protocol.name)
    gcu2.subscribe_to_protocol(protocol.name)

    # 3. Create interconnect
    ei = ExistentialInterconnect(security_level=SecurityLevel.CONFIDENTIAL)
    result = ei.transfer_information(
        source_gcu_id=gcu1.entity_id,
        target_gcu_id=gcu2.entity_id,
        data={"test": "data", "encrypted": True, "access_control": {"role": "admin"}},
    )
    assert result["success"] is True

    # 4. E-AI automation
    e_ai = ExistentialAI(name="Integration E-AI")
    e_ai.register_gcu(gcu1)
    e_ai.register_gcu(gcu2)
    e_ai.register_interconnect(ei)

    # 5. SECE monitoring
    sece = SelfEvolvingConsciousnessEntity(name="Integration SECE")
    sece.observe_gcu(gcu1)
    sece.observe_gcu(gcu2)
    sece.observe_interconnect(ei)

    # 6. Architecture validation
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
    enforcer.validate_architecture(architecture)

    assert len(sece.observed_gcus) == 2
    assert len(e_ai.managed_gcus) == 2
    print("✅ Complete integration test passed")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("COSMIC EXISTENTIAL ARCHITECTURE - STANDALONE TESTS")
    print("=" * 80 + "\n")

    tests = [
        test_gcu_creation,
        test_gcu_protocol_subscription,
        test_ei_transfer,
        test_epp_validation,
        test_protocol_factory,
        test_dual_consciousness_rule,
        test_infinite_scalability_rule,
        test_cosmic_design_enforcer,
        test_existential_ai,
        test_sece,
        test_complete_integration,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {str(e)}")
            failed += 1
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} total tests")
    print("=" * 80 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
