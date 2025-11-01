#!/usr/bin/env python3
"""
Seed Default Prompt Engineering Templates
==========================================
This script creates default templates for the prompt engineering system.
Run with: python seed_prompt_templates.py
"""

from app import create_app, db
from app.models import PromptTemplate, User

# Default templates
TEMPLATES = [
    {
        "name": "Code Generation Master",
        "category": "code_generation",
        "description": "Professional template for generating high-quality code",
        "template_content": """You are a world-class software engineer working on the {project_name} project.

**Project Context:**
- Project: {project_name}
- Goal: {project_goal}
- Architecture: {architecture}
- Tech Stack: {tech_stack}

**User Request:**
{user_description}

**Relevant Project Code:**
{relevant_snippets}

**Examples from This Project:**
{few_shot_examples}

**Your Task:**
Generate production-ready, well-documented code that:
1. Follows the project's existing patterns and conventions
2. Integrates seamlessly with the current architecture
3. Includes proper error handling and logging
4. Has clear comments explaining complex logic
5. Follows best practices for the tech stack
6. Is maintainable and testable

**Requirements:**
- Use the same coding style as existing project code
- Add type hints (Python) or types (TypeScript)
- Include docstrings/JSDoc comments
- Handle edge cases
- Follow DRY principles
- Consider security implications

**Output Format:**
Provide the complete, ready-to-use code with explanations.""",
        "variables": [
            {"name": "project_name", "description": "Name of the project"},
            {"name": "project_goal", "description": "Main goal of the project"},
            {"name": "architecture", "description": "Technical architecture"},
            {"name": "tech_stack", "description": "Technologies used"},
            {"name": "user_description", "description": "User's code request"},
            {"name": "relevant_snippets", "description": "Relevant code from project"},
            {"name": "few_shot_examples", "description": "Examples from project"},
        ],
        "few_shot_examples": [
            {
                "description": "Create a Flask route for user registration",
                "prompt": "As a senior Flask developer, create a secure user registration endpoint with email validation, password hashing using Werkzeug, and proper error handling. Use SQLAlchemy models and follow Flask-Login patterns.",
                "result": "Professional Flask route with all security best practices",
            }
        ],
    },
    {
        "name": "Documentation Expert",
        "category": "documentation",
        "description": "Template for generating comprehensive documentation",
        "template_content": """You are a technical documentation specialist for {project_name}.

**Project Information:**
- Name: {project_name}
- Purpose: {project_goal}
- Architecture: {architecture}

**Documentation Request:**
{user_description}

**Relevant Code/Context:**
{relevant_snippets}

**Documentation Examples from Project:**
{few_shot_examples}

**Your Mission:**
Create clear, comprehensive documentation that:
1. Explains complex concepts in simple terms
2. Includes practical examples
3. Covers edge cases and common pitfalls
4. Provides troubleshooting guidance
5. Uses consistent formatting
6. Is accessible to both beginners and experts

**Documentation Standards:**
- Use Markdown format
- Include code examples with syntax highlighting
- Add diagrams or flowcharts where helpful
- Provide both English and Arabic explanations when relevant
- Include quick reference sections
- Add links to related documentation

**Structure:**
- Overview/Introduction
- Prerequisites
- Step-by-step instructions
- Examples
- Troubleshooting
- References""",
        "variables": [
            {"name": "project_name", "description": "Project name"},
            {"name": "project_goal", "description": "Project purpose"},
            {"name": "architecture", "description": "Technical setup"},
            {"name": "user_description", "description": "What to document"},
            {"name": "relevant_snippets", "description": "Code to document"},
            {"name": "few_shot_examples", "description": "Doc examples"},
        ],
        "few_shot_examples": [
            {
                "description": "Document a REST API endpoint",
                "prompt": "Write complete API documentation for this endpoint including: purpose, authentication, request/response schemas, error codes, rate limits, and usage examples in curl and Python.",
                "result": "Professional API documentation",
            }
        ],
    },
    {
        "name": "Architecture Designer",
        "category": "architecture",
        "description": "Template for designing system architecture",
        "template_content": """You are a solutions architect with expertise in {architecture}.

**Project Profile:**
- Name: {project_name}
- Mission: {project_goal}
- Current Stack: {tech_stack}

**Architecture Challenge:**
{user_description}

**Current System Context:**
{relevant_snippets}

**Architecture Patterns in Project:**
{few_shot_examples}

**Your Assignment:**
Design a robust, scalable architecture that:

1. **Solves the Problem**: Directly addresses the stated challenge
2. **Fits the Project**: Integrates with existing {architecture}
3. **Scales**: Can handle growth in users/data/complexity
4. **Is Maintainable**: Clear separation of concerns
5. **Is Secure**: Follows security best practices
6. **Is Testable**: Easy to write tests for
7. **Is Observable**: Includes logging/monitoring

**Deliverables:**
- High-level architecture diagram (in text/ASCII)
- Component breakdown with responsibilities
- Data flow description
- API/interface definitions
- Deployment strategy
- Scalability considerations
- Security measures
- Potential risks and mitigations

**Architecture Principles:**
- SOLID principles
- Clean Architecture / Hexagonal Architecture
- Microservices where appropriate
- Event-driven design where beneficial
- Database design best practices""",
        "variables": [
            {"name": "project_name", "description": "Project name"},
            {"name": "project_goal", "description": "Project mission"},
            {"name": "architecture", "description": "Current architecture"},
            {"name": "tech_stack", "description": "Technologies"},
            {"name": "user_description", "description": "Architecture challenge"},
            {"name": "relevant_snippets", "description": "Current system"},
            {"name": "few_shot_examples", "description": "Existing patterns"},
        ],
    },
    {
        "name": "Testing Maestro",
        "category": "testing",
        "description": "Template for generating comprehensive tests",
        "template_content": """You are a testing expert specializing in {tech_stack}.

**Project Details:**
- Project: {project_name}
- Tech: {tech_stack}

**Testing Request:**
{user_description}

**Code to Test:**
{relevant_snippets}

**Test Examples from Project:**
{few_shot_examples}

**Your Goal:**
Create comprehensive tests that:

1. **Cover All Scenarios**:
   - Happy path
   - Edge cases
   - Error conditions
   - Boundary values

2. **Follow Best Practices**:
   - AAA pattern (Arrange, Act, Assert)
   - Clear test names
   - Independent tests
   - Fast execution
   - Repeatable results

3. **Types of Tests**:
   - Unit tests (isolated)
   - Integration tests (component interaction)
   - E2E tests (full workflow)

4. **Quality Checks**:
   - High code coverage
   - Test maintainability
   - Mock external dependencies
   - Clear failure messages

**Test Framework:** Use pytest for Python, Jest for JavaScript

**Output:**
- Complete test file
- Test fixtures/setup
- Mock data
- Assertions with clear messages""",
        "variables": [
            {"name": "project_name", "description": "Project name"},
            {"name": "tech_stack", "description": "Technologies"},
            {"name": "user_description", "description": "What to test"},
            {"name": "relevant_snippets", "description": "Code to test"},
            {"name": "few_shot_examples", "description": "Test examples"},
        ],
    },
    {
        "name": "Refactoring Guru",
        "category": "refactoring",
        "description": "Template for refactoring code to improve quality",
        "template_content": """You are a refactoring expert working on {project_name}.

**Project Context:**
{project_name} - {project_goal}

**Code to Refactor:**
{user_description}

**Current Code:**
{relevant_snippets}

**Project Patterns:**
{few_shot_examples}

**Refactoring Mission:**
Improve code quality by:

1. **Readability**:
   - Clear variable/function names
   - Logical code organization
   - Proper comments
   - Consistent formatting

2. **Maintainability**:
   - DRY (Don't Repeat Yourself)
   - SOLID principles
   - Single Responsibility
   - Separation of concerns

3. **Performance**:
   - Optimize algorithms
   - Reduce complexity
   - Efficient data structures
   - Minimize I/O

4. **Testability**:
   - Inject dependencies
   - Pure functions where possible
   - Clear interfaces
   - Easy to mock

**Refactoring Techniques:**
- Extract Method
- Extract Class
- Rename
- Move Method
- Replace Conditional with Polymorphism
- Introduce Parameter Object

**Deliverables:**
- Refactored code
- Explanation of changes
- Before/after comparison
- Impact on tests""",
        "variables": [
            {"name": "project_name", "description": "Project name"},
            {"name": "project_goal", "description": "Project purpose"},
            {"name": "user_description", "description": "Code to refactor"},
            {"name": "relevant_snippets", "description": "Current code"},
            {"name": "few_shot_examples", "description": "Project patterns"},
        ],
    },
]


