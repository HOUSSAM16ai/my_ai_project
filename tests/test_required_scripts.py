#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the three required scripts:
1. apply_migrations.py
2. setup_supabase_connection.py
3. run.py
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_apply_migrations_script_exists():
    """Test that apply_migrations.py exists and can be imported"""
    script_path = Path(__file__).parent.parent / 'apply_migrations.py'
    assert script_path.exists(), "apply_migrations.py script not found"
    
    # Test that the script can be imported
    import apply_migrations
    assert hasattr(apply_migrations, 'main'), "apply_migrations.py missing main function"
    assert hasattr(apply_migrations, 'print_success'), "apply_migrations.py missing print_success function"
    print("✅ apply_migrations.py exists and has required functions")


def test_setup_supabase_connection_script_exists():
    """Test that setup_supabase_connection.py exists and can be imported"""
    script_path = Path(__file__).parent.parent / 'setup_supabase_connection.py'
    assert script_path.exists(), "setup_supabase_connection.py script not found"
    
    # Test that the script can be imported
    import setup_supabase_connection
    assert hasattr(setup_supabase_connection, 'main'), "setup_supabase_connection.py missing main function"
    assert hasattr(setup_supabase_connection, 'print_success'), "setup_supabase_connection.py missing print_success function"
    print("✅ setup_supabase_connection.py exists and has required functions")


def test_run_script_exists():
    """Test that run.py exists and can be imported"""
    script_path = Path(__file__).parent.parent / 'run.py'
    assert script_path.exists(), "run.py script not found"
    
    # Test that the script has the required structure
    with open(script_path, 'r') as f:
        content = f.read()
        assert 'from app import create_app' in content, "run.py missing app import"
        assert 'if __name__' in content, "run.py missing main execution block"
    print("✅ run.py exists and has required structure")


def test_scripts_are_executable():
    """Test that all scripts are executable"""
    scripts = [
        'apply_migrations.py',
        'setup_supabase_connection.py'
    ]
    
    for script in scripts:
        script_path = Path(__file__).parent.parent / script
        assert os.access(script_path, os.X_OK), f"{script} is not executable"
    
    print("✅ All required scripts are executable")


if __name__ == "__main__":
    print("Testing required scripts...")
    test_apply_migrations_script_exists()
    test_setup_supabase_connection_script_exists()
    test_run_script_exists()
    test_scripts_are_executable()
    print("\n✅ All tests passed!")
