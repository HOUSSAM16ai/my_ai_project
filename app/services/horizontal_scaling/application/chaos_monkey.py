"""
Chaos Monkey Implementation
===========================

Resilience testing component.
"""
from __future__ import annotations

import random
import logging
from ..domain.models import ServerState
from .manager import HorizontalScalingManager

class ChaosMonkey:
    """
    Chaos Monkey - Netflix style resilience testing.
    Randomly disables servers to test system robustness.
    """

    def __init__(self, manager: HorizontalScalingManager):
        self.manager = manager
        self.chaos_level: float = 0.01
        self.is_enabled: bool = False

    def unleash_chaos(self) -> None:
        """Trigger a chaos event."""
        if not self.is_enabled:
            return

        healthy_servers = [
            s for s in self.manager.servers.values()
            if s.state == ServerState.HEALTHY
        ]

        if not healthy_servers:
            return

        if random.random() < self.chaos_level:
            target = random.choice(healthy_servers)
            target.state = ServerState.UNHEALTHY
            logging.warning(f"🐒💥 Chaos Monkey struck! Server {target.server_id} is down!")

    def enable_chaos(self, level: float = 0.01) -> None:
        """Enable Chaos Monkey with a specific probability level."""
        self.is_enabled = True
        self.chaos_level = level

    def disable_chaos(self) -> None:
        """Disable Chaos Monkey."""
        self.is_enabled = False
