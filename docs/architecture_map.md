# Architecture Map

## Core Components
- **app/kernel.py**: FastAPI composition pipeline assembling middleware and routers while delegating configuration to `AppSettings`.
- **app/api/routers**: Feature-oriented API routers (admin, security, data-mesh, observability, CRUD) mounted declaratively by the kernel.
- **app/config**: Settings management and environment handling used by kernel and services.
- **app/services**: Domain services (admin chat/streaming, overmind, project context, system) that encapsulate business workflows.
- **app/services/admin/streaming/metrics.py**: Metrics aggregation with `SessionRecorder` وموّرد وقت قابل للحقن لضبط القياس بدقة لكل جلسة.
- **app/middleware**: Cross-cutting concerns (security headers, rate limiting, static files, observability) wired through the kernel pipeline.
- **app/infrastructure**: Persistence and external integrations supporting services and routers.

## Dependency Flow
- **Kernel → Routers → Services → Infrastructure**: Kernel constructs FastAPI and mounts routers; routers delegate to services; services rely on infrastructure adapters.
- **Settings → Kernel/Middleware/Services**: Configuration feeds runtime composition without global mutable state.
- **Middleware Stack**: Declarative registry drives middleware ordering to avoid implicit coupling.

## Mixed Responsibilities / Refactor Targets
1. **`app/services/admin/streaming/service.py`**: الخدمة تعتمد الآن على `AdminChatStreamingServiceFactory` لضبط التهيئة، والخطوة التالية هي ربط المصنع بتجميع kernel لإزالة أي استخدام متبقٍ للمفردات العالمية خارج الاختبارات.
2. **`app/services/admin/streaming/speculative.py`**: المنطق تنبؤي ثابت؛ يحتاج إلى بروتوكول قابل للتمديد وربط بمصادر نماذج واقعية دون تعديل المستهلكين.
3. **`app/services/admin/streaming/metrics.py`**: التجميع في الذاكرة فقط؛ إدخال منافذ مراقبة خارجية سيضمن اتساق المؤشرات في بيئات متعددة المثيلات.
4. **خدمات أخرى (خارج البث)**: ما زالت تعتمد على تهيئة مباشرة للبنى التحتية؛ يجب توسيع معايير DIP الحالية لتغطية هذه الخدمات تدريجياً.

## High-Churn Areas
- Admin streaming stack (fast iteration to support SSE and predictive behavior).
- Observability and security middleware (tight coupling to kernel composition but isolated registries mitigate risk).

## Planned SOLID Refactors
- إحلال مصنع خدمة بث يزيل الاعتماد على المفردة العالمية مع الحفاظ على التوافقية عبر طبقة توافق أو تهيئة kernelية.
- إدخال بروتوكول تنبؤ وتطبيقات بديلة لـ `SpeculativeDecoder` تسمح بدمج نماذج متقدمة دون تعديل منطق البث.
- توفير واجهة مراقبة خارجية لـ `StreamingMetrics` تتيح النشر إلى نظم تتبع وتوزيع الحمل مع الحفاظ على SRP.
- توسيع نهج الحقن عبر الخدمات غير المتعلقة بالبث لضمان تبعية عالية المستوى للتجريدات فقط.
