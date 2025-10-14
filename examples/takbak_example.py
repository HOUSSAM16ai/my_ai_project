#!/usr/bin/env python3
"""
Takbak Service Example - مثال على استخدام خدمة الطبقات
========================================================
This script demonstrates how to use the Takbak (layers) service
for organizing educational content hierarchically.

يوضح هذا السكريبت كيفية استخدام خدمة الطبقات لتنظيم المحتوى التعليمي
"""

from app.services.takbak_service import TakbakService


def create_educational_structure():
    """
    إنشاء هيكل تعليمي نموذجي
    Create a sample educational structure
    """
    service = TakbakService()

    print("🎓 Creating Educational Content Structure...")
    print("=" * 60)

    # Create main course
    print("\n1️⃣ Creating main course...")
    course = service.create_layer(
        layer_id="python-fundamentals",
        name="Python Programming Fundamentals",
        description="Complete beginner course for Python programming",
        metadata={
            "level": "beginner",
            "duration_weeks": 8,
            "language": "en",
            "prerequisites": []
        }
    )
    print(f"   ✅ Created: {course['name']}")

    # Create modules
    print("\n2️⃣ Creating course modules...")
    modules = [
        {
            "layer_id": "module-1-basics",
            "name": "Module 1: Python Basics",
            "description": "Introduction to Python syntax and basic concepts",
            "parent_id": "python-fundamentals",
            "metadata": {"order": 1, "duration_days": 7}
        },
        {
            "layer_id": "module-2-data-structures",
            "name": "Module 2: Data Structures",
            "description": "Lists, Tuples, Dictionaries, and Sets",
            "parent_id": "python-fundamentals",
            "metadata": {"order": 2, "duration_days": 10}
        },
        {
            "layer_id": "module-3-functions",
            "name": "Module 3: Functions & Modules",
            "description": "Creating and using functions and modules",
            "parent_id": "python-fundamentals",
            "metadata": {"order": 3, "duration_days": 10}
        }
    ]

    for module_data in modules:
        module = service.create_layer(**module_data)
        print(f"   ✅ Created: {module['name']}")

    # Create lessons for Module 1
    print("\n3️⃣ Creating lessons for Module 1...")
    lessons = [
        {
            "layer_id": "lesson-1-1-intro",
            "name": "Lesson 1.1: Introduction to Python",
            "description": "What is Python and why use it?",
            "parent_id": "module-1-basics",
            "metadata": {"order": 1, "video_url": "https://example.com/video1"}
        },
        {
            "layer_id": "lesson-1-2-variables",
            "name": "Lesson 1.2: Variables and Data Types",
            "description": "Understanding variables, strings, numbers, and booleans",
            "parent_id": "module-1-basics",
            "metadata": {"order": 2, "video_url": "https://example.com/video2"}
        },
        {
            "layer_id": "lesson-1-3-operators",
            "name": "Lesson 1.3: Operators and Expressions",
            "description": "Arithmetic, comparison, and logical operators",
            "parent_id": "module-1-basics",
            "metadata": {"order": 3, "video_url": "https://example.com/video3"}
        }
    ]

    for lesson_data in lessons:
        lesson = service.create_layer(**lesson_data)
        print(f"   ✅ Created: {lesson['name']}")

    # Display structure
    print("\n4️⃣ Displaying complete hierarchy...")
    print("-" * 60)
    hierarchy = service.get_hierarchy()
    display_hierarchy(hierarchy['roots'][0], indent=0)

    # Get path to a specific lesson
    print("\n5️⃣ Getting path to 'Lesson 1.2'...")
    path = service.get_path("lesson-1-2-variables")
    print("   📍 Path:", " → ".join([layer['name'] for layer in path]))

    # List all children of Module 1
    print("\n6️⃣ Listing all lessons in Module 1...")
    module1_children = service.list_layers(parent_id="module-1-basics")
    for child in module1_children:
        print(f"   📚 {child['name']}")

    # Update a layer
    print("\n7️⃣ Updating lesson metadata...")
    service.update_layer(
        layer_id="lesson-1-2-variables",
        metadata={"completed_students": 1250, "rating": 4.8}
    )
    updated = service.get_layer("lesson-1-2-variables")
    print(f"   ✅ Updated: {updated['name']}")
    print(f"   📊 Completed Students: {updated['metadata']['completed_students']}")
    print(f"   ⭐ Rating: {updated['metadata']['rating']}")

    print("\n" + "=" * 60)
    print("✅ Educational structure created successfully!")
    print(f"📊 Total layers: {len(service.layers)}")

    return service


def display_hierarchy(layer, indent=0):
    """
    Display hierarchy in a tree format
    عرض الهيكل الهرمي بصيغة شجرة
    """
    prefix = "  " * indent
    icon = "📂" if layer.get("children") else "📄"
    print(f"{prefix}{icon} {layer['name']}")

    for child in layer.get("children", []):
        display_hierarchy(child, indent + 1)


def demonstrate_advanced_features():
    """
    Demonstrate advanced features
    عرض الميزات المتقدمة
    """
    service = TakbakService()

    print("\n\n🚀 Advanced Features Demonstration")
    print("=" * 60)

    # Create a multi-level hierarchy
    print("\n1️⃣ Creating deep hierarchy...")
    service.create_layer("level-1", "Level 1")
    service.create_layer("level-2", "Level 2", parent_id="level-1")
    service.create_layer("level-3", "Level 3", parent_id="level-2")
    service.create_layer("level-4", "Level 4", parent_id="level-3")
    service.create_layer("level-5", "Level 5", parent_id="level-4")

    path = service.get_path("level-5")
    print(f"   📍 Depth: {len(path)} levels")
    print(f"   📍 Path: {' → '.join([l['name'] for l in path])}")

    # Test cascade delete
    print("\n2️⃣ Testing cascade deletion...")
    print("   Creating parent with 3 children...")
    service.create_layer("parent", "Parent Layer")
    service.create_layer("child-1", "Child 1", parent_id="parent")
    service.create_layer("child-2", "Child 2", parent_id="parent")
    service.create_layer("child-3", "Child 3", parent_id="parent")

    print(f"   📊 Total layers before delete: {len(service.layers)}")
    service.delete_layer("parent", cascade=True)
    print(f"   📊 Total layers after cascade delete: {len(service.layers)}")
    print("   ✅ Parent and all children deleted successfully")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Main demonstration
    service = create_educational_structure()

    # Advanced features
    demonstrate_advanced_features()

    print("\n✨ Takbak Service demonstration completed!")
    print("\n📚 For API usage, see TAKBAK_SERVICE_GUIDE.md")
