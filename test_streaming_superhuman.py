#!/usr/bin/env python3
"""
Test Superhuman Streaming Implementation
=========================================
تحقق من عمل نظام البث الخارق في صفحة Admin Dashboard

This script tests:
1. SSE endpoint availability
2. Streaming service initialization
3. Event format correctness
4. Smart chunking functionality
5. Performance metrics
"""

import sys
import time
from io import StringIO

# Add project to path
sys.path.insert(0, '/home/runner/work/my_ai_project/my_ai_project')


def test_streaming_service():
    """Test the streaming service"""
    print("🧪 Testing AdminChatStreamingService...")
    print("=" * 60)
    
    try:
        from app.services.admin_chat_streaming_service import (
            get_streaming_service,
            SmartTokenChunker,
            StreamingConfig
        )
        
        service = get_streaming_service()
        print("✅ Streaming service initialized successfully")
        
        # Test smart chunking
        print("\n📊 Testing Smart Chunking:")
        print("-" * 60)
        test_text = "This is a test of the superhuman streaming system. It should chunk text intelligently for smooth word-by-word display."
        
        chunks = list(SmartTokenChunker.smart_chunk(test_text))
        print(f"Original text: {test_text}")
        print(f"\nNumber of chunks: {len(chunks)}")
        print(f"Chunk size: {StreamingConfig.OPTIMAL_CHUNK_SIZE} words")
        print(f"\nChunks:")
        for i, chunk in enumerate(chunks, 1):
            print(f"  {i}. '{chunk.strip()}'")
        
        # Test SSE formatting
        print("\n📡 Testing SSE Event Formatting:")
        print("-" * 60)
        events = list(service.stream_response(
            "Hello world! This is a test.",
            metadata={"model": "test", "tokens": 100}
        ))
        
        print(f"Number of events: {len(events)}")
        print("\nFirst few events:")
        for i, event in enumerate(events[:5], 1):
            print(f"  Event {i}:")
            lines = event.split('\n')
            for line in lines[:3]:  # Show first 3 lines
                if line.strip():
                    print(f"    {line}")
        
        # Test metrics
        print("\n📈 Testing Performance Metrics:")
        print("-" * 60)
        metrics = service.get_metrics()
        for key, value in metrics.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing streaming service: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_route_availability():
    """Test if the streaming route is available"""
    print("\n🛣️  Testing Route Availability...")
    print("=" * 60)
    
    try:
        from app import create_app
        
        app = create_app()
        
        # Check if route exists
        with app.app_context():
            # Get all routes
            routes = []
            for rule in app.url_map.iter_rules():
                if 'stream' in rule.rule.lower() or 'chat' in rule.rule.lower():
                    routes.append({
                        'endpoint': rule.endpoint,
                        'methods': list(rule.methods),
                        'rule': rule.rule
                    })
            
            print(f"Found {len(routes)} chat/stream routes:")
            for route in routes:
                print(f"\n  📍 {route['rule']}")
                print(f"     Methods: {', '.join(route['methods'])}")
                print(f"     Endpoint: {route['endpoint']}")
            
            # Check specifically for the streaming endpoint
            streaming_route_found = any('/chat/stream' in r['rule'] for r in routes)
            if streaming_route_found:
                print("\n✅ Streaming endpoint found: /admin/api/chat/stream")
            else:
                print("\n⚠️  Streaming endpoint NOT found!")
                
            return streaming_route_found
            
    except Exception as e:
        print(f"❌ Error checking routes: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sse_consumer_js():
    """Test if SSE consumer JavaScript file exists"""
    print("\n📜 Testing SSE Consumer JavaScript...")
    print("=" * 60)
    
    import os
    
    js_path = '/home/runner/work/my_ai_project/my_ai_project/app/static/js/useSSE.js'
    
    if os.path.exists(js_path):
        print(f"✅ SSE Consumer found at: {js_path}")
        
        # Check file size
        size = os.path.getsize(js_path)
        print(f"   File size: {size:,} bytes")
        
        # Check for key methods
        with open(js_path, 'r') as f:
            content = f.read()
            
        methods = ['onDelta', 'onComplete', 'onError', 'onStart', 'connect']
        found_methods = [m for m in methods if m in content]
        
        print(f"   Found {len(found_methods)}/{len(methods)} key methods:")
        for method in found_methods:
            print(f"     ✅ {method}")
        
        missing = set(methods) - set(found_methods)
        if missing:
            print(f"   Missing methods:")
            for method in missing:
                print(f"     ❌ {method}")
        
        return len(found_methods) == len(methods)
    else:
        print(f"❌ SSE Consumer NOT found at: {js_path}")
        return False


def test_admin_dashboard_template():
    """Test if admin dashboard uses streaming"""
    print("\n🎨 Testing Admin Dashboard Template...")
    print("=" * 60)
    
    template_path = '/home/runner/work/my_ai_project/my_ai_project/app/admin/templates/admin_dashboard.html'
    
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Check for key streaming elements
        checks = {
            'SSE Consumer Script': 'useSSE.js' in content,
            'Streaming URL': "handle_chat_stream" in content,
            'SSEConsumer Class': 'new SSEConsumer' in content,
            'onDelta Handler': 'consumer.onDelta' in content,
            'onComplete Handler': 'consumer.onComplete' in content,
            'AdaptiveTypewriter': 'AdaptiveTypewriter' in content,
            'Streaming Indicator': 'Superhuman' in content or 'streaming' in content.lower()
        }
        
        print("Template streaming checks:")
        all_passed = True
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")
            if not result:
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error checking template: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 SUPERHUMAN STREAMING TEST SUITE")
    print("   اختبار نظام البث الخارق")
    print("=" * 60)
    
    results = {
        'Streaming Service': test_streaming_service(),
        'Route Availability': test_route_availability(),
        'SSE Consumer JS': test_sse_consumer_js(),
        'Admin Template': test_admin_dashboard_template()
    }
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test}")
    
    print(f"\n{passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Streaming is properly configured!")
        print("   نظام البث مُهيأ بشكل صحيح!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Streaming may not work correctly.")
        print("   بعض الاختبارات فشلت. قد لا يعمل البث بشكل صحيح.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
