#!/usr/bin/env python3
"""
محلل الكود الميت (Dead Code Analyzer)
يفحص الملفات والدوال والكلاسات غير المستخدمة
"""

import ast
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


class CodeAnalyzer(ast.NodeVisitor):
    """محلل AST لاستخراج التعريفات والاستخدامات"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.functions = []
        self.classes = []
        self.imports = []
        self.function_calls = []
        self.class_instantiations = []
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """زيارة تعريف دالة"""
        self.functions.append({
            'name': node.name,
            'lineno': node.lineno,
            'is_private': node.name.startswith('_'),
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'decorators': [self._get_decorator_name(d) for d in node.decorator_list]
        })
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """زيارة تعريف دالة async"""
        self.visit_FunctionDef(node)
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """زيارة تعريف كلاس"""
        self.classes.append({
            'name': node.name,
            'lineno': node.lineno,
            'bases': [self._get_name(base) for base in node.bases],
            'methods': []
        })
        self.generic_visit(node)
        
    def visit_Import(self, node: ast.Import) -> None:
        """زيارة استيراد"""
        for alias in node.names:
            self.imports.append({
                'module': alias.name,
                'alias': alias.asname,
                'type': 'import'
            })
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """زيارة استيراد من"""
        if node.module:
            for alias in node.names:
                self.imports.append({
                    'module': node.module,
                    'name': alias.name,
                    'alias': alias.asname,
                    'type': 'from'
                })
        self.generic_visit(node)
        
    def visit_Call(self, node: ast.Call) -> None:
        """زيارة استدعاء دالة"""
        func_name = self._get_name(node.func)
        if func_name:
            self.function_calls.append(func_name)
        self.generic_visit(node)
        
    def _get_name(self, node: Any) -> str:
        """استخراج الاسم من عقدة AST"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return ""
        
    def _get_decorator_name(self, node: Any) -> str:
        """استخراج اسم decorator"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Attribute):
            return self._get_name(node)
        return ""


def analyze_file(filepath: str) -> dict:
    """تحليل ملف Python واحد"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content, filename=filepath)
        analyzer = CodeAnalyzer(filepath)
        analyzer.visit(tree)
        
        return {
            'filepath': filepath,
            'functions': analyzer.functions,
            'classes': analyzer.classes,
            'imports': analyzer.imports,
            'function_calls': analyzer.function_calls,
            'lines': len(content.splitlines())
        }
    except Exception as e:
        return {
            'filepath': filepath,
            'error': str(e),
            'functions': [],
            'classes': [],
            'imports': [],
            'function_calls': [],
            'lines': 0
        }


def find_python_files(directories: list[str]) -> list[str]:
    """البحث عن جميع ملفات Python"""
    files = []
    for directory in directories:
        path = Path(directory)
        if path.exists():
            files.extend([str(f) for f in path.rglob("*.py")])
    return files


def analyze_imports(all_files_data: list[dict]) -> dict:
    """تحليل الاستيرادات لإيجاد الملفات غير المستوردة"""
    # بناء خريطة الملفات
    file_modules = {}
    for data in all_files_data:
        filepath = data['filepath']
        # تحويل المسار إلى اسم module
        module_path = filepath.replace('/', '.').replace('\\', '.')
        if module_path.startswith('.'):
            module_path = module_path[1:]
        if module_path.endswith('.py'):
            module_path = module_path[:-3]
        file_modules[module_path] = filepath
        
    # جمع جميع الاستيرادات
    imported_modules = set()
    for data in all_files_data:
        for imp in data['imports']:
            if imp['type'] == 'import':
                imported_modules.add(imp['module'])
            else:
                imported_modules.add(imp['module'])
                
    # إيجاد الملفات غير المستوردة
    never_imported = []
    for module_path, filepath in file_modules.items():
        # تجاهل __init__.py و __main__.py و test files
        if '__init__' in filepath or '__main__' in filepath or 'test_' in filepath:
            continue
        if 'tests/' in filepath:
            continue
            
        # التحقق من الاستيراد
        is_imported = False
        for imported in imported_modules:
            if module_path in imported or imported in module_path:
                is_imported = True
                break
                
        if not is_imported:
            never_imported.append(filepath)
            
    return {
        'total_modules': len(file_modules),
        'imported_modules': len(imported_modules),
        'never_imported': never_imported
    }


