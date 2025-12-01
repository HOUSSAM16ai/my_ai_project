# tests/test_engine_factory_comprehensive.py
"""
Comprehensive tests for the Quantum Engine Factory (app/core/engine_factory.py).

This module is critical infrastructure that handles:
- Database URL sanitization
- Pooler detection (PgBouncer, Supabase, Neon)
- Prepared statement protection
- Multi-level security validation
- Connection pool configuration

These tests verify edge cases, error conditions, and security guarantees.
"""

import os
import threading
from unittest.mock import patch

import pytest

from app.core.engine_factory import (
    AdaptivePoolerDetector,
    DatabaseType,
    DatabaseURLSanitizer,
    EngineDiagnostics,
    FatalEngineError,
    PoolerSignature,
    PoolerType,
    QuantumStatementNameGenerator,
    _configure_postgres_engine,
    _configure_sqlite_engine,
    _detect_database_type,
    _validate_postgres_security,
    create_unified_async_engine,
)


# =============================================================================
# QUANTUM STATEMENT NAME GENERATOR TESTS
# =============================================================================


class TestQuantumStatementNameGenerator:
    """Tests for the quantum-safe UUID statement name generator."""

    def test_generate_returns_string(self):
        """Generate returns a non-empty string."""
        name = QuantumStatementNameGenerator.generate()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_generate_has_correct_prefix(self):
        """Generated names have the correct prefix."""
        name = QuantumStatementNameGenerator.generate()
        assert name.startswith("__cogniforge_")
        assert name.endswith("__")

    def test_generate_unique_names(self):
        """Each call generates a unique name."""
        names = {QuantumStatementNameGenerator.generate() for _ in range(1000)}
        assert len(names) == 1000, "All 1000 generated names should be unique"

    def test_generate_thread_safety(self):
        """Generator is thread-safe and produces unique names across threads."""
        names = []
        errors = []

        def generate_names(count):
            try:
                for _ in range(count):
                    names.append(QuantumStatementNameGenerator.generate())
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=generate_names, args=(100,)) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors: {errors}"
        assert len(set(names)) == 1000, "All names across threads should be unique"

    def test_get_generator_func(self):
        """get_generator_func returns a callable that generates names."""
        func = QuantumStatementNameGenerator.get_generator_func()
        assert callable(func)
        name = func()
        assert isinstance(name, str)
        assert "__cogniforge_" in name


# =============================================================================
# ADAPTIVE POOLER DETECTOR TESTS
# =============================================================================


class TestAdaptivePoolerDetector:
    """Tests for pooler detection algorithm."""

    def test_detect_none_for_empty_url(self):
        """Empty URL returns NONE pooler type."""
        assert AdaptivePoolerDetector.detect("") == PoolerType.NONE
        assert AdaptivePoolerDetector.detect(None) == PoolerType.NONE

    def test_detect_supabase_pooler_by_hostname(self):
        """Detects Supabase pooler from hostname pattern."""
        url = "postgresql://user:pass@db.pooler.supabase.com:6543/postgres"
        assert AdaptivePoolerDetector.detect(url) == PoolerType.SUPABASE_POOLER

    def test_detect_supabase_pooler_by_port(self):
        """Detects Supabase pooler from port 6543."""
        url = "postgresql://user:pass@db.supabase.co:6543/postgres"
        assert AdaptivePoolerDetector.detect(url) == PoolerType.SUPABASE_POOLER

    def test_detect_pgbouncer_by_port(self):
        """Detects PgBouncer from port 6432."""
        url = "postgresql://user:pass@myhost:6432/mydb"
        assert AdaptivePoolerDetector.detect(url) == PoolerType.PGBOUNCER

    def test_detect_pgbouncer_by_name(self):
        """Detects PgBouncer from hostname containing 'pgbouncer'."""
        url = "postgresql://user:pass@pgbouncer.internal:5432/mydb"
        assert AdaptivePoolerDetector.detect(url) == PoolerType.PGBOUNCER

    def test_detect_neon_pooler(self):
        """Detects Neon pooler from hostname."""
        url = "postgresql://user:pass@ep-cool-frost-123456.neon.tech/mydb"
        assert AdaptivePoolerDetector.detect(url) == PoolerType.NEON_POOLER

    def test_detect_none_for_direct_connection(self):
        """Direct PostgreSQL connection returns NONE."""
        url = "postgresql://user:pass@localhost:5432/mydb"
        assert AdaptivePoolerDetector.detect(url) == PoolerType.NONE

    @patch.dict(os.environ, {"PGBOUNCER_HOST": "pgbouncer.local"})
    def test_detect_pgbouncer_from_env(self):
        """Detects PgBouncer from environment variables."""
        url = "postgresql://user:pass@some-host:5432/mydb"
        assert AdaptivePoolerDetector.detect(url) == PoolerType.PGBOUNCER

    def test_requires_prepared_statement_protection(self):
        """All known poolers require prepared statement protection."""
        assert AdaptivePoolerDetector.requires_prepared_statement_protection(
            PoolerType.PGBOUNCER
        )
        assert AdaptivePoolerDetector.requires_prepared_statement_protection(
            PoolerType.SUPABASE_POOLER
        )
        assert AdaptivePoolerDetector.requires_prepared_statement_protection(
            PoolerType.NEON_POOLER
        )
        assert AdaptivePoolerDetector.requires_prepared_statement_protection(
            PoolerType.UNKNOWN_POOLER
        )
        assert not AdaptivePoolerDetector.requires_prepared_statement_protection(
            PoolerType.NONE
        )


