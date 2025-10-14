# 🔧 دليل استكشاف الأخطاء - GitHub Actions
# 🔧 GitHub Actions Troubleshooting Guide

<div align="center">

**مرجع سريع لحل مشاكل GitHub Actions**

**Quick Reference for Fixing GitHub Actions Issues**

</div>

---

## 🚨 حالة "Action Required"

### الأعراض | Symptoms:
- ❌ علامة حمراء على workflow
- ⚠️ GitHub يعرض "Action required"
- 🔴 الحالة غير واضحة

### الحل السريع | Quick Fix:

```bash
# 1. تأكد من أن كل step ينتهي بحالة واضحة
# Ensure every step ends with clear status

- name: Your Step
  run: |
    # Your commands here
    echo "✅ Step completed successfully"
    exit 0  # ← هذا مهم جداً | This is critical
```

```yaml
# 2. في الوظائف التي تستخدم if: always()
# For jobs using if: always()

- name: ✅ Verify Success
  run: |
    # Check dependent job results
    RESULT="${{ needs.job-name.result }}"
    
    if [ "$RESULT" = "failure" ]; then
      echo "❌ Job failed!"
      exit 1
    fi
    
    echo "✅ All jobs completed successfully!"
    exit 0
```

---

## 🔄 Workflows تتشغل باستمرار

### الأعراض | Symptoms:
- 🔄 Workflow يشغل نفسه
- ⚠️ تكرار لا نهائي
- 📊 استهلاك كبير للموارد

### الحل | Solution:

```yaml
# 1. لا تراقب workflow نفسه
# Don't monitor the workflow itself

on:
  workflow_run:
    workflows: ["Other Workflow 1", "Other Workflow 2"]  # ✅
    # NOT: ["This Workflow"]  # ❌
    types:
      - completed
```

```yaml
# 2. استخدم شروط واضحة
# Use clear conditions

jobs:
  monitor:
    if: |
      github.event.workflow_run.conclusion == 'failure' ||
      github.event_name == 'workflow_dispatch'
    # لا تستخدم: if: true  # ❌
```

---

## ⏭️ Jobs تتخطى (Skipped)

### الأعراض | Symptoms:
- ⏭️ بعض jobs تظهر "skipped"
- ⚠️ الشروط لا تتحقق
- 🔴 workflow غير مكتمل

### الحل | Solution:

```yaml
# 1. تحقق من الشروط
# Check conditions

jobs:
  job1:
    if: |
      github.event_name == 'push' ||
      github.event_name == 'pull_request' ||
      github.event_name == 'workflow_dispatch'
    # ✅ شروط شاملة | Comprehensive conditions
```

```yaml
# 2. استخدم needs بحذر
# Use needs carefully

jobs:
  job2:
    needs: job1
    if: always()  # ← يعمل حتى لو job1 فشل | Runs even if job1 fails
```

---

## ❌ Workflows تفشل بدون سبب واضح

### الأعراض | Symptoms:
- ❌ فشل مفاجئ
- 🤔 لا توجد رسائل خطأ واضحة
- 📝 logs غير مفيدة

### الحل | Solution:

```yaml
# 1. أضف logging مفصل
# Add detailed logging

- name: Debug Step
  run: |
    echo "════════════════════════════════════════"
    echo "🔍 Debugging Information:"
    echo "Event: ${{ github.event_name }}"
    echo "Ref: ${{ github.ref }}"
    echo "SHA: ${{ github.sha }}"
    echo "════════════════════════════════════════"
```

```yaml
# 2. استخدم set -x للتتبع
# Use set -x for tracing

- name: Your Step
  run: |
    set -x  # ← يعرض كل command | Shows every command
    # Your commands here
```

---

## 🔐 مشاكل Secrets والتوكنات

### الأعراض | Symptoms:
- 🔐 توكن غير صالح
- ❌ فشل المصادقة
- ⚠️ API errors

### الحل | Solution:

```yaml
# 1. استخدم fallback للتوكنات
# Use token fallback

- name: Setup Token
  env:
    AI_AGENT_TOKEN: ${{ secrets.AI_AGENT_TOKEN }}
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: |
    if [ -n "$AI_AGENT_TOKEN" ]; then
      TOKEN="$AI_AGENT_TOKEN"
      echo "✅ Using AI_AGENT_TOKEN"
    else
      TOKEN="$GITHUB_TOKEN"
      echo "⚠️  Using GITHUB_TOKEN (limited features)"
    fi
    
    echo "token=$TOKEN" >> $GITHUB_OUTPUT
```

```yaml
# 2. تحقق من صلاحية التوكن
# Validate token

- name: Validate Token
  run: |
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
      -H "Authorization: token $TOKEN" \
      https://api.github.com/user)
    
    if [ "$RESPONSE" = "200" ]; then
      echo "✅ Token is valid"
    else
      echo "❌ Token validation failed (HTTP $RESPONSE)"
      exit 1
    fi
```

---

## 📊 Monitoring Jobs تفشل

