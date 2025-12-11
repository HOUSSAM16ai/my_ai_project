# app/services/developer_portal/application/ticket_manager.py
"""Support Ticket Management Service - Single Responsibility"""

import uuid
from datetime import datetime, UTC
from typing import Any

from app.services.developer_portal.domain.models import (
    SupportTicket,
    TicketStatus,
    TicketPriority,
)
from app.services.developer_portal.domain.ports import TicketRepository


class TicketManager:
    """
    Manages support tickets.
    
    Single Responsibility: Ticket creation, assignment, resolution.
    """

    def __init__(self, repository: TicketRepository):
        self._repo = repository

    def create_ticket(
        self,
        developer_id: str,
        subject: str,
        description: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        category: str = "general",
    ) -> SupportTicket:
        """Create new support ticket"""
        ticket = SupportTicket(
            ticket_id=str(uuid.uuid4()),
            developer_id=developer_id,
            subject=subject,
            description=description,
            priority=priority,
            status=TicketStatus.OPEN,
            created_at=datetime.now(UTC),
            category=category,
        )

        self._repo.create(ticket)
        return ticket

    def assign_ticket(self, ticket_id: str, assignee: str) -> bool:
        """Assign ticket to support agent"""
        ticket = self._repo.get(ticket_id)
        if not ticket:
            return False

        ticket.assigned_to = assignee
        ticket.status = TicketStatus.IN_PROGRESS
        self._repo.update(ticket)
        return True

    def add_message(
        self,
        ticket_id: str,
        sender: str,
        message: str,
    ) -> bool:
        """Add message to ticket"""
        ticket = self._repo.get(ticket_id)
        if not ticket:
            return False

        ticket.messages.append(
            {
                "sender": sender,
                "message": message,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        self._repo.update(ticket)
        return True

    def resolve_ticket(self, ticket_id: str) -> bool:
        """Resolve ticket"""
        ticket = self._repo.get(ticket_id)
        if not ticket:
            return False

        ticket.status = TicketStatus.RESOLVED
        ticket.resolved_at = datetime.now(UTC)
        self._repo.update(ticket)
        return True

    def close_ticket(self, ticket_id: str) -> bool:
        """Close ticket"""
        ticket = self._repo.get(ticket_id)
        if not ticket:
            return False

        ticket.status = TicketStatus.CLOSED
        ticket.closed_at = datetime.now(UTC)
        self._repo.update(ticket)
        return True
