# 🚀 GitLab CI/CD Pipeline - دليل شامل

## نظرة عامة

تم بناء نظام CI/CD خارق يتجاوز معايير الشركات العملاقة (Google, Meta, Microsoft, OpenAI) مع:
- ✅ 10 مراحل متقدمة
- ✅ فحوصات أمنية شاملة (SAST, DAST, Container, Dependency, Secret)
- ✅ تكامل كامل مع Kubernetes
- ✅ Automated rollback
- ✅ Performance testing
- ✅ DORA metrics tracking

---

## 📋 جدول المحتويات

1. [بنية Pipeline](#بنية-pipeline)
2. [المراحل](#المراحل)
3. [Security Scanning](#security-scanning)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [الإعداد](#الإعداد)
6. [الاستخدام](#الاستخدام)
7. [استكشاف الأخطاء](#استكشاف-الأخطاء)

---

## 🏗️ بنية Pipeline

```
┌─────────────┐
│  VALIDATE   │  Syntax, YAML, Docker, Linting
└──────┬──────┘
       │
┌──────▼──────┐
│    BUILD    │  Docker images, Frontend assets
└──────┬──────┘
       │
┌──────▼──────┐
│    TEST     │  Unit, Integration, E2E (parallel)
└──────┬──────┘
       │
┌──────▼──────┐
│  SECURITY   │  SAST, Dependency, Container, Secret
└──────┬──────┘
       │
┌──────▼──────┐
│   QUALITY   │  Coverage, Complexity, SonarQube
└──────┬──────┘
       │
┌──────▼──────┐
│   PACKAGE   │  Artifacts, Helm charts
└──────┬──────┘
       │
┌──────▼──────┐
│   DEPLOY    │  Dev → Staging → Production
└──────┬──────┘
       │
┌──────▼──────┐
│   MONITOR   │  Metrics, Performance
└──────┬──────┘
       │
┌──────▼──────┐
│   VERIFY    │  Health checks, Smoke tests
└──────┬──────┘
       │
┌──────▼──────┐
│   CLEANUP   │  Old images, Cache
└─────────────┘
```

---

## 📊 المراحل

### 1️⃣ VALIDATE (التحقق)

**الهدف:** التحقق من صحة الكود قبل البناء

**Jobs:**
- `validate:syntax` - فحص Python syntax
- `validate:yaml` - فحص YAML files
- `validate:docker` - فحص Dockerfile مع Hadolint
- `lint:ruff` - Linting مع Ruff

**متى يتم التشغيل:**
- على كل Merge Request
- على كل Push لـ main branch

### 2️⃣ BUILD (البناء)

**الهدف:** بناء Docker images والـ assets

**Jobs:**
- `build:docker` - بناء Docker image مع multi-stage build
- `build:assets` - بناء Frontend assets مع npm

**Features:**
- Docker layer caching
- BuildKit optimization
- Push to GitLab Container Registry

### 3️⃣ TEST (الاختبارات)

**الهدف:** اختبار شامل للكود

**Jobs:**
- `test:unit` - Unit tests مع coverage
- `test:integration` - Integration tests (parallel: 3)
- `test:e2e` - End-to-end tests مع Playwright

**Metrics:**
- Code coverage: 70% minimum
- JUnit reports
- HTML coverage reports

### 4️⃣ SECURITY (الأمان)

**الهدف:** فحص أمني شامل

**Jobs:**
- `security:sast` - Static Application Security Testing (Semgrep)
- `security:dependency` - Dependency scanning (Safety, pip-audit)
- `security:container` - Container scanning (Trivy)
- `security:secrets` - Secret detection (detect-secrets, GitLeaks)
- `security:bandit` - Python security linter

**Reports:**
- SAST report
- Dependency report
- Container scanning report
- Secrets report

### 5️⃣ QUALITY (الجودة)

**الهدف:** ضمان جودة الكود

**Jobs:**
- `quality:coverage` - Coverage threshold check (70%)
- `quality:complexity` - Complexity analysis (Radon, Xenon)
- `quality:sonarqube` - SonarQube analysis

**Gates:**
- Minimum coverage: 70%
- Maximum complexity: 15
- SonarQube quality gate

### 6️⃣ PACKAGE (التعبئة)

**الهدف:** تعبئة artifacts للنشر

**Jobs:**
- `package:artifacts` - Create deployment package
- `package:helm` - Package Helm chart

**Artifacts:**
- Deployment tarball
- Helm chart (.tgz)

### 7️⃣ DEPLOY (النشر)

**الهدف:** نشر على Kubernetes

**Environments:**

#### Development
- **Trigger:** Automatic on main
- **Replicas:** 1
- **Resources:** 100m CPU, 256Mi RAM
- **URL:** https://dev.cogniforge.com

#### Staging
- **Trigger:** Manual
- **Replicas:** 2
- **Resources:** 250m CPU, 512Mi RAM
- **URL:** https://staging.cogniforge.com
- **Requires:** Development deployment + Security scans

#### Production
- **Trigger:** Manual
- **Replicas:** 5 (HPA: 5-50)
- **Resources:** 1000m CPU, 1Gi RAM
- **URL:** https://cogniforge.com
- **Requires:** Staging deployment + Quality gates

**Features:**
- Rolling updates
- Zero-downtime deployment
- Automated rollback on failure
- Health checks

### 8️⃣ MONITOR (المراقبة)

**الهدف:** مراقبة ما بعد النشر

**Jobs:**
- `monitor:metrics` - Collect deployment metrics
- `monitor:performance` - Performance testing (k6)

**Metrics:**
- Deployment time
- Error rate
- Response time
- Throughput

### 9️⃣ VERIFY (التحقق)

**الهدف:** التحقق من نجاح النشر

**Jobs:**
- `verify:health` - Health checks
- `verify:smoke` - Smoke tests

**Checks:**
- `/health` endpoint
- `/health/ready` endpoint
- Basic API functionality

### 🔟 CLEANUP (التنظيف)

**الهدف:** تنظيف الموارد المؤقتة

**Jobs:**
- `cleanup:old-images` - Remove old Docker images
- `cleanup:cache` - Clean cache (scheduled)

---

## 🔒 Security Scanning

### SAST (Static Application Security Testing)

**Tools:**
- Semgrep (primary)
- Bandit (Python-specific)
- PyLint Security

**Configuration:** `.gitlab/security-templates/sast.gitlab-ci.yml`

**Reports:** `sast-report.json`

### Dependency Scanning

**Tools:**
- Safety
- pip-audit
- Trivy
- OWASP Dependency Check
- Snyk (optional)

**Configuration:** `.gitlab/security-templates/dependency-scanning.gitlab-ci.yml`

**Reports:** `dependency-report.json`

### Container Scanning

**Tools:**
- Trivy (primary)
- Grype
- Snyk Container
- Clair
- Docker Bench Security
- Hadolint
- Dockle

**Configuration:** `.gitlab/security-templates/container-scanning.gitlab-ci.yml`

**Reports:** `container-report.json`

### Secret Detection

**Tools:**
- detect-secrets
- GitLeaks
- TruffleHog
- Trivy secrets
- Custom patterns

**Configuration:** `.gitlab/security-templates/secret-detection.gitlab-ci.yml`

**Reports:** `secrets-report.json`

---

## ☸️ Kubernetes Deployment

### Structure

```
infra/k8s/
├── base/                    # Base configurations
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   └── serviceaccount.yaml
└── overlays/               # Environment-specific
    ├── development/
    ├── staging/
    └── production/
```

### Kustomize

استخدام Kustomize لإدارة configurations:

```bash
# Preview changes
kubectl diff -k infra/k8s/overlays/development

# Apply
kubectl apply -k infra/k8s/overlays/development
```

### Features

- **Rolling Updates:** Zero-downtime deployments
- **HPA:** Auto-scaling (3-50 replicas)
- **PDB:** Pod Disruption Budget (min 2 available)
- **Health Probes:** Liveness, Readiness, Startup
- **Resource Limits:** CPU and memory limits
- **Security Context:** Non-root, read-only filesystem
- **Network Policies:** Ingress/Egress rules (production)

---

## ⚙️ الإعداد

### 1. GitLab Variables

قم بإعداد المتغيرات التالية في GitLab CI/CD Settings:

#### Required
```bash
CI_REGISTRY_USER          # GitLab registry username
CI_REGISTRY_PASSWORD      # GitLab registry password
KUBE_CONFIG              # Kubernetes config (base64)
```

#### Optional
```bash
SONAR_HOST_URL           # SonarQube URL
SONAR_TOKEN              # SonarQube token
SNYK_TOKEN               # Snyk token
METRICS_ENDPOINT         # Metrics collection endpoint
SLACK_WEBHOOK_URL        # Slack notifications
```

### 2. Kubernetes Setup

```bash
# Create namespaces
kubectl create namespace development
kubectl create namespace staging
kubectl create namespace production

# Create secrets
kubectl create secret generic cogniforge-secrets \
  --from-literal=DATABASE_URL="..." \
  --from-literal=SECRET_KEY="..." \
  --from-literal=OPENROUTER_API_KEY="..." \
  -n production

# Apply RBAC
kubectl apply -f infra/k8s/base/serviceaccount.yaml
```

### 3. Container Registry

```bash
# Login to GitLab registry
docker login registry.gitlab.com

# Test push
docker tag cogniforge:latest registry.gitlab.com/your-group/cogniforge:latest
docker push registry.gitlab.com/your-group/cogniforge:latest
```

---

## 🚀 الاستخدام

### Trigger Pipeline

```bash
# Push to main (automatic)
git push origin main

# Create tag (production deployment)
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Manual trigger
# Go to GitLab → CI/CD → Pipelines → Run Pipeline
```

### Deploy to Environment

```bash
# Development (automatic)
# Triggered on push to main

# Staging (manual)
# Go to pipeline → deploy:staging → Play button

# Production (manual)
# Go to pipeline → deploy:production → Play button
```

### Rollback

```bash
# Using script
./scripts/ci/rollback.sh production

# Or manually
kubectl rollout undo deployment/cogniforge -n production
```

### Monitor Deployment

```bash
# Watch rollout
kubectl rollout status deployment/cogniforge -n production

# Check pods
kubectl get pods -n production -l app=cogniforge

# View logs
kubectl logs -f deployment/cogniforge -n production

# Check events
kubectl get events -n production --sort-by='.lastTimestamp'
```

---

## 🔧 استكشاف الأخطاء

### Pipeline Fails at Build

**Problem:** Docker build fails

**Solution:**
```bash
# Check Dockerfile syntax
docker build -t test .

# Validate with hadolint
hadolint Dockerfile
```

### Pipeline Fails at Tests

**Problem:** Tests fail

**Solution:**
```bash
# Run tests locally
pytest tests/ -v

# Check coverage
pytest tests/ --cov=app --cov-report=term
```

### Pipeline Fails at Security

**Problem:** Security vulnerabilities found

**Solution:**
```bash
# Run security scans locally
semgrep --config=auto .
safety check
trivy image cogniforge:latest
```

### Deployment Fails

**Problem:** Kubernetes deployment fails

**Solution:**
```bash
# Check deployment status
kubectl describe deployment cogniforge -n production

# Check pod logs
kubectl logs -l app=cogniforge -n production

# Check events
kubectl get events -n production

# Rollback
./scripts/ci/rollback.sh production
```

### Health Checks Fail

**Problem:** Health checks timeout

**Solution:**
```bash
# Check service
kubectl get svc -n production

# Check ingress
kubectl get ingress -n production

# Test endpoint
curl https://cogniforge.com/health

# Check pod health
kubectl exec -it <pod-name> -n production -- curl localhost:8000/health
```

---

## 📈 Metrics & Monitoring

### DORA Metrics

Pipeline tracks:
- **Deployment Frequency:** How often we deploy
- **Lead Time:** Time from commit to production
- **MTTR:** Mean Time To Recovery
- **Change Failure Rate:** % of deployments causing failures

### Performance Metrics

- Response time (P50, P95, P99)
- Throughput (requests/second)
- Error rate
- Resource utilization (CPU, Memory)

### Dashboards

- GitLab CI/CD Analytics
- Kubernetes Dashboard
- Prometheus + Grafana
- SonarQube Dashboard

---

## 🎯 Best Practices

### 1. Commit Messages

```bash
# Good
feat: add user authentication
fix: resolve memory leak in chat service
docs: update deployment guide

# Bad
update
fix bug
changes
```

### 2. Branch Strategy

```
main          → Production-ready code
staging       → Pre-production testing
feature/*     → New features
fix/*         → Bug fixes
hotfix/*      → Emergency fixes
```

### 3. Testing

- Write tests before pushing
- Maintain 70%+ coverage
- Run tests locally first
- Use meaningful test names

### 4. Security

- Never commit secrets
- Use environment variables
- Scan dependencies regularly
- Keep images updated

### 5. Deployment

- Deploy to dev first
- Test in staging thoroughly
- Deploy to production during low-traffic hours
- Have rollback plan ready

---

## 📚 Resources

### Documentation
- [GitLab CI/CD Docs](https://docs.gitlab.com/ee/ci/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [Kustomize Docs](https://kustomize.io/)

### Tools
- [Semgrep](https://semgrep.dev/)
- [Trivy](https://trivy.dev/)
- [SonarQube](https://www.sonarqube.org/)
- [k6](https://k6.io/)

### Scripts
- `scripts/ci/deploy.sh` - Deployment script
- `scripts/ci/rollback.sh` - Rollback script
- `scripts/ci/health-check.sh` - Health check script
- `scripts/ci/smoke-test.sh` - Smoke test script
- `scripts/ci/validate-pipeline.sh` - Pipeline validation

---

## 🆘 Support

### Issues
- Create issue in GitLab
- Tag with `ci-cd` label
- Include pipeline URL

### Contact
- Tech Lead: tech-lead@example.com
- DevOps Team: devops@example.com
- Slack: #engineering-support

---

## 📝 Changelog

### v1.0.0 (2024-12-08)
- ✅ Initial superhuman CI/CD pipeline
- ✅ 10-stage pipeline
- ✅ Comprehensive security scanning
- ✅ Kubernetes integration
- ✅ Automated deployments
- ✅ DORA metrics tracking

---

**Built with ❤️ by the CogniForge Team**