### الأعراض | Symptoms:
- 📊 وظائف المراقبة لا تعمل
- ⚠️ Reports غير موجودة
- 🔴 Dashboard قديم

### الحل | Solution:

```yaml
# 1. اجعل monitoring jobs قوية
# Make monitoring jobs robust

monitoring:
  runs-on: ubuntu-latest
  if: always()  # ← يعمل دائماً | Always runs
  needs: [job1, job2, job3]
  
  steps:
    - name: Check Results
      run: |
        # Check each job individually
        for job in job1 job2 job3; do
          RESULT="${{ needs.$job.result }}"
          echo "$job: $RESULT"
        done
        
        # Always succeed (monitoring shouldn't fail workflow)
        exit 0
```

---

## 🧪 Tests تفشل في CI لكن تعمل محلياً

### الأعراض | Symptoms:
- ✅ Tests تعمل محلياً
- ❌ تفشل في GitHub Actions
- 🤔 نفس الكود!

### الحل | Solution:

```yaml
# 1. تأكد من البيئة متطابقة
# Ensure environment matches

- name: Setup Environment
  env:
    FLASK_ENV: testing
    TESTING: "1"
    SECRET_KEY: test-secret-key
    DATABASE_URL: sqlite:///test.db  # ✅ Use SQLite for tests
  run: |
    pytest --verbose
```

```yaml
# 2. استخدم نفس إصدار Python
# Use same Python version

- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"  # ← حدد الإصدار بدقة | Specify exact version
    cache: 'pip'
```

---

## 🎯 Best Practices - أفضل الممارسات

### ✅ افعل | DO:

```yaml
# 1. استخدم exit codes صريحة
# Use explicit exit codes
- name: Step
  run: |
    # commands
    exit 0  # ✅ Success

# 2. أضف تأكيدات نجاح
# Add success confirmations
- name: ✅ Verify Success
  run: |
    echo "✅ Job completed successfully!"
    exit 0

# 3. استخدم if: always() بحذر
# Use if: always() carefully
final-job:
  if: always()
  needs: [job1, job2]
  steps:
    - name: Check Status
      run: |
        # Verify dependent jobs
        exit 0

# 4. أضف logging مفيد
# Add useful logging
- name: Step
  run: |
    echo "🔍 Starting process..."
    # commands
    echo "✅ Process completed!"
```

### ❌ لا تفعل | DON'T:

```yaml
# 1. لا تترك steps بدون exit code
# Don't leave steps without exit code
- name: Bad Step
  run: |
    echo "Done"
    # ❌ No exit code

# 2. لا تستخدم شروط معقدة جداً
# Don't use overly complex conditions
- name: Step
  if: |
    (github.event_name == 'push' && github.ref == 'refs/heads/main') ||
    (github.event_name == 'pull_request' && ...) ||
    ...  # ❌ Too complex

# 3. لا تراقب workflow نفسه
# Don't monitor the workflow itself
on:
  workflow_run:
    workflows: ["This Workflow"]  # ❌ Creates loop

# 4. لا تتجاهل الأخطاء
# Don't ignore errors
- name: Step
  run: |
    command || true  # ❌ Hides errors
```

---

## 🔧 أدوات مفيدة | Useful Tools

### 1. GitHub CLI

```bash
# فحص حالة workflows
# Check workflow status
gh workflow list

# عرض آخر runs
# View recent runs
gh run list --limit 10

# فحص run محدد
# Check specific run
gh run view <run-id>

# إعادة تشغيل failed run
# Rerun failed run
gh run rerun <run-id>
```

### 2. YAML Validation

```bash
# التحقق من صحة YAML
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.github/workflows/file.yml'))"

# أو | or
yamllint .github/workflows/
```

### 3. Local Testing

```bash
# اختبار workflows محلياً
# Test workflows locally
act -l  # List workflows
act -j job-name  # Run specific job
```

---

## 📚 مراجع إضافية | Additional References

### الملفات المهمة | Important Files:
- `SUPERHUMAN_ACTION_FIX_FINAL.md` - الحل الكامل | Complete solution
- `SUPERHUMAN_FIX_COMPLETE_AR.md` - الحل السابق | Previous solution
- `GITHUB_ACTIONS_FIX_COMPLETE_AR.md` - إصلاح سابق | Earlier fix

### الروابط المفيدة | Useful Links:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Expression Syntax](https://docs.github.com/en/actions/reference/context-and-expression-syntax-for-github-actions)

---

<div align="center">

## ✅ تذكر | Remember

**كل workflow يجب أن:**
1. ينتهي بـ `exit 0` صريح عند النجاح
2. يستخدم `exit 1` عند الفشل
3. يحتوي على logging واضح
4. يتعامل مع الأخطاء بذكاء

**Every workflow should:**
1. End with explicit `exit 0` on success
2. Use `exit 1` on failure
3. Have clear logging
4. Handle errors intelligently

---

**Built with ❤️ by Houssam Benmerah**

**🚀 Superhuman Quality - Surpassing All Tech Giants!**

</div>
