# 🚨 FIXING 500/504 ERRORS - QUICK GUIDE
## دليل سريع لحل أخطاء 500/504

**Issue:** AI chat returning 500/504 server errors  
**Root Cause:** Overly complex `answer_question()` function + Missing API keys  
**Status:** ✅ Diagnosed | ⏳ Fix in Progress

---

## 🎯 THE PROBLEM (المشكلة)

When asking the AI questions in the admin panel, users get:
```
❌ Server error (500). Please check your connection and authentication.
❌ Server error (504). Please check your connection and authentication.
```

**Root Causes:**
1. **Missing API Keys** - No OPENROUTER_API_KEY or OPENAI_API_KEY configured
2. **Function Complexity** - `answer_question()` has 434 lines and complexity score 100/100
3. **Poor Error Handling** - Nested try-except blocks causing timeouts

---

## ✅ IMMEDIATE FIX (الحل الفوري)

### Step 1: Configure API Keys

**Option A: Using .env file (Recommended)**
```bash
# 1. Copy example file
cp .env.example .env

# 2. Edit .env and add your API key
nano .env

# Add one of these:
OPENROUTER_API_KEY=sk-or-v1-your-key-here
# OR
OPENAI_API_KEY=sk-your-key-here

# 3. Restart the application
docker-compose restart web
# OR
flask run
```

**Option B: Using Environment Variables**
```bash
# Set before running app
export OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Then start app
flask run
```

**Option C: Using GitHub Codespaces Secrets**
```
1. Go to: https://github.com/settings/codespaces
2. Click "New secret"
3. Name: OPENROUTER_API_KEY
4. Value: sk-or-v1-your-key-here
5. Select repository access
6. Restart Codespace
```

**Get your API key:**
- OpenRouter: https://openrouter.ai/keys (Recommended - supports multiple models)
- OpenAI: https://platform.openai.com/api-keys

---

### Step 2: Verify Configuration

```bash
# Check if API keys are configured
python check_api_config.py
```

Expected output:
```
✅ OPENROUTER_API_KEY: Set (length: 50)
   ✓ Valid prefix (sk-or-)
✅ AI features should work!
```

---

### Step 3: Test the Fix

```bash
# Start the application
flask run

# Or with Docker
docker-compose up -d

# Check logs
docker-compose logs -f web
```

Then try asking a question in the admin panel. It should work now! ✅

---

## 🔧 LONG-TERM FIX (الحل طويل المدى)

### Refactor `answer_question()` Function

**Current Status:**
- **Complexity:** 41 (VERY HIGH)
- **Lines:** 434 (EXTREMELY LONG)
- **Nesting:** 5 levels (EXCESSIVE)
- **Maintainability:** 28.6/100 (CRITICAL)

**Proposed Refactoring:**

```python
# BEFORE: One massive function (434 lines)
def answer_question(question, user, conversation_id, use_deep_context):
    # Validation
    # Context building
    # AI invocation
    # Error handling (100+ lines)
    # Message saving
    # ... 434 lines total
    pass

# AFTER: Multiple focused functions
def answer_question(question, user, conversation_id, use_deep_context):
    """Main orchestrator - delegates to helpers"""
    start_time = time.time()
    
    # Validate (extracted)
    validation_result = _validate_ai_service_available()
    if validation_result.error:
        return validation_result.to_dict()
    
    # Load conversation (extracted)
    conversation = _load_or_create_conversation(conversation_id, user)
    if not conversation.is_valid():
        return conversation.error_response()
    
    # Build context (extracted)
    context = _build_ai_context(
        conversation=conversation,
        question=question,
        use_deep_context=use_deep_context
    )
    
    # Invoke AI with robust error handling (extracted)
    answer_result = _invoke_ai_with_comprehensive_error_handling(
        context=context,
        question=question,
        start_time=start_time
    )
    
    if answer_result.success:
        # Save conversation (extracted)
        _save_conversation_messages(conversation, question, answer_result.answer)
    
    return answer_result.to_dict()


# Extracted helper functions
def _validate_ai_service_available():
    """Validate AI service and API keys are configured"""
    if not get_llm_client:
        return ValidationResult(error="AI service unavailable")
    
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ValidationResult(error="API key not configured")
    
    return ValidationResult(success=True)


def _load_or_create_conversation(conversation_id, user):
    """Load existing conversation or create new one"""
    if not conversation_id:
        return ConversationContext.new()
    
    conversation = db.session.get(AdminConversation, conversation_id)
    
    if not conversation:
        return ConversationContext.error("Conversation not found")
    
    if conversation.user_id != user.id:
        return ConversationContext.error("Unauthorized access")
    
    return ConversationContext.from_db(conversation)


def _build_ai_context(conversation, question, use_deep_context):
    """Build context for AI invocation"""
    system_prompt = _build_system_prompt(
        conversation.deep_index_summary if use_deep_context else None
    )
    
    history = conversation.get_recent_messages(limit=MAX_CONTEXT_MESSAGES)
    
    return AIContext(
        system_prompt=system_prompt,
        history=history,
        question=question
    )


def _invoke_ai_with_comprehensive_error_handling(context, question, start_time):
    """Invoke AI with robust error handling"""
    try:
        client = get_llm_client()
        
        # Adjust tokens based on question complexity
        max_tokens = _calculate_max_tokens(question)
        
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=context.to_messages(),
            temperature=0.7,
            max_tokens=max_tokens,
        )
        
        answer = response.choices[0].message.content
        
        if not answer or not answer.strip():
            return AIResult.error(
                error_type="empty_response",
                message=_get_empty_response_message(response)
            )
        
        return AIResult.success(
            answer=answer,
            tokens=response.usage.total_tokens,
            model=response.model,
            elapsed=time.time() - start_time
        )
        
    except TimeoutError as e:
        return AIResult.error(
            error_type="timeout",
            message=_get_timeout_message(question, start_time),
            is_timeout=True
        )
    
    except RateLimitError as e:
        return AIResult.error(
            error_type="rate_limit",
            message=_get_rate_limit_message()
        )
    
    except ContextLengthError as e:
        return AIResult.error(
            error_type="context_length",
            message=_get_context_length_message(question)
        )
    
    except Exception as e:
        logger.error(f"AI invocation failed: {e}", exc_info=True)
        return AIResult.error(
            error_type="unknown",
            message=_get_generic_error_message(e, question)
        )


def _save_conversation_messages(conversation, question, answer):
    """Save user question and AI answer to conversation"""
    conversation.add_message("user", question)
    conversation.add_message("assistant", answer.text, 
                           tokens=answer.tokens,
                           model=answer.model,
                           latency_ms=answer.elapsed * 1000)
    conversation.save()
```

