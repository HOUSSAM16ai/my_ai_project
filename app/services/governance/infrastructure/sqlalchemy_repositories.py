# app/services/governance/infrastructure/sqlalchemy_repositories.py
"""
SQLAlchemy Repository Implementations
======================================
Concrete implementations using SQLAlchemy ORM.
"""

from __future__ import annotations

from typing import Any

from app.core.database import get_sync_session
from app.models import (
    ConsciousnessSignature,
    CosmicGovernanceCouncil,
    ExistentialProtocol,
    ExistentialTransparencyLog,
)


class SQLAlchemyProtocolRepository:
    """SQLAlchemy protocol repository"""
    
    def save(self, protocol: ExistentialProtocol) -> ExistentialProtocol:
        """Save protocol"""
        with get_sync_session() as session:
            session.add(protocol)
            session.flush()
            session.refresh(protocol)
            protocol_id = protocol.id
        # Return protocol (may be detached after session closes)
        return protocol
    
    def get(self, protocol_id: int) -> ExistentialProtocol | None:
        """Get protocol by ID"""
        with get_sync_session() as session:
            return session.query(ExistentialProtocol).filter_by(id=protocol_id).first()
    
    def get_all(self) -> list[ExistentialProtocol]:
        """Get all protocols"""
        with get_sync_session() as session:
            return session.query(ExistentialProtocol).all()
    
    def update(self, protocol: ExistentialProtocol) -> None:
        """Update protocol"""
        with get_sync_session() as session:
            session.merge(protocol)


class SQLAlchemyCouncilRepository:
    """SQLAlchemy council repository"""
    
    def save(self, council: CosmicGovernanceCouncil) -> CosmicGovernanceCouncil:
        """Save council"""
        with get_sync_session() as session:
            session.add(council)
            session.flush()
            session.refresh(council)
            council_id = council.id
        return council
    
    def get(self, council_id: int) -> CosmicGovernanceCouncil | None:
        """Get council by ID"""
        with get_sync_session() as session:
            return session.query(CosmicGovernanceCouncil).filter_by(id=council_id).first()
    
    def get_all(self) -> list[CosmicGovernanceCouncil]:
        """Get all councils"""
        with get_sync_session() as session:
            return session.query(CosmicGovernanceCouncil).all()
    
    def update(self, council: CosmicGovernanceCouncil) -> None:
        """Update council"""
        with get_sync_session() as session:
            session.merge(council)


class SQLAlchemyConsciousnessRepository:
    """SQLAlchemy consciousness repository"""
    
    def get(self, signature: str) -> ConsciousnessSignature | None:
        """Get consciousness by signature"""
        with get_sync_session() as session:
            return session.query(ConsciousnessSignature).filter_by(
                signature=signature
            ).first()
    
    def update(self, consciousness: ConsciousnessSignature) -> None:
        """Update consciousness"""
        with get_sync_session() as session:
            session.merge(consciousness)


class SQLAlchemyTransparencyRepository:
    """SQLAlchemy transparency repository"""
    
    def save(self, log: ExistentialTransparencyLog) -> None:
        """Save transparency log"""
        with get_sync_session() as session:
            session.add(log)
    
    def query(
        self,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[ExistentialTransparencyLog]:
        """Query transparency logs"""
        with get_sync_session() as session:
            query = session.query(ExistentialTransparencyLog)
            
            if event_type:
                query = query.filter_by(event_type=event_type)
            
            query = query.order_by(ExistentialTransparencyLog.timestamp.desc())
            query = query.limit(limit)
            
            return query.all()


__all__ = [
    "SQLAlchemyProtocolRepository",
    "SQLAlchemyCouncilRepository",
    "SQLAlchemyConsciousnessRepository",
    "SQLAlchemyTransparencyRepository",
]