def analyze_functions(all_files_data: list[dict]) -> dict:
    """تحليل الدوال لإيجاد الدوال غير المستدعاة"""
    # جمع جميع الدوال المعرفة
    defined_functions = defaultdict(list)
    for data in all_files_data:
        for func in data['functions']:
            # تجاهل الدوال الخاصة والدوال السحرية
            if func['name'].startswith('__') and func['name'].endswith('__'):
                continue
            # تجاهل test functions
            if func['name'].startswith('test_'):
                continue
            defined_functions[func['name']].append({
                'file': data['filepath'],
                'line': func['lineno'],
                'is_private': func['is_private']
            })
            
    # جمع جميع استدعاءات الدوال
    called_functions = set()
    for data in all_files_data:
        for call in data['function_calls']:
            # استخراج اسم الدالة من الاستدعاء
            if '.' in call:
                func_name = call.split('.')[-1]
            else:
                func_name = call
            called_functions.add(func_name)
            
    # إيجاد الدوال غير المستدعاة
    uncalled_functions = []
    for func_name, locations in defined_functions.items():
        if func_name not in called_functions:
            # تجاهل الدوال الخاصة (قد تكون مستخدمة داخلياً)
            if not func_name.startswith('_'):
                for loc in locations:
                    uncalled_functions.append({
                        'name': func_name,
                        'file': loc['file'],
                        'line': loc['line']
                    })
                    
    return {
        'total_functions': sum(len(locs) for locs in defined_functions.values()),
        'called_functions': len(called_functions),
        'uncalled_functions': uncalled_functions
    }


def analyze_classes(all_files_data: list[dict]) -> dict:
    """تحليل الكلاسات لإيجاد الكلاسات غير المستخدمة"""
    # جمع جميع الكلاسات المعرفة
    defined_classes = defaultdict(list)
    for data in all_files_data:
        for cls in data['classes']:
            defined_classes[cls['name']].append({
                'file': data['filepath'],
                'line': cls['lineno']
            })
            
    # جمع جميع استخدامات الكلاسات (من الاستيرادات والاستدعاءات)
    used_classes = set()
    for data in all_files_data:
        # من الاستيرادات
        for imp in data['imports']:
            if imp['type'] == 'from' and imp.get('name'):
                used_classes.add(imp['name'])
        # من الاستدعاءات (قد تكون instantiation)
        for call in data['function_calls']:
            if '.' in call:
                class_name = call.split('.')[0]
            else:
                class_name = call
            # الكلاسات عادة تبدأ بحرف كبير
            if class_name and class_name[0].isupper():
                used_classes.add(class_name)
                
    # إيجاد الكلاسات غير المستخدمة
    unused_classes = []
    for class_name, locations in defined_classes.items():
        if class_name not in used_classes:
            for loc in locations:
                unused_classes.append({
                    'name': class_name,
                    'file': loc['file'],
                    'line': loc['line']
                })
                
    return {
        'total_classes': sum(len(locs) for locs in defined_classes.values()),
        'used_classes': len(used_classes),
        'unused_classes': unused_classes
    }


def find_circular_dependencies(all_files_data: list[dict]) -> list:
    """إيجاد التبعيات الدائرية"""
    # بناء graph التبعيات
    dependencies = defaultdict(set)
    
    for data in all_files_data:
        filepath = data['filepath']
        module_path = filepath.replace('/', '.').replace('\\', '.')
        if module_path.startswith('.'):
            module_path = module_path[1:]
        if module_path.endswith('.py'):
            module_path = module_path[:-3]
            
        for imp in data['imports']:
            imported_module = imp['module']
            if imported_module.startswith('app.'):
                dependencies[module_path].add(imported_module)
                
    # البحث عن الدوائر
    def find_cycle(node, visited, rec_stack, path):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in dependencies.get(node, []):
            if neighbor not in visited:
                cycle = find_cycle(neighbor, visited, rec_stack, path[:])
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                # وجدنا دائرة
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
                
        rec_stack.remove(node)
        return None
        
    cycles = []
    visited = set()
    
    for node in dependencies:
        if node not in visited:
            cycle = find_cycle(node, visited, set(), [])
            if cycle:
                cycles.append(cycle)
                
    return cycles


