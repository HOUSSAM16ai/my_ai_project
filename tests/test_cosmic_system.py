"""
Tests for Cosmic Security and Governance System
Year Million Test Suite

Tests:
- Existential Encryption
- Consciousness Signatures
- Cosmic Ledger
- SECEs (Self-Evolving Conscious Entities)
- Existential Protocols
- Cosmic Governance Councils
- Existential Transparency
"""

import pytest
from datetime import datetime

from app import db, create_app
from app.models import (
    ExistentialNode,
    ConsciousnessSignature,
    CosmicLedgerEntry,
    SelfEvolvingConsciousEntity,
    ExistentialProtocol,
    CosmicGovernanceCouncil,
    ExistentialTransparencyLog,
    ConsciousnessSignatureType,
    ExistentialNodeStatus,
    CosmicPolicyStatus,
)
from app.services.cosmic_security_service import CosmicSecurityService
from app.services.cosmic_governance_service import CosmicGovernanceService


# ======================================================================================
# SECURITY TESTS
# ======================================================================================


class TestExistentialEncryption:
    """Tests for existential encryption"""

    def test_encrypt_content(self, app):
        """Test encrypting content at existential level"""
        with app.app_context():
            content = "Cosmic secret data"
            node = CosmicSecurityService.encrypt_existential(
                content=content, dimension_layer=3, meta_physical_layer=0
            )
            db.session.commit()

            assert node.id is not None
            assert node.existential_signature is not None
            assert len(node.existential_signature) > 0
            assert node.cosmic_hash is not None
            assert node.dimension_layer == 3
            assert node.meta_physical_layer == 0
            assert node.status == ExistentialNodeStatus.COHERENT
            assert node.coherence_level == 1.0
            assert node.distortion_count == 0

    def test_encrypt_multidimensional(self, app):
        """Test encryption across multiple dimensions"""
        with app.app_context():
            content = "Multi-dimensional data"
            node = CosmicSecurityService.encrypt_existential(
                content=content, dimension_layer=7, meta_physical_layer=2
            )
            db.session.commit()

            assert node.dimension_layer == 7
            assert node.meta_physical_layer == 2
            assert "entanglement_nodes" in node.cosmic_pattern
            assert len(node.cosmic_pattern["entanglement_nodes"]) == 7

    def test_verify_node_coherence(self, app):
        """Test verifying existential node coherence"""
        with app.app_context():
            node = CosmicSecurityService.encrypt_existential(content="Test data", dimension_layer=3)
            db.session.commit()

            result = CosmicSecurityService.verify_existential_coherence(node)

            assert result["is_coherent"] is True
            assert result["coherence_level"] == 1.0
            assert len(result["issues"]) == 0

    def test_harmonize_node(self, app):
        """Test harmonizing a distorted node"""
        with app.app_context():
            node = CosmicSecurityService.encrypt_existential(content="Test data", dimension_layer=3)
            db.session.commit()

            # Simulate distortion
            node.distortion_count = 3
            node.coherence_level = 0.7
            db.session.commit()

            # Harmonize
            success = CosmicSecurityService.harmonize_existential_node(node)
            db.session.commit()

            assert success is True
            assert node.distortion_count == 0
            assert node.coherence_level == 1.0
            assert node.status == ExistentialNodeStatus.HARMONIZED


class TestConsciousnessSignatures:
    """Tests for consciousness signatures"""

    def test_create_consciousness_signature(self, app):
        """Test creating a consciousness signature"""
        with app.app_context():
            consciousness = CosmicSecurityService.create_consciousness_signature(
                entity_name="Test Entity",
                entity_type=ConsciousnessSignatureType.HUMAN,
                entity_origin="Earth",
                consciousness_level=1.5,
            )
            db.session.commit()

            assert consciousness.id is not None
            assert consciousness.signature_hash is not None
            assert consciousness.entity_name == "Test Entity"
            assert consciousness.entity_type == ConsciousnessSignatureType.HUMAN
            assert consciousness.consciousness_level == 1.5

    def test_track_existential_interaction(self, app):
        """Test tracking interactions in cosmic ledger"""
        with app.app_context():
            # Create node and consciousness
            node = CosmicSecurityService.encrypt_existential("Test data")
            consciousness = CosmicSecurityService.create_consciousness_signature(
                entity_name="Test Entity", entity_type=ConsciousnessSignatureType.SUPER_AI
            )
            db.session.commit()

            # Track interaction
            entry = CosmicSecurityService.track_existential_interaction(
                node=node,
                consciousness=consciousness,
                action="read",
                details={"access_level": "full"},
            )
            db.session.commit()

            assert entry.id is not None
            assert entry.event_type == "EXISTENTIAL_INTERACTION"
            assert entry.consciousness_id == consciousness.id
            assert entry.existential_node_id == node.id
            assert node.interaction_count == 1
            assert consciousness.total_interactions == 1


