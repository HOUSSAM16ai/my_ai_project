# tests/test_api_first_platform.py
# =============================================================================
# ==   TESTS FOR API-FIRST PLATFORM SERVICE                                ==
# =============================================================================

import time
from datetime import UTC, datetime

import pytest

from app.services.api_first_platform_service import (
    APIContract,
    APIFirstPlatformService,
    ContractRegistry,
    ContractType,
    IdempotencyStore,
    RateLimitConfig,
    RateLimiter,
    WebhookSigner,
    generate_etag,
)

# =============================================================================
# Contract Management Tests
# =============================================================================


class TestContractManagement:
    """اختبارات إدارة العقود"""

    def test_create_api_contract(self):
        """اختبار إنشاء عقد API"""
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/test": {"get": {"summary": "Test endpoint"}}},
        }

        contract = APIContract(
            name="test-api", type=ContractType.OPENAPI, version="v1", specification=spec
        )

        assert contract.name == "test-api"
        assert contract.type == ContractType.OPENAPI
        assert contract.version == "v1"
        assert contract.checksum is not None
        assert len(contract.checksum) == 64  # SHA256 hex

    def test_contract_checksum_consistency(self):
        """اختبار ثبات checksum"""
        spec = {"test": "data"}

        contract1 = APIContract(
            name="test", type=ContractType.OPENAPI, version="v1", specification=spec
        )

        contract2 = APIContract(
            name="test", type=ContractType.OPENAPI, version="v1", specification=spec
        )

        assert contract1.checksum == contract2.checksum

    def test_contract_registry(self):
        """اختبار سجل العقود"""
        registry = ContractRegistry()

        contract = APIContract(
            name="accounts-api",
            type=ContractType.OPENAPI,
            version="v1",
            specification={"test": "data"},
        )

        registry.register(contract)

        retrieved = registry.get("accounts-api")
        assert retrieved is not None
        assert retrieved.name == "accounts-api"

    def test_breaking_changes_detection(self):
        """اختبار كشف التغييرات المكسّرة"""
        registry = ContractRegistry()

        old_contract = APIContract(
            name="test", type=ContractType.OPENAPI, version="v1", specification={}
        )

        new_contract = APIContract(
            name="test", type=ContractType.OPENAPI, version="v2", specification={}
        )

        breaking_changes = registry.validate_breaking_changes(old_contract, new_contract)

        assert len(breaking_changes) > 0
        assert "Major version change" in breaking_changes[0]


# =============================================================================
# Idempotency Tests
# =============================================================================


class TestIdempotency:
    """اختبارات التماثل"""

    def test_idempotency_store_set_get(self):
        """اختبار حفظ واسترجاع"""
        store = IdempotencyStore()

        key = "idp_test_123"
        response = {"id": "acc_123", "status": "created"}

        store.set(key, response)
        retrieved = store.get(key)

        assert retrieved is not None
        assert retrieved == response

    def test_idempotency_key_expiration(self):
        """اختبار انتهاء صلاحية المفتاح"""
        from datetime import timedelta

        store = IdempotencyStore()
        store._ttl = timedelta(seconds=0)  # Set TTL to 0 for immediate expiration

        key = "idp_test_expired"
        response = {"test": "data"}

        store.set(key, response)
        time.sleep(0.1)  # Small delay

        retrieved = store.get(key)
        assert retrieved is None

    def test_idempotency_cleanup(self):
        """اختبار تنظيف المفاتيح المنتهية"""
        from datetime import timedelta

        store = IdempotencyStore()
        store._ttl = timedelta(seconds=0)

        store.set("key1", {"data": 1})
        store.set("key2", {"data": 2})

        time.sleep(0.1)
        store.cleanup()

        assert len(store._store) == 0


# =============================================================================
# Rate Limiting Tests
# =============================================================================


