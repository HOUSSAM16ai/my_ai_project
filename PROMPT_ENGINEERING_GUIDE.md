# 🎯 Superhuman Prompt Engineering System

## النظام الخارق لهندسة Prompts - دليل شامل

[![Status](https://img.shields.io/badge/Status-Production%20Ready-success)]()
[![Version](https://img.shields.io/badge/Version-1.0.0-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

---

## 📖 Overview | نظرة عامة

This is the **most advanced prompt engineering system** designed specifically for the CogniForge project. It generates professional, context-aware prompts that understand your project deeply - every comma and its relationship to every other comma in the codebase.

هذا هو **أكثر نظام متقدم لهندسة Prompts** مصمم خصيصاً لمشروع CogniForge. يولد prompts احترافية مدركة للسياق تفهم مشروعك بعمق - كل فاصلة وعلاقتها بكل فاصلة أخرى في الكود.

### 🌟 Key Features | المميزات الرئيسية

1. **🧠 Deep Project Understanding**
   - Analyzes entire codebase structure
   - Understands relationships between components
   - Maintains project context across prompts
   - يحلل بنية الكود بالكامل
   - يفهم العلاقات بين المكونات
   - يحافظ على سياق المشروع

2. **🔍 Advanced RAG (Retrieval-Augmented Generation)**
   - Retrieves relevant code snippets
   - Contextual documentation lookup
   - Semantic search capabilities
   - استرجاع مقتطفات الكود ذات الصلة
   - البحث الدلالي المتقدم

3. **📝 Meta-Prompt Templates**
   - Dynamic variable substitution
   - Project-specific customization
   - Reusable template library
   - قوالب ديناميكية قابلة للتخصيص
   - مكتبة قوالب قابلة لإعادة الاستخدام

4. **🎓 Few-Shot Learning**
   - Learns from project examples
   - Adapts to coding patterns
   - Improves over time
   - يتعلم من أمثلة المشروع
   - يتكيف مع أنماط البرمجة

5. **⭐ RLHF (Reinforcement Learning from Human Feedback)**
   - Rate generated prompts
   - Continuous improvement
   - Success rate tracking
   - تقييم Prompts المولدة
   - تحسين مستمر

---

## 🚀 Quick Start | البداية السريعة

### Installation | التثبيت

The feature is already integrated into CogniForge. Just make sure you have:

```bash
# 1. Apply database migrations
flask db upgrade

# 2. Seed default templates (optional but recommended)
python seed_prompt_templates.py

# 3. Verify installation
flask mindgate prompt-templates
```

### First Prompt Generation | أول توليد لـ Prompt

#### Via Web UI | عبر واجهة الويب

1. Navigate to Admin Dashboard: `/admin/dashboard`
2. Click on "🎯 Prompt Engineering" in sidebar
3. Select prompt type (e.g., "Code Generation")
4. Enter your description
5. Click "توليد Prompt" (Generate Prompt)
6. Rate the result to improve the system!

#### Via CLI | عبر سطر الأوامر

```bash
# Generate a code generation prompt
flask mindgate prompt-generate "create a REST API endpoint for user authentication"

# Generate with specific type
flask mindgate prompt-generate "write tests for database service" --type testing

# Generate documentation prompt
flask mindgate prompt-generate "document the admin panel API" --type documentation

# Disable RAG for faster generation
flask mindgate prompt-generate "simple prompt" --no-rag
```

---

## 📚 Usage Guide | دليل الاستخدام

### Prompt Types | أنواع Prompts

The system supports multiple prompt types, each optimized for specific tasks:

| Type | Description | Best For |
|------|-------------|----------|
| `general` | General-purpose prompts | Any task |
| `code_generation` | Code creation prompts | Creating new features, APIs, functions |
| `documentation` | Documentation prompts | Writing docs, README files, API specs |
| `architecture` | System design prompts | Designing architecture, planning systems |
| `testing` | Test generation prompts | Writing unit tests, integration tests |
| `refactoring` | Code improvement prompts | Refactoring, optimization, cleanup |

### Templates | القوالب

#### Default Templates | القوالب الافتراضية

The system comes with 5 professionally crafted templates:

1. **Code Generation Master** - For generating production-ready code
2. **Documentation Expert** - For comprehensive documentation
3. **Architecture Designer** - For system architecture design
4. **Testing Maestro** - For comprehensive test suites
5. **Refactoring Guru** - For code quality improvement

#### Creating Custom Templates | إنشاء قوالب مخصصة

**Via API:**

```python
POST /admin/api/prompt-engineering/templates
Content-Type: application/json

{
  "name": "My Custom Template",
  "description": "Description of what this template does",
  "category": "code_generation",
  "template_content": "You are working on {project_name}...",
  "variables": [
    {"name": "project_name", "description": "Project name"},
    {"name": "user_description", "description": "User request"}
  ],
  "few_shot_examples": [
    {
      "description": "Example task",
      "prompt": "Example prompt",
      "result": "Expected outcome"
    }
  ]
}
```

**Via Python:**

```python
from app.services.prompt_engineering_service import get_prompt_engineering_service

service = get_prompt_engineering_service()
result = service.create_template(
    name="Custom Template",
    template_content="Template with {variables}...",
    user=current_user,
    category="general"
)
```

### RAG Configuration | إعدادات RAG

The RAG system retrieves relevant context from your project:

```python
# Enable RAG (default)
result = service.generate_prompt(
    user_description="Your request",
    user=user,
    use_rag=True  # Will retrieve relevant snippets
)

# Disable RAG for faster generation
result = service.generate_prompt(
    user_description="Your request",
    user=user,
    use_rag=False  # Faster, but less context-aware
)
```

**Environment Variables:**

```bash
# Maximum context snippets to retrieve
PROMPT_ENG_MAX_CONTEXT_SNIPPETS=5

# Maximum few-shot examples
PROMPT_ENG_MAX_FEW_SHOT_EXAMPLES=3

# Enable/disable RAG
PROMPT_ENG_ENABLE_RAG=1
```

### Rating Prompts (RLHF) | تقييم Prompts

Help improve the system by rating generated prompts:

**Via Web UI:**
- Click the star buttons (⭐) below generated prompts
- Rate from 1 to 5 stars
- Optionally add feedback text

**Via CLI:**

```bash
flask mindgate prompt-rate 123 --rating 5 --feedback "Excellent prompt!"
```

**Via API:**

```python
POST /admin/api/prompt-engineering/rate/123
Content-Type: application/json

{
  "rating": 5,
  "feedback": "Perfect prompt, exactly what I needed!"
}
```

---

## 🏗️ Architecture | البنية المعمارية

### System Components | مكونات النظام

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│  ┌──────────────┐         ┌──────────────┐             │
│  │  Web UI      │         │   CLI        │             │
│  │  (Dashboard) │         │  (Mindgate)  │             │
│  └──────┬───────┘         └──────┬───────┘             │
└─────────┼────────────────────────┼─────────────────────┘
          │                        │
          ▼                        ▼
┌─────────────────────────────────────────────────────────┐
│                   API Layer                              │
│     /admin/api/prompt-engineering/generate              │
│     /admin/api/prompt-engineering/templates             │
│     /admin/api/prompt-engineering/rate/<id>             │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           Prompt Engineering Service                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │  1. Project Context Builder                      │   │
│  │     - Index project files                        │   │
│  │     - Extract metadata                           │   │
│  │     - Cache context (5min TTL)                   │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  2. RAG Retrieval Engine                         │   │
│  │     - Keyword extraction                         │   │
│  │     - Semantic search                            │   │
│  │     - Relevance ranking                          │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  3. Few-Shot Example Builder                     │   │
│  │     - Load from templates                        │   │
│  │     - Generate dynamic examples                  │   │
│  │     - Limit to max count                         │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  4. Meta-Prompt Constructor                      │   │
│  │     - Variable substitution                      │   │
│  │     - Context injection                          │   │
│  │     - Template rendering                         │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  5. LLM Generator                                │   │
│  │     - Send to OpenRouter                         │   │
│  │     - Parse response                             │   │
│  │     - Handle errors                              │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                Database Layer                            │
│  ┌──────────────────┐    ┌──────────────────┐          │
│  │ prompt_templates │    │ generated_prompts│          │
│  │  - name          │    │  - description   │          │
│  │  - content       │    │  - prompt        │          │
│  │  - category      │    │  - rating        │          │
│  │  - examples      │    │  - feedback      │          │
│  │  - usage_count   │    │  - metadata      │          │
│  └──────────────────┘    └──────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

### Data Flow | تدفق البيانات

1. **User Input** → User enters description
2. **Context Building** → System indexes project
3. **RAG Retrieval** → Relevant snippets retrieved
4. **Template Selection** → Appropriate template chosen
5. **Meta-Prompt Construction** → Variables injected
6. **LLM Generation** → Final prompt generated
7. **Storage** → Saved to database
8. **RLHF Feedback** → User rates prompt

---

## 🔧 API Reference | مرجع API

### Generate Prompt

**Endpoint:** `POST /admin/api/prompt-engineering/generate`

**Request:**
```json
{
  "description": "Create a Flask route for user login",
  "prompt_type": "code_generation",
  "template_id": 1,  // optional
  "conversation_id": 123,  // optional
  "use_rag": true
}
```

**Response:**
```json
{
  "status": "success",
  "prompt_id": 456,
  "generated_prompt": "You are a senior Flask developer...",
  "meta_prompt": "Internal meta-prompt used...",
  "context_snippets": [...],
  "few_shot_examples": [...],
  "template_name": "Code Generation Master",
  "metadata": {
    "model": "anthropic/claude-3.7-sonnet:thinking",
    "elapsed_seconds": 3.2,
    "context_chunks": 5,
    "few_shot_count": 2
  }
}
```

### List Templates

**Endpoint:** `GET /admin/api/prompt-engineering/templates`

**Query Parameters:**
- `category` - Filter by category
- `active_only` - Show only active templates (default: true)

**Response:**
```json
{
  "status": "success",
  "templates": [
    {
      "id": 1,
      "name": "Code Generation Master",
      "category": "code_generation",
      "usage_count": 42,
      "success_rate": 95.5
    }
  ],
  "count": 1
}
```

### Rate Prompt

**Endpoint:** `POST /admin/api/prompt-engineering/rate/<prompt_id>`

**Request:**
```json
{
  "rating": 5,
  "feedback": "Excellent prompt!"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "✅ شكراً على تقييمك!"
}
```

---

## 📊 Analytics & Monitoring | التحليلات والمراقبة

### Metrics Tracked | المقاييس المتتبعة

- **Template Usage**: How often each template is used
- **Success Rate**: Average rating per template
- **Generation Time**: Time taken to generate prompts
- **Token Usage**: Tokens consumed per generation
- **Context Efficiency**: RAG retrieval effectiveness

### Querying Analytics

```python
from app.models import PromptTemplate, GeneratedPrompt
from sqlalchemy import func

# Most used templates
top_templates = db.session.query(
    PromptTemplate.name,
    PromptTemplate.usage_count,
    PromptTemplate.success_rate
).order_by(PromptTemplate.usage_count.desc()).limit(10).all()

# Average rating by category
ratings = db.session.query(
    PromptTemplate.category,
    func.avg(GeneratedPrompt.rating)
).join(
    GeneratedPrompt, PromptTemplate.id == GeneratedPrompt.template_id
).group_by(PromptTemplate.category).all()

# Recent high-rated prompts
recent_best = GeneratedPrompt.query.filter(
    GeneratedPrompt.rating >= 4
).order_by(GeneratedPrompt.created_at.desc()).limit(20).all()
```

---

## 🎓 Best Practices | أفضل الممارسات

### Writing Good Descriptions

✅ **Good:**
- "Create a Flask route that handles user registration with email validation and password hashing"
- "Write comprehensive tests for the database service including connection handling and error cases"
- "Document the authentication API with request/response examples and error codes"

❌ **Avoid:**
- "make api" (too vague)
- "do the thing" (unclear)
- Extremely long descriptions (>10,000 chars)

### Using RAG Effectively

- Enable RAG for prompts that need project context
- Disable RAG for general programming questions
- RAG is most effective for:
  - Code generation in existing codebase
  - Refactoring existing code
  - Writing tests for existing functions

### Template Creation Tips

1. **Clear Structure**: Organize template into sections
2. **Comprehensive Variables**: Define all placeholders
3. **Good Examples**: Provide 2-3 quality few-shot examples
4. **Context Awareness**: Include project-specific guidance
5. **Flexibility**: Make templates adaptable to various requests

---

## 🐛 Troubleshooting | استكشاف الأخطاء

### Common Issues

**Issue: "Template not found"**
- Solution: Run `python seed_prompt_templates.py` to create defaults

**Issue: Slow generation**
- Try disabling RAG: `--no-rag`
- Check network connection to OpenRouter
- Verify `DEFAULT_AI_MODEL` is set correctly

**Issue: Generic prompts**
- Enable RAG for better context
- Provide more detailed descriptions
- Use specific prompt types

**Issue: Database error**
- Run migrations: `flask db upgrade`
- Check `DATABASE_URL` environment variable

---

## 🔮 Future Enhancements | التحسينات المستقبلية

- [ ] Vector embeddings for semantic search
- [ ] Fine-tuning on project-specific data
- [ ] Prompt chaining for complex tasks
- [ ] Multi-language prompt generation
- [ ] Automated template optimization
- [ ] Integration with more LLM providers
- [ ] Prompt versioning and comparison
- [ ] Collaborative prompt editing

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built with ❤️ by the CogniForge team using:
- Flask & SQLAlchemy
- OpenRouter API
- Claude & GPT-4
- Advanced RAG techniques
- RLHF principles

---

**Version:** 1.0.0  
**Last Updated:** October 16, 2025  
**Status:** Production Ready ✅