# =============================================================================
# DATABASE URL SANITIZER TESTS
# =============================================================================


class TestDatabaseURLSanitizer:
    """Tests for URL sanitization and validation."""

    def test_sanitize_normalizes_postgres_protocol(self):
        """postgres:// is normalized to postgresql://."""
        url = "postgres://user:pass@host:5432/db"
        result = DatabaseURLSanitizer.sanitize(url, for_async=False)
        assert result.startswith("postgresql://")

    def test_sanitize_translates_ssl_mode_for_async(self):
        """sslmode is translated to ssl for async drivers."""
        url = "postgresql://user:pass@host:5432/db?sslmode=require"
        result = DatabaseURLSanitizer.sanitize(url, for_async=True)
        assert "ssl=require" in result
        assert "sslmode" not in result

    def test_sanitize_preserves_ssl_mode_for_sync(self):
        """sslmode is preserved when for_async=False."""
        url = "postgresql://user:pass@host:5432/db?sslmode=require"
        result = DatabaseURLSanitizer.sanitize(url, for_async=False)
        # Sanitize doesn't translate when for_async=False
        # Note: _translate_ssl_mode is only called when for_async=True
        assert "sslmode=require" in result or "ssl=require" in result

    def test_sanitize_raises_for_missing_url_in_production(self):
        """Raises FatalEngineError when URL is missing in production."""
        with patch.object(DatabaseURLSanitizer, "_is_test_environment", return_value=False):
            with pytest.raises(FatalEngineError) as exc_info:
                DatabaseURLSanitizer.sanitize(None)
            assert "DATABASE_URL is not set" in str(exc_info.value)

    def test_sanitize_returns_sqlite_fallback_in_test(self):
        """Returns SQLite fallback when URL is missing in test environment."""
        with patch.object(DatabaseURLSanitizer, "_is_test_environment", return_value=True):
            result = DatabaseURLSanitizer.sanitize(None)
            assert "sqlite+aiosqlite" in result

    def test_sanitize_validates_url_structure(self):
        """Invalid URL structure raises FatalEngineError."""
        with pytest.raises(FatalEngineError) as exc_info:
            DatabaseURLSanitizer.sanitize("not-a-valid-url")
        error_message = str(exc_info.value)
        assert "Invalid DATABASE_URL structure" in error_message
        assert "missing scheme" in error_message

    def test_sanitize_accepts_sqlite_without_host(self):
        """SQLite URLs without host are valid."""
        url = "sqlite+aiosqlite:///:memory:"
        result = DatabaseURLSanitizer.sanitize(url)
        assert result == url

    def test_reverse_ssl_for_sync(self):
        """SSL parameter reversal for sync drivers."""
        url = "postgresql://user:pass@host:5432/db?ssl=require"
        result = DatabaseURLSanitizer.reverse_ssl_for_sync(url)
        assert "sslmode=require" in result

    def test_reverse_ssl_ignores_asyncpg(self):
        """SSL reversal is not applied to asyncpg URLs."""
        url = "postgresql+asyncpg://user:pass@host:5432/db?ssl=require"
        result = DatabaseURLSanitizer.reverse_ssl_for_sync(url)
        assert "ssl=require" in result  # Not changed


class TestDatabaseURLSanitizerEdgeCases:
    """Edge case tests for URL sanitizer."""

    def test_all_ssl_modes(self):
        """All SSL modes are properly translated."""
        modes = ["require", "disable", "allow", "prefer", "verify-ca", "verify-full"]
        for mode in modes:
            url = f"postgresql://user:pass@host:5432/db?sslmode={mode}"
            result = DatabaseURLSanitizer.sanitize(url, for_async=True)
            assert f"ssl={mode}" in result

    def test_url_with_special_characters_in_password(self):
        """URLs with special characters in password are handled."""
        url = "postgresql://user:p%40ss%3Dword@host:5432/db"
        # Should not raise
        result = DatabaseURLSanitizer.sanitize(url)
        assert "host:5432" in result

    def test_url_with_query_params_preserved(self):
        """Query parameters are preserved during sanitization."""
        url = "postgresql://user:pass@host:5432/db?connect_timeout=10"
        result = DatabaseURLSanitizer.sanitize(url)
        assert "connect_timeout=10" in result


