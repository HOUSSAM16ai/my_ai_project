# app/cli/mindgate_commands.py - v3.1 (Defaulting to GPT-4o-mini)

import click
import openai
from flask import Blueprint, current_app

# The blueprint definition remains the same: powerful and scalable.
mindgate_cli = Blueprint('mindgate', __name__, cli_group="mindgate")

@mindgate_cli.cli.command("chat")
# --- هذا هو التعديل الوحيد والمهم ---
# لقد قمنا بتغيير القيمة الافتراضية إلى النموذج الجديد
@click.option('--model', default='openai/gpt-4o-mini', help='Specify the AI model ID from OpenRouter.')
def chat_command(model):
    """
    Opens the Mind Gate for a direct, interactive conversation with the AI.
    """
    click.secho("--- Initializing Mind Gate ---", fg="magenta")
    
    api_key = current_app.config.get("OPENROUTER_API_KEY")

    if not api_key:
        click.secho("FATAL ERROR: OPENROUTER_API_KEY not found in app configuration.", fg="red")
        return

    try:
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        click.secho("AI Client configured. The Gate is open.", fg="green")
    except Exception as e:
        click.secho(f"FATAL ERROR: Could not configure AI client: {e}", fg="red")
        return

    click.echo(f"Model in use: {model}")
    click.echo("Type 'exit' or 'quit' to close the gate.")
    click.echo("-" * 30)
    
    while True:
        user_question = click.prompt("You", prompt_suffix="> ")
        if user_question.lower() in ["exit", "quit"]:
            break
        
        if not user_question.strip():
            continue

        try:
            click.echo("AI is thinking...")
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_question}],
                timeout=120.0
            )
            ai_response = completion.choices[0].message.content
            
            # We confidently print the raw response.
            click.secho(f"AI: {ai_response}", fg="cyan")

        except openai.APITimeoutError:
             click.secho("AI Error: The request timed out. The AI is taking too long to respond.", fg="yellow")
        except Exception as e:
            # Handle potential encoding errors gracefully
            error_message = str(e).encode('utf-8', 'replace').decode('utf-8')
            click.secho(f"An unexpected error occurred: {error_message}", fg="red")
    
    click.secho("--- Mind Gate Closed ---", fg="magenta")