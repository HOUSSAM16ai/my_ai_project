# 🚀 GitLab CI/CD - دليل البدء السريع

## ⚡ البدء في 5 دقائق

### 1️⃣ إعداد GitLab Variables

انتقل إلى: **Settings → CI/CD → Variables**

```bash
# Required
CI_REGISTRY_USER=your-gitlab-username
CI_REGISTRY_PASSWORD=your-gitlab-token
KUBE_CONFIG=<base64-encoded-kubeconfig>

# Optional
SONAR_TOKEN=your-sonar-token
SNYK_TOKEN=your-snyk-token
```

### 2️⃣ إعداد Kubernetes

```bash
# Create namespaces
kubectl create namespace development
kubectl create namespace staging
kubectl create namespace production

# Create secrets
kubectl create secret generic cogniforge-secrets \
  --from-literal=DATABASE_URL="postgresql://..." \
  --from-literal=SECRET_KEY="your-secret-key" \
  -n production
```

### 3️⃣ Push الكود

```bash
git add .
git commit -m "feat: enable GitLab CI/CD"
git push origin main
```

### 4️⃣ مراقبة Pipeline

انتقل إلى: **CI/CD → Pipelines**

---

## 📊 Pipeline Stages

```
VALIDATE → BUILD → TEST → SECURITY → QUALITY → PACKAGE → DEPLOY → MONITOR → VERIFY → CLEANUP
```

### ⏱️ Expected Duration

- **Validate:** 2-3 min
- **Build:** 5-7 min
- **Test:** 8-10 min
- **Security:** 10-15 min
- **Quality:** 5-7 min
- **Package:** 2-3 min
- **Deploy:** 5-10 min
- **Monitor:** 2-3 min
- **Verify:** 2-3 min
- **Cleanup:** 1-2 min

**Total:** ~45-60 minutes

---

## 🎯 Common Tasks

### Deploy to Development

```bash
# Automatic on push to main
git push origin main
```

### Deploy to Staging

1. Go to pipeline
2. Find `deploy:staging` job
3. Click ▶️ Play button

### Deploy to Production

1. Create tag:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```
2. Go to pipeline
3. Find `deploy:production` job
4. Click ▶️ Play button

### Rollback

```bash
./scripts/ci/rollback.sh production
```

---

## 🔍 Monitoring

### Check Deployment Status

```bash
kubectl get pods -n production -l app=cogniforge
kubectl rollout status deployment/cogniforge -n production
```

### View Logs

```bash
kubectl logs -f deployment/cogniforge -n production
```

### Health Check

```bash
curl https://cogniforge.com/health
```

---

## ❌ Troubleshooting

### Pipeline Fails

1. Check job logs in GitLab
2. Run locally:
   ```bash
   # Validate
   ./scripts/ci/validate-pipeline.sh
   
   # Test
   pytest tests/ -v
   
   # Security
   semgrep --config=auto .
   ```

### Deployment Fails

```bash
# Check status
kubectl describe deployment cogniforge -n production

# Check events
kubectl get events -n production

# Rollback
./scripts/ci/rollback.sh production
```

---

## 📚 Next Steps

- Read full guide: [docs/gitlab-ci-cd-guide.md](gitlab-ci-cd-guide.md)
- Configure SonarQube
- Set up monitoring
- Enable notifications

---

## 🆘 Need Help?

- Slack: #engineering-support
- Email: devops@example.com
- Create issue with `ci-cd` label