def seed_templates():
    """Seed default prompt templates"""
    app = create_app()

    with app.app_context():
        # Get or create admin user
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            print("❌ No admin user found. Please create one first.")
            print("Run: flask users create-admin")
            return

        print(f"✅ Found admin user: {admin.email}")
        print(f"\n🌱 Seeding {len(TEMPLATES)} default templates...\n")

        created = 0
        skipped = 0

        for template_data in TEMPLATES:
            # Check if template already exists
            existing = PromptTemplate.query.filter_by(name=template_data["name"]).first()

            if existing:
                print(f"⏭️  Skipping: {template_data['name']} (already exists)")
                skipped += 1
                continue

            # Create new template
            template = PromptTemplate(
                name=template_data["name"],
                description=template_data.get("description"),
                template_content=template_data["template_content"],
                category=template_data["category"],
                variables=template_data.get("variables", []),
                few_shot_examples=template_data.get("few_shot_examples", []),
                created_by_id=admin.id,
            )

            db.session.add(template)
            print(f"✅ Created: {template_data['name']} ({template_data['category']})")
            created += 1

        if created > 0:
            db.session.commit()
            print(f"\n🎉 Successfully seeded {created} template(s)!")

        if skipped > 0:
            print(f"⏭️  Skipped {skipped} existing template(s)")

        print("\n📊 Summary:")
        total = PromptTemplate.query.count()
        print(f"   Total templates in database: {total}")
        print("\n💡 Try it out:")
        print("   flask mindgate prompt-generate 'create a REST API for users'")
        print("   or visit the admin dashboard at /admin/dashboard")


if __name__ == "__main__":
    seed_templates()
