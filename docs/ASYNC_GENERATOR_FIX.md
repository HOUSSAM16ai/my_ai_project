# Async Generator Usage Guide - حل مشكلة await على async generator

## المشكلة (The Problem)

```
TypeError: object async_generator can't be used in 'await' expression
```

هذا الخطأ يحدث عندما تحاول استخدام `await` على دالة من نوع async generator (دالة `async def` تحتوي على `yield`).

## السبب الجذري (Root Cause)

في Python، عندما تقوم باستدعاء دالة async generator، فإنها تُرجع كائن async generator مباشرة - **لا تحتاج إلى await**. الاستخدام الصحيح هو التكرار عليها باستخدام `async for`.

### مثال على الخطأ (Wrong Example)

```python
async def my_generator() -> AsyncGenerator[str, None]:
    yield "chunk 1"
    yield "chunk 2"

# ❌ خطأ - محاولة await على async generator
async def wrong_usage():
    result = await my_generator()  # TypeError!
```

### الطريقة الصحيحة (Correct Example)

```python
async def my_generator() -> AsyncGenerator[str, None]:
    yield "chunk 1"
    yield "chunk 2"

# ✅ صح - استخدام async for للتكرار
async def correct_usage():
    async for chunk in my_generator():
        print(chunk)
```

## الحل المطبق (The Fix Applied)

### في `app/core/patterns/strategy.py`

تم تحسين دالة `StrategyRegistry.execute()` للتعامل بشكل صحيح مع جميع أنواع النتائج:

```python
async def execute(self, context: TInput) -> TOutput | None:
    # تنفيذ الاستراتيجية بدون await (لأنها قد تكون async generator)
    result = strategy.execute(context)
    
    # 1. التحقق إذا كانت async generator - إرجاع مباشر
    if inspect.isasyncgen(result):
        return result  # ✅ لا نستخدم await!
    
    # 2. إذا كانت coroutine - await ثم تحقق مرة أخرى
    if inspect.iscoroutine(result):
        result = await result
        # قد تُرجع الـ coroutine async generator بعد await
        if inspect.isasyncgen(result):
            return result
    
    # 3. قيمة عادية
    return result
```

## الأنماط المدعومة (Supported Patterns)

### 1. Async Generator المباشر (Direct Async Generator)

```python
class MyStrategy(Strategy[Context, AsyncGenerator[str, None]]):
    async def execute(self, context) -> AsyncGenerator[str, None]:
        yield "chunk 1"
        yield "chunk 2"
```

### 2. Async Generator المتداخل (Nested Async Generator)

```python
class MyStrategy(Strategy[Context, AsyncGenerator[str, None]]):
    async def _inner_gen(self) -> AsyncGenerator[str, None]:
        yield "inner 1"
        yield "inner 2"
    
    async def execute(self, context) -> AsyncGenerator[str, None]:
        # ✅ الطريقة الصحيحة: iterate and re-yield
        async for item in self._inner_gen():
            yield f"wrapped: {item}"
```

### 3. Coroutine عادي (Regular Coroutine)

```python
class MyStrategy(Strategy[Context, str]):
    async def execute(self, context) -> str:
        return "simple result"
```

## قواعد الاستخدام (Usage Rules)

### ✅ افعل (DO)

1. **استخدم yield في async generators:**
   ```python
   async def execute(...) -> AsyncGenerator[str, None]:
       yield "data"
   ```

2. **كرر على async generators بـ async for:**
   ```python
   async for chunk in my_generator():
       process(chunk)
   ```

3. **إذا أردت تغليف async generator، استخدم yield:**
   ```python
   async def wrapper() -> AsyncGenerator[str, None]:
       async for item in other_generator():
           yield item
   ```

### ❌ لا تفعل (DON'T)

1. **لا تستخدم await على async generator مباشرة:**
   ```python
   # ❌ خطأ
   result = await my_generator()
   ```

2. **لا تُرجع async generator من coroutine بدون yield:**
   ```python
   # ❌ خطأ
   async def wrapper() -> AsyncGenerator[str, None]:
       return my_generator()  # سيسبب مشاكل!
   ```

3. **لا تخلط بين return و yield في نفس الدالة:**
   ```python
   # ❌ خطأ
   async def confused():
       if condition:
           return "value"  # لا يمكن الجمع
       else:
           yield "chunk"   # بين return و yield
   ```

## التحقق من النوع (Type Checking)

يمكنك استخدام `inspect` module للتحقق من نوع الكائن:

```python
import inspect

# التحقق من async generator
if inspect.isasyncgen(obj):
    async for item in obj:
        process(item)

# التحقق من coroutine
if inspect.iscoroutine(obj):
    result = await obj
```

## الاختبار (Testing)

تم إضافة اختبارات شاملة في `tests/unit/test_async_generator_fix.py`:

```bash
# تشغيل الاختبارات
python tests/unit/test_async_generator_fix.py
```

## الأمثلة العملية (Practical Examples)

### مثال 1: Chat Streaming Handler

```python
class ChatHandler(Strategy[ChatContext, AsyncGenerator[str, None]]):
    async def execute(self, context) -> AsyncGenerator[str, None]:
        async for chunk in context.ai_client.stream_chat(messages):
            if chunk:
                yield chunk
```

### مثال 2: File Reading with Progress

```python
class FileReadHandler(Strategy[FileContext, AsyncGenerator[str, None]]):
    async def execute(self, context) -> AsyncGenerator[str, None]:
        with open(context.path) as f:
            for line in f:
                yield line
                # Optional: add progress reporting
                await asyncio.sleep(0)  # Yield control
```

### مثال 3: Multi-Source Streaming

```python
class MultiStreamHandler(Strategy[Context, AsyncGenerator[str, None]]):
    async def execute(self, context) -> AsyncGenerator[str, None]:
        # Stream from multiple sources
        async for chunk in source1():
            yield f"Source1: {chunk}"
        
        async for chunk in source2():
            yield f"Source2: {chunk}"
```

## المراجع (References)

- [PEP 525 – Asynchronous Generators](https://peps.python.org/pep-0525/)
- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [inspect module documentation](https://docs.python.org/3/library/inspect.html)

## الملخص (Summary)

| الحالة | الاستخدام الصحيح | الاستخدام الخاطئ |
|--------|------------------|-------------------|
| Async Generator | `async for x in gen()` | `await gen()` ❌ |
| Coroutine | `await coro()` | `for x in coro()` ❌ |
| Wrapping Generator | `async for x in gen(): yield x` | `return gen()` ❌ |

---

**التاريخ:** 2026-01-01  
**الحالة:** ✅ تم الحل (Resolved)  
**المطور:** GitHub Copilot + Human Review
