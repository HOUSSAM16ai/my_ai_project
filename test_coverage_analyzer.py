#!/usr/bin/env python3
"""
محلل تغطية الاختبارات للكود الميت
يفحص الاختبارات التي تختبر كود غير موجود أو غير مستخدم
"""

import ast
import json
import os
from pathlib import Path
from typing import Any


def extract_imports_from_test(filepath: str) -> list[dict]:
    """استخراج الاستيرادات من ملف اختبار"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=filepath)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'name': None,
                        'alias': alias.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        imports.append({
                            'type': 'from',
                            'module': node.module,
                            'name': alias.name,
                            'alias': alias.asname
                        })
        
        return imports
    except Exception as e:
        return []


def check_module_exists(module_path: str) -> dict:
    """التحقق من وجود module"""
    # تحويل module path إلى file path
    file_path = module_path.replace('.', '/') + '.py'
    
    exists = os.path.exists(file_path)
    
    if not exists:
        # ربما يكون package
        package_path = module_path.replace('.', '/') + '/__init__.py'
        exists = os.path.exists(package_path)
        file_path = package_path if exists else file_path
    
    return {
        'exists': exists,
        'path': file_path if exists else None
    }


def check_entity_exists_in_module(module_path: str, entity_name: str) -> bool:
    """التحقق من وجود entity في module"""
    file_path = module_path.replace('.', '/') + '.py'
    
    if not os.path.exists(file_path):
        # ربما يكون package
        file_path = module_path.replace('.', '/') + '/__init__.py'
    
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=file_path)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == entity_name:
                    return True
        
        return False
    except Exception:
        return False


def analyze_test_file(filepath: str) -> dict:
    """تحليل ملف اختبار واحد"""
    imports = extract_imports_from_test(filepath)
    
    issues = []
    
    for imp in imports:
        if imp['module'].startswith('app.'):
            # التحقق من وجود الـ module
            module_check = check_module_exists(imp['module'])
            
            if not module_check['exists']:
                issues.append({
                    'type': 'missing_module',
                    'module': imp['module'],
                    'severity': 'high',
                    'message': f"Module '{imp['module']}' does not exist"
                })
            elif imp['name'] and imp['type'] == 'from':
                # التحقق من وجود الـ entity
                if not check_entity_exists_in_module(imp['module'], imp['name']):
                    issues.append({
                        'type': 'missing_entity',
                        'module': imp['module'],
                        'entity': imp['name'],
                        'severity': 'medium',
                        'message': f"Entity '{imp['name']}' not found in '{imp['module']}'"
                    })
    
    return {
        'filepath': filepath,
        'imports': imports,
        'issues': issues
    }


def find_orphaned_tests() -> list[dict]:
    """البحث عن اختبارات يتيمة (تختبر كود محذوف)"""
    test_files = list(Path('tests').rglob('*.py'))
    
    orphaned_tests = []
    
    for test_file in test_files:
        if test_file.name == '__init__.py':
            continue
        
        analysis = analyze_test_file(str(test_file))
        
        if analysis['issues']:
            orphaned_tests.append(analysis)
    
    return orphaned_tests


def analyze_test_for_dead_code_patterns(filepath: str) -> list[dict]:
    """تحليل الاختبار للبحث عن أنماط الكود الميت"""
    patterns = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # البحث عن استيرادات من الملفات المشتبه بها
        suspicious_modules = [
            'app.boundaries.service_boundaries',
            'app.boundaries.policy',
            'app.boundaries.data',
            'app.core.base_profiler',
            'app.core.base_repository',
            'app.core.base_service',
        ]
        
        for module in suspicious_modules:
            if module in content:
                patterns.append({
                    'type': 'suspicious_import',
                    'module': module,
                    'message': f"Test imports from potentially dead module: {module}"
                })
        
        # البحث عن استخدام الكلاسات المكررة
        duplicate_classes = [
            'CircuitBreaker',
            'EventBus',
            'BoundedContext',
            'CircuitBreakerConfig',
        ]
        
        for cls in duplicate_classes:
            if f'from app.boundaries.service_boundaries import {cls}' in content:
                patterns.append({
                    'type': 'duplicate_class_usage',
                    'class': cls,
                    'message': f"Test uses duplicate class: {cls} from service_boundaries"
                })
    
    except Exception:
        pass
    
    return patterns


def main():
    """الدالة الرئيسية"""
    print("🧪 تحليل الاختبارات للكود الميت")
    print("=" * 80)
    
    # البحث عن الاختبارات اليتيمة
    print("\n🔍 البحث عن اختبارات تختبر كود محذوف...")
    orphaned = find_orphaned_tests()
    
    print(f"   وجدت {len(orphaned)} ملف اختبار به مشاكل")
    
    # تحليل أنماط الكود الميت
    print("\n🔍 البحث عن أنماط الكود الميت في الاختبارات...")
    test_files = list(Path('tests').rglob('*.py'))
    
    tests_with_patterns = []
    for test_file in test_files:
        if test_file.name == '__init__.py':
            continue
        
        patterns = analyze_test_for_dead_code_patterns(str(test_file))
        if patterns:
            tests_with_patterns.append({
                'filepath': str(test_file),
                'patterns': patterns
            })
    
    print(f"   وجدت {len(tests_with_patterns)} ملف اختبار يستخدم أنماط مشتبه بها")
    
    # طباعة التفاصيل
    print("\n" + "=" * 80)
    print("📝 تفاصيل النتائج:")
    print("=" * 80)
    
    if orphaned:
        print("\n🚫 اختبارات تستورد كود غير موجود:")
        for test in orphaned[:10]:
            print(f"\n   📄 {test['filepath']}")
            for issue in test['issues']:
                severity_icon = "🔴" if issue['severity'] == 'high' else "🟡"
                print(f"      {severity_icon} {issue['message']}")
        
        if len(orphaned) > 10:
            print(f"\n   ... و {len(orphaned) - 10} ملف آخر")
    
    if tests_with_patterns:
        print("\n⚠️  اختبارات تستخدم أنماط مشتبه بها:")
        for test in tests_with_patterns[:15]:
            print(f"\n   📄 {test['filepath']}")
            for pattern in test['patterns']:
                print(f"      • {pattern['message']}")
        
        if len(tests_with_patterns) > 15:
            print(f"\n   ... و {len(tests_with_patterns) - 15} ملف آخر")
    
    # إحصائيات
    print("\n" + "=" * 80)
    print("📊 إحصائيات:")
    print("=" * 80)
    
    total_issues = sum(len(t['issues']) for t in orphaned)
    total_patterns = sum(len(t['patterns']) for t in tests_with_patterns)
    
    print(f"   إجمالي ملفات الاختبار: {len(test_files)}")
    print(f"   اختبارات بها استيرادات مفقودة: {len(orphaned)}")
    print(f"   إجمالي المشاكل: {total_issues}")
    print(f"   اختبارات بها أنماط مشتبه بها: {len(tests_with_patterns)}")
    print(f"   إجمالي الأنماط المشتبه بها: {total_patterns}")
    
    # حفظ النتائج
    results = {
        'summary': {
            'total_test_files': len(test_files),
            'orphaned_tests': len(orphaned),
            'total_issues': total_issues,
            'tests_with_patterns': len(tests_with_patterns),
            'total_patterns': total_patterns
        },
        'orphaned_tests': orphaned,
        'tests_with_patterns': tests_with_patterns
    }
    
    with open('test_coverage_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n💾 تم حفظ النتائج في: test_coverage_analysis.json")
    print("\n✅ اكتمل التحليل!")


if __name__ == '__main__':
    main()
