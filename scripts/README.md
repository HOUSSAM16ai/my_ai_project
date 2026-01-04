# ⚡ Quick Start: Structure Protection System

## 🚨 Important for All Developers

This project has a **critical protection system** to prevent catastrophic structure errors.

هذا المشروع لديه **نظام حماية حرج** لمنع أخطاء البنية الكارثية.

---

## ✅ Before Every Commit - قبل كل Commit

Run this command:
```bash
./scripts/pre-commit-validation.sh
```

Or manually:
```bash
python scripts/validate_structure.py
pytest tests/integration/test_chat_e2e.py::TestServiceMethodsAccessibility -v
```

**If it fails, DO NOT commit until you fix the errors.**

**إذا فشل، لا تقم بالـ commit حتى تصلح الأخطاء.**

---

## 📖 Full Documentation

- **Complete Guide:** [`PREVENTION_GUIDE.md`](../PREVENTION_GUIDE.md)
- **System Documentation:** [`STRUCTURE_PROTECTION_SYSTEM.md`](../STRUCTURE_PROTECTION_SYSTEM.md)
- **Resolution Summary:** [`CATASTROPHE_RESOLUTION_SUMMARY.md`](../CATASTROPHE_RESOLUTION_SUMMARY.md)

---

## 🔧 Common Issues & Solutions

### Issue: "Method appears to be OUTSIDE the class"

**Solution:**
```python
# ❌ WRONG - Method outside class
class MyService:
    def __init__(self):
        pass

async def my_method(self):  # WRONG! Not inside class
    pass

# ✅ CORRECT - Method inside class
class MyService:
    def __init__(self):
        pass
    
    async def my_method(self):  # ✅ Correct indentation
        pass
```

### Issue: Tests fail with AttributeError

**Solution:**
Check that all public methods are inside the class, not at module level.

---

## 🎯 Remember

1. ✅ Always run validation before commit
2. ✅ All public methods must be inside the class
3. ✅ Use 4 spaces for indentation
4. ✅ Check GitHub Actions results

**This system prevents production catastrophes!**

**هذا النظام يمنع كوارث الإنتاج!**
