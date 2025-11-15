import os

# This script checks if the OPENROUTER_API_KEY environment variable is accessible.
api_key = os.getenv('OPENROUTER_API_KEY')

if api_key:
    print(f"✅ Success: OPENROUTER_API_KEY is accessible.")
    # Print the first few and last few characters for verification, but not the whole key.
    print(f"   Key value: {api_key[:7]}...{api_key[-4:]}")
else:
    print("❌ Error: OPENROUTER_API_KEY is NOT found in the environment variables.")