def analyze_duplicates(all_files_data: list[dict]) -> dict:
    """تحليل الكود المكرر"""
    # تجميع الدوال حسب الاسم
    function_names = defaultdict(list)
    for data in all_files_data:
        for func in data['functions']:
            function_names[func['name']].append({
                'file': data['filepath'],
                'line': func['lineno']
            })
            
    # إيجاد الدوال المكررة
    duplicate_functions = {}
    for name, locations in function_names.items():
        if len(locations) > 1:
            # تجاهل الدوال الخاصة والسحرية
            if not (name.startswith('__') and name.endswith('__')):
                duplicate_functions[name] = locations
                
    # تجميع الكلاسات حسب الاسم
    class_names = defaultdict(list)
    for data in all_files_data:
        for cls in data['classes']:
            class_names[cls['name']].append({
                'file': data['filepath'],
                'line': cls['lineno']
            })
            
    # إيجاد الكلاسات المكررة
    duplicate_classes = {}
    for name, locations in class_names.items():
        if len(locations) > 1:
            duplicate_classes[name] = locations
            
    return {
        'duplicate_functions': duplicate_functions,
        'duplicate_classes': duplicate_classes
    }


def main():
    """الدالة الرئيسية"""
    print("🔍 بدء تحليل الكود الميت...")
    print("=" * 80)
    
    # المجلدات المستهدفة
    target_dirs = [
        'app/boundaries',
        'app/services',
        'app/core',
        'app/middleware',
        'app/security'
    ]
    
    # البحث عن الملفات
    print("\n📁 البحث عن ملفات Python...")
    files = find_python_files(target_dirs)
    print(f"   وجدت {len(files)} ملف")
    
    # تحليل الملفات
    print("\n🔬 تحليل الملفات...")
    all_files_data = []
    for filepath in files:
        data = analyze_file(filepath)
        all_files_data.append(data)
        
    # إحصائيات عامة
    total_lines = sum(d['lines'] for d in all_files_data)
    total_functions = sum(len(d['functions']) for d in all_files_data)
    total_classes = sum(len(d['classes']) for d in all_files_data)
    
    print(f"\n📊 إحصائيات عامة:")
    print(f"   إجمالي الأسطر: {total_lines:,}")
    print(f"   إجمالي الدوال: {total_functions:,}")
    print(f"   إجمالي الكلاسات: {total_classes:,}")
    
    # تحليل الاستيرادات
    print("\n📦 تحليل الاستيرادات...")
    import_analysis = analyze_imports(all_files_data)
    print(f"   الملفات غير المستوردة أبداً: {len(import_analysis['never_imported'])}")
    
    # تحليل الدوال
    print("\n🔧 تحليل الدوال...")
    function_analysis = analyze_functions(all_files_data)
    print(f"   الدوال غير المستدعاة: {len(function_analysis['uncalled_functions'])}")
    
    # تحليل الكلاسات
    print("\n🏗️  تحليل الكلاسات...")
    class_analysis = analyze_classes(all_files_data)
    print(f"   الكلاسات غير المستخدمة: {len(class_analysis['unused_classes'])}")
    
    # تحليل التبعيات الدائرية
    print("\n🔄 تحليل التبعيات الدائرية...")
    cycles = find_circular_dependencies(all_files_data)
    print(f"   التبعيات الدائرية: {len(cycles)}")
    
    # تحليل التكرار
    print("\n📋 تحليل الكود المكرر...")
    duplicate_analysis = analyze_duplicates(all_files_data)
    print(f"   الدوال المكررة: {len(duplicate_analysis['duplicate_functions'])}")
    print(f"   الكلاسات المكررة: {len(duplicate_analysis['duplicate_classes'])}")
    
    # طباعة التفاصيل
    print("\n" + "=" * 80)
    print("📝 تفاصيل النتائج:")
    print("=" * 80)
    
    # الملفات غير المستوردة
    if import_analysis['never_imported']:
        print("\n🚫 الملفات التي لا يتم استيرادها أبداً:")
        for filepath in sorted(import_analysis['never_imported'])[:20]:
            print(f"   - {filepath}")
        if len(import_analysis['never_imported']) > 20:
            print(f"   ... و {len(import_analysis['never_imported']) - 20} ملف آخر")
            
    # الدوال غير المستدعاة
    if function_analysis['uncalled_functions']:
        print("\n🔇 الدوال التي لا يتم استدعاؤها:")
        for func in sorted(function_analysis['uncalled_functions'], 
                          key=lambda x: x['file'])[:30]:
            print(f"   - {func['name']} في {func['file']}:{func['line']}")
        if len(function_analysis['uncalled_functions']) > 30:
            print(f"   ... و {len(function_analysis['uncalled_functions']) - 30} دالة أخرى")
            
    # الكلاسات غير المستخدمة
    if class_analysis['unused_classes']:
        print("\n🏚️  الكلاسات غير المستخدمة:")
        for cls in sorted(class_analysis['unused_classes'], 
                         key=lambda x: x['file'])[:20]:
            print(f"   - {cls['name']} في {cls['file']}:{cls['line']}")
        if len(class_analysis['unused_classes']) > 20:
            print(f"   ... و {len(class_analysis['unused_classes']) - 20} كلاس آخر")
            
    # التبعيات الدائرية
    if cycles:
        print("\n♻️  التبعيات الدائرية:")
        for i, cycle in enumerate(cycles[:5], 1):
            print(f"   {i}. {' -> '.join(cycle)}")
        if len(cycles) > 5:
            print(f"   ... و {len(cycles) - 5} دائرة أخرى")
            
    # الدوال المكررة
    if duplicate_analysis['duplicate_functions']:
        print("\n👥 الدوال المكررة:")
        for name, locations in sorted(duplicate_analysis['duplicate_functions'].items())[:15]:
            print(f"   - {name} ({len(locations)} نسخة):")
            for loc in locations[:3]:
                print(f"     • {loc['file']}:{loc['line']}")
        if len(duplicate_analysis['duplicate_functions']) > 15:
            print(f"   ... و {len(duplicate_analysis['duplicate_functions']) - 15} دالة مكررة أخرى")
            
    # الكلاسات المكررة
    if duplicate_analysis['duplicate_classes']:
        print("\n🏢 الكلاسات المكررة:")
        for name, locations in sorted(duplicate_analysis['duplicate_classes'].items())[:10]:
            print(f"   - {name} ({len(locations)} نسخة):")
            for loc in locations:
                print(f"     • {loc['file']}:{loc['line']}")
                
    print("\n" + "=" * 80)
    print("✅ اكتمل التحليل!")
    
    # حفظ النتائج
    import json
    results = {
        'summary': {
            'total_files': len(files),
            'total_lines': total_lines,
            'total_functions': total_functions,
            'total_classes': total_classes,
            'never_imported_files': len(import_analysis['never_imported']),
            'uncalled_functions': len(function_analysis['uncalled_functions']),
            'unused_classes': len(class_analysis['unused_classes']),
            'circular_dependencies': len(cycles),
            'duplicate_functions': len(duplicate_analysis['duplicate_functions']),
            'duplicate_classes': len(duplicate_analysis['duplicate_classes'])
        },
        'details': {
            'never_imported': import_analysis['never_imported'],
            'uncalled_functions': function_analysis['uncalled_functions'],
            'unused_classes': class_analysis['unused_classes'],
            'circular_dependencies': cycles,
            'duplicate_functions': {k: v for k, v in duplicate_analysis['duplicate_functions'].items()},
            'duplicate_classes': {k: v for k, v in duplicate_analysis['duplicate_classes'].items()}
        }
    }
    
    with open('dead_code_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n💾 تم حفظ النتائج في: dead_code_analysis.json")


if __name__ == '__main__':
    main()
