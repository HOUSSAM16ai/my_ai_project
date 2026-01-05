"""
End-to-End Integration Tests for Chat Functionality

هذه الاختبارات تضمن أن المحادثات تعمل من البداية للنهاية
وتكتشف أي مشاكل في البنية أو الوصول للدوال
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestServiceMethodsAccessibility:
    """
    CRITICAL: Tests to verify all service methods are accessible
    
    These tests prevent the catastrophic failure where methods
    were defined outside the class scope
    """
    
    def test_admin_chat_boundary_service_has_all_methods(self):
        """
        Verify AdminChatBoundaryService has all required methods
        
        This test will FAIL if methods are not properly indented inside the class
        """
        from app.services.boundaries.admin_chat_boundary_service import AdminChatBoundaryService
        from unittest.mock import MagicMock
        
        required_methods = [
            'verify_conversation_access',
            'get_or_create_conversation',
            'save_message',
            'get_chat_history',
            'stream_chat_response',
            'stream_chat_response_safe',
            'orchestrate_chat_stream',
            'get_latest_conversation_details',
            'list_user_conversations',
            'get_conversation_details'
        ]
        
        # Create service with mock db
        mock_db = MagicMock()
        service = AdminChatBoundaryService(db=mock_db)
        
        for method_name in required_methods:
            assert hasattr(service, method_name), \
                f"CRITICAL: Method '{method_name}' not found in AdminChatBoundaryService! Check class indentation."
            
            method = getattr(service, method_name)
            assert callable(method), \
                f"CRITICAL: '{method_name}' is not callable! Check class indentation."
    
    def test_methods_are_instance_methods_not_module_functions(self):
        """
        Verify methods are bound to instance, not module-level functions
        
        This catches the indentation error where methods were at module level
        """
        from app.services.boundaries.admin_chat_boundary_service import AdminChatBoundaryService
        from unittest.mock import MagicMock
        import inspect
        
        mock_db = MagicMock()
        service = AdminChatBoundaryService(db=mock_db)
        
        # Test a few critical methods
        critical_methods = [
            'orchestrate_chat_stream',
            'get_latest_conversation_details',
            'list_user_conversations'
        ]
        
        for method_name in critical_methods:
            method = getattr(service, method_name)
            
            # Verify it's a bound method
            assert inspect.ismethod(method), \
                f"CRITICAL: '{method_name}' is not a bound method! It might be defined outside the class."
            
            # Verify it has 'self' as first parameter (excluding first param which is self)
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())
            
            # For bound methods, 'self' is already bound and won't appear in signature
            # But we can check that the method is bound to the instance
            assert method.__self__ is service, \
                f"CRITICAL: '{method_name}' is not bound to service instance!"


class TestStructureValidation:
    """
    Structure validation tests to prevent indentation catastrophes
    """
    
    def test_no_module_level_async_defs_in_service(self):
        """
        Verify no async def functions exist at module level in service file
        (All should be methods inside the class)
        """
        service_file = Path(__file__).resolve().parents[2] / "app/services/boundaries/admin_chat_boundary_service.py"
        
        with open(service_file, 'r') as f:
            lines = f.readlines()
        
        in_class = False
        class_indent = 0
        issues = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            
            # Track when we're inside the class
            if stripped.startswith('class AdminChatBoundaryService'):
                in_class = True
                class_indent = indent
                continue
            
            # If we find a class at same level, we're out of the previous class
            if in_class and stripped.startswith('class ') and indent == class_indent:
                in_class = False
            
            # Check for async def at wrong indentation
            if stripped.startswith('async def '):
                # Methods should be indented inside class (at least class_indent + 4)
                if in_class and indent <= class_indent:
                    issues.append(f"Line {i}: Method '{stripped[:40]}' appears to be outside class (indent: {indent}, class: {class_indent})")
                elif not in_class and not stripped.startswith('async def _'):
                    # Module-level functions should be private (start with _)
                    issues.append(f"Line {i}: Public async function at module level: '{stripped[:40]}'")
        
        assert len(issues) == 0, \
            f"CRITICAL STRUCTURE ERRORS FOUND:\n" + "\n".join(issues)
