# app/cli_handlers/genesis_cli.py
"""
Genesis CLI Handler.
Connects the simple agent to the command line.
"""
import click
import logging
import datetime
from app.genesis.core import GenesisAgent
from app.core.cli_logging import setup_cli_logger
from app.genesis.tools.code_explorer import grep_code, read_file_segment, list_files, identify_hotspots

logger = logging.getLogger("genesis.cli")

def get_current_time() -> str:
    """Returns the current server time."""
    return datetime.datetime.now().isoformat()

def calculator(a: float, b: float, operation: str) -> str:
    """
    Performs basic arithmetic.
    operation can be: add, subtract, multiply, divide
    """
    if operation == "add":
        return str(a + b)
    elif operation == "subtract":
        return str(a - b)
    elif operation == "multiply":
        return str(a * b)
    elif operation == "divide":
        if b == 0:
            return "Error: Division by zero"
        return str(a / b)
    return "Error: Unknown operation"

def register_genesis_commands(cli):
    """Registers the genesis command group."""

    @cli.group()
    def genesis():
        """Genesis: The Simple Super Agent."""
        pass

    @genesis.command()
    @click.argument("message")
    @click.option("--model", default="gpt-4o", help="The model to use")
    def chat(message, model):
        """Start a task with Genesis."""
        setup_cli_logger()

        click.echo(f"🌀 Genesis Agent Initialized (Model: {model})")
        click.echo("------------------------------------------------")

        try:
            agent = GenesisAgent(model=model)

            # Register Tools
            # 1. Basic
            agent.register_tool(get_current_time)
            agent.register_tool(calculator)

            # 2. Code Explorer (Superhuman Vision)
            agent.register_tool(grep_code)
            agent.register_tool(read_file_segment)
            agent.register_tool(list_files)
            agent.register_tool(identify_hotspots)

            result = agent.run(message)
            click.echo("------------------------------------------------")
            click.echo(f"🤖 Answer: {result}")
        except Exception as e:
            logger.exception("Genesis crashed")
            click.echo(f"💥 Error: {e}")
