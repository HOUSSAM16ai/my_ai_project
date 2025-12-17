# app/services/governance/application/consciousness_manager.py
"""
Consciousness Manager Service
==============================
Single Responsibility: Manage consciousness realignment and protocol adoption.
"""

from __future__ import annotations

from typing import Protocol

# Import models from facade instead of app.models since they don't exist there
# (Circular import is avoided because facade imports *from* application but we only import types from facade,
#  Wait, Facade imports ConsciousnessManager from here. Importing types from Facade HERE causes circular import.
#  We must define types or import them from a common place.
#  Since we defined them in Facade to solve the first issue, we should move them to a separate models file
#  that both can import.
#  However, for now, let's use Type Checking imports or just assume they exist if we mock them.)
# Better yet, let's create a shared models file in app/services/governance/domain/models.py
# and update Facade to import from there, and this file to import from there.

# Plan:
# 1. Update app/services/governance/domain/models.py to include the missing dataclasses.
# 2. Update Facade to import from domain/models.py.
# 3. Update this file to import from domain/models.py.

from app.services.governance.domain.models import ConsciousnessSignature, ExistentialProtocol


class ConsciousnessRepository(Protocol):
    def get(self, signature: str) -> ConsciousnessSignature | None: ...
    def update(self, consciousness: ConsciousnessSignature) -> None: ...


class ProtocolRepository(Protocol):
    def get(self, protocol_id: int) -> ExistentialProtocol | None: ...


class TransparencyLogger(Protocol):
    def log_event(self, event_type: str, subject: str, details: dict, reasoning: str, impact: dict) -> None: ...


class ConsciousnessManager:
    """
    Consciousness manager.

    Responsibilities:
    - Protocol opt-in
    - Consciousness realignment
    - Protocol compliance tracking
    """

    MIN_UNDERSTANDING_LEVEL = 1.0

    def __init__(
        self,
        consciousness_repository: ConsciousnessRepository,
        protocol_repository: ProtocolRepository,
        transparency_logger: TransparencyLogger,
    ):
        self._consciousness_repo = consciousness_repository
        self._protocol_repo = protocol_repository
        self._transparency = transparency_logger

    def opt_into_protocol(
        self,
        consciousness_signature: str,
        protocol: ExistentialProtocol,
        understanding_level: float,
    ) -> bool:
        """Opt consciousness into protocol"""
        if understanding_level < self.MIN_UNDERSTANDING_LEVEL:
            return False

        consciousness = self._consciousness_repo.get(consciousness_signature)
        if not consciousness:
            return False

        # Add protocol to adopted protocols
        if not consciousness.adopted_protocols:
            consciousness.adopted_protocols = []

        if protocol.id not in consciousness.adopted_protocols:
            consciousness.adopted_protocols.append(protocol.id)
            self._consciousness_repo.update(consciousness)

            self._transparency.log_event(
                event_type="PROTOCOL_ADOPTED",
                subject=f"Protocol Adopted: {protocol.protocol_name}",
                details={
                    "consciousness": consciousness_signature,
                    "protocol_id": protocol.id,
                    "understanding_level": understanding_level,
                },
                reasoning="Consciousness chose to adopt protocol",
                impact={"protocol_adoption": True},
            )

            return True

        return False

    def auto_realign_consciousness(
        self,
        consciousness_signature: str,
        new_understanding_level: float,
    ) -> bool:
        """Auto-realign consciousness based on understanding"""
        consciousness = self._consciousness_repo.get(consciousness_signature)
        if not consciousness:
            return False

        # Update understanding level
        if not consciousness.metadata_json:
            consciousness.metadata_json = {}

        consciousness.metadata_json["understanding_level"] = new_understanding_level
        self._consciousness_repo.update(consciousness)

        self._transparency.log_event(
            event_type="CONSCIOUSNESS_REALIGNED",
            subject=f"Consciousness Realigned: {consciousness_signature}",
            details={
                "consciousness": consciousness_signature,
                "new_understanding": new_understanding_level,
            },
            reasoning="Consciousness understanding evolved",
            impact={"realignment": True},
        )

        return True
