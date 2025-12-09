# خطة إعادة البناء الشاملة

## الحالة الحالية
- **التغطية الاختبارية**: 51.94% (المطلوب: ≥80%)
- **التعقيد الدوري**: 116 انتهاك (المطلوب: ≤10)
- **تكرار الكود**: 7+ حالات (المطلوب: 0%)
- **البنية المعمارية**: 40% Hexagonal (المطلوب: 100%)

## المرحلة 1: إعادة بناء الدوال المعقدة (Priority: CRITICAL)

### الدوال التي يجب إعادة بناؤها فوراً (Complexity > 15):

1. **app/core/ai_gateway.py:351 - stream_chat** (23)
   - تقسيم إلى: validate_input, recall_from_cache, route_to_nodes, assess_quality
   
2. **app/services/ai_model_metrics_service.py:625 - calculate_fairness_metrics** (23)
   - تقسيم إلى: calculate_demographic_parity, calculate_equal_opportunity, calculate_disparate_impact
   
3. **app/services/security_metrics_engine.py:321 - calculate_developer_security_score** (21)
   - تقسيم إلى: calculate_code_quality_score, calculate_vulnerability_score, aggregate_scores
   
4. **app/services/api_advanced_analytics_service.py:514 - detect_anomalies** (21)
   - تقسيم إلى: detect_rate_anomalies, detect_error_anomalies, detect_latency_anomalies
   
5. **app/services/agent_tools/fs_tools.py:394 - ensure_file** (21)
   - تقسيم إلى: validate_path, create_directories, write_file_content
   
6. **app/services/agent_tools/utils.py:100 - _safe_path** (21)
   - تقسيم إلى: normalize_path, validate_path_safety, resolve_path
   
7. **app/services/overmind/core.py:148 - _phase_execution_step** (21)
   - تقسيم إلى: prepare_phase, execute_phase, handle_phase_result
   
8. **app/services/project_context_service.py:206 - get_deep_file_analysis** (20)
   - تقسيم إلى: analyze_imports, analyze_functions, analyze_classes
   
9. **app/services/security_metrics_engine.py:512 - generate_comprehensive_report** (20)
   - تقسيم إلى: generate_summary, generate_details, format_report
   
10. **app/core/database.py:64 - validate_and_fix_schema** (19)
    - تقسيم إلى: validate_schema, fix_schema_issues, verify_fix

## المرحلة 2: إزالة التكرار (Priority: HIGH)

### حالات التكرار المكتشفة:

1. **Resilience Services** (36 سطر مكرر)
   - `app.services.distributed_resilience_service:[66:101]`
   - `app.services.resilience.__init__:[43:78]`
   - الحل: إنشاء `app/domain/resilience/base.py`

2. **Config Reading** (19 سطر مكرر)
   - `app.overmind.planning.hyper_planner.config:[7:25]`
   - `app.services.agent_tools.definitions:[36:54]`
   - الحل: إنشاء `app/infrastructure/config/reader.py`

3. **Chat Services** (12 سطر مكرر)
   - `app.services.chat.__init__:[9:20]`
   - `app.services.chat_orchestrator_service:[9:20]`
   - الحل: دمج في `app/application/chat/exports.py`

4. **Streaming Logic** (19 سطر مكرر)
   - `app.services.chat.refactored.handlers:[192:200]`
   - `app.services.chat.service:[183:201]`
   - الحل: إنشاء `app/domain/chat/streaming.py`

## المرحلة 3: تطبيق Hexagonal Architecture (Priority: HIGH)

### البنية الجديدة:

```
app/
├── domain/                    # Domain Layer (Pure Business Logic)
│   ├── entities/             # Domain Entities
│   │   ├── user.py
│   │   ├── mission.py
│   │   └── conversation.py
│   ├── repositories/         # Repository Interfaces (Ports)
│   │   ├── user_repository.py
│   │   └── mission_repository.py
│   ├── services/             # Domain Services
│   │   └── chat_domain_service.py
│   └── value_objects/        # Value Objects
│       └── email.py
│
├── application/              # Application Layer (Use Cases)
│   ├── use_cases/
│   │   ├── create_user.py
│   │   ├── process_mission.py
│   │   └── handle_chat.py
│   ├── ports/
│   │   ├── inbound/         # API Contracts
│   │   └── outbound/        # Infrastructure Contracts
│   └── mappers/             # DTOs
│       └── user_mapper.py
│
├── infrastructure/           # Infrastructure Layer (Adapters)
│   ├── persistence/
│   │   ├── models/          # SQLAlchemy Models
│   │   └── repositories/    # Repository Implementations
│   ├── external/
│   │   └── ai_service_adapter.py
│   └── config/
│       └── database.py
│
└── api/                     # API Layer (Inbound Adapters)
    └── routers/
        └── user_router.py
```

### الخطوات:

1. **فصل Domain Entities عن Persistence Models**
   - نقل `app/models.py` إلى `app/infrastructure/persistence/models/`
   - إنشاء Domain Entities في `app/domain/entities/`

2. **تطبيق Repository Pattern**
   - إنشاء Repository Interfaces في `app/domain/repositories/`
   - تطبيق Adapters في `app/infrastructure/persistence/repositories/`

3. **نقل Business Logic إلى Use Cases**
   - تحويل Services إلى Use Cases
   - Use Cases تعتمد على Repository Interfaces فقط

4. **إزالة الوصول المباشر للقاعدة**
   - API Routers تستخدم Use Cases فقط
   - لا يوجد import لـ AsyncSession أو models في API

## المرحلة 4: زيادة التغطية الاختبارية (Priority: MEDIUM)

### الملفات التي تحتاج اختبارات:

1. **Domain Layer** (Target: 95%)
   - Domain Entities
   - Domain Services
   - Value Objects

2. **Application Layer** (Target: 90%)
   - Use Cases
   - Mappers

3. **Infrastructure Layer** (Target: 70%)
   - Repository Implementations
   - External Adapters

4. **API Layer** (Target: 85%)
   - Routers
   - DTOs

### استراتيجية الاختبار:

- **Unit Tests**: Domain + Application (isolated)
- **Integration Tests**: Infrastructure + API
- **Contract Tests**: Ports validation
- **E2E Tests**: Full flow

## الأولويات

### Week 1: Critical Fixes
- [ ] إعادة بناء أعلى 10 دوال تعقيداً
- [ ] إزالة التكرار الأساسي
- [ ] فصل Domain عن Infrastructure

### Week 2: Architecture
- [ ] تطبيق Repository Pattern
- [ ] إنشاء Use Cases
- [ ] تطبيق Dependency Inversion

### Week 3: Testing
- [ ] اختبارات Domain Layer (95%)
- [ ] اختبارات Application Layer (90%)
- [ ] اختبارات Integration (70%)

### Week 4: Verification
- [ ] التحقق من التغطية ≥ 80%
- [ ] التحقق من Complexity ≤ 10
- [ ] التحقق من Duplication = 0%
- [ ] التحقق من Hexagonal Architecture

## معايير النجاح

- ✅ Test Coverage ≥ 80%
- ✅ Cyclomatic Complexity ≤ 10 (max 15)
- ✅ Code Duplication = 0%
- ✅ Hexagonal Architecture = 100%
- ✅ All tests passing
- ✅ No architectural violations