class TestRateLimiting:
    """اختبارات تحديد المعدل"""

    def test_rate_limiter_basic(self):
        """اختبار تحديد المعدل الأساسي"""
        config = RateLimitConfig(requests_per_minute=5)
        limiter = RateLimiter(config)

        key = "test_user"

        # Should allow first 5 requests
        for i in range(5):
            allowed, info = limiter.check_limit(key)
            assert allowed is True
            assert info["remaining"] == 4 - i

        # Should deny 6th request
        allowed, info = limiter.check_limit(key)
        assert allowed is False
        assert info["remaining"] == 0

    def test_rate_limiter_reset(self):
        """اختبار إعادة تعيين الحد"""
        config = RateLimitConfig(requests_per_minute=5)
        limiter = RateLimiter(config)

        key = "test_user"

        # Use up the limit
        for _ in range(5):
            limiter.check_limit(key)

        # Manually reset by advancing time
        limiter._buckets[key]["minute"] = int(time.time() / 60) - 1

        # Should allow again
        allowed, info = limiter.check_limit(key)
        assert allowed is True

    def test_rate_limiter_multiple_keys(self):
        """اختبار تحديد المعدل لمفاتيح متعددة"""
        config = RateLimitConfig(requests_per_minute=3)
        limiter = RateLimiter(config)

        # Different keys should have independent limits
        for _ in range(3):
            allowed, _ = limiter.check_limit("user1")
            assert allowed is True

        for _ in range(3):
            allowed, _ = limiter.check_limit("user2")
            assert allowed is True

        # Both should be rate limited now
        allowed, _ = limiter.check_limit("user1")
        assert allowed is False

        allowed, _ = limiter.check_limit("user2")
        assert allowed is False


# =============================================================================
# ETag Tests
# =============================================================================


class TestETag:
    """اختبارات ETags"""

    def test_generate_etag_from_dict(self):
        """اختبار توليد ETag من dict"""
        data = {"id": "acc_123", "name": "Test Account"}

        etag = generate_etag(data)

        assert etag is not None
        assert len(etag) == 32  # MD5 hex

    def test_generate_etag_consistency(self):
        """اختبار ثبات ETag"""
        data = {"id": "123", "name": "Test"}

        etag1 = generate_etag(data)
        etag2 = generate_etag(data)

        assert etag1 == etag2

    def test_etag_changes_with_data(self):
        """اختبار تغير ETag مع البيانات"""
        data1 = {"id": "123"}
        data2 = {"id": "456"}

        etag1 = generate_etag(data1)
        etag2 = generate_etag(data2)

        assert etag1 != etag2


# =============================================================================
# Webhook Signature Tests
# =============================================================================


class TestWebhookSignatures:
    """اختبارات توقيع Webhooks"""

    def test_webhook_sign_and_verify(self):
        """اختبار التوقيع والتحقق"""
        signer = WebhookSigner(secret="test_secret")

        payload = {"event": "account.created", "data": {"id": "acc_123"}}

        signature = signer.sign(payload)

        # Verify the signature
        assert signer.verify(payload, signature) is True

    def test_webhook_verify_invalid_signature(self):
        """اختبار رفض التوقيع غير الصحيح"""
        signer = WebhookSigner(secret="test_secret")

        payload = {"event": "account.created"}
        invalid_signature = "t=1234567890,v1=invalid_signature"

        assert signer.verify(payload, invalid_signature) is False

    def test_webhook_timestamp_tolerance(self):
        """اختبار تسامح الوقت"""
        signer = WebhookSigner(secret="test_secret")

        payload = {"event": "test"}

        # Sign with old timestamp
        old_timestamp = int(time.time()) - 400  # 400 seconds ago
        signature = signer.sign(payload, old_timestamp)

        # Should fail with default tolerance (300s)
        assert signer.verify(payload, signature, tolerance=300) is False

        # Should pass with larger tolerance
        assert signer.verify(payload, signature, tolerance=500) is True


# =============================================================================
# API-First Platform Service Tests
# =============================================================================


