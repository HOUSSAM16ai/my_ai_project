#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check API Configuration Status
===============================
This script checks if API keys are properly configured for the AI features.

Usage:
    python check_api_config.py

This will check:
1. Environment variables (OPENROUTER_API_KEY, OPENAI_API_KEY)
2. .env file existence and content
3. Provide guidance on how to fix configuration issues
"""

import os
import sys
from pathlib import Path


def check_env_file():
    """Check if .env file exists and contains API keys"""
    env_file = Path('.env')
    
    if not env_file.exists():
        return {
            'exists': False,
            'has_openrouter': False,
            'has_openai': False,
            'message': '❌ .env file not found'
        }
    
    # Read .env file
    content = env_file.read_text()
    has_openrouter = 'OPENROUTER_API_KEY' in content and '=' in content
    has_openai = 'OPENAI_API_KEY' in content and '=' in content
    
    return {
        'exists': True,
        'has_openrouter': has_openrouter,
        'has_openai': has_openai,
        'message': f'✅ .env file found (OpenRouter: {has_openrouter}, OpenAI: {has_openai})'
    }


def check_environment_variables():
    """Check if API keys are set in environment variables"""
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    return {
        'openrouter': {
            'set': bool(openrouter_key),
            'length': len(openrouter_key) if openrouter_key else 0,
            'valid_prefix': openrouter_key.startswith('sk-or-') if openrouter_key else False
        },
        'openai': {
            'set': bool(openai_key),
            'length': len(openai_key) if openai_key else 0,
            'valid_prefix': openai_key.startswith('sk-') if openai_key else False
        }
    }


def print_status():
    """Print configuration status and guidance"""
    print("=" * 70)
    print("🔍 API Configuration Check")
    print("=" * 70)
    print()
    
    # Check environment variables
    print("1️⃣  Environment Variables:")
    print("-" * 70)
    env_vars = check_environment_variables()
    
    if env_vars['openrouter']['set']:
        print(f"✅ OPENROUTER_API_KEY: Set (length: {env_vars['openrouter']['length']})")
        if env_vars['openrouter']['valid_prefix']:
            print("   ✓ Valid prefix (sk-or-)")
        else:
            print("   ⚠️  Warning: Key doesn't start with 'sk-or-' (might be invalid)")
    else:
        print("❌ OPENROUTER_API_KEY: Not set")
    
    print()
    
    if env_vars['openai']['set']:
        print(f"✅ OPENAI_API_KEY: Set (length: {env_vars['openai']['length']})")
        if env_vars['openai']['valid_prefix']:
            print("   ✓ Valid prefix (sk-)")
        else:
            print("   ⚠️  Warning: Key doesn't start with 'sk-' (might be invalid)")
    else:
        print("❌ OPENAI_API_KEY: Not set")
    
    print()
    
    # Check .env file
    print("2️⃣  .env File:")
    print("-" * 70)
    env_file_info = check_env_file()
    print(env_file_info['message'])
    
    if env_file_info['exists']:
        if env_file_info['has_openrouter']:
            print("   ✓ Contains OPENROUTER_API_KEY")
        if env_file_info['has_openai']:
            print("   ✓ Contains OPENAI_API_KEY")
    
    print()
    
    # Determine overall status
    has_api_key = (env_vars['openrouter']['set'] or env_vars['openai']['set'] or 
                   (env_file_info['exists'] and (env_file_info['has_openrouter'] or env_file_info['has_openai'])))
    
    print("3️⃣  Overall Status:")
    print("-" * 70)
    
    if has_api_key:
        print("✅ AI features should work!")
        print()
        print("ℹ️  Notes:")
        print("   - The application will use environment variables first")
        print("   - Then fall back to .env file")
        print("   - OpenRouter is recommended for better model access")
    else:
        print("❌ AI features will NOT work - No API keys configured")
        print()
        print("📝 How to fix:")
        print()
        print("Option 1: Using .env file (Recommended for local development)")
        print("-" * 70)
        print("1. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print()
        print("2. Edit .env and add your API key:")
        print("   OPENROUTER_API_KEY=sk-or-v1-your-key-here")
        print("   # OR")
        print("   OPENAI_API_KEY=sk-your-key-here")
        print()
        print("3. Get your API key:")
        print("   OpenRouter: https://openrouter.ai/keys")
        print("   OpenAI: https://platform.openai.com/api-keys")
        print()
        print("4. Restart the application")
        print()
        
        print("Option 2: Using Codespaces Secrets")
        print("-" * 70)
        print("1. Go to: https://github.com/settings/codespaces")
        print("2. Under 'Codespaces secrets', click 'New secret'")
        print("3. Name: OPENROUTER_API_KEY (or OPENAI_API_KEY)")
        print("4. Value: Your API key")
        print("5. Select repository access")
        print("6. Restart your Codespace")
        print()
        
        print("Option 3: Using Environment Variables (Production/CI)")
        print("-" * 70)
        print("1. Set environment variable before running:")
        print("   export OPENROUTER_API_KEY=sk-or-v1-your-key-here")
        print("   # OR")
        print("   export OPENAI_API_KEY=sk-your-key-here")
        print()
        print("2. Run the application")
        print()
    
    print("=" * 70)
    print()
    
    # Return exit code
    return 0 if has_api_key else 1


if __name__ == '__main__':
    sys.exit(print_status())
