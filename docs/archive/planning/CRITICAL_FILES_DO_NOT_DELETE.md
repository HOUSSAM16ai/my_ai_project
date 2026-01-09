# 🛡️ ملفات حيوية - ممنوع الحذف

## ⚠️ تحذير
الملفات التالية **حيوية** لعمل المشروع والبنية التحتية. **لا تحذفها أبداً**.

---

## 🔧 1. GitHub Codespaces (حيوي جداً)

### .devcontainer/
```
✅ .devcontainer/devcontainer.json          - تكوين Codespaces الرئيسي
✅ .devcontainer/docker-compose.host.yml    - Docker compose للتطوير
✅ .devcontainer/on-create.sh               - سكريبت الإنشاء
✅ .devcontainer/on-start.sh                - سكريبت البدء
✅ .devcontainer/on-attach.sh               - سكريبت الاتصال
✅ .devcontainer/utils.sh                   - أدوات مساعدة
```

**السبب**: ضرورية لعمل GitHub Codespaces

---

## 🌐 2. Gitpod (حيوي)

```
✅ .gitpod.yml                              - تكوين Gitpod
```

**السبب**: ضرورية لعمل Gitpod

---

## 🤖 3. GitHub Actions (حيوي للأتمتة)

### .github/workflows/
```
✅ .github/workflows/ci.yml                 - CI/CD الرئيسي
✅ .github/workflows/comprehensive_testing.yml - اختبارات شاملة
✅ .github/workflows/omega_pipeline.yml     - Pipeline متقدم
✅ .github/workflows/universal_sync.yml     - مزامنة الريبو
```

### .github/actions/
```
✅ .github/actions/setup/action.yml         - إعداد البيئة
```

### .github/ (ملفات أخرى)
```
✅ .github/dependabot.yml                   - تحديث التبعيات
✅ .github/copilot-instructions.md          - تعليمات Copilot
✅ .github/BRANCH_PROTECTION_GUIDE.md       - دليل حماية الفروع
✅ .github/VERIFICATION_CHECKLIST.md        - قائمة التحقق
```

**السبب**: ضرورية للـ CI/CD والأتمتة

---

## 🔄 4. CI/CD الأخرى

```
✅ .gitlab-ci.yml                           - GitLab CI
✅ .cicd/gate_checks.yaml                   - فحوصات الجودة
```

**السبب**: ضرورية لـ GitLab CI

---

## 📜 5. سكريبتات الأتمتة الحيوية

### scripts/ (حيوية)
```
✅ scripts/setup_dev.sh                     - إعداد بيئة التطوير
✅ scripts/codespace_guardian.sh            - حماية Codespaces
✅ scripts/force_start_codespaces.sh        - إصلاح مشاكل البدء
✅ scripts/bootstrap_db.py                  - إعداد قاعدة البيانات
✅ scripts/preflight_check.sh               - فحوصات ما قبل البدء
✅ scripts/preflight_step2.sh               - فحوصات المرحلة 2
✅ scripts/start.sh                         - بدء التطبيق
✅ scripts/start_dev.sh                     - بدء بيئة التطوير
✅ scripts/start-backend.sh                 - بدء Backend
✅ scripts/start-docker.sh                  - بدء Docker
✅ scripts/format_code.sh                   - تنسيق الكود
✅ scripts/auto_fix_quality.sh              - إصلاح الجودة تلقائياً
✅ scripts/run_comprehensive_tests.sh       - تشغيل الاختبارات
✅ scripts/security_scan.sh                 - فحص الأمان
✅ scripts/verify_all.sh                    - التحقق الشامل
```

**السبب**: ضرورية للتطوير والأتمتة

---

## 🏗️ 6. البنية التحتية (Infrastructure)

### infra/
```
✅ infra/terraform/*                        - Infrastructure as Code
✅ infra/k8s/*                              - Kubernetes configs
✅ infra/argocd/*                           - GitOps
✅ infra/monitoring/*                       - المراقبة
✅ infra/pipelines/*                        - ML Pipelines
```

**السبب**: ضرورية للنشر والإنتاج

---

## ⚙️ 7. ملفات التكوين الأساسية

### Python & Testing
```
✅ pyproject.toml                           - تكوين Python الرئيسي
✅ pytest.ini                               - تكوين pytest
✅ mypy.ini                                 - تكوين Type Checking
✅ .flake8                                  - تكوين Flake8
✅ .semgrep.yml                             - تكوين Semgrep
✅ .semgrepignore                           - استثناءات Semgrep
✅ .mutmut_config.py                        - تكوين Mutation Testing
```

### Git & Pre-commit
```
✅ .pre-commit-config.yaml                  - Git hooks
✅ .gitignore                               - ملفات مستثناة من Git
```

### Docker
```
✅ Dockerfile                               - بناء صورة Docker
✅ docker-compose.yml                       - تشغيل محلي
✅ .dockerignore                            - ملفات مستثناة من Docker
✅ entrypoint.sh                            - نقطة دخول Docker
```

### Build & Development
```
✅ Makefile                                 - أوامر التطوير
✅ requirements.txt                         - التبعيات الرئيسية
✅ requirements-prod.txt                    - تبعيات الإنتاج
✅ requirements-dev.txt                     - تبعيات التطوير
✅ requirements-test.txt                    - تبعيات الاختبار
✅ requirements-lock.txt                    - قفل التبعيات
```

### Database
```
✅ alembic.ini                              - تكوين Alembic
✅ migrations/*                             - Database migrations
```

