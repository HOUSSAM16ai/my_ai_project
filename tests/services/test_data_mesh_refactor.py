import pytest
from app.services.data_mesh import (
    DataMeshService,
    get_data_mesh_service,
    DataDomainType,
    DataContract,
    SchemaCompatibility,
    DataProduct,
    DataQualityMetrics,
    DataProductStatus,
    GovernancePolicy,
    GovernanceLevel,
)
from datetime import datetime, UTC

@pytest.fixture
def data_mesh_service():
    # Force a fresh instance for testing
    return DataMeshService()

@pytest.mark.asyncio
async def test_data_mesh_initialization(data_mesh_service):
    assert data_mesh_service is not None
    assert len(data_mesh_service.governance_policies) > 0

@pytest.mark.asyncio
async def test_create_data_contract(data_mesh_service):
    contract = DataContract(
        contract_id="contract-001",
        domain=DataDomainType.ANALYTICS,
        name="User Activity Schema",
        description="Schema for user activity events",
        schema_version="1.0.0",
        schema_definition={
            "type": "record",
            "properties": {"user_id": "string", "action": "string"}
        },
        compatibility_mode=SchemaCompatibility.BACKWARD,
        owners=["team-analytics"],
        consumers=["team-marketing"],
        sla_guarantees={}
    )

    success = data_mesh_service.create_data_contract(contract)
    assert success is True
    assert "contract-001" in data_mesh_service.data_contracts

@pytest.mark.asyncio
async def test_schema_evolution(data_mesh_service):
    # Create initial contract
    contract = DataContract(
        contract_id="contract-002",
        domain=DataDomainType.USER_MANAGEMENT,
        name="User Profile",
        description="User profile data",
        schema_version="1.0.0",
        schema_definition={
            "type": "record",
            "properties": {"user_id": "string", "email": "string"},
            "required": ["user_id"]
        },
        compatibility_mode=SchemaCompatibility.BACKWARD,
        owners=["team-users"],
        consumers=[],
        sla_guarantees={}
    )
    data_mesh_service.create_data_contract(contract)

    # Evolve schema (Backward compatible: adding optional field)
    new_schema = {
        "type": "record",
        "properties": {"user_id": "string", "email": "string", "phone": "string"},
        "required": ["user_id"]
    }

    evolution = data_mesh_service.evolve_contract_schema(
        contract_id="contract-002",
        new_schema=new_schema,
        new_version="1.1.0",
        changes=[{"type": "field_added", "field": "phone"}]
    )

    assert evolution is not None
    # Adding an optional field is technically FULL compatibility (old readers can read new data, new readers can read old data)
    # The logic in _detect_schema_compatibility returns FULL when subsets match
    assert evolution.compatibility in [SchemaCompatibility.BACKWARD, SchemaCompatibility.FULL]
    assert data_mesh_service.data_contracts["contract-002"].schema_version == "1.1.0"

@pytest.mark.asyncio
async def test_governance_policy_enforcement(data_mesh_service):
    # Breaking change policy is enabled by default
    contract = DataContract(
        contract_id="contract-003",
        domain=DataDomainType.BILLING,
        name="Invoice",
        description="Invoice data",
        schema_version="1.0.0",
        schema_definition={
            "type": "record",
            "properties": {"invoice_id": "string"},
            "required": ["invoice_id"]
        },
        compatibility_mode=SchemaCompatibility.BACKWARD,
        owners=["team-billing"],
        consumers=[],
        sla_guarantees={}
    )
    data_mesh_service.create_data_contract(contract)

    # Try breaking change (remove required field)
    new_schema = {
        "type": "record",
        "properties": {},
        "required": []
    }

    evolution = data_mesh_service.evolve_contract_schema(
        contract_id="contract-003",
        new_schema=new_schema,
        new_version="2.0.0",
        changes=[{"type": "field_removed", "field": "invoice_id"}]
    )

    # Should be rejected by policy
    assert evolution is None

@pytest.mark.asyncio
async def test_singleton_accessor():
    service1 = get_data_mesh_service()
    service2 = get_data_mesh_service()
    assert service1 is service2