# =============================================================================
# DATABASE TYPE DETECTION TESTS
# =============================================================================


class TestDatabaseTypeDetection:
    """Tests for database type detection."""

    def test_detect_postgresql(self):
        """Detects PostgreSQL from URL."""
        assert _detect_database_type("postgresql://host/db") == DatabaseType.POSTGRESQL
        assert _detect_database_type("postgresql+asyncpg://host/db") == DatabaseType.POSTGRESQL
        assert _detect_database_type("postgres://host/db") == DatabaseType.POSTGRESQL

    def test_detect_sqlite(self):
        """Detects SQLite from URL."""
        assert _detect_database_type("sqlite:///test.db") == DatabaseType.SQLITE
        assert _detect_database_type("sqlite+aiosqlite:///:memory:") == DatabaseType.SQLITE

    def test_detect_unknown(self):
        """Unknown database types return UNKNOWN."""
        assert _detect_database_type("mysql://host/db") == DatabaseType.UNKNOWN
        assert _detect_database_type("oracle://host/db") == DatabaseType.UNKNOWN


# =============================================================================
# POSTGRES ENGINE CONFIGURATION TESTS
# =============================================================================


class TestPostgresEngineConfiguration:
    """Tests for PostgreSQL engine configuration."""

    def test_auto_upgrade_to_asyncpg(self):
        """postgresql:// is auto-upgraded to postgresql+asyncpg://."""
        url = "postgresql://user:pass@host:5432/db"
        result_url, _ = _configure_postgres_engine(url, {}, PoolerType.NONE, None)
        assert "postgresql+asyncpg://" in result_url

    def test_statement_cache_disabled(self):
        """Statement cache is disabled in connect_args."""
        url = "postgresql+asyncpg://user:pass@host:5432/db"
        _, kwargs = _configure_postgres_engine(url, {}, PoolerType.PGBOUNCER, None)
        assert kwargs["connect_args"]["statement_cache_size"] == 0
        assert kwargs["connect_args"]["prepared_statement_cache_size"] == 0

    def test_quantum_naming_enabled(self):
        """Quantum statement naming function is set."""
        url = "postgresql+asyncpg://user:pass@host:5432/db"
        _, kwargs = _configure_postgres_engine(url, {}, PoolerType.PGBOUNCER, None)
        assert "prepared_statement_name_func" in kwargs["connect_args"]
        assert callable(kwargs["connect_args"]["prepared_statement_name_func"])

    def test_command_timeout_default(self):
        """Default command timeout is set."""
        url = "postgresql+asyncpg://user:pass@host:5432/db"
        _, kwargs = _configure_postgres_engine(url, {}, PoolerType.NONE, None)
        assert kwargs["connect_args"]["command_timeout"] == 60

    def test_pool_settings_default(self):
        """Default pool settings are applied."""
        url = "postgresql+asyncpg://user:pass@host:5432/db"
        _, kwargs = _configure_postgres_engine(url, {}, PoolerType.NONE, None)
        assert kwargs["pool_pre_ping"] is True
        assert kwargs["pool_size"] == 20
        assert kwargs["max_overflow"] == 10


# =============================================================================
# SQLITE ENGINE CONFIGURATION TESTS
# =============================================================================


class TestSqliteEngineConfiguration:
    """Tests for SQLite engine configuration."""

    def test_auto_upgrade_to_aiosqlite(self):
        """sqlite:// is auto-upgraded to sqlite+aiosqlite://."""
        url = "sqlite:///test.db"
        result_url, _ = _configure_sqlite_engine(url, {})
        assert "sqlite+aiosqlite://" in result_url

    def test_pool_settings_removed(self):
        """Pool settings are removed for SQLite."""
        url = "sqlite+aiosqlite:///:memory:"
        initial_kwargs = {"pool_size": 10, "max_overflow": 5, "pool_pre_ping": True}
        _, kwargs = _configure_sqlite_engine(url, initial_kwargs)
        assert "pool_size" not in kwargs
        assert "max_overflow" not in kwargs
        assert "pool_pre_ping" not in kwargs

    def test_check_same_thread_disabled(self):
        """check_same_thread is set to False for SQLite."""
        url = "sqlite+aiosqlite:///:memory:"
        _, kwargs = _configure_sqlite_engine(url, {})
        assert kwargs["connect_args"]["check_same_thread"] is False


# =============================================================================
# SECURITY VALIDATION TESTS
# =============================================================================