class TestAPIFirstPlatformService:
    """اختبارات خدمة منصة API-First"""

    @pytest.fixture
    def service(self):
        """خدمة للاختبار"""
        return APIFirstPlatformService()

    def test_register_contract(self, service):
        """اختبار تسجيل عقد"""
        spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
        }

        contract = service.register_contract(
            name="test-api", contract_type=ContractType.OPENAPI, version="v1", specification=spec
        )

        assert contract is not None
        assert contract.name == "test-api"

    def test_get_contract(self, service):
        """اختبار الحصول على عقد"""
        spec = {"test": "data"}
        service.register_contract(
            name="test", contract_type=ContractType.OPENAPI, version="v1", specification=spec
        )

        contract = service.get_contract("test")

        assert contract is not None
        assert contract.name == "test"

    def test_list_contracts(self, service):
        """اختبار قائمة العقود"""
        service.register_contract(
            name="api1", contract_type=ContractType.OPENAPI, version="v1", specification={}
        )

        service.register_contract(
            name="api2", contract_type=ContractType.GRAPHQL, version="v1", specification={}
        )

        contracts = service.list_contracts()

        assert len(contracts) >= 2

    def test_deprecate_version(self, service):
        """اختبار إيقاف إصدار"""
        sunset_date = datetime(2025, 12, 31, tzinfo=UTC)
        migration_guide = "https://docs.example.com/migration"

        deprecation = service.deprecate_version(
            version="v1", sunset_date=sunset_date, migration_guide=migration_guide
        )

        assert deprecation["version"] == "v1"
        assert deprecation["deprecated"] is True
        assert sunset_date.isoformat() in deprecation["sunset_date"]

    def test_create_webhook_delivery(self, service):
        """اختبار إنشاء تسليم webhook"""
        delivery = service.create_webhook_delivery(
            url="https://example.com/webhook",
            event_type="account.created",
            payload={"id": "acc_123"},
        )

        assert delivery is not None
        assert delivery["url"] == "https://example.com/webhook"
        assert delivery["event_type"] == "account.created"
        assert "signature" in delivery
        assert delivery["status"] == "pending"

    def test_verify_webhook_signature(self, service):
        """اختبار التحقق من توقيع webhook"""
        payload = {"event": "test"}

        # Create a delivery to get the signature
        delivery = service.create_webhook_delivery(
            url="https://test.com", event_type="test", payload=payload
        )

        signature = delivery["signature"]

        # Verify it
        is_valid = service.verify_webhook_signature(payload, signature)
        assert is_valid is True

    def test_track_api_usage(self, service, app):
        """اختبار تتبع استخدام API"""
        with app.app_context():
            usage = service.track_api_usage(
                endpoint="/v1/accounts", method="GET", status_code=200, duration_ms=42.5
            )

        assert usage["endpoint"] == "/v1/accounts"
        assert usage["method"] == "GET"
        assert usage["status_code"] == 200
        assert usage["duration_ms"] == 42.5
        assert "timestamp" in usage

    def test_generate_api_key(self, service):
        """اختبار توليد مفتاح API"""
        api_key = service.generate_api_key(
            user_id="user_123", name="Production Key", scopes=["read", "write"]
        )

        assert api_key is not None
        assert api_key["key"].startswith("sk_live_")
        assert api_key["user_id"] == "user_123"
        assert api_key["name"] == "Production Key"
        assert api_key["scopes"] == ["read", "write"]
        assert "rate_limit" in api_key

    def test_rotate_api_key(self, service):
        """اختبار تدوير مفتاح API"""
        rotation = service.rotate_api_key(key_id="key_old_123")

        assert rotation is not None
        assert rotation["old_key_id"] == "key_old_123"
        assert rotation["new_key"].startswith("sk_live_")
        assert rotation["grace_period_hours"] == 24


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """اختبارات التكامل"""

    def test_full_api_lifecycle(self, app):
        """اختبار دورة حياة API كاملة"""
        service = APIFirstPlatformService()

        with app.app_context():
            # 1. Register contract
            spec = {
                "openapi": "3.1.0",
                "info": {"title": "Accounts API", "version": "1.0.0"},
                "paths": {
                    "/accounts": {
                        "post": {
                            "operationId": "createAccount",
                            "requestBody": {
                                "content": {"application/json": {"schema": {"type": "object"}}}
                            },
                        }
                    }
                },
            }

            contract = service.register_contract(
                name="accounts-api",
                contract_type=ContractType.OPENAPI,
                version="v1",
                specification=spec,
            )

            assert contract is not None

            # 2. Generate API key
            api_key = service.generate_api_key(
                user_id="dev_001", name="Test Key", scopes=["accounts:read", "accounts:write"]
            )

            assert api_key["key"] is not None

            # 3. Track API usage
            usage = service.track_api_usage(
                endpoint="/v1/accounts", method="POST", status_code=201, duration_ms=85.3
            )

            assert usage is not None

            # 4. Create webhook
            webhook = service.create_webhook_delivery(
                url="https://client.com/webhook",
                event_type="account.created",
                payload={"id": "acc_123", "name": "Test Account"},
            )

            assert webhook is not None
            assert "signature" in webhook

            # 5. Verify webhook signature
            is_valid = service.verify_webhook_signature(webhook["payload"], webhook["signature"])
            assert is_valid is True