class TestCosmicLedger:
    """Tests for cosmic ledger"""

    def test_cosmic_ledger_chain(self, app):
        """Test cosmic ledger creates a chain"""
        with app.app_context():
            # Create multiple entries
            for i in range(5):
                CosmicSecurityService._log_cosmic_event(
                    event_type=f"TEST_EVENT_{i}",
                    description=f"Test event {i}",
                    payload={"index": i},
                )
            db.session.commit()

            # Get ledger chain
            entries = CosmicSecurityService.get_cosmic_ledger_chain(limit=5)

            assert len(entries) == 5

            # Verify chain linkage (entries are in reverse order)
            for i in range(len(entries) - 1):
                current = entries[i]
                next_entry = entries[i + 1]
                # Current's previous should link to next's hash
                if current.previous_ledger_hash:
                    assert current.previous_ledger_hash == next_entry.ledger_hash

    def test_verify_ledger_integrity(self, app):
        """Test verifying cosmic ledger integrity"""
        with app.app_context():
            # Create some entries
            for i in range(3):
                CosmicSecurityService._log_cosmic_event(
                    event_type=f"TEST_EVENT_{i}", description=f"Test event {i}", payload={}
                )
            db.session.commit()

            # Verify integrity
            result = CosmicSecurityService.verify_cosmic_ledger_integrity()

            assert result["valid"] is True
            assert result["total_entries"] == 3
            assert result["integrity_score"] == 1.0
            assert len(result["broken_chains"]) == 0


class TestSECEs:
    """Tests for Self-Evolving Conscious Entities"""

    def test_create_sece(self, app):
        """Test creating a SECE"""
        with app.app_context():
            sece = CosmicSecurityService.create_sece(
                entity_name="Guardian Alpha", evolution_level=1, intelligence_quotient=100.0
            )
            db.session.commit()

            assert sece.id is not None
            assert sece.entity_name == "Guardian Alpha"
            assert sece.evolution_level == 1
            assert sece.intelligence_quotient == 100.0
            assert sece.is_active is True
            assert sece.detected_threats == 0
            assert sece.neutralized_threats == 0

    def test_evolve_sece(self, app):
        """Test evolving a SECE"""
        with app.app_context():
            sece = CosmicSecurityService.create_sece(
                entity_name="Guardian Beta", evolution_level=1, intelligence_quotient=100.0
            )
            db.session.commit()

            # Evolve
            success = CosmicSecurityService.evolve_sece(sece)
            db.session.commit()

            assert success is True
            assert sece.evolution_level == 2
            assert sece.intelligence_quotient > 100.0  # Should increase
            assert len(sece.adaptation_history) == 1

    def test_detect_distortion(self, app):
        """Test SECE detecting existential distortion"""
        with app.app_context():
            # Create node and SECE
            node = CosmicSecurityService.encrypt_existential("Test data")
            sece = CosmicSecurityService.create_sece("Guardian Gamma")
            db.session.commit()

            # Introduce distortion
            node.coherence_level = 0.7
            db.session.commit()

            # Detect
            result = CosmicSecurityService.detect_existential_distortion(node, sece)
            db.session.commit()

            assert result is not None
            assert result["distorted"] is True
            assert sece.detected_threats > 0


# ======================================================================================
# GOVERNANCE TESTS
# ======================================================================================


