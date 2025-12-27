#!/usr/bin/env python3
"""
محلل تفصيلي للملفات الكبيرة المشتبه بها
"""

import ast
import json
from pathlib import Path


def analyze_specific_file(filepath: str) -> dict:
    """تحليل تفصيلي لملف محدد"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    tree = ast.parse(content, filename=filepath)
    
    # استخراج جميع التعريفات
    functions = []
    classes = []
    imports = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # حساب عدد الأسطر
            if hasattr(node, 'end_lineno'):
                lines = node.end_lineno - node.lineno + 1
            else:
                lines = 0
                
            functions.append({
                'name': node.name,
                'lineno': node.lineno,
                'end_lineno': getattr(node, 'end_lineno', None),
                'lines': lines,
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'decorators': [get_decorator_name(d) for d in node.decorator_list],
                'args': [arg.arg for arg in node.args.args],
                'docstring': ast.get_docstring(node)
            })
            
        elif isinstance(node, ast.ClassDef):
            if hasattr(node, 'end_lineno'):
                lines = node.end_lineno - node.lineno + 1
            else:
                lines = 0
                
            # استخراج الميثودات
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
                    
            classes.append({
                'name': node.name,
                'lineno': node.lineno,
                'end_lineno': getattr(node, 'end_lineno', None),
                'lines': lines,
                'bases': [get_name(base) for base in node.bases],
                'methods': methods,
                'docstring': ast.get_docstring(node)
            })
            
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'module': alias.name,
                        'alias': alias.asname
                    })
            else:
                if node.module:
                    for alias in node.names:
                        imports.append({
                            'type': 'from',
                            'module': node.module,
                            'name': alias.name,
                            'alias': alias.asname
                        })
                        
    return {
        'filepath': filepath,
        'total_lines': len(content.splitlines()),
        'functions': functions,
        'classes': classes,
        'imports': imports,
        'stats': {
            'total_functions': len(functions),
            'total_classes': len(classes),
            'total_imports': len(imports),
            'avg_function_lines': sum(f['lines'] for f in functions) / len(functions) if functions else 0,
            'avg_class_lines': sum(c['lines'] for c in classes) / len(classes) if classes else 0
        }
    }


def get_name(node):
    """استخراج الاسم من عقدة AST"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        value = get_name(node.value)
        return f"{value}.{node.attr}" if value else node.attr
    return ""


def get_decorator_name(node):
    """استخراج اسم decorator"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Call):
        return get_name(node.func)
    elif isinstance(node, ast.Attribute):
        return get_name(node)
    return ""


def check_usage_in_codebase(entity_name: str, search_dirs: list[str]) -> dict:
    """البحث عن استخدام entity في الكود"""
    import subprocess
    
    # البحث في الملفات
    try:
        result = subprocess.run(
            ['grep', '-r', entity_name, '--include=*.py'] + search_dirs,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        lines = result.stdout.strip().split('\n') if result.stdout else []
        # تصفية النتائج
        filtered_lines = [
            line for line in lines 
            if line and not line.strip().startswith('#')
        ]
        
        return {
            'found': len(filtered_lines) > 0,
            'occurrences': len(filtered_lines),
            'files': list(set(line.split(':')[0] for line in filtered_lines if ':' in line))
        }
    except Exception as e:
        return {
            'found': False,
            'occurrences': 0,
            'files': [],
            'error': str(e)
        }


def main():
    """الدالة الرئيسية"""
    print("🔍 تحليل تفصيلي للملفات الكبيرة المشتبه بها")
    print("=" * 80)
    
    # الملفات المستهدفة
    target_files = [
        'app/boundaries/service_boundaries.py',
        'app/telemetry/unified_observability.py',
        'app/core/gateway/mesh.py',
        'app/core/error_handling.py'
    ]
    
    search_dirs = ['app/', 'tests/']
    
    all_results = {}
    
    for filepath in target_files:
        print(f"\n{'=' * 80}")
        print(f"📄 تحليل: {filepath}")
        print('=' * 80)
        
        if not Path(filepath).exists():
            print(f"   ❌ الملف غير موجود")
            continue
            
        # تحليل الملف
        analysis = analyze_specific_file(filepath)
        
        print(f"\n📊 إحصائيات:")
        print(f"   إجمالي الأسطر: {analysis['total_lines']}")
        print(f"   عدد الدوال: {analysis['stats']['total_functions']}")
        print(f"   عدد الكلاسات: {analysis['stats']['total_classes']}")
        print(f"   عدد الاستيرادات: {analysis['stats']['total_imports']}")
        print(f"   متوسط أسطر الدالة: {analysis['stats']['avg_function_lines']:.1f}")
        print(f"   متوسط أسطر الكلاس: {analysis['stats']['avg_class_lines']:.1f}")
        
        # فحص استخدام الكلاسات
        print(f"\n🏗️  فحص استخدام الكلاسات:")
        unused_classes = []
        for cls in analysis['classes']:
            usage = check_usage_in_codebase(cls['name'], search_dirs)
            # إذا كان الاستخدام فقط في نفس الملف
            if usage['occurrences'] <= 2:  # التعريف + استخدام واحد محتمل
                unused_classes.append(cls)
                print(f"   ⚠️  {cls['name']} (السطر {cls['lineno']}, {cls['lines']} سطر)")
                print(f"      استخدامات: {usage['occurrences']}")
                
        # فحص استخدام الدوال
        print(f"\n🔧 فحص استخدام الدوال:")
        unused_functions = []
        for func in analysis['functions'][:20]:  # أول 20 دالة
            # تجاهل الدوال الخاصة والسحرية
            if func['name'].startswith('__') and func['name'].endswith('__'):
                continue
            if func['name'].startswith('_'):
                continue
                
            usage = check_usage_in_codebase(func['name'], search_dirs)
            if usage['occurrences'] <= 2:
                unused_functions.append(func)
                print(f"   ⚠️  {func['name']} (السطر {func['lineno']}, {func['lines']} سطر)")
                print(f"      استخدامات: {usage['occurrences']}")
                
        # حفظ النتائج
        all_results[filepath] = {
            'analysis': analysis,
            'unused_classes': unused_classes,
            'unused_functions': unused_functions
        }
        
    # حفظ النتائج الكاملة
    with open('specific_files_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 80)
    print("✅ اكتمل التحليل التفصيلي!")
    print("💾 تم حفظ النتائج في: specific_files_analysis.json")
    
    # ملخص نهائي
    print("\n📋 ملخص نهائي:")
    for filepath, results in all_results.items():
        print(f"\n   {filepath}:")
        print(f"      كلاسات غير مستخدمة: {len(results['unused_classes'])}")
        print(f"      دوال غير مستخدمة: {len(results['unused_functions'])}")
        
        # حساب الأسطر القابلة للحذف
        deletable_lines = (
            sum(c['lines'] for c in results['unused_classes']) +
            sum(f['lines'] for f in results['unused_functions'])
        )
        total_lines = results['analysis']['total_lines']
        percentage = (deletable_lines / total_lines * 100) if total_lines > 0 else 0
        
        print(f"      أسطر قابلة للحذف: {deletable_lines} ({percentage:.1f}%)")


if __name__ == '__main__':
    main()
