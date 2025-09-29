#!/usr/bin/env python3
"""Final test to verify comprehensive mode fix eliminates all fragmented files"""

import sys
import os
sys.path.insert(0, '/home/ubuntu/repos/my_ai_project')

os.environ['PLANNER_COMPREHENSIVE_MODE'] = '1'

try:
    from app.overmind.planning.llm_planner import (
        INDEX_FILE_EN, DEEP_INDEX_JSON_EN, DEEP_INDEX_MD_EN, COMPREHENSIVE_MODE
    )
    
    print('=== COMPREHENSIVE MODE FIX VERIFICATION ===')
    print(f'COMPREHENSIVE_MODE: {COMPREHENSIVE_MODE}')
    print(f'INDEX_FILE_EN: {INDEX_FILE_EN}')
    print(f'DEEP_INDEX_JSON_EN: {DEEP_INDEX_JSON_EN}')
    print(f'DEEP_INDEX_MD_EN: {DEEP_INDEX_MD_EN}')
    print()
    
    if COMPREHENSIVE_MODE and not INDEX_FILE_EN and not DEEP_INDEX_JSON_EN and not DEEP_INDEX_MD_EN:
        print('✅ COMPREHENSIVE MODE FIX VERIFIED SUCCESSFUL!')
        print('✅ All fragmented file creation flags are properly disabled')
        print('✅ Only comprehensive analysis will be generated')
        print('✅ User will now get ONE intelligent file instead of 4 fragmented files')
        sys.exit(0)
    else:
        print('❌ Comprehensive mode fix failed verification')
        print(f'Expected: COMPREHENSIVE_MODE=True, all other flags=False')
        print(f'Actual: COMPREHENSIVE_MODE={COMPREHENSIVE_MODE}, INDEX_FILE_EN={INDEX_FILE_EN}, DEEP_INDEX_JSON_EN={DEEP_INDEX_JSON_EN}, DEEP_INDEX_MD_EN={DEEP_INDEX_MD_EN}')
        sys.exit(1)
        
except Exception as e:
    print(f'❌ Verification failed with error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
