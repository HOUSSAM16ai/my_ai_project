# Migration Map - High Risk Flask References

### Path: `./test_streaming_superhuman.py`

- **Line:** 95
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_streaming_superhuman_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./init_db.py`

- **Line:** 6
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_init_db_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./list_database_tables.py`

- **Line:** 81
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_list_database_tables_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./auto_diagnose_and_fix.py`

- **Line:** 196
- **Excerpt:** `'app.app_context().push(); db.engine.connect(); print("OK")',`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_auto_diagnose_and_fix_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./verify_sse_fix.py`

- **Line:** 80
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_verify_sse_fix_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./tools/discover.py`

- **Line:** 17
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_discover_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./check_migrations_status.py`

- **Line:** 48
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_check_migrations_status_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/middleware/error_response_factory.py`

- **Line:** 22
- **Excerpt:** `from flask import Flask, current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_error_response_factory_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/middleware/error_response_factory.py`

- **Line:** 97
- **Excerpt:** `(app or current_app).config.get("DEBUG", False)`
- **Category:** middleware
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_error_response_factory_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/middleware/error_response_factory.py`

- **Line:** 98
- **Excerpt:** `if app or hasattr(current_app, "config")`
- **Category:** middleware
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_error_response_factory_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/middleware/error_response_factory.py`

- **Line:** 125
- **Excerpt:** `(app or current_app).config.get("DEBUG", False)`
- **Category:** middleware
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_error_response_factory_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/middleware/error_response_factory.py`

- **Line:** 126
- **Excerpt:** `if app or hasattr(current_app, "config")`
- **Category:** middleware
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_error_response_factory_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/middleware/error_response_factory.py`

- **Line:** 158
- **Excerpt:** `(app or current_app).config.get("DEBUG", False)`
- **Category:** middleware
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_error_response_factory_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/middleware/error_response_factory.py`

- **Line:** 159
- **Excerpt:** `if app or hasattr(current_app, "config")`
- **Category:** middleware
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_error_response_factory_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/aiops_self_healing_service.py`

- **Line:** 27
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_aiops_self_healing_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/aiops_self_healing_service.py`

