#!/usr/bin/env python3
"""
Verify Prompt Engineering Feature Implementation
=================================================
Quick verification script to ensure all components are working.
"""

import sys
import traceback

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from app.models import PromptTemplate, GeneratedPrompt
        print("✅ Models imported successfully")
    except Exception as e:
        print(f"❌ Failed to import models: {e}")
        return False
    
    try:
        from app.services.prompt_engineering_service import (
            PromptEngineeringService, 
            get_prompt_engineering_service
        )
        print("✅ Service imported successfully")
    except Exception as e:
        print(f"❌ Failed to import service: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_model_structure():
    """Test model structure"""
    print("\n🔍 Testing model structure...")
    
    try:
        from app.models import PromptTemplate, GeneratedPrompt
        
        # Check PromptTemplate attributes
        required_attrs = [
            'name', 'description', 'template_content', 'category',
            'few_shot_examples', 'rag_config', 'variables',
            'usage_count', 'success_rate', 'version', 'is_active',
            'created_by_id'
        ]
        
        for attr in required_attrs:
            if not hasattr(PromptTemplate, attr):
                print(f"❌ PromptTemplate missing attribute: {attr}")
                return False
        
        print("✅ PromptTemplate structure correct")
        
        # Check GeneratedPrompt attributes
        required_attrs = [
            'user_description', 'template_id', 'generated_prompt',
            'context_snippets', 'generation_metadata', 'rating',
            'feedback_text', 'conversation_id', 'created_by_id',
            'content_hash'
        ]
        
        for attr in required_attrs:
            if not hasattr(GeneratedPrompt, attr):
                print(f"❌ GeneratedPrompt missing attribute: {attr}")
                return False
        
        print("✅ GeneratedPrompt structure correct")
        
        return True
        
    except Exception as e:
        print(f"❌ Model structure test failed: {e}")
        traceback.print_exc()
        return False


def test_service_methods():
    """Test service has required methods"""
    print("\n🔍 Testing service methods...")
    
    try:
        from app.services.prompt_engineering_service import PromptEngineeringService
        
        service = PromptEngineeringService()
        
        required_methods = [
            'generate_prompt',
            'create_template',
            'list_templates',
            'rate_prompt',
            '_get_project_context',
            '_retrieve_relevant_snippets',
            '_build_few_shot_examples',
            '_construct_meta_prompt',
        ]
        
        for method in required_methods:
            if not hasattr(service, method):
                print(f"❌ Service missing method: {method}")
                return False
        
        print("✅ Service methods correct")
        return True
        
    except Exception as e:
        print(f"❌ Service methods test failed: {e}")
        traceback.print_exc()
        return False


def test_cli_commands():
    """Test CLI commands are defined"""
    print("\n🔍 Testing CLI commands...")
    
    try:
        # Just check the file exists and has the commands
        with open('app/cli/mindgate_commands.py', 'r') as f:
            content = f.read()
            
        required_commands = [
            'prompt-generate',
            'prompt-templates',
            'prompt-rate',
        ]
        
        for cmd in required_commands:
            if cmd not in content:
                print(f"❌ CLI command not found: {cmd}")
                return False
        
        print("✅ CLI commands defined")
        return True
        
    except Exception as e:
        print(f"❌ CLI commands test failed: {e}")
        return False


def test_api_routes():
    """Test API routes are defined"""
    print("\n🔍 Testing API routes...")
    
    try:
        with open('app/admin/routes.py', 'r') as f:
            content = f.read()
        
        required_routes = [
            'handle_generate_prompt',
            'handle_list_templates',
            'handle_create_template',
            'handle_rate_prompt',
        ]
        
        for route in required_routes:
            if route not in content:
                print(f"❌ API route not found: {route}")
                return False
        
        print("✅ API routes defined")
        return True
        
    except Exception as e:
        print(f"❌ API routes test failed: {e}")
        return False


def test_ui_integration():
    """Test UI components exist"""
    print("\n🔍 Testing UI integration...")
    
    try:
        with open('app/admin/templates/admin_dashboard.html', 'r') as f:
            content = f.read()
        
        required_elements = [
            'prompt-engineering-container',
            'prompt-engineering',
            'generatePrompt',
            'ratePrompt',
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"❌ UI element not found: {element}")
                return False
        
        print("✅ UI integration correct")
        return True
        
    except Exception as e:
        print(f"❌ UI integration test failed: {e}")
        return False


def test_migration_exists():
    """Test migration file exists"""
    print("\n🔍 Testing migration...")
    
    try:
        import os
        migration_file = 'migrations/versions/20251016_prompt_engineering.py'
        
        if not os.path.exists(migration_file):
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            content = f.read()
        
        if 'prompt_templates' not in content or 'generated_prompts' not in content:
            print("❌ Migration missing table definitions")
            return False
        
        print("✅ Migration file exists and looks correct")
        return True
        
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        return False


def main():
    """Run all verification tests"""
    print("=" * 70)
    print("🚀 PROMPT ENGINEERING FEATURE VERIFICATION")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Model Structure", test_model_structure),
        ("Service Methods", test_service_methods),
        ("CLI Commands", test_cli_commands),
        ("API Routes", test_api_routes),
        ("UI Integration", test_ui_integration),
        ("Migration", test_migration_exists),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n🎯 Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Feature is ready to use!")
        print("\n📝 Next steps:")
        print("   1. Run database migrations: flask db upgrade")
        print("   2. Seed templates: python seed_prompt_templates.py")
        print("   3. Try it: flask mindgate prompt-generate 'test prompt'")
        print("   4. Or visit: /admin/dashboard")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
