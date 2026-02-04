#!/bin/bash
# Quick Setup Script for AI Features
# This script helps you quickly set up API keys for AI features

set -e

echo "========================================================================"
echo "🚀 AI Features Quick Setup"
echo "========================================================================"
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    echo ""
    read -p "Do you want to update it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting without changes."
        exit 0
    fi
else
    echo "Creating new .env file..."
    cp .env.example .env
    echo "✅ .env file created from .env.example"
    echo ""
fi

# Ask user which service they want to use
echo "Which AI service do you want to configure?"
echo ""
echo "1) OpenRouter (Recommended)"
echo "   - Multiple models available"
echo "   - More affordable"
echo "   - Free trial"
echo "   - Get key at: https://openrouter.ai/keys"
echo ""
echo "2) OpenAI"
echo "   - GPT-4 and GPT-3.5"
echo "   - Requires paid account"
echo "   - Get key at: https://platform.openai.com/api-keys"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "Enter your OpenRouter API key (starts with sk-or-v1-):"
        read -r api_key

        if [[ ! $api_key == sk-or-* ]]; then
            echo "⚠️  Warning: OpenRouter keys usually start with 'sk-or-'"
            echo "   But continuing anyway..."
        fi

        # Update .env file
        if grep -q "^OPENROUTER_API_KEY=" .env 2>/dev/null; then
            # Update existing line
            sed -i.bak "s|^OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=\"$api_key\"|" .env
        else
            # Add new line
            echo "OPENROUTER_API_KEY=\"$api_key\"" >> .env
        fi

        echo "✅ OpenRouter API key configured!"
        ;;

    2)
        echo ""
        echo "Enter your OpenAI API key (starts with sk-):"
        read -r api_key

        if [[ ! $api_key == sk-* ]]; then
            echo "⚠️  Warning: OpenAI keys usually start with 'sk-'"
            echo "   But continuing anyway..."
        fi

        # Update .env file
        if grep -q "^OPENAI_API_KEY=" .env 2>/dev/null; then
            # Update existing line
            sed -i.bak "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=\"$api_key\"|" .env
        else
            # Add new line
            echo "OPENAI_API_KEY=\"$api_key\"" >> .env
        fi

        echo "✅ OpenAI API key configured!"
        ;;

    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "========================================================================"
echo "✅ Setup Complete!"
echo "========================================================================"
echo ""
echo "Next steps:"
echo "1. Restart your application (if running)"
echo "2. Run: python check_api_config.py"
echo "3. Test AI features in the admin dashboard"
echo ""
echo "Need help? See: FIX_ANALYZE_PROJECT_500_ERROR.md"
echo "========================================================================"
