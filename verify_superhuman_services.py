#!/usr/bin/env python3
"""
Quick verification script for superhuman services
This script can be run standalone without pytest
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_governance_service():
    """Test API Governance Service"""
    print("Testing API Governance Service...")
    from app.services.api_governance_service import get_governance_service
    
    governance = get_governance_service()
    assert governance is not None, "Governance service should initialize"
    assert 'v1' in governance.versions, "Should have v1"
    assert 'v2' in governance.versions, "Should have v2"
    print("✅ API Governance Service: PASS")


def test_slo_service():
    """Test SLO/SLI Service"""
    print("\nTesting SLO/SLI Service...")
    from app.services.api_slo_sli_service import get_slo_service
    
    slo = get_slo_service()
    assert slo is not None, "SLO service should initialize"
    assert 'availability_30d' in slo.slos, "Should have availability SLO"
    assert 'latency_30d' in slo.slos, "Should have latency SLO"
    
    # Test recording a request
    slo.record_request(
        endpoint='/api/test',
        method='GET',
        status_code=200,
        response_time_ms=100.0
    )
    
    dashboard = slo.get_dashboard()
    assert dashboard is not None, "Should get dashboard"
    assert 'slis' in dashboard, "Dashboard should have SLIs"
    print("✅ SLO/SLI Service: PASS")


def test_config_secrets_service():
    """Test Config & Secrets Management Service"""
    print("\nTesting Config & Secrets Management Service...")
    from app.services.api_config_secrets_service import (
        get_config_secrets_service,
        Environment,
        SecretType
    )
    
    config = get_config_secrets_service()
    assert config is not None, "Config service should initialize"
    
    # Test environment configuration
    dev_debug = config.get_config(Environment.DEVELOPMENT, 'debug_mode')
    prod_debug = config.get_config(Environment.PRODUCTION, 'debug_mode')
    assert dev_debug is True, "Dev should have debug enabled"
    assert prod_debug is False, "Production should have debug disabled"
    
    # Test secret management
    secret_id = config.create_secret(
        name='test_secret',
        value='super-secret',
        secret_type=SecretType.API_KEY,
        environment=Environment.DEVELOPMENT
    )
    assert secret_id is not None, "Should create secret"
    
    value = config.get_secret(secret_id)
    assert value == 'super-secret', "Should retrieve secret correctly"
    print("✅ Config & Secrets Management Service: PASS")


def test_disaster_recovery_service():
    """Test Disaster Recovery Service"""
    print("\nTesting Disaster Recovery Service...")
    from app.services.api_disaster_recovery_service import (
        get_disaster_recovery_service,
        BackupMetadata
    )
    from datetime import datetime, timezone
    
    dr = get_disaster_recovery_service()
    assert dr is not None, "DR service should initialize"
    assert 'database_dr' in dr.dr_plans, "Should have database DR plan"
    
    # Test backup registration
    backup = BackupMetadata(
        backup_id='test_backup',
        backup_type='database',
        created_at=datetime.now(timezone.utc),
        size_bytes=1024 * 1024,
        location='test://backup',
        retention_days=30,
        encryption_enabled=True
    )
    
    success = dr.register_backup(backup)
    assert success is True, "Should register backup"
    print("✅ Disaster Recovery Service: PASS")


def test_incident_service():
    """Test On-Call Incident Service"""
    print("\nTesting On-Call Incident Service...")
    from app.services.api_disaster_recovery_service import (
        get_oncall_incident_service,
        IncidentSeverity
    )
    
    incidents = get_oncall_incident_service()
    assert incidents is not None, "Incident service should initialize"
    
    # Create incident
    incident_id = incidents.create_incident(
        title='Test incident',
        description='Test incident description',
        severity=IncidentSeverity.SEV3,
        detected_by='test_script',
        affected_services=['test']
    )
    
    assert incident_id is not None, "Should create incident"
    assert incident_id in incidents.incidents, "Incident should be stored"
    print("✅ On-Call Incident Service: PASS")


def test_bulkhead_service():
    """Test Bulkheads Pattern Service"""
    print("\nTesting Bulkheads Pattern Service...")
    from app.services.api_gateway_chaos import get_bulkhead_service
    
    bulkhead = get_bulkhead_service()
    assert bulkhead is not None, "Bulkhead service should initialize"
    assert 'database' in bulkhead.bulkheads, "Should have database bulkhead"
    assert 'llm' in bulkhead.bulkheads, "Should have LLM bulkhead"
    
    # Test operation execution
    def test_op():
        return "success"
    
    success, result, error = bulkhead.call('database', test_op)
    assert success is True, "Operation should succeed"
    assert result == "success", "Should return correct result"
    print("✅ Bulkheads Pattern Service: PASS")


def test_event_driven_service():
    """Test Event-Driven Architecture Service"""
    print("\nTesting Event-Driven Architecture Service...")
    from app.services.api_event_driven_service import (
        get_event_driven_service,
        EventPriority
    )
    
    events = get_event_driven_service()
    assert events is not None, "Event service should initialize"
    assert 'api_events' in events.streams, "Should have API events stream"
    
    # Test event publishing
    event_id = events.publish(
        event_type='test.event',
        payload={'message': 'test'},
        priority=EventPriority.NORMAL
    )
    
    assert event_id is not None, "Should publish event"
    
    # Test event retrieval
    event = events.get_event(event_id)
    assert event is not None, "Should retrieve event"
    assert event.event_type == 'test.event', "Event type should match"
    print("✅ Event-Driven Architecture Service: PASS")


def test_cqrs_service():
    """Test CQRS Service"""
    print("\nTesting CQRS Service...")
    from app.services.api_event_driven_service import get_cqrs_service
    
    cqrs = get_cqrs_service()
    assert cqrs is not None, "CQRS service should initialize"
    
    # Register handler
    def test_handler(command):
        return {'result': 'success', 'data': command.payload}
    
    cqrs.register_command_handler('test_command', test_handler)
    
    # Execute command
    success, result = cqrs.execute_command(
        'test_command',
        {'key': 'value'}
    )
    
    assert success is True, "Command should execute successfully"
    assert result['result'] == 'success', "Should return correct result"
    print("✅ CQRS Service: PASS")


def main():
    """Run all tests"""
    print("=" * 70)
    print("SUPERHUMAN SERVICES VERIFICATION")
    print("=" * 70)
    
    tests = [
        test_governance_service,
        test_slo_service,
        test_config_secrets_service,
        test_disaster_recovery_service,
        test_incident_service,
        test_bulkhead_service,
        test_event_driven_service,
        test_cqrs_service,
    ]
    
    failed = []
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ {test.__name__}: FAILED - {e}")
            failed.append((test.__name__, str(e)))
    
    print("\n" + "=" * 70)
    if failed:
        print(f"RESULTS: {len(tests) - len(failed)}/{len(tests)} tests passed")
        print("\nFailed tests:")
        for name, error in failed:
            print(f"  - {name}: {error}")
        sys.exit(1)
    else:
        print(f"🎉 ALL {len(tests)} TESTS PASSED!")
        print("\n✅ All superhuman services are operational!")
        print("=" * 70)
        sys.exit(0)


if __name__ == '__main__':
    main()
