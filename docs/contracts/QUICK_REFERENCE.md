# 📋 Quick Reference Guide
# دليل المرجع السريع

> **Quick commands and workflows for developers**  
> **أوامر وسير عمل سريع للمطورين**

---

## 🚀 Development Workflow | سير العمل التطويري

### 1. Start Development | بدء التطوير

```bash
# Clone repository
git clone https://github.com/ai-for-solution-labs/my_ai_project.git
cd my_ai_project

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
flask db upgrade
flask users create-admin

# Start development server
flask run
```

### 2. Contract-First Development | تطوير العقد أولاً

```bash
# 1. Design API contract (OpenAPI/AsyncAPI)
# Edit files in docs/contracts/openapi/ or docs/contracts/asyncapi/

# 2. Validate contract
make docs-validate
# OR
spectral lint docs/contracts/openapi/your-api.yaml --ruleset docs/contracts/policies/.spectral.yaml

# 3. Generate documentation
make docs
# OR
python scripts/generate_docs.py

# 4. Implement API endpoints
# Write code in app/routes.py or app/api/

# 5. Test implementation
pytest tests/test_your_feature.py -v

# 6. Commit changes
git add .
git commit -m "feat: implement your feature"
git push
```

### 3. Quality Checks | فحوصات الجودة

```bash
# Run all quality checks
make quality

# Individual checks
make format        # Auto-format code
make lint          # Run linters
make type-check    # Type checking
make security      # Security scans
make test          # Run tests

# Contract validation
make docs-validate
```

---

## 📄 Contract Management | إدارة العقود

### OpenAPI (REST APIs)

```bash
# Location
docs/contracts/openapi/*.yaml

# Validate
spectral lint docs/contracts/openapi/accounts-api.yaml \
  --ruleset docs/contracts/policies/.spectral.yaml

# Generate docs
python scripts/generate_docs.py

# View interactive docs
make docs-serve
# Open: http://localhost:8000
```

### AsyncAPI (Events)

```bash
# Location
docs/contracts/asyncapi/*.yaml

# Validate
spectral lint docs/contracts/asyncapi/events-api.yaml \
  --ruleset docs/contracts/policies/.spectral.yaml

# Generate docs
python scripts/generate_docs.py
```

### gRPC (High-performance APIs)

```bash
# Location
docs/contracts/grpc/*.proto

# Validate syntax
protoc --proto_path=docs/contracts/grpc \
       --python_out=. \
       docs/contracts/grpc/accounts.proto

# Generate Python code
python -m grpc_tools.protoc \
  -I docs/contracts/grpc \
  --python_out=. \
  --grpc_python_out=. \
  docs/contracts/grpc/accounts.proto
```

### GraphQL (Flexible queries)

```bash
# Location
docs/contracts/graphql/*.graphql

# Validate (requires graphql-js)
npx graphql-schema-linter docs/contracts/graphql/schema.graphql
```

---

## 🔐 Authentication & API Keys | المصادقة ومفاتيح API

### Generate API Key

```bash
# Via CLI
flask users create --email dev@example.com --name "Developer"

# Via Python
python -c "
from app.services.api_first_platform_service import APIFirstPlatformService
service = APIFirstPlatformService()
key = service.generate_api_key('dev_001', 'Dev Key', ['read', 'write'])
print(f'API Key: {key[\"key\"]}')
"
```

### Use API Key

```bash
# cURL
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:5000/api/v1/accounts

# Python requests
import requests
headers = {"Authorization": "Bearer YOUR_API_KEY"}
response = requests.get("http://localhost:5000/api/v1/accounts", headers=headers)
```

---

## 📚 Documentation | التوثيق

### Generate Documentation

```bash
# Generate all docs
make docs

# Manual generation
python scripts/generate_docs.py --format both --output docs/generated

# Options:
#   --format: markdown, html, both (default: both)
#   --output: output directory (default: docs/generated)
```

### Serve Documentation

```bash
# Start local server
make docs-serve

# Manual serve
cd docs/generated && python -m http.server 8000

# Open browser
open http://localhost:8000
```

### Update Documentation

```bash
# 1. Update contract files in docs/contracts/
# 2. Regenerate docs
make docs
# 3. Review generated files in docs/generated/
```

