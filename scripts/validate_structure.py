"""
Pre-commit Structure Validation Script

هذا السكريبت يفحص البنية قبل كل commit لمنع أخطاء المسافات البادئة
"""
import ast
import sys
from pathlib import Path
from typing import List, Tuple


class ServiceStructureValidator:
    """Validates service class structures"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_file(self, filepath: Path) -> bool:
        """Validate a Python service file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            
            # Find service classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if node.name.endswith('Service'):
                        self._validate_service_class(node, filepath)
            
            return len(self.errors) == 0
            
        except SyntaxError as e:
            self.errors.append(f"{filepath}:{e.lineno} - Syntax Error: {e.msg}")
            return False
    
    def _validate_service_class(self, class_node: ast.ClassDef, filepath: Path):
        """Validate a service class structure"""
        class_name = class_node.name
        
        # Get all methods in the class
        methods = [n for n in class_node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        public_methods = [m for m in methods if not m.name.startswith('_')]
        
        if len(public_methods) < 3:
            self.warnings.append(
                f"{filepath} - {class_name}: Only {len(public_methods)} public methods found. "
                f"This might indicate methods are defined outside the class."
            )
        
        # Check for proper __init__ method
        init_methods = [m for m in methods if m.name == '__init__']
        if not init_methods:
            self.warnings.append(
                f"{filepath} - {class_name}: No __init__ method found"
            )
    
    def validate_indentation_consistency(self, filepath: Path) -> bool:
        """Validate indentation consistency in service files"""
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_class = False
        class_indent = None
        class_name = None
        method_indent = None
        
        for line_no, line in enumerate(lines, 1):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            
            # Detect class definition
            if stripped.startswith('class ') and 'Service' in stripped:
                in_class = True
                class_indent = indent
                class_name = stripped.split('(')[0].replace('class ', '').strip()
                method_indent = None
                continue
            
            if not in_class:
                continue
            
            # Detect method definitions inside class
            if stripped.startswith(('def ', 'async def ')):
                # Skip private helper functions (they're allowed at module level)
                if indent == 0 and (stripped.startswith('def _') or stripped.startswith('async def _')):
                    continue
                
                # Skip singleton getter functions at module level (pattern: def get_xxx_service())
                if indent == 0 and 'def get_' in stripped and '_service()' in stripped:
                    continue
                
                # Skip decorator functions at module level
                if indent == 0 and stripped.startswith('def ') and '(' in stripped:
                    func_name = stripped.split('(')[0].replace('def ', '').strip()
                    if func_name in ['resilient', 'cached', 'retry', 'with_timeout']:
                        continue
                
                if method_indent is None and indent > class_indent:
                    method_indent = indent
                
                # Methods should be indented relative to class
                if indent > 0 and indent <= class_indent:
                    self.errors.append(
                        f"{filepath}:{line_no} - CRITICAL: Public method '{stripped[:50]}' "
                        f"has incorrect indentation (indent={indent}, class_indent={class_indent}). "
                        f"Method appears to be defined OUTSIDE the '{class_name}' class!"
                    )
                elif method_indent and indent > class_indent and indent != method_indent:
                    self.warnings.append(
                        f"{filepath}:{line_no} - Inconsistent method indentation "
                        f"(expected={method_indent}, got={indent})"
                    )
            
            # Check for class end
            if stripped.startswith('class ') and indent == class_indent:
                in_class = False
                class_indent = None
                method_indent = None
        
        return len(self.errors) == 0
    
    def print_report(self):
        """Print validation report"""
        if self.errors:
            print("\n" + "="*80)
            print("❌ CRITICAL STRUCTURE ERRORS FOUND:")
            print("="*80)
            for error in self.errors:
                print(f"  ❌ {error}")
            print("="*80)
        
        if self.warnings:
            print("\n" + "="*80)
            print("⚠️  WARNINGS:")
            print("="*80)
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
            print("="*80)
        
        if not self.errors and not self.warnings:
            print("✅ All structure validations passed!")


def main():
    """Main validation function"""
    validator = ServiceStructureValidator()
    
    # Find all service files
    project_root = Path("/home/runner/work/my_ai_project/my_ai_project")
    service_files = list(project_root.glob("app/services/**/*service*.py"))
    
    print(f"Validating {len(service_files)} service files...")
    
    all_valid = True
    for service_file in service_files:
        print(f"  Checking {service_file.name}...")
        
        # Validate AST structure
        if not validator.validate_file(service_file):
            all_valid = False
        
        # Validate indentation
        if not validator.validate_indentation_consistency(service_file):
            all_valid = False
    
    validator.print_report()
    
    if not all_valid:
        print("\n❌ VALIDATION FAILED - Please fix the errors above before committing!")
        sys.exit(1)
    else:
        print("\n✅ All validations passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
