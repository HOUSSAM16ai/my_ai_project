#!/usr/bin/env python3
"""
محلل رسم التبعيات والعلاقات
يفحص العلاقات بين الملفات والوحدات
"""

import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def extract_imports(filepath: str) -> list[str]:
    """استخراج جميع الاستيرادات من ملف"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=filepath)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('app.'):
                        imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('app.'):
                    imports.append(node.module)
        
        return list(set(imports))
    except Exception:
        return []


def build_dependency_graph(directories: list[str]) -> dict:
    """بناء رسم التبعيات"""
    graph = defaultdict(set)
    file_to_module = {}
    
    # جمع جميع الملفات
    files = []
    for directory in directories:
        path = Path(directory)
        if path.exists():
            files.extend([str(f) for f in path.rglob("*.py")])
    
    # بناء خريطة الملفات إلى modules
    for filepath in files:
        module_path = filepath.replace('/', '.').replace('\\', '.')
        if module_path.startswith('.'):
            module_path = module_path[1:]
        if module_path.endswith('.py'):
            module_path = module_path[:-3]
        file_to_module[filepath] = module_path
    
    # بناء الرسم
    for filepath in files:
        module = file_to_module[filepath]
        imports = extract_imports(filepath)
        
        for imp in imports:
            graph[module].add(imp)
    
    return dict(graph), file_to_module


def find_isolated_modules(graph: dict) -> list[str]:
    """إيجاد الوحدات المعزولة (لا تستورد ولا تُستورد)"""
    all_modules = set(graph.keys())
    imported_modules = set()
    
    for imports in graph.values():
        imported_modules.update(imports)
    
    # الوحدات التي لا تستورد شيء
    no_imports = [m for m, imports in graph.items() if not imports]
    
    # الوحدات التي لا تُستورد
    not_imported = [m for m in all_modules if m not in imported_modules]
    
    # الوحدات المعزولة تماماً
    isolated = [m for m in no_imports if m in not_imported]
    
    return isolated


def find_highly_coupled_modules(graph: dict, threshold: int = 10) -> list[tuple]:
    """إيجاد الوحدات عالية الاقتران"""
    highly_coupled = []
    
    for module, imports in graph.items():
        if len(imports) >= threshold:
            highly_coupled.append((module, len(imports)))
    
    return sorted(highly_coupled, key=lambda x: x[1], reverse=True)


def find_hub_modules(graph: dict, threshold: int = 10) -> list[tuple]:
    """إيجاد الوحدات المحورية (التي تُستورد كثيراً)"""
    import_count = defaultdict(int)
    
    for imports in graph.values():
        for imp in imports:
            import_count[imp] += 1
    
    hubs = [(module, count) for module, count in import_count.items() 
            if count >= threshold]
    
    return sorted(hubs, key=lambda x: x[1], reverse=True)


def analyze_module_relationships(graph: dict, target_modules: list[str]) -> dict:
    """تحليل علاقات وحدات محددة"""
    results = {}
    
    for target in target_modules:
        # من يستورد هذه الوحدة؟
        importers = [m for m, imports in graph.items() if target in imports]
        
        # ماذا تستورد هذه الوحدة؟
        imports = list(graph.get(target, []))
        
        results[target] = {
            'imported_by': importers,
            'imports': imports,
            'imported_by_count': len(importers),
            'imports_count': len(imports)
        }
    
    return results


def main():
    """الدالة الرئيسية"""
    print("🕸️  تحليل رسم التبعيات")
    print("=" * 80)
    
    # المجلدات المستهدفة
    target_dirs = [
        'app/boundaries',
        'app/services',
        'app/core',
        'app/middleware',
        'app/security'
    ]
    
    print("\n📊 بناء رسم التبعيات...")
    graph, file_to_module = build_dependency_graph(target_dirs)
    
    print(f"   إجمالي الوحدات: {len(graph)}")
    print(f"   إجمالي التبعيات: {sum(len(imports) for imports in graph.values())}")
    
    # الوحدات المعزولة
    print("\n🏝️  الوحدات المعزولة (لا تستورد ولا تُستورد):")
    isolated = find_isolated_modules(graph)
    print(f"   وجدت {len(isolated)} وحدة معزولة")
    
    for module in isolated[:10]:
        print(f"   - {module}")
    
    if len(isolated) > 10:
        print(f"   ... و {len(isolated) - 10} وحدة أخرى")
    
    # الوحدات عالية الاقتران
    print("\n🔗 الوحدات عالية الاقتران (تستورد الكثير):")
    highly_coupled = find_highly_coupled_modules(graph, threshold=10)
    print(f"   وجدت {len(highly_coupled)} وحدة عالية الاقتران")
    
    for module, count in highly_coupled[:15]:
        print(f"   - {module}: {count} استيراد")
    
    # الوحدات المحورية
    print("\n⭐ الوحدات المحورية (تُستورد كثيراً):")
    hubs = find_hub_modules(graph, threshold=5)
    print(f"   وجدت {len(hubs)} وحدة محورية")
    
    for module, count in hubs[:15]:
        print(f"   - {module}: مستوردة {count} مرة")
    
    # تحليل الوحدات المشتبه بها
    print("\n🔍 تحليل الوحدات المشتبه بها:")
    suspicious_modules = [
        'app.boundaries.service_boundaries',
        'app.boundaries.policy_boundaries',
        'app.boundaries.data_boundaries',
        'app.core.base_profiler',
        'app.core.base_repository',
        'app.core.base_service',
        'app.services.data_mesh.facade',
        'app.services.api.api_config_secrets_service'
    ]
    
    relationships = analyze_module_relationships(graph, suspicious_modules)
    
    for module, data in relationships.items():
        print(f"\n   📦 {module}")
        print(f"      مستوردة من: {data['imported_by_count']} وحدة")
        print(f"      تستورد: {data['imports_count']} وحدة")
        
        if data['imported_by_count'] == 0:
            print(f"      ⚠️  لا أحد يستوردها - مرشحة للحذف!")
        elif data['imported_by_count'] <= 2:
            print(f"      ⚠️  استخدام محدود جداً")
            for importer in data['imported_by']:
                print(f"         • {importer}")
    
    # تحليل التكرارات
    print("\n🔄 تحليل الوحدات المكررة:")
    
    duplicate_patterns = {
        'CircuitBreaker': [
            'app.boundaries.service_boundaries',
            'app.infrastructure.patterns.circuit_breaker',
            'app.core.gateway.circuit_breaker',
            'app.core.resilience.circuit_breaker',
            'app.services.system.resilience.circuit_breaker',
            'app.services.llm_client.application.circuit_breaker'
        ],
        'EventBus': [
            'app.boundaries.service_boundaries',
            'app.infrastructure.patterns.event_bus',
            'app.core.event_bus'
        ],
        'BoundedContext': [
            'app.boundaries.service_boundaries',
            'app.core.domain_events',
            'app.services.data_mesh.domain.models'
        ]
    }
    
    for pattern_name, modules in duplicate_patterns.items():
        print(f"\n   🔁 {pattern_name}:")
        for module in modules:
            if module in graph or any(module in m for m in graph.keys()):
                rel = relationships.get(module, {})
                imported_by = rel.get('imported_by_count', 0)
                print(f"      • {module}")
                print(f"        مستوردة من: {imported_by} وحدة")
    
    # حفظ النتائج
    results = {
        'summary': {
            'total_modules': len(graph),
            'total_dependencies': sum(len(imports) for imports in graph.values()),
            'isolated_modules': len(isolated),
            'highly_coupled_modules': len(highly_coupled),
            'hub_modules': len(hubs)
        },
        'isolated_modules': isolated,
        'highly_coupled_modules': [{'module': m, 'imports': c} for m, c in highly_coupled],
        'hub_modules': [{'module': m, 'imported_by': c} for m, c in hubs],
        'suspicious_modules': relationships
    }
    
    with open('dependency_graph_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("✅ اكتمل التحليل!")
    print("💾 تم حفظ النتائج في: dependency_graph_analysis.json")


if __name__ == '__main__':
    main()