---

## 🧪 Testing | الاختبار

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_api_first_platform.py -v

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_api_first_platform.py::test_register_contract -v
```

### Contract Testing

```bash
# Test that implementation matches contract
pytest tests/test_contract_compliance.py

# Manual contract validation
spectral lint docs/contracts/openapi/*.yaml \
  --ruleset docs/contracts/policies/.spectral.yaml
```

---

## 🚀 Deployment | النشر

### Docker Deployment

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down
```

### Production Deployment

```bash
# Build for production
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl http://localhost:5000/health
```

### Kubernetes Deployment

```bash
# Apply configurations
kubectl apply -f infra/k8s/

# Check status
kubectl get pods -n cogniforge

# View logs
kubectl logs -f deployment/cogniforge-api -n cogniforge
```

---

## 🔧 Common Tasks | المهام الشائعة

### Database Operations

```bash
# Create migration
flask db migrate -m "description"

# Apply migrations
flask db upgrade

# Rollback
flask db downgrade

# Database health
flask db health

# Database stats
flask db stats
```

### User Management

```bash
# Create admin user
flask users create-admin

# List users
flask users list

# Create regular user
flask users create --email user@example.com --name "User Name"
```

### Service Management

```bash
# Start service
flask run

# Development mode
FLASK_DEBUG=1 flask run

# Production mode
gunicorn -c gunicorn.conf.py app:create_app()
```

---

## 🐛 Troubleshooting | حل المشاكل

### Debug Mode

```bash
# Enable debug logging
export FLASK_DEBUG=1
export LOG_LEVEL=DEBUG
flask run
```

### Database Issues

```bash
# Reset database
flask db downgrade base
flask db upgrade

# Check connection
flask db health

# View schema
flask db tables
```

### API Issues

```bash
# Test endpoint
curl -v http://localhost:5000/api/v1/accounts

# Check logs
docker-compose logs web

# Validate contract
spectral lint docs/contracts/openapi/accounts-api.yaml
```

---

## 📞 Getting Help | الحصول على المساعدة

### Documentation

- 📖 [Getting Started](GETTING_STARTED.md)
- 📋 [API Style Guide](API_STYLE_GUIDE.md)
- 🗺️ [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md)
- 📝 [Changelog](CHANGELOG.md)

### Support Channels

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/ai-for-solution-labs/my_ai_project/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/ai-for-solution-labs/my_ai_project/discussions)
- 📧 **Email**: support@cogniforge.com

### Useful Links

- [Main README](README.md)
- [OpenAPI Specs](openapi/)
- [AsyncAPI Specs](asyncapi/)
- [gRPC Protos](grpc/)
- [GraphQL Schema](graphql/)

---

## ⚡ Keyboard Shortcuts | اختصارات لوحة المفاتيح

### Make Commands

```bash
make help          # Show all commands
make install       # Install dependencies
make quality       # Run all quality checks
make test          # Run tests
make docs          # Generate documentation
make docs-serve    # Serve documentation
make docs-validate # Validate contracts
make clean         # Clean build artifacts
```

### Git Workflow

```bash
# Feature branch
git checkout -b feature/your-feature
git add .
git commit -m "feat: your feature"
git push origin feature/your-feature

# Create PR via GitHub UI

# After merge
git checkout main
git pull origin main
git branch -d feature/your-feature
```

---

## 🎯 Best Practices | أفضل الممارسات

### 1. Contract-First Development
- Design API contract before implementation
- Validate contract with Spectral
- Generate documentation
- Implement and test

### 2. Code Quality
- Run `make quality` before committing
- Write tests for new features
- Follow API Style Guide
- Use type hints

### 3. Documentation
- Update contracts when API changes
- Regenerate docs after contract changes
- Keep Getting Started guide updated
- Maintain CHANGELOG

### 4. Version Control
- Use semantic versioning
- Write clear commit messages
- Create feature branches
- Review PRs carefully

### 5. Testing
- Write contract tests
- Test happy and sad paths
- Use test fixtures
- Maintain test coverage

---

**🌟 Built with ❤️ by Houssam Benmerah**

*Quick reference for productive development!*  
*مرجع سريع للتطوير المنتج!*
