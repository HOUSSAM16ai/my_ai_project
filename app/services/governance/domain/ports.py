# app/services/governance/domain/ports.py
"""
Governance Domain Ports
=======================
Protocols for governance dependencies.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.models import (
    ConsciousnessSignature,
    CosmicGovernanceCouncil,
    ExistentialProtocol,
    ExistentialTransparencyLog,
)


class ProtocolRepository(Protocol):
    """Port for protocol storage"""
    def save(self, protocol: ExistentialProtocol) -> ExistentialProtocol: ...
    def get(self, protocol_id: int) -> ExistentialProtocol | None: ...
    def get_all(self) -> list[ExistentialProtocol]: ...
    def update(self, protocol: ExistentialProtocol) -> None: ...


class CouncilRepository(Protocol):
    """Port for council storage"""
    def save(self, council: CosmicGovernanceCouncil) -> CosmicGovernanceCouncil: ...
    def get(self, council_id: int) -> CosmicGovernanceCouncil | None: ...
    def get_all(self) -> list[CosmicGovernanceCouncil]: ...
    def update(self, council: CosmicGovernanceCouncil) -> None: ...


class ConsciousnessRepository(Protocol):
    """Port for consciousness storage"""
    def get(self, signature: str) -> ConsciousnessSignature | None: ...
    def update(self, consciousness: ConsciousnessSignature) -> None: ...


class TransparencyLogger(Protocol):
    """Port for transparency logging"""
    def log_event(
        self,
        event_type: str,
        subject: str,
        details: dict[str, Any],
        reasoning: str,
        impact: dict[str, Any],
    ) -> None: ...

    def query_logs(
        self,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[ExistentialTransparencyLog]: ...