class TestExistentialProtocols:
    """Tests for existential protocols"""

    def test_create_protocol(self, app):
        """Test creating an existential protocol"""
        with app.app_context():
            protocol = CosmicGovernanceService.create_existential_protocol(
                protocol_name="Test Protocol",
                description="A test protocol",
                cosmic_rules={"test_rule": {"type": "required_field", "field": "test"}},
                version="1.0.0",
            )
            db.session.commit()

            assert protocol.id is not None
            assert protocol.protocol_name == "Test Protocol"
            assert protocol.status == CosmicPolicyStatus.PROPOSED
            assert protocol.adoption_count == 0

    def test_activate_protocol(self, app):
        """Test activating a protocol"""
        with app.app_context():
            protocol = CosmicGovernanceService.create_existential_protocol(
                protocol_name="Test Protocol 2", description="Another test", cosmic_rules={}
            )
            db.session.commit()

            # Activate
            success = CosmicGovernanceService.activate_protocol(protocol)
            db.session.commit()

            assert success is True
            assert protocol.status == CosmicPolicyStatus.ACTIVE
            assert protocol.activated_at is not None

    def test_opt_into_protocol(self, app):
        """Test consciousness opting into protocol"""
        with app.app_context():
            # Create protocol and consciousness
            protocol = CosmicGovernanceService.create_existential_protocol(
                protocol_name="Opt-in Test", description="Test opt-in", cosmic_rules={}
            )
            CosmicGovernanceService.activate_protocol(protocol)

            consciousness = CosmicSecurityService.create_consciousness_signature(
                entity_name="Test Entity", entity_type=ConsciousnessSignatureType.HUMAN
            )
            db.session.commit()

            # Opt in
            success = CosmicGovernanceService.opt_into_protocol(consciousness, protocol)
            db.session.commit()

            assert success is True
            assert protocol.id in consciousness.opted_protocols
            assert protocol.adoption_count == 1

    def test_check_protocol_compliance(self, app):
        """Test checking protocol compliance"""
        with app.app_context():
            # Create protocol with rules
            protocol = CosmicGovernanceService.create_existential_protocol(
                protocol_name="Compliance Test",
                description="Test compliance",
                cosmic_rules={
                    "forbidden_action": {
                        "type": "forbidden_action",
                        "actions": ["delete", "destroy"],
                        "severity": "HIGH",
                    }
                },
            )
            CosmicGovernanceService.activate_protocol(protocol)

            consciousness = CosmicSecurityService.create_consciousness_signature(
                entity_name="Test Entity", entity_type=ConsciousnessSignatureType.HUMAN
            )
            CosmicGovernanceService.opt_into_protocol(consciousness, protocol)
            db.session.commit()

            # Check compliance - allowed action
            result = CosmicGovernanceService.check_protocol_compliance(
                consciousness=consciousness, action="read", context={}
            )
            assert result["compliant"] is True

            # Check compliance - forbidden action
            result = CosmicGovernanceService.check_protocol_compliance(
                consciousness=consciousness, action="delete", context={}
            )
            assert result["compliant"] is False
            assert len(result["violations"]) > 0


class TestCosmicGovernanceCouncils:
    """Tests for cosmic governance councils"""

    def test_create_council(self, app):
        """Test creating a cosmic governance council"""
        with app.app_context():
            council = CosmicGovernanceService.create_cosmic_council(
                council_name="Test Council", purpose="Testing governance", founding_members=[]
            )
            db.session.commit()

            assert council.id is not None
            assert council.council_name == "Test Council"
            assert council.member_count == 0
            assert council.is_active is True
            assert council.total_decisions == 0

    def test_add_council_member(self, app):
        """Test adding member to council"""
        with app.app_context():
            council = CosmicGovernanceService.create_cosmic_council(
                council_name="Growth Council", purpose="Testing membership", founding_members=[]
            )
            db.session.commit()

            # Add member
            success = CosmicGovernanceService.add_council_member(
                council=council, consciousness_signature="signature_hash_123"
            )
            db.session.commit()

            assert success is True
            assert council.member_count == 1
            assert "signature_hash_123" in council.member_signatures

    def test_propose_decision(self, app):
        """Test proposing a decision to council"""
        with app.app_context():
            council = CosmicGovernanceService.create_cosmic_council(
                council_name="Decision Council", purpose="Testing decisions", founding_members=[]
            )
            db.session.commit()

            # Propose decision
            success = CosmicGovernanceService.propose_council_decision(
                council=council,
                decision_subject="Test Decision",
                decision_details={"impact": "high"},
                proposed_by="proposer_signature",
            )
            db.session.commit()

            assert success is True
            assert len(council.pending_decisions) == 1
            assert council.pending_decisions[0]["subject"] == "Test Decision"

    def test_consciousness_consensus(self, app):
        """Test reaching consciousness consensus"""
        with app.app_context():
            # Create council with members
            members = [f"member_{i}" for i in range(5)]
            council = CosmicGovernanceService.create_cosmic_council(
                council_name="Consensus Council",
                purpose="Testing consensus",
                founding_members=members,
            )

            # Propose decision
            CosmicGovernanceService.propose_council_decision(
                council=council,
                decision_subject="Important Decision",
                decision_details={},
                proposed_by="member_0",
            )
            db.session.commit()

            decision_id = council.pending_decisions[0]["id"]

            # Vote (4 out of 5 = 80% consensus)
            for i in range(4):
                CosmicGovernanceService.vote_on_decision(
                    council=council,
                    decision_id=decision_id,
                    consciousness_signature=f"member_{i}",
                    vote=True,
                )
            db.session.commit()

            # Check consensus
            result = CosmicGovernanceService.reach_consciousness_consensus(
                council=council, decision_id=decision_id
            )
            db.session.commit()

            assert result["consensus_reached"] is True
            assert result["consensus_ratio"] == 1.0  # 4/4 voted yes
            assert council.total_decisions == 1
            assert len(council.pending_decisions) == 0