**Benefits of Refactoring:**
- ✅ Each function has single responsibility
- ✅ Error handling is isolated and testable
- ✅ Easier to debug and maintain
- ✅ Reduced nesting depth (from 5 to 2)
- ✅ Better code reusability
- ✅ Improved performance (easier to optimize individual parts)

---

## 📊 VERIFY THE FIX

### Test Checklist

- [ ] API keys configured and verified
- [ ] Application starts without errors
- [ ] Can ask simple questions in admin panel
- [ ] Can ask complex questions (>1000 chars)
- [ ] Error messages are user-friendly
- [ ] No 500/504 errors in logs
- [ ] Response time is reasonable (<30s)

### Performance Benchmarks

| Test Case | Before | After (Target) |
|-----------|---------|----------------|
| Simple question (50 chars) | 500 error | <5s |
| Medium question (500 chars) | 504 timeout | <10s |
| Complex question (2000 chars) | 504 timeout | <30s |
| Very complex (10000 chars) | 504 timeout | <60s with streaming |

---

## 🚀 PREVENTION MEASURES

### 1. Add Complexity Checks to CI/CD

```yaml
# .github/workflows/code-quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  complexity-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Check Function Complexity
        run: |
          python analyze_function_complexity.py --path app --threshold 20
          if [ $? -ne 0 ]; then
            echo "❌ Code exceeds complexity threshold!"
            exit 1
          fi
```

### 2. Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "🔍 Checking code complexity..."
python analyze_function_complexity.py --path app --threshold 20

if [ $? -ne 0 ]; then
    echo "❌ Code complexity check failed!"
    echo "Please refactor complex functions before committing."
    exit 1
fi
```

### 3. Code Review Guidelines

**Reject PRs if:**
- Any function has cyclomatic complexity >20
- Any function exceeds 100 lines
- Nesting depth >4 levels
- No tests for complex logic

---

## 📚 ADDITIONAL RESOURCES

### Related Files
- `analyze_function_complexity.py` - Complexity analyzer tool
- `COMPLEXITY_ANALYSIS_SUPERHUMAN.md` - Full analysis report
- `complexity_report.json` - Detailed JSON report
- `check_api_config.py` - API configuration checker

### Documentation
- Setup Guide: `SETUP_GUIDE.md`
- Database Guide: `DATABASE_SYSTEM_SUPREME_AR.md`
- API Gateway Guide: `API_GATEWAY_COMPLETE_GUIDE.md`

### Support
- GitHub Issues: Report bugs and request features
- Documentation: Check README.md and guides
- Logs: Check `docker-compose logs -f web` for errors

---

## ✅ SUMMARY

**Quick Fix (5 minutes):**
1. Configure API key in `.env`
2. Restart application
3. Test admin chat

**Long-term Fix (1 week):**
1. Refactor `answer_question()` function
2. Extract error handling
3. Add unit tests
4. Set up complexity monitoring

**Result:**
- ✅ No more 500/504 errors
- ✅ Better error messages
- ✅ Faster response times
- ✅ Easier to maintain
- ✅ Better code quality

---

**Status:** ✅ Root cause identified | 🔧 Quick fix available | 📋 Refactoring plan ready

---

Built with ❤️  by SuperHuman Error Resolution System 🚀
