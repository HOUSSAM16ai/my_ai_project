#!/usr/bin/env python3
"""Test script to verify comprehensive mode works correctly"""

import sys
import os
sys.path.insert(0, '/home/ubuntu/repos/my_ai_project')

try:
    from app.services.generation_service import get_generation_service
    
    print("Testing comprehensive mode...")
    svc = get_generation_service()
    result = svc.generate_comprehensive_response('تحليل معمارية المشروع والحاويات')
    
    print(f"Status: {result.get('status')}")
    print(f"Response type: {result.get('meta', {}).get('response_type')}")
    print(f"Consolidated: {result.get('meta', {}).get('consolidated')}")
    
    if result.get('answer'):
        print(f"Answer length: {len(result['answer'])}")
        print(f"First 200 chars: {result['answer'][:200]}")
        print("✅ Comprehensive response generation successful!")
    else:
        print("❌ No answer generated")
        
except Exception as e:
    print(f"❌ Comprehensive mode test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
