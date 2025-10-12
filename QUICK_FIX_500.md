# ⚡ سريع! حل خطأ 500 / Quick! Fix 500 Error

## 🎯 الحل السريع / Quick Solution

```bash
# الطريقة 1: استخدم السكريبت التلقائي / Method 1: Use automatic script
./quick_setup_ai.sh

# الطريقة 2: يدوياً / Method 2: Manual
cp .env.example .env
nano .env  # أضف OPENROUTER_API_KEY=sk-or-v1-your-key

# تحقق من التكوين / Verify
python check_api_config.py
```

---

## 📖 التوثيق الكامل / Full Documentation

للحصول على شرح مفصل وحلول متعددة، راجع:  
For detailed explanation and multiple solutions, see:

**[FIX_ANALYZE_PROJECT_500_ERROR.md](FIX_ANALYZE_PROJECT_500_ERROR.md)**

---

## ❓ الأسئلة الشائعة / FAQ

### س: لماذا أحصل على خطأ 500؟
**ج:** مفاتيح API غير مهيأة. استخدم `quick_setup_ai.sh` للإصلاح السريع.

### Q: Why am I getting 500 error?
**A:** API keys not configured. Use `quick_setup_ai.sh` for quick fix.

---

### س: أين أحصل على مفتاح API؟
**ج:** 
- OpenRouter (موصى به): https://openrouter.ai/keys
- OpenAI: https://platform.openai.com/api-keys

### Q: Where do I get an API key?
**A:**
- OpenRouter (recommended): https://openrouter.ai/keys
- OpenAI: https://platform.openai.com/api-keys

---

### س: هل أحتاج لإعادة تشغيل التطبيق؟
**ج:** نعم، بعد تعيين مفاتيح API.

### Q: Do I need to restart the app?
**A:** Yes, after setting API keys.

---

## 🛠️ أدوات مساعدة / Helper Tools

| الأداة / Tool | الوصف / Description |
|--------------|---------------------|
| `quick_setup_ai.sh` | إعداد تلقائي لمفاتيح API / Automatic API key setup |
| `check_api_config.py` | فحص التكوين الحالي / Check current configuration |
| `FIX_ANALYZE_PROJECT_500_ERROR.md` | التوثيق الكامل / Complete documentation |

---

Created: 2025-10-12  
Status: ✅ Active