- **Line:** 194
- **Excerpt:** `current_app.logger.info("AIOps Service initialized successfully")`
- **Category:** ai_integration
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_aiops_self_healing_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/aiops_self_healing_service.py`

- **Line:** 308
- **Excerpt:** `current_app.logger.warning(`
- **Category:** ai_integration
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_aiops_self_healing_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/aiops_self_healing_service.py`

- **Line:** 367
- **Excerpt:** `current_app.logger.info(`
- **Category:** ai_integration
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_aiops_self_healing_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_chaos_monkey_service.py`

- **Line:** 26
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_chaos_monkey_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_chaos_monkey_service.py`

- **Line:** 243
- **Excerpt:** `current_app.logger.info(f"🐒 Chaos Monkey enabled in {mode.value} mode")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_chaos_monkey_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_chaos_monkey_service.py`

- **Line:** 249
- **Excerpt:** `current_app.logger.info("🐒 Chaos Monkey disabled")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_chaos_monkey_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_chaos_monkey_service.py`

- **Line:** 322
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_chaos_monkey_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_chaos_monkey_service.py`

- **Line:** 333
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_chaos_monkey_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 27
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 211
- **Excerpt:** `current_app.logger.info("Data Mesh Service initialized successfully")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 256
- **Excerpt:** `current_app.logger.warning(f"Bounded context already exists: {context.context_id}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 260
- **Excerpt:** `current_app.logger.info(f"Registered bounded context: {context.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 276
- **Excerpt:** `current_app.logger.error(f"Schema compatibility validation failed: {contract.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 281
- **Excerpt:** `current_app.logger.error(f"Governance compliance check failed: {contract.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 285
- **Excerpt:** `current_app.logger.info(f"Created data contract: {contract.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 321
- **Excerpt:** `current_app.logger.error("Breaking schema changes not allowed")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 343
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 390
- **Excerpt:** `current_app.logger.info(f"Registered data product: {product.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 416
- **Excerpt:** `current_app.logger.info(f"Added governance policy: {policy.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 431
- **Excerpt:** `current_app.logger.error(f"Governance violation: {policy.name} - {rule}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 483
- **Excerpt:** `current_app.logger.warning(f"Governance action: {policy.name} - {reason}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/data_mesh_service.py`

- **Line:** 536
- **Excerpt:** `current_app.logger.info(f"Subscribed to {event_type}: {subscription_id}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_data_mesh_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/edge_multicloud_service.py`

- **Line:** 24
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_edge_multicloud_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/edge_multicloud_service.py`

- **Line:** 145
- **Excerpt:** `current_app.logger.info("Edge & Multi-Cloud Service initialized")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_edge_multicloud_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/edge_multicloud_service.py`

- **Line:** 258
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_edge_multicloud_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/edge_multicloud_service.py`

- **Line:** 317
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_edge_multicloud_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/micro_frontends_service.py`

- **Line:** 24
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_micro_frontends_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/micro_frontends_service.py`

- **Line:** 118
- **Excerpt:** `current_app.logger.info("Micro Frontends Service initialized")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_micro_frontends_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/micro_frontends_service.py`

- **Line:** 130
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_micro_frontends_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/micro_frontends_service.py`

- **Line:** 152
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_micro_frontends_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/distributed_tracing.py`

- **Line:** 27
- **Excerpt:** `from flask import current_app, g, request`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_distributed_tracing_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/distributed_tracing.py`

- **Line:** 169
- **Excerpt:** `current_app.logger.error(f"Failed to extract trace context: {e}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_distributed_tracing_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_governance_service.py`

- **Line:** 27
- **Excerpt:** `from flask import current_app, jsonify, request`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_governance_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_governance_service.py`

- **Line:** 420
- **Excerpt:** `current_app.logger.warning(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_governance_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/advanced_streaming_service.py`

- **Line:** 26
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_advanced_streaming_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/advanced_streaming_service.py`

- **Line:** 158
- **Excerpt:** `current_app.logger.info("Advanced Streaming Service initialized")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_advanced_streaming_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/advanced_streaming_service.py`

- **Line:** 181
- **Excerpt:** `current_app.logger.info(f"Created stream: {config.name} ({config.protocol.value})")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_advanced_streaming_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/advanced_streaming_service.py`

- **Line:** 208
- **Excerpt:** `current_app.logger.error(f"Schema validation failed for stream {stream_id}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_advanced_streaming_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/advanced_streaming_service.py`

- **Line:** 279
- **Excerpt:** `current_app.logger.info(f"Consumer {consumer_id} subscribed to {stream_id}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_advanced_streaming_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/advanced_streaming_service.py`

- **Line:** 293
- **Excerpt:** `current_app.logger.error(f"Consumer {consumer.consumer_id} error: {e}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_advanced_streaming_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/advanced_streaming_service.py`

- **Line:** 312
- **Excerpt:** `current_app.logger.info(f"Registered schema: {schema.schema_id}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_advanced_streaming_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/advanced_streaming_service.py`

- **Line:** 367
- **Excerpt:** `current_app.logger.info(f"Replicating stream {stream_id} to region {target_region}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_advanced_streaming_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/advanced_streaming_service.py`

- **Line:** 401
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_advanced_streaming_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_chaos.py`

- **Line:** 25
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_chaos_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_chaos.py`

- **Line:** 122
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_chaos_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_chaos.py`

- **Line:** 140
- **Excerpt:** `current_app.logger.info(f"Stopped chaos experiment: {experiment.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_chaos_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_chaos.py`

- **Line:** 264
- **Excerpt:** `current_app.logger.info(f"Circuit breaker {service_id}: OPEN -> HALF_OPEN")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_chaos_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_chaos.py`

- **Line:** 281
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_chaos_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_chaos.py`

- **Line:** 299
- **Excerpt:** `current_app.logger.warning(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_chaos_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_chaos.py`

- **Line:** 318
- **Excerpt:** `current_app.logger.info(f"Circuit breaker {service_id}: manually reset to CLOSED")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_chaos_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/service_catalog_service.py`

- **Line:** 24
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_service_catalog_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/service_catalog_service.py`

- **Line:** 154
- **Excerpt:** `current_app.logger.info("Service Catalog initialized successfully")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_service_catalog_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/service_catalog_service.py`

- **Line:** 167
- **Excerpt:** `"app.py": "# Flask application\nfrom flask import Flask\napp = Flask(__name__)",`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_service_catalog_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/service_catalog_service.py`

- **Line:** 193
- **Excerpt:** `current_app.logger.info(f"Registered service: {service.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_service_catalog_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/service_catalog_service.py`

- **Line:** 237
- **Excerpt:** `current_app.logger.info(f"Registered API spec for {spec.service_id}: {spec.version}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_service_catalog_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_service.py`

- **Line:** 410
- **Excerpt:** `current_app.logger.warning(f"Error evaluating provider {provider_name}: {e}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_service.py`

- **Line:** 620
- **Excerpt:** `current_app.logger.error(f"Policy evaluation error: {e}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_service.py`

- **Line:** 703
- **Excerpt:** `current_app.logger.info(f"Registered route: {route.route_id} -> {route.path_pattern}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_service.py`

- **Line:** 708
- **Excerpt:** `current_app.logger.info(f"Registered upstream service: {service.service_id}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_service.py`

- **Line:** 771
- **Excerpt:** `current_app.logger.error(f"Gateway processing error: {e}", exc_info=True)`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_service.py`

- **Line:** 836
- **Excerpt:** `current_app.logger.error(f"Endpoint error: {e}", exc_info=True)`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_deployment.py`

- **Line:** 24
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_deployment_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_deployment.py`

- **Line:** 148
- **Excerpt:** `current_app.logger.info(f"Created A/B test: {experiment.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_deployment_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_deployment.py`

- **Line:** 237
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_deployment_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_deployment.py`

- **Line:** 273
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_deployment_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_deployment.py`

- **Line:** 365
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_deployment_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_deployment.py`

- **Line:** 384
- **Excerpt:** `current_app.logger.warning(f"Rolled back canary deployment: {deployment.service_id}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_deployment_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_gateway_deployment.py`

- **Line:** 415
- **Excerpt:** `current_app.logger.info(f"Created feature flag: {flag.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_gateway_deployment_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/gitops_policy_service.py`

- **Line:** 26
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_gitops_policy_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/gitops_policy_service.py`

- **Line:** 198
- **Excerpt:** `current_app.logger.info("GitOps Service initialized successfully")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_gitops_policy_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/gitops_policy_service.py`

- **Line:** 252
- **Excerpt:** `current_app.logger.warning(f"Application already exists: {app.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_gitops_policy_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/gitops_policy_service.py`

- **Line:** 256
- **Excerpt:** `current_app.logger.info(f"Registered GitOps application: {app.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_gitops_policy_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/gitops_policy_service.py`

- **Line:** 302
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_gitops_policy_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/gitops_policy_service.py`

- **Line:** 310
- **Excerpt:** `current_app.logger.error(f"Sync failed for {app.name}: {e}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_gitops_policy_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/gitops_policy_service.py`

- **Line:** 352
- **Excerpt:** `current_app.logger.info(f"Added policy: {policy.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_gitops_policy_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/gitops_policy_service.py`

- **Line:** 422
- **Excerpt:** `current_app.logger.warning(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_gitops_policy_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/gitops_policy_service.py`

- **Line:** 532
- **Excerpt:** `current_app.logger.info(f"Auto-remediating drift for {drift.resource_name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_gitops_policy_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_subscription_service.py`

- **Line:** 26
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_subscription_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_subscription_service.py`

- **Line:** 286
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_subscription_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_subscription_service.py`

- **Line:** 314
- **Excerpt:** `current_app.logger.warning(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_subscription_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_subscription_service.py`

- **Line:** 389
- **Excerpt:** `current_app.logger.info(f"Upgraded subscription {subscription_id} to {new_plan.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_subscription_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/history_service.py`

- **Line:** 3
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_history_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/history_service.py`

- **Line:** 26
- **Excerpt:** `current_app.logger.error(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_history_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/history_service.py`

- **Line:** 50
- **Excerpt:** `current_app.logger.warning(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_history_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/history_service.py`

- **Line:** 61
- **Excerpt:** `current_app.logger.info(f"User {current_user.id} rated message {message_id} as '{rating}'.")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_history_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/history_service.py`

- **Line:** 69
- **Excerpt:** `current_app.logger.error(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_history_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/history_service.py`

- **Line:** 75
- **Excerpt:** `current_app.logger.error(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_history_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/sre_error_budget_service.py`

- **Line:** 24
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_sre_error_budget_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/sre_error_budget_service.py`

- **Line:** 152
- **Excerpt:** `current_app.logger.info("SRE & Error Budget Service initialized")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_sre_error_budget_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/sre_error_budget_service.py`

- **Line:** 166
- **Excerpt:** `current_app.logger.info(f"Created SLO: {slo.name} ({slo.target_percentage}%)")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_sre_error_budget_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/sre_error_budget_service.py`

- **Line:** 308
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_sre_error_budget_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/sre_error_budget_service.py`

- **Line:** 338
- **Excerpt:** `current_app.logger.info(f"Started canary deployment: {service_name} ({canary_percentage}%)")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_sre_error_budget_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/llm_client_service.py`

- **Line:** 136
- **Excerpt:** `from flask import current_app, has_app_context`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_llm_client_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/llm_client_service.py`

- **Line:** 138
- **Excerpt:** `current_app = None`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_llm_client_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/llm_client_service.py`

- **Line:** 395
- **Excerpt:** `if has_app_context() and current_app:`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_llm_client_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/llm_client_service.py`

- **Line:** 397
- **Excerpt:** `val = current_app.config.get(key)`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_llm_client_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_developer_portal_service.py`

- **Line:** 26
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_developer_portal_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_developer_portal_service.py`

- **Line:** 312
- **Excerpt:** `current_app.logger.info(f"Created API key {key_id} for developer {developer_id}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_developer_portal_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_developer_portal_service.py`

- **Line:** 347
- **Excerpt:** `current_app.logger.info(f"Revoked API key {key_id}: {reason}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_developer_portal_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_developer_portal_service.py`

- **Line:** 390
- **Excerpt:** `current_app.logger.info(f"Created ticket {ticket_id} for developer {developer_id}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_developer_portal_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_developer_portal_service.py`

- **Line:** 458
- **Excerpt:** `current_app.logger.info(f"Generated {language.value} SDK version {version}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_developer_portal_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/distributed_resilience_service.py`

- **Line:** 42
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_distributed_resilience_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/distributed_resilience_service.py`

- **Line:** 743
- **Excerpt:** `if current_app:`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_distributed_resilience_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/distributed_resilience_service.py`

- **Line:** 744
- **Excerpt:** `current_app.logger.warning(f"Fallback level {level.value} failed: {e}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_distributed_resilience_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/workflow_orchestration_service.py`

- **Line:** 27
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_workflow_orchestration_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/workflow_orchestration_service.py`

- **Line:** 131
- **Excerpt:** `current_app.logger.info("Workflow Orchestration Service initialized")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_workflow_orchestration_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/workflow_orchestration_service.py`

- **Line:** 146
- **Excerpt:** `current_app.logger.info(f"Registered workflow: {workflow.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_workflow_orchestration_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/workflow_orchestration_service.py`

- **Line:** 166
- **Excerpt:** `current_app.logger.info(f"Workflow completed: {workflow.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_workflow_orchestration_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/workflow_orchestration_service.py`

- **Line:** 172
- **Excerpt:** `current_app.logger.error(f"Workflow failed: {workflow.name} - {e}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_workflow_orchestration_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/workflow_orchestration_service.py`

- **Line:** 232
- **Excerpt:** `current_app.logger.info(f"Compensating workflow: {workflow.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_workflow_orchestration_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/workflow_orchestration_service.py`

- **Line:** 242
- **Excerpt:** `current_app.logger.error(f"Compensation failed for {activity.name}: {e}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_workflow_orchestration_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_security_service.py`

- **Line:** 30
- **Excerpt:** `from flask import current_app, g, jsonify, request`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_security_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_security_service.py`

- **Line:** 555
- **Excerpt:** `return current_app.config.get("SECRET_KEY", "dev-secret-change-in-production")`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_security_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/api_security_service.py`

- **Line:** 562
- **Excerpt:** `return current_app.config.get("API_SIGNING_SECRET", self._get_jwt_secret())`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_security_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/master_agent_service.py`

- **Line:** 71
- **Excerpt:** `from flask import current_app, has_app_context`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_master_agent_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/master_agent_service.py`

- **Line:** 278
- **Excerpt:** `logger = current_app.logger`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_master_agent_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/master_agent_service.py`

- **Line:** 1970
- **Excerpt:** `self._app_ref = current_app._get_current_object()`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_master_agent_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/system_service.py`

- **Line:** 41
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_system_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/system_service.py`

- **Line:** 164
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_system_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/system_service.py`

- **Line:** 453
- **Excerpt:** `current_app.logger.warning("DB bootstrap for %s failed: %s", rel_path, e)`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_system_service_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 30
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 201
- **Excerpt:** `current_app.logger.warning(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 274
- **Excerpt:** `current_app.logger.info(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 282
- **Excerpt:** `current_app.logger.info("🐒 Chaos Monkey disabled")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 307
- **Excerpt:** `current_app.logger.info(f"Chaos experiment created: {name} ({experiment_id})")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 332
- **Excerpt:** `current_app.logger.info(f"Validating steady state for experiment: {experiment.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 337
- **Excerpt:** `current_app.logger.error(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 352
- **Excerpt:** `current_app.logger.info(f"Injecting {len(experiment.fault_injections)} faults")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 400
- **Excerpt:** `current_app.logger.info(f"Experiment completed: {experiment.name} - {result}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 405
- **Excerpt:** `current_app.logger.error(f"Experiment error: {e}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 416
- **Excerpt:** `current_app.logger.warning(`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 422
- **Excerpt:** `current_app.logger.info(f"Rolling back faults for experiment: {experiment.name}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/services/chaos_engineering.py`

- **Line:** 453
- **Excerpt:** `current_app.logger.info(f"Game Day scheduled: {name} at {scheduled_at.isoformat()}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_chaos_engineering_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/overmind/planning/deep_indexer.py`

- **Line:** 317
- **Excerpt:** `return bool(any(x in lower for x in ("fastapi(", "flask(", "blueprint(", "apirouter(")))`
- **Category:** router
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_deep_indexer_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/api_versioning.py`

- **Line:** 15
- **Excerpt:** `from flask import Blueprint, current_app, jsonify, request`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_versioning_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/api_versioning.py`

- **Line:** 92
- **Excerpt:** `current_app.logger.warning(f"Using deprecated API version: {current_version}")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_api_versioning_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 22
- **Excerpt:** `from flask import Request, current_app, g, jsonify, request`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 87
- **Excerpt:** `current_app.logger.info(f"New user registered: {email}")`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 98
- **Excerpt:** `current_app.logger.error(f"Registration failed: {str(e)}")`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 141
- **Excerpt:** `current_app.logger.warning(f"Failed login attempt: {email} from {ip_address}")`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 156
- **Excerpt:** `current_app.logger.info(f"Successful login: {email} from {ip_address}")`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 198
- **Excerpt:** `current_app.logger.warning(`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 221
- **Excerpt:** `current_app.logger.info(f"Password changed for user {user_id}")`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 231
- **Excerpt:** `current_app.logger.error(f"Password change failed: {str(e)}")`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 261
- **Excerpt:** `current_app.logger.warning(`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 271
- **Excerpt:** `current_app.logger.warning(`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 277
- **Excerpt:** `current_app.logger.info(f"Admin access granted to user {g.user_id} for {request.path}")`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 335
- **Excerpt:** `current_app.logger.warning(`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 343
- **Excerpt:** `current_app.logger.warning(`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./app/security/secure_templates.py`

- **Line:** 518
- **Excerpt:** `# upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')`
- **Category:** security
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_secure_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_admin_chat_persistence.py`

- **Line:** 56
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_admin_chat_persistence_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 2
- **Excerpt:** `Simple compatibility shim for `flask.current_app` and related helpers.`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 3
- **Excerpt:** `This file is intentionally minimal: it provides a `current_app` object with`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 13
- **Excerpt:** `_logger = logging.getLogger("compat.current_app")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 27
- **Excerpt:** `# `current_app` object compatibility`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 28
- **Excerpt:** `current_app = SimpleNamespace(config=_config, logger=_logger, name="compat_app")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 38
- **Excerpt:** `If called with an object, replace current_app for the scope of process.`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 40
- **Excerpt:** `global _app_context_active, current_app`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 43
- **Excerpt:** `current_app = app_obj`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 47
- **Excerpt:** `global _app_context_active, current_app`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 50
- **Excerpt:** `current_app = SimpleNamespace(config=_config, logger=_logger, name="compat_app")`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 53
- **Excerpt:** `def get_current_app():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/current_app.py`

- **Line:** 54
- **Excerpt:** `return current_app`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_current_app_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./compat/__init__.py`

- **Line:** 2
- **Excerpt:** `__all__ = ["current_app", "has_app_context", "get_current_app"]`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test___init___compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_admin_routes.py`

- **Line:** 21
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_admin_routes_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_admin_chat_error_fix.py`

- **Line:** 29
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_admin_chat_error_fix_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_admin_chat_error_fix.py`

- **Line:** 113
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_admin_chat_error_fix_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_conversation_continuation.py`

- **Line:** 66
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_conversation_continuation_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./verify_admin_chat_migration.py`

- **Line:** 55
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_verify_admin_chat_migration_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./verify_admin_chat_migration.py`

- **Line:** 153
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_verify_admin_chat_migration_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_superhuman_admin_chat.py`

- **Line:** 46
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_superhuman_admin_chat_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./setup_supabase_connection.py`

- **Line:** 195
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_setup_supabase_connection_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_superhuman_enhancements.py`

- **Line:** 15
- **Excerpt:** `app = Flask(__name__)`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_test_superhuman_enhancements_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_superhuman_enhancements.py`

- **Line:** 21
- **Excerpt:** `ctx = app.app_context()`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_superhuman_enhancements_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_complex_question_fix.py`

- **Line:** 25
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_complex_question_fix_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_complex_question_fix.py`

- **Line:** 132
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_complex_question_fix_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_complex_question_fix.py`

- **Line:** 164
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_complex_question_fix_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./verify_supabase_connection.py`

- **Line:** 131
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_verify_supabase_connection_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./verify_supabase_connection.py`

- **Line:** 164
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_verify_supabase_connection_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./verify_supabase_connection.py`

- **Line:** 201
- **Excerpt:** `with app.app_context():`
- **Category:** unknown
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_verify_supabase_connection_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./seed_prompt_templates.py`

- **Line:** 322
- **Excerpt:** `with app.app_context():`
- **Category:** templates
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_seed_prompt_templates_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./tests/create_test_user.py`

- **Line:** 15
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_create_test_user_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./tests/test_api_first_platform.py`

- **Line:** 396
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_api_first_platform_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./tests/test_api_first_platform.py`

- **Line:** 442
- **Excerpt:** `with app.app_context():`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_test_api_first_platform_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./test_superhuman_system.py`

- **Line:** 24
- **Excerpt:** `app = Flask(__name__)`
- **Category:** tests
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_test_superhuman_system_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `.github/workflows/migration-readiness.yml`

- **Line:** 38
- **Excerpt:** `for p in "from flask" "import flask" "flask\." "current_app" "app_context" "flask_login" "flask_socketio" "socketio" "FastAPI" "uvicorn" "asgiref" "WebSocket" "websocket" "render_template"; do`
- **Category:** ci
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_migration-readiness.yml_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./MASSIVE_FUNCTIONS_README.md`

- **Line:** 233
- **Excerpt:** `app = Flask(__name__)`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_MASSIVE_FUNCTIONS_README.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_ERROR_HANDLING_FIX.md`

- **Line:** 196
- **Excerpt:** `# If using Gunicorn`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_ERROR_HANDLING_FIX.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_ERROR_HANDLING_FIX.md`

- **Line:** 197
- **Excerpt:** `pkill gunicorn && gunicorn run:app`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_ERROR_HANDLING_FIX.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_MIDDLEWARE_QUICK_REF_AR.md`

- **Line:** 70
- **Excerpt:** `app = Flask(__name__)`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_MIDDLEWARE_QUICK_REF_AR.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_MIDDLEWARE_QUICK_REF_AR.md`

- **Line:** 85
- **Excerpt:** `app = Flask(__name__)`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_MIDDLEWARE_QUICK_REF_AR.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./API_ENHANCEMENTS_SUMMARY.md`

- **Line:** 321
- **Excerpt:** `- Production setup with Gunicorn`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_API_ENHANCEMENTS_SUMMARY.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./houssam.md`

- **Line:** 89
- **Excerpt:** `- **التوازن**: Load Balancing عبر Gunicorn`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_houssam.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./houssam.md`

- **Line:** 113
- **Excerpt:** `- **الخدمة**: Flask + Gunicorn`
- **Category:** cli
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_houssam.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./WORLD_CLASS_API_QUICKSTART.md`

- **Line:** 82
- **Excerpt:** `gunicorn -w 4 -b 0.0.0.0:5000 run:app`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_WORLD_CLASS_API_QUICKSTART.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_IMPLEMENTATION_GUIDE.md`

- **Line:** 680
- **Excerpt:** `app = Flask(__name__)`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_IMPLEMENTATION_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./WEB_SOCKET_FLASK_CONFLICT_REPORT.md`

- **Line:** 5
- **Excerpt:** `This report provides a detailed analysis of the hybrid Flask and FastAPI application, focusing on the deep-rooted dependencies on Flask's application context. The production runtime is an ASGI environment serving a FastAPI application (`app/main:app`), but the core business logic, services, and tooling are still tightly coupled to Flask's global objects (`current_app`, `db.session`). This creates a significant architectural conflict, making it impossible to run services in a pure ASGI context (like a WebSocket handler) without encountering "working outside of application context" errors. The test suite is also a hybrid, with a mix of FastAPI and Flask context-dependent tests, further complicating the migration path. This document outlines the key blockers, their severity, and a prioritized list of atomic tasks to begin the decoupling process.`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_WEB_SOCKET_FLASK_CONFLICT_REPORT.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./WEB_SOCKET_FLASK_CONFLICT_REPORT.md`

- **Line:** 12
- **Excerpt:** `| `app/services/history_service.py` | 3 | `from flask import current_app` | **High** |`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_WEB_SOCKET_FLASK_CONFLICT_REPORT.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./WEB_SOCKET_FLASK_CONFLICT_REPORT.md`

- **Line:** 15
- **Excerpt:** `| `cli.py` | 35 | `with flask_app.app_context():` | **Medium** |`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_WEB_SOCKET_FLASK_CONFLICT_REPORT.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./WEB_SOCKET_FLASK_CONFLICT_REPORT.md`

- **Line:** 29
- **Excerpt:** `*   **Task:** Refactor a single test file (e.g., `test_admin_routes.py`) that uses `with app.app_context():` to use the FastAPI `TestClient` fixture instead. This will involve adapting the tests to make HTTP requests to the FastAPI app rather than calling Flask functions directly.`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_WEB_SOCKET_FLASK_CONFLICT_REPORT.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./WEB_SOCKET_FLASK_CONFLICT_REPORT.md`

- **Line:** 44
- **Excerpt:** `grep -R --line-number --include="*.py" -E "current_app|app_context|has_app_context|g\\b|flask_login|flask_migrate|flask_sqlalchemy|flask_wtf" || true`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_WEB_SOCKET_FLASK_CONFLICT_REPORT.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./WEB_SOCKET_FLASK_CONFLICT_REPORT.md`

- **Line:** 50
- **Excerpt:** `grep -R --line-number --include="tests/*.py" -E "app.app_context|app_context|flask_client|client_fixture|test_client" || true`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace with a framework-agnostic approach. Create a compatibility wrapper in `app/core/compat.py` to emulate app context until removal.
- **Tests to Write:** `tests/transcendent/test_WEB_SOCKET_FLASK_CONFLICT_REPORT.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_SECURITY_AR.md`

- **Line:** 207
- **Excerpt:** `app = Flask(__name__)`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_SECURITY_AR.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./API_GATEWAY_QUICKSTART.md`

- **Line:** 28
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_API_GATEWAY_QUICKSTART.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./WEBSOCKET_FLASK_CONFLICT_REPORT.md`

- **Line:** 57
- **Excerpt:** `| **HIGH** | `current_app` Usage in Services         | Tightly couples all services to the Flask application context for logging and configuration.            |`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_WEBSOCKET_FLASK_CONFLICT_REPORT.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_MIDDLEWARE_ARCHITECTURE_COMPLETE.md`

- **Line:** 126
- **Excerpt:** `app = Flask(__name__)`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_MIDDLEWARE_ARCHITECTURE_COMPLETE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_MIDDLEWARE_ARCHITECTURE_COMPLETE.md`

- **Line:** 141
- **Excerpt:** `app = Flask(__name__)`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_MIDDLEWARE_ARCHITECTURE_COMPLETE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 85
- **Excerpt:** `### 1. Install Production Server (Gunicorn)`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 88
- **Excerpt:** `pip install gunicorn`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 91
- **Excerpt:** `### 2. Create Gunicorn Configuration`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 93
- **Excerpt:** `Create `gunicorn.conf.py`:`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 96
- **Excerpt:** `# Gunicorn configuration`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 107
- **Excerpt:** `accesslog = "logs/gunicorn-access.log"`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 108
- **Excerpt:** `errorlog = "logs/gunicorn-error.log"`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 132
- **Excerpt:** `### 3. Run with Gunicorn`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 135
- **Excerpt:** `gunicorn -c gunicorn.conf.py "app:create_app()"`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 156
- **Excerpt:** `ExecStart=/var/www/cogniforge/venv/bin/gunicorn -c gunicorn.conf.py "app:create_app()"`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 261
- **Excerpt:** `# Proxy to Gunicorn`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 324
- **Excerpt:** `- `gunicorn-access.log` - Access logs`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./DEPLOYMENT_GUIDE.md`

- **Line:** 325
- **Excerpt:** `- `gunicorn-error.log` - Error logs`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_DEPLOYMENT_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./docs/config/SETTINGS_LAYER.md`

- **Line:** 9
- **Excerpt:** `Previously, the application's configuration was tightly coupled to Flask's global `current_app.config` object. This presented several architectural challenges:`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_SETTINGS_LAYER.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./docs/db/SESSION_FACTORY.md`

- **Line:** 10
- **Excerpt:** `- **Independence:** It has zero dependencies on the Flask application context (`current_app`, `g`, etc.). This allows it to be used in any part of the application, including FastAPI endpoints, WebSocket handlers, CLI commands, and standalone scripts.`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_SESSION_FACTORY.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./docs/core/DEPENDENCY_LAYER.md`

- **Line:** 5
- **Excerpt:** `The legacy application architecture is tightly coupled to Flask's global context objects, primarily `current_app`. This creates several significant challenges:`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_DEPENDENCY_LAYER.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./docs/core/DEPENDENCY_LAYER.md`

- **Line:** 53
- **Excerpt:** `from flask import current_app`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_DEPENDENCY_LAYER.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./docs/cli/CLI_GUIDELINES.md`

- **Line:** 7
- **Excerpt:** `- **No Flask Imports**: CLI handlers in `app/cli_handlers` must not import `current_app` or any other Flask-specific context variables. This ensures that the CLI is decoupled from the web application.`
- **Category:** cli
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** Replace `current_app` with dependency injection. Use `Depends(get_settings)` for configuration and `Depends(get_logger)` for logging.
- **Tests to Write:** `tests/transcendent/test_CLI_GUIDELINES.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_SECURITY_TELEMETRY_GUIDE.md`

- **Line:** 379
- **Excerpt:** `app = Flask(__name__)`
- **Category:** docs
- **Current Behavior:** Direct dependency on Flask application context or app creation.
- **Recommended Action:** This is an app factory. Replace with a FastAPI app factory and use APIRouters.
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_SECURITY_TELEMETRY_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./MIGRATION_REVISION_FIX_GUIDE.md`

- **Line:** 77
- **Excerpt:** `export FLASK_APP=run:app`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_MIGRATION_REVISION_FIX_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./MIGRATION_REVISION_FIX_GUIDE.md`

- **Line:** 105
- **Excerpt:** `export FLASK_APP=run:app`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_MIGRATION_REVISION_FIX_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./MIGRATION_REVISION_FIX_GUIDE.md`

- **Line:** 151
- **Excerpt:** `export FLASK_APP=run:app`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_MIGRATION_REVISION_FIX_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPABASE_SETUP_GUIDE.md`

- **Line:** 192
- **Excerpt:** `export FLASK_APP=run:app`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_SUPABASE_SETUP_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_ERROR_HANDLING_FIX_AR.md`

- **Line:** 80
- **Excerpt:** `# إذا كنت تستخدم Gunicorn`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_ERROR_HANDLING_FIX_AR.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SUPERHUMAN_ERROR_HANDLING_FIX_AR.md`

- **Line:** 81
- **Excerpt:** `pkill gunicorn && gunicorn run:app`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_SUPERHUMAN_ERROR_HANDLING_FIX_AR.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./MIGRATION_FIX_QUICKSTART.md`

- **Line:** 26
- **Excerpt:** `export FLASK_APP=run:app`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_MIGRATION_FIX_QUICKSTART.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./MIGRATION_FIX_QUICKSTART.md`

- **Line:** 114
- **Excerpt:** `export FLASK_APP=run:app`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_MIGRATION_FIX_QUICKSTART.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SSE_STREAMING_IMPLEMENTATION_REPORT.md`

- **Line:** 296
- **Excerpt:** `gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_SSE_STREAMING_IMPLEMENTATION_REPORT.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SSE_STREAMING_GUIDE.md`

- **Line:** 164
- **Excerpt:** `gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_SSE_STREAMING_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./SSE_STREAMING_GUIDE.md`

- **Line:** 313
- **Excerpt:** `2. ✅ **Scale workers:** `gunicorn -w 8``
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_SSE_STREAMING_GUIDE.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---

### Path: `./CRUD_API_GUIDE_AR.md`

- **Line:** 802
- **Excerpt:** `1. استخدم Gunicorn كخادم WSGI`
- **Category:** docs
- **Current Behavior:** Application entrypoint definition.
- **Recommended Action:** N/A
- **Tests to Write:** `tests/transcendent/test_CRUD_API_GUIDE_AR.md_compatibility.py`
- **Estimated Effort:** Medium
- **Blocker:** Likely used by other components. Needs further analysis.

---
