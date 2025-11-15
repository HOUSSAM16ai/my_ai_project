#!/usr/bin/env python3
"""
Check environment configuration for OPENROUTER_API_KEY
"""
import os
import sys

print("=" * 70)
print("🔍 ENVIRONMENT CONFIGURATION CHECK")
print("=" * 70)

# Check if we're in Codespaces
is_codespaces = os.getenv('CODESPACES', 'false') == 'true'
print(f"\n📍 Environment: {'GitHub Codespaces' if is_codespaces else 'Local/Other'}")

# Check for OPENROUTER_API_KEY
openrouter_key = os.getenv('OPENROUTER_API_KEY')

if openrouter_key:
    # Show only first and last 4 characters for security
    masked_key = f"{openrouter_key[:7]}...{openrouter_key[-4:]}" if len(openrouter_key) > 11 else "***"
    print(f"✅ OPENROUTER_API_KEY: Found ({masked_key})")
    print(f"   Length: {len(openrouter_key)} characters")
    
    # Validate format
    if openrouter_key.startswith('sk-or-v1-'):
        print("   Format: ✅ Valid OpenRouter format")
    else:
        print("   Format: ⚠️  Unexpected format (should start with 'sk-or-v1-')")
else:
    print("❌ OPENROUTER_API_KEY: NOT FOUND")
    print("\n⚠️  To fix this in GitHub Codespaces:")
    print("   1. Go to: https://github.com/settings/codespaces")
    print("   2. Or: Repository Settings > Secrets > Codespaces")
    print("   3. Add secret: OPENROUTER_API_KEY")
    print("   4. Value: Your OpenRouter API key (starts with sk-or-v1-)")
    print("   5. Rebuild the Codespace")

# Check other important variables
print("\n📋 Other Configuration:")
for key in ['SECRET_KEY', 'DATABASE_URL', 'DEFAULT_AI_MODEL']:
    value = os.getenv(key)
    if value:
        if 'KEY' in key or 'PASSWORD' in key:
            print(f"   ✅ {key}: Set (hidden)")
        else:
            preview = value[:50] + "..." if len(value) > 50 else value
            print(f"   ✅ {key}: {preview}")
    else:
        print(f"   ⚠️  {key}: Not set")

print("\n" + "=" * 70)

sys.exit(0 if openrouter_key else 1)
