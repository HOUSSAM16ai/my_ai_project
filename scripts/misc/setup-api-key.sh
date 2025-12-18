#!/bin/bash
# ======================================================================================
# ==           QUICK API KEY SETUP SCRIPT - Superhuman Edition                       ==
# ======================================================================================
# This script helps you quickly configure the AI service for the admin dashboard.
# It creates or updates your .env file with the necessary API key.

set -e

echo "🚀 CogniForge AI Service Setup"
echo "================================"
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists."
    read -p "Do you want to update it? (y/n): " update_env
    if [ "$update_env" != "y" ] && [ "$update_env" != "Y" ]; then
        echo "Setup cancelled."
        exit 0
    fi
    echo ""
fi

# Ask which service to use
echo "Which AI service would you like to use?"
echo ""
echo "1) OpenRouter (Recommended - Access to multiple models)"
echo "2) OpenAI Direct"
echo ""
read -p "Enter your choice (1 or 2): " service_choice

case $service_choice in
    1)
        echo ""
        echo "📝 You selected: OpenRouter"
        echo ""
        echo "To get your OpenRouter API key:"
        echo "1. Visit: https://openrouter.ai/keys"
        echo "2. Sign up or log in"
        echo "3. Create a new API key"
        echo "4. Copy the key (starts with 'sk-or-v1-')"
        echo ""
        read -p "Enter your OpenRouter API key: " api_key
        
        if [[ ! $api_key =~ ^sk-or-v1- ]]; then
            echo ""
            echo "⚠️  Warning: OpenRouter keys usually start with 'sk-or-v1-'"
            read -p "Continue anyway? (y/n): " continue_anyway
            if [ "$continue_anyway" != "y" ] && [ "$continue_anyway" != "Y" ]; then
                echo "Setup cancelled."
                exit 1
            fi
        fi
        
        # Create or update .env
        if [ -f .env ]; then
            # Update existing .env
            if grep -q "^OPENROUTER_API_KEY=" .env; then
                sed -i "s|^OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=\"$api_key\"|" .env
            else
                echo "OPENROUTER_API_KEY=\"$api_key\"" >> .env
            fi
            
            if ! grep -q "^DEFAULT_AI_MODEL=" .env; then
                echo "DEFAULT_AI_MODEL=\"openai/gpt-4o-mini\"" >> .env
            fi
        else
            # Create new .env from template
            cp .env.example .env
            sed -i "s|OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=\"$api_key\"|" .env
            sed -i "s|DEFAULT_AI_MODEL=.*|DEFAULT_AI_MODEL=\"openai/gpt-4o-mini\"|" .env
        fi
        ;;
        
    2)
        echo ""
        echo "📝 You selected: OpenAI Direct"
        echo ""
        echo "To get your OpenAI API key:"
        echo "1. Visit: https://platform.openai.com/api-keys"
        echo "2. Sign up or log in"
        echo "3. Create a new API key"
        echo "4. Copy the key (starts with 'sk-')"
        echo ""
        read -p "Enter your OpenAI API key: " api_key
        
        if [[ ! $api_key =~ ^sk- ]]; then
            echo ""
            echo "⚠️  Warning: OpenAI keys usually start with 'sk-'"
            read -p "Continue anyway? (y/n): " continue_anyway
            if [ "$continue_anyway" != "y" ] && [ "$continue_anyway" != "Y" ]; then
                echo "Setup cancelled."
                exit 1
            fi
        fi
        
        # Create or update .env
        if [ -f .env ]; then
            # Update existing .env
            if grep -q "^OPENAI_API_KEY=" .env; then
                sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=\"$api_key\"|" .env
            else
                echo "OPENAI_API_KEY=\"$api_key\"" >> .env
            fi
            
            if ! grep -q "^DEFAULT_AI_MODEL=" .env; then
                echo "DEFAULT_AI_MODEL=\"gpt-4o-mini\"" >> .env
            fi
        else
            # Create new .env from template
            cp .env.example .env
            sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=\"$api_key\"|" .env
            sed -i "s|DEFAULT_AI_MODEL=.*|DEFAULT_AI_MODEL=\"gpt-4o-mini\"|" .env
        fi
        ;;
        
    *)
        echo ""
        echo "❌ Invalid choice. Please run the script again and select 1 or 2."
        exit 1
        ;;
esac

echo ""
echo "✅ API key configured successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Restart your application:"
echo "   - Docker: docker-compose restart"
echo "   - Flask: flask run"
echo "   - Gunicorn: pkill gunicorn && gunicorn run:app"
echo ""
echo "2. Navigate to /admin/dashboard"
echo "3. Try asking a question in the AI chat"
echo ""
echo "🎉 You're all set! Enjoy your superhuman AI assistant!"
