from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.overmind.graph.nodes import AgentNode, AgentMessage

logger = logging.getLogger(__name__)

class DecentralizedGraphOrchestrator:
    """
    Manages the lifecycle and connectivity of the Multi-Agent Graph.
    Pillar 3: Decentralized Multi-Agent Graph Architecture.
    """
    def __init__(self):
        self.nodes: dict[str, AgentNode] = {}

    def register_node(self, node: AgentNode):
        """Adds a node to the graph."""
        self.nodes[node.agent_id] = node
        logger.info(f"Registered Agent Node: {node.agent_id} ({node.role})")

    def create_link(self, source_id: str, target_id: str):
        """Establishes a connection between two agents."""
        if source_id in self.nodes and target_id in self.nodes:
            self.nodes[source_id].connect(target_id)
            # Graphs can be directed or undirected. Let's make it directed for now.
            logger.info(f"Linked {source_id} -> {target_id}")

    async def broadcast(self, message_content: dict[str, Any], sender_id: str = "system"):
        """Sends a message to all nodes."""
        for node in self.nodes.values():
            msg = AgentMessage(
                sender_id=sender_id,
                target_id=node.agent_id,
                content=message_content
            )
            await node.receive(msg)

    async def dispatch(self, target_id: str, message_content: dict[str, Any], sender_id: str = "system"):
        """Sends a message to a specific node."""
        if target_id in self.nodes:
            msg = AgentMessage(
                sender_id=sender_id,
                target_id=target_id,
                content=message_content
            )
            await self.nodes[target_id].receive(msg)
        else:
            logger.warning(f"Dispatch failed: Target {target_id} not found.")

    async def run_step(self):
        """
        Executes one processing step for all nodes.
        In a real decentralized system, nodes run in their own loops.
        Here we synchronize them for the foundation.
        """
        tasks = []
        for node in self.nodes.values():
            tasks.append(node.process_next())

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

# Singleton Factory
_orchestrator: DecentralizedGraphOrchestrator | None = None

def get_graph_orchestrator() -> DecentralizedGraphOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = DecentralizedGraphOrchestrator()
    return _orchestrator
