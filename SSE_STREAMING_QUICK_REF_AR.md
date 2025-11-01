# دليل البث الخارق (SSE Streaming) - مرجع سريع 🌊

## المشكلة الأصلية

**الخطأ**: "Stream connection error" بعد أول سؤال

**السبب**:
1. تهيئة SSE غير صحيحة
2. تخزين مؤقت من Proxy
3. غياب Heartbeats
4. عدم تفريغ المخزن (flush)
5. قارئ Frontend لا يتعامل مع UTF-8 متعدد البايتات

## الحل الخارق ✨

### الخادم (Backend)

#### ملف جديد: `app/api/stream_routes.py`
```python
# نقطة نهاية SSE خارقة مع:
- تنسيق أحداث SSE صحيح
- نبضات قلب كل 20 ثانية (ping)
- معالجة أخطاء شاملة
- دعم إعادة الاتصال
- أحداث تقدم للمهام (صور، فيديو، PDF)
```

#### تحديث: `app/admin/routes.py`
```python
# إضافة رؤوس HTTP صحيحة:
headers = {
    "Cache-Control": "no-cache, no-transform",  # منع التخزين
    "Content-Type": "text/event-stream; charset=utf-8",
    "X-Accel-Buffering": "no",  # تعطيل تخزين NGINX
}
```

### الواجهة (Frontend)

#### ملف جديد: `app/static/js/useSSE.js`

**SSEConsumer - مستهلك خارق للأحداث:**
```javascript
const consumer = new SSEConsumer('/api/v1/stream/chat?q=سؤالي');

consumer.onDelta((data) => {
  // إضافة النص تدريجيًا
  displayText += data.text;
});

consumer.onComplete(() => {
  console.log('اكتمل البث! ✅');
});

consumer.connect();
```

**المميزات الخارقة:**
- ✅ **TextDecoder مع stream=true** - يتعامل مع UTF-8 العربي بشكل صحيح
- ✅ **تحليل سطر بسطر** - يحترم حدود SSE (\n\n)
- ✅ **إعادة اتصال تلقائية** - يستخدم Last-Event-ID
- ✅ **استرجاع من الأخطاء** - محاولة مجددة مع تأخير تصاعدي

**AdaptiveTypewriter - آلة كاتبة ذكية:**
```javascript
const typewriter = new AdaptiveTypewriter(element, {
  baseDelayMs: 8,                    // سرعة أساسية
  punctuationDelayMultiplier: 10,    // أبطأ عند النقاط
  commaDelayMultiplier: 4,           // متوسط عند الفواصل
  charsPerStep: 4                    // أحرف لكل دفعة
});

typewriter.append('مرحباً بك!');
```

**التأثير**: سرعة متكيفة حسب علامات الوقف لقراءة أفضل!

### البنية التحتية (Infrastructure)

#### ملف: `infra/nginx/sse.conf`

```nginx
# إعدادات NGINX الحرجة للبث:
proxy_buffering off;          # حرج: تعطيل التخزين المؤقت
proxy_cache off;              # لا تخزين
gzip off;                     # لا ضغط
proxy_read_timeout 3600s;     # مهلة ساعة
proxy_http_version 1.1;       # HTTP/1.1 مطلوب
```

**الاستخدام:**
```nginx
location /api/v1/stream/ {
    include /path/to/infra/nginx/sse.conf;
    proxy_pass http://backend;
}
```

## أنواع الأحداث

| الحدث | البيانات | الغرض |
|-------|----------|--------|
| `hello` | `{ts, model}` | الاتصال تم |
| `start` | `{status}` | بدأ البث |
| `delta` | `{text}` | جزء من المحتوى |
| `done` | `{reason}` | انتهى البث |
| `error` | `{message}` | حدث خطأ |
| `ping` | `"🔧"` | نبضة قلب |

## الاستخدام السريع

### 1. تشغيل محليًا
```bash
cd /home/runner/work/my_ai_project/my_ai_project
flask run
```

### 2. اختبار SSE
```bash
curl -N "http://localhost:5000/api/v1/stream/chat?q=مرحبا"
```

### 3. فتح المتصفح
```
http://localhost:5000/admin/dashboard
```

## حل المشاكل الشائعة

### المشكلة: "Stream connection error"

**الحلول:**
1. ✅ تحقق من إعدادات NGINX: `proxy_buffering off`
2. ✅ تحقق من الرؤوس: `Content-Type: text/event-stream`
3. ✅ تحقق من المهلات: يجب أن تكون ≥120 ثانية
4. ✅ اختبر مباشرة: `curl -N` لتجاوز NGINX

### المشكلة: البث يتوقف في المنتصف

