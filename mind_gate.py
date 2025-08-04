import os
import openai
from dotenv import load_dotenv
import sys

# --- 1. الإعداد والتحقق ---

def setup_ai_client():
    """Loads API key and configures the OpenRouter client."""
    print("🧠 Mind Gate Initializing...")
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        print("\n❌ FATAL ERROR: OPENROUTER_API_KEY not found in your .env file.")
        print("   Please ensure your key is correctly set in the .env file.")
        sys.exit(1)

    print("   ✅ API Key loaded.")

    try:
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        print("   ✅ AI Client configured. The Gate is open.")
        return client
    except Exception as e:
        print(f"\n❌ FATAL ERROR: Could not configure AI client: {e}")
        sys.exit(1)

# --- 2. دورة المحادثة ---

def start_conversation(client):
    """Starts an interactive conversation loop with the AI."""
    print("\n" + "="*50)
    print("🚀 Welcome to the CogniForge Mind Gate")
    print("   You are now talking directly to the AI.")
    print("   Type 'exit' or 'quit' to close the gate.")
    print("="*50 + "\n")

    while True:
        try:
            user_question = input("You: ")

            if user_question.lower() in ["exit", "quit"]:
                print("\n🚪 Mind Gate closing. Goodbye!")
                break
            
            if not user_question.strip():
                continue

            print("AI is thinking...")
            
            # --- هذا هو الجزء الذي تم تصحيحه ---
            # تم دمج 'model' و 'messages' في نفس استدعاء الدالة
            completion = client.chat.completions.create(
                model="google/gemini-2.5-pro",
                messages=[
                    {"role": "user", "content": user_question},
                ],
                timeout=90.0,
            )
            
            ai_response = completion.choices[0].message.content
            
            print(f"\nAI: {ai_response}\n")

        except openai.APITimeoutError:
            print("\n🚨 AI Error: The request timed out. The network might be slow. Please try again.\n")
        except Exception as e:
            print(f"\n🚨 An unexpected error occurred: {e}\n")


# --- 3. نقطة البداية ---

if __name__ == "__main__":
    ai_client = setup_ai_client()
    if ai_client:
        start_conversation(ai_client)