class TestExistentialTransparency:
    """Tests for existential transparency"""

    def test_query_transparency_logs(self, app):
        """Test querying transparency logs"""
        with app.app_context():
            # Create some logs via governance actions
            for i in range(3):
                CosmicGovernanceService.create_existential_protocol(
                    protocol_name=f"Protocol {i}", description=f"Test protocol {i}", cosmic_rules={}
                )
            db.session.commit()

            # Query logs
            logs = CosmicGovernanceService.query_transparency_logs(
                event_type="PROTOCOL_CREATED", limit=10
            )

            assert len(logs) == 3
            assert all(log.event_type == "PROTOCOL_CREATED" for log in logs)
            assert all(log.view_count > 0 for log in logs)  # View count incremented


# ======================================================================================
# API TESTS
# ======================================================================================


class TestCosmicAPI:
    """Tests for cosmic API endpoints"""

    def test_health_endpoint(self, client, app):
        """Test cosmic health endpoint"""
        with app.app_context():
            response = client.get("/api/cosmic/health")
            data = response.get_json()

            assert response.status_code == 200
            assert data["ok"] is True
            assert data["status"] == "operational"

    def test_stats_endpoint(self, client, app):
        """Test cosmic stats endpoint"""
        with app.app_context():
            response = client.get("/api/cosmic/stats")
            data = response.get_json()

            assert response.status_code == 200
            assert data["ok"] is True
            assert "existential_nodes" in data["data"]
            assert "consciousness_signatures" in data["data"]
            assert "cosmic_ledger" in data["data"]

    def test_encrypt_api(self, client, app):
        """Test encryption API endpoint"""
        with app.app_context():
            response = client.post(
                "/api/cosmic/security/encrypt",
                json={"content": "Test content", "dimension_layer": 3},
            )
            data = response.get_json()

            assert response.status_code == 201
            assert data["ok"] is True
            assert "node_id" in data["data"]
            assert data["data"]["status"] == "COHERENT"

    def test_list_nodes_api(self, client, app):
        """Test list nodes API endpoint"""
        with app.app_context():
            # Create some nodes
            for i in range(3):
                CosmicSecurityService.encrypt_existential(f"Content {i}")
            db.session.commit()

            response = client.get("/api/cosmic/security/nodes")
            data = response.get_json()

            assert response.status_code == 200
            assert data["ok"] is True
            assert len(data["data"]) == 3

    def test_create_protocol_api(self, client, app):
        """Test create protocol API endpoint"""
        with app.app_context():
            response = client.post(
                "/api/cosmic/governance/protocols",
                json={
                    "protocol_name": "API Test Protocol",
                    "description": "Test protocol via API",
                    "version": "1.0.0",
                },
            )
            data = response.get_json()

            assert response.status_code == 201
            assert data["ok"] is True
            assert data["data"]["protocol_name"] == "API Test Protocol"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