**الحلول:**
1. ✅ تفعيل النبضات: موجودة (كل 20 ثانية)
2. ✅ تحقق من سجلات الخادم
3. ✅ زيادة المهلات
4. ✅ تفعيل إعادة الاتصال: `reconnect: true`

### المشكلة: أحرف UTF-8 مشوهة

**الحلول:**
1. ✅ استخدم TextDecoder: موجود مع `stream: true`
2. ✅ تعيين charset: الخادم يرسل `charset=utf-8`
3. ✅ تحقق من الترميز: السيرفر وقاعدة البيانات UTF-8

## النشر على الإنتاج

### مع NGINX
```bash
# 1. انسخ الإعدادات
sudo cp infra/nginx/sse.conf /etc/nginx/conf.d/

# 2. اختبر
sudo nginx -t

# 3. أعد التحميل
sudo systemctl reload nginx
```

### مع Cloudflare
```
⚠️ تحذير: Cloudflare قد يتداخل مع SSE

الحل:
1. أنشئ نطاق فرعي: stream.yourdomain.com
2. وجهه مباشرة للسيرفر (تجاوز Cloudflare)
3. استخدمه لنقاط نهاية SSE فقط
```

### مع Vercel
```
⚠️ تحذير: Vercel Serverless له مهلة 10-60 ثانية

الحل:
1. استخدم Edge Runtime
2. أو انقل البث لخدمة خارجية (Railway, Fly.io)
```

## الأداء الأمثل

### الخادم
```python
# حجم جزء مثالي: 3-8 كلمات
OPTIMAL_CHUNK_SIZE = 6

# أرسل عند علامات الوقف
if token_count % 6 == 0 or token[-1] in ".!?,;:":
    yield sse_event("delta", {"text": buffer})
```

### الواجهة
```javascript
// سرعات آلة الكاتبة
baseDelayMs: 5-10,              // نص عادي
punctuationDelayMultiplier: 8,   // أبطأ عند الجمل
commaDelayMultiplier: 3,         // متوسط عند الفواصل
```

## الميزات المستقبلية 🚀

### المرحلة 2: WebSocket Fallback
```javascript
// تبديل تلقائي لـ WebSocket
if (!window.EventSource) {
  consumer = new WebSocketConsumer(url);
}
```

### المرحلة 3: الوسائط المتعددة

**توليد الصور:**
```javascript
consumer.onProgress((data) => {
  progressBar.style.width = data.pct + '%';
});

consumer.onPreview((data) => {
  img.src = data.url;  // معاينة تدريجية
});
```

**بث الصوت (TTS):**
```javascript
const audioStream = new AudioStreamConsumer('/api/v1/stream/tts');
audioStream.onChunk((audioData) => {
  playAudio(audioData);
});
```

**فيديو/AR/3D:**
- WebRTC للفيديو الحي
- three.js/Babylon.js لنماذج 3D
- WebXR لتجارب AR

## الأمان

### التحقق من المدخلات
```python
MAX_QUESTION_LENGTH = 10000
if len(question) > MAX_QUESTION_LENGTH:
    yield sse_event("error", {"message": "السؤال طويل جدًا"})
```

### تحديد المعدل
```python
@limiter.limit("5 per minute")
@bp.route("/chat")
def sse_chat():
    # 5 طلبات كحد أقصى في الدقيقة
```

### المصادقة
```python
@bp.route("/chat")
@login_required
def sse_chat():
    # المستخدمون المسجلون فقط
```

## المراقبة

### المقاييس الرئيسية
```python
- عدد اتصالات SSE النشطة
- متوسط مدة البث
- معدل الأخطاء
- معدل انقطاع النبض
- محاولات إعادة الاتصال
- البايتات المنقولة
```

## الخلاصة

هذا التنفيذ يوفر:
- ✅ **بث SSE قوي** يحل مشكلة "Stream connection error"
- ✅ **دعم UTF-8 متعدد البايتات** للنصوص العربية
- ✅ **إعادة اتصال واسترجاع من الأخطاء** للموثوقية
- ✅ **تجربة مستخدم سلسة** مع آلة كاتبة ذكية
- ✅ **جاهز للإنتاج** مع أدلة NGINX، Cloudflare، Vercel
- ✅ **جاهز للمستقبل** لبث الوسائط المتعددة

**مبني بـ ❤️ من حسام بن مراح**

---

للأسئلة أو المشاكل، راجع:
- الخادم: `app/api/stream_routes.py`
- الواجهة: `app/static/js/useSSE.js`
- البنية التحتية: `infra/nginx/sse.conf`
- الدليل الكامل: `SSE_STREAMING_GUIDE.md`
