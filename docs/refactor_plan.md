# Refactor Plan

Each slice is designed to be small, reviewable, and verifiable.

## Progress Tracking
- [x] Phase 0: Baseline + repo map + standards + plan.
- [ ] Slice 1: Baseline formatting alignment.
- [ ] Slice 2: API gateway router consistency.
- [ ] Slice 3: Versioned system endpoints.
- [ ] Slice 4: JWT auth middleware hardening.
- [ ] Slice 5: Rate limit + auth integration.
- [ ] Slice 6: Plan registry boundary cleanup.
- [ ] Slice 7: Domain model consolidation.
- [ ] Slice 8: Error handling consistency.
- [ ] Slice 9: Logging standardization.
- [ ] Slice 10: Configuration centralization.
- [ ] Slice 11: API surface normalization.
- [ ] Slice 12: Test hygiene.
- [ ] Slice 13: Clean dependency boundaries.
- [ ] Slice 14: Final consistency report.

1) **Slice: Baseline Formatting Alignment**
- Scope: formatting-only changes in `app/api`, `app/middleware`, `app/core` touched by recent changes.
- Intent: align import ordering, whitespace, and formatting.
- Risk: Low
- Verification: `make check`

2) **Slice: API Gateway Router Consistency**
- Scope: `app/api/routers/gateway.py`, `app/api/schemas/gateway.py`.
- Intent: unify docstrings, response shapes, and dependency resolution.
- Risk: Low
- Verification: `make test-fast`

3) **Slice: Versioned System Endpoints**
- Scope: `app/api/routers/versioned_system.py`, system schemas.
- Intent: align v1 health endpoints with common response structure.
- Risk: Low
- Verification: `make test-fast`

4) **Slice: JWT Auth Middleware Hardening**
- Scope: `app/middleware/security/jwt_auth_middleware.py`.
- Intent: improve token parsing, error consistency, and context propagation.
- Risk: Medium
- Verification: targeted auth tests + `make test-fast`

5) **Slice: Rate Limit + Auth Integration**
- Scope: `app/middleware/security/rate_limit_middleware.py`, kernel stack.
- Intent: ensure correct ordering and metadata usage.
- Risk: Medium
- Verification: `make test-fast`

6) **Slice: Plan Registry Boundary Cleanup**
- Scope: `app/services/overmind/plan_registry.py`, `app/api/routers/agents.py`.
- Intent: clarify interfaces, reduce coupling, verify DB-backed storage.
- Risk: Medium
- Verification: `tests/api/test_agents_plan.py`

7) **Slice: Domain Model Consolidation**
- Scope: `app/core/domain/models.py`, schema validator.
- Intent: ensure new table definitions are consistent and documented.
- Risk: Low
- Verification: `make test-fast`

8) **Slice: Error Handling Consistency**
- Scope: `app/middleware/fastapi_error_handlers.py`, API error responses.
- Intent: normalize API error shape and mapping.
- Risk: Medium
- Verification: `make test-fast`

9) **Slice: Logging Standardization**
- Scope: `app/core/logging/*`, middleware logging.
- Intent: structured logging with correlation IDs.
- Risk: Medium
- Verification: `make test-fast`

10) **Slice: Configuration Centralization**
- Scope: `app/config/settings.py`, config usage across services.
- Intent: reduce scattered env reads and unify defaults.
- Risk: Medium
- Verification: `make type-check`

11) **Slice: API Surface Normalization**
- Scope: `app/api/routers/*`, schemas.
- Intent: normalize prefixes and pagination patterns.
- Risk: Medium
- Verification: `make test-fast`

12) **Slice: Test Hygiene**
- Scope: `tests/*` where flakiness or auth assumptions exist.
- Intent: stabilize tests and align with auth flow.
- Risk: Medium
- Verification: `make test`

13) **Slice: Clean Dependency Boundaries**
- Scope: `app/services`, `app/application`, `app/core`.
- Intent: enforce layer boundaries and remove cross-layer imports.
- Risk: High
- Verification: `make test-fast`

14) **Slice: Final Consistency Report**
- Scope: `docs/codebase_consistency_report.md`.
- Intent: document outcomes, risks, and verification steps.
- Risk: Low
- Verification: manual review
