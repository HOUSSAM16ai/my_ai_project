#!/usr/bin/env python3
"""
Test script to verify admin routes can be imported and initialized
"""
import os
import sys

# Set minimal environment
os.environ['FLASK_ENV'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key-for-validation'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'
os.environ['OPENROUTER_API_KEY'] = 'sk-test-key'

try:
    print("Testing admin routes import...")
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        # Check if our route is registered
        routes = [str(rule) for rule in app.url_map.iter_rules()]
        stream_route = '/admin/api/chat/stream'
        
        if any(stream_route in route for route in routes):
            print(f"✓ Stream route found: {stream_route}")
        else:
            print("✗ Stream route NOT found!")
            print("Available admin routes:")
            for route in routes:
                if '/admin/' in route:
                    print(f"  - {route}")
        
        print("\n✓ Admin routes successfully imported and initialized")
        sys.exit(0)
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
