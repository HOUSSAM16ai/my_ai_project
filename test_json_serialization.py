#!/usr/bin/env python3
"""Test script to verify JSON serialization works after fixes"""

import sys
import os
sys.path.insert(0, '/home/ubuntu/repos/my_ai_project')

try:
    from app.overmind.planning.deep_indexer import build_index
    import json
    
    print("Testing deep indexer JSON serialization...")
    idx = build_index('.')
    
    json_str = json.dumps(idx)
    print(f"JSON serialization successful! Length: {len(json_str)} characters")
    
    print(f"Files scanned: {idx.get('files_scanned', 0)}")
    print(f"Global metrics: {bool(idx.get('global_metrics'))}")
    print(f"Config included: {bool(idx.get('config'))}")
    
    print("✅ All JSON serialization tests passed!")
    
except Exception as e:
    print(f"❌ JSON serialization failed: {e}")
    sys.exit(1)