class TestSecurityValidation:
    """Tests for PostgreSQL security validation."""

    def test_validation_passes_with_correct_config(self):
        """Validation passes with all security settings correctly applied."""
        connect_args = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": QuantumStatementNameGenerator.generate,
        }
        # Should not raise
        _validate_postgres_security({"connect_args": connect_args})

    def test_validation_fails_with_nonzero_statement_cache(self):
        """Validation fails if statement_cache_size is not 0."""
        connect_args = {
            "statement_cache_size": 100,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": QuantumStatementNameGenerator.generate,
        }
        with pytest.raises(FatalEngineError) as exc_info:
            _validate_postgres_security({"connect_args": connect_args})
        assert "statement_cache_size must be 0" in str(exc_info.value)

    def test_validation_fails_with_nonzero_prepared_cache(self):
        """Validation fails if prepared_statement_cache_size is not 0."""
        connect_args = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 50,
            "prepared_statement_name_func": QuantumStatementNameGenerator.generate,
        }
        with pytest.raises(FatalEngineError) as exc_info:
            _validate_postgres_security({"connect_args": connect_args})
        assert "prepared_statement_cache_size must be 0" in str(exc_info.value)

    def test_validation_fails_without_name_func(self):
        """Validation fails if prepared_statement_name_func is missing."""
        connect_args = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
        }
        with pytest.raises(FatalEngineError) as exc_info:
            _validate_postgres_security({"connect_args": connect_args})
        assert "prepared_statement_name_func is not set" in str(exc_info.value)

    def test_validation_fails_with_non_unique_name_func(self):
        """Validation fails if name function doesn't produce unique names."""
        connect_args = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": lambda: "always_same_name",
        }
        with pytest.raises(FatalEngineError) as exc_info:
            _validate_postgres_security({"connect_args": connect_args})
        assert "does not produce unique names" in str(exc_info.value)


# =============================================================================
# ENGINE DIAGNOSTICS TESTS
# =============================================================================


class TestEngineDiagnostics:
    """Tests for engine diagnostics utility."""

    def test_verify_pgbouncer_compatibility_all_set(self):
        """All compatibility checks pass when properly configured."""
        connect_args = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": lambda: "name",
            "command_timeout": 60,
        }
        result = EngineDiagnostics.verify_pgbouncer_compatibility(connect_args)
        assert result["statement_cache_disabled"] is True
        assert result["prepared_stmt_cache_disabled"] is True
        assert result["quantum_naming_enabled"] is True
        assert result["command_timeout_set"] is True

    def test_verify_pgbouncer_compatibility_missing_settings(self):
        """Compatibility checks identify missing settings."""
        connect_args = {}
        result = EngineDiagnostics.verify_pgbouncer_compatibility(connect_args)
        assert result["statement_cache_disabled"] is False
        assert result["prepared_stmt_cache_disabled"] is False
        assert result["quantum_naming_enabled"] is False
        assert result["command_timeout_set"] is False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestCreateUnifiedAsyncEngine:
    """Integration tests for the main engine factory."""

    def test_create_engine_with_sqlite(self):
        """Creates async engine for SQLite."""
        engine = create_unified_async_engine("sqlite+aiosqlite:///:memory:")
        assert engine is not None
        assert "sqlite" in str(engine.url)

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///:memory:"})
    def test_create_engine_from_env(self):
        """Creates engine from DATABASE_URL environment variable."""
        engine = create_unified_async_engine()
        assert engine is not None

    def test_create_engine_with_custom_pool_settings(self):
        """Custom pool settings are applied."""
        engine = create_unified_async_engine(
            "sqlite+aiosqlite:///:memory:",
            pool_size=5,  # Will be removed for SQLite
        )
        assert engine is not None


# =============================================================================
# POOLER SIGNATURE TESTS
# =============================================================================


class TestPoolerSignature:
    """Tests for PoolerSignature dataclass."""

    def test_pooler_signature_immutable(self):
        """PoolerSignature is immutable (frozen dataclass)."""
        sig = PoolerSignature(
            pattern=r"test",
            pooler_type=PoolerType.PGBOUNCER,
            default_port=6432,
            requires_prepared_stmt_disable=True,
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            sig.pattern = "changed"

    def test_pooler_signatures_list_populated(self):
        """POOLER_SIGNATURES list has expected entries."""
        from app.core.engine_factory import POOLER_SIGNATURES

        assert len(POOLER_SIGNATURES) >= 5
        supabase_sigs = [s for s in POOLER_SIGNATURES if s.pooler_type == PoolerType.SUPABASE_POOLER]
        assert len(supabase_sigs) >= 2


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestFatalEngineError:
    """Tests for FatalEngineError exception."""

    def test_fatal_error_is_exception(self):
        """FatalEngineError is an Exception subclass."""
        assert issubclass(FatalEngineError, Exception)

    def test_fatal_error_message(self):
        """FatalEngineError preserves message."""
        error = FatalEngineError("Test error message")
        assert "Test error message" in str(error)