### Editor Config
```
✅ .editorconfig                            - تكوين المحرر
✅ .vscode/*                                - تكوين VS Code
✅ .cursor/*                                - تكوين Cursor
```

### Environment
```
✅ .env.example                             - مثال متغيرات البيئة
✅ .env.docker                              - متغيرات Docker
✅ .env.security.example                    - مثال متغيرات الأمان
✅ .python-version                          - إصدار Python
```

### Documentation
```
✅ README.md                                - الوثائق الرئيسية
✅ CONTRIBUTING.md                          - دليل المساهمة
✅ CHANGELOG.md                             - سجل التغييرات
✅ AGENTS.md                                - وثائق الوكلاء
✅ CREATE_PR_INSTRUCTIONS.md                - تعليمات PR
✅ PROJECT_METRICS.md                       - مقاييس المشروع
```

### Quality & Security
```
✅ sonar-project.properties                 - تكوين SonarQube
✅ .trivy.yml                               - تكوين Trivy
✅ .yamllint                                - تكوين YAML Lint
```

**السبب**: ضرورية لعمل المشروع والتطوير

---

## 🚀 8. ملفات التطبيق الأساسية

### Entry Points
```
✅ app/main.py                              - نقطة دخول FastAPI
✅ app/kernel.py                            - Kernel الرئيسي
✅ app/cli.py                               - CLI الرئيسي
✅ cli.py                                   - CLI wrapper
```

### Core Configuration
```
✅ app.core.config.py                   - الإعدادات الرئيسية
✅ app.core.ai_config.py                  - تكوين نماذج AI
✅ app/core/config.py               - Dependency Injection
```

### Database
```
✅ app/models.py                            - نماذج قاعدة البيانات
✅ app/core/database.py                     - اتصال قاعدة البيانات
```

### Security
```
✅ app/security/*                           - جميع ملفات الأمان
```

### Middleware
```
✅ app/middleware/*                         - جميع Middleware
```

**السبب**: ضرورية لعمل التطبيق

---

## 📊 9. ملفات التحليل (الجديدة)

```
✅ COMPREHENSIVE_ANALYSIS_REPORT.md         - التقرير الشامل
✅ ACTIONABLE_CLEANUP_LIST.md               - قائمة الإجراءات
✅ ANALYSIS_SUMMARY.md                      - ملخص التحليل
✅ CRITICAL_FILES_DO_NOT_DELETE.md          - هذا الملف
```

**السبب**: وثائق التحليل والتحسين

---

## ⚠️ ملفات يمكن حذفها بحذر

### ملفات مؤقتة (آمن للحذف)
```
❌ __pycache__/                             - ملفات Python المؤقتة
❌ .pytest_cache/                           - ملفات pytest المؤقتة
❌ *.pyc                                    - ملفات bytecode
❌ .coverage                                - ملفات التغطية
❌ htmlcov/                                 - تقارير التغطية HTML
❌ .mypy_cache/                             - ملفات mypy المؤقتة
❌ .ruff_cache/                             - ملفات ruff المؤقتة
❌ logs/*                                   - ملفات السجلات (احتفظ بالمجلد)
❌ reports/*                                - التقارير المؤقتة
```

### ملفات قاعدة البيانات المحلية (آمن للحذف في التطوير)
```
⚠️ cogniforge.db                            - قاعدة بيانات SQLite محلية
⚠️ *.db                                     - ملفات قاعدة بيانات أخرى
```

**تحذير**: لا تحذف في الإنتاج!

---

## 🔍 كيفية التحقق من أهمية ملف

### قبل حذف أي ملف، تحقق من:

1. **هل يستخدم في CI/CD؟**
   ```bash
   grep -r "filename" .github/ .gitlab-ci.yml .cicd/
   ```

2. **هل يستخدم في Docker؟**
   ```bash
   grep -r "filename" Dockerfile docker-compose.yml .devcontainer/
   ```

3. **هل يستخدم في Scripts؟**
   ```bash
   grep -r "filename" scripts/
   ```

4. **هل يستخدم في الكود؟**
   ```bash
   grep -r "filename" app/ tests/
   ```

5. **هل هو ملف تكوين؟**
   - إذا كان في الجذر وله امتداد `.yml`, `.yaml`, `.toml`, `.ini`, `.cfg` → **لا تحذفه**

---

## 📋 قاعدة عامة

### ✅ آمن للحذف
- ملفات `__pycache__/`
- ملفات `.pyc`
- ملفات `.coverage`
- مجلدات `.cache/`
- ملفات `logs/*.log` (ليس المجلد)

### ⚠️ احذر
- أي ملف في `.github/`
- أي ملف في `.devcontainer/`
- أي ملف في `scripts/`
- أي ملف في `infra/`
- أي ملف تكوين في الجذر

### 🛑 لا تحذف أبداً
- ملفات CI/CD
- ملفات Docker
- ملفات التكوين الرئيسية
- ملفات البنية التحتية
- ملفات الأمان

---

## 🆘 في حالة الحذف الخاطئ

### استرجاع من Git
```bash
# استرجاع ملف واحد
git checkout HEAD -- path/to/file

# استرجاع مجلد كامل
git checkout HEAD -- path/to/directory/

# استرجاع كل التغييرات
git reset --hard HEAD
```

### استرجاع من GitHub
```bash
# تحميل من الريبو الأصلي
git fetch origin
git checkout origin/main -- path/to/file
```

---

**تاريخ الإنشاء**: 2024-12-25
**الحالة**: مرجع دائم
**الإصدار**: 1.0

**ملاحظة**: هذا الملف نفسه حيوي - لا تحذفه! 🛡️
