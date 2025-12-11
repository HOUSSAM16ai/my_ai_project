# app/services/event_driven/application/cqrs_manager.py
"""
CQRS Manager - Command Query Responsibility Segregation
======================================================
Application layer service for CQRS pattern implementation
"""

from __future__ import annotations

import hashlib
import logging
import threading
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from ..domain.models import Command, Query


class CQRSManager:
    """
    CQRS (Command Query Responsibility Segregation) Service

    Separates write operations (commands) from read operations (queries)
    for better scalability and performance
    """

    def __init__(self):
        self.command_handlers: dict[str, Callable] = {}
        self.query_handlers: dict[str, Callable] = {}
        self.command_history: deque = deque(maxlen=10000)
        self.lock = threading.RLock()

    def register_command_handler(self, command_type: str, handler: Callable):
        """Register a command handler"""
        with self.lock:
            self.command_handlers[command_type] = handler

    def register_query_handler(self, query_type: str, handler: Callable):
        """Register a query handler"""
        with self.lock:
            self.query_handlers[query_type] = handler

    def execute_command(
        self, command_type: str, payload: dict[str, Any], issued_by: str = "system"
    ) -> tuple[bool, Any]:
        """Execute a command"""
        command_id = hashlib.sha256(
            f"{command_type}{datetime.now(UTC)}".encode()
        ).hexdigest()[:16]

        command = Command(
            command_id=command_id,
            command_type=command_type,
            payload=payload,
            issued_by=issued_by,
            issued_at=datetime.now(UTC),
        )

        with self.lock:
            if command_type not in self.command_handlers:
                return False, f"No handler for command type: {command_type}"

            handler = self.command_handlers[command_type]

        try:
            result = handler(command)
            command.executed = True
            command.result = result

            with self.lock:
                self.command_history.append(command)

            return True, result

        except Exception as e:
            logging.error(f"Command execution failed: {e}")
            return False, str(e)

    def execute_query(
        self, query_type: str, parameters: dict[str, Any], requested_by: str = "system"
    ) -> tuple[bool, Any]:
        """Execute a query"""
        with self.lock:
            if query_type not in self.query_handlers:
                return False, f"No handler for query type: {query_type}"

            handler = self.query_handlers[query_type]

        query = Query(
            query_id=hashlib.sha256(
                f"{query_type}{datetime.now(UTC)}".encode()
            ).hexdigest()[:16],
            query_type=query_type,
            parameters=parameters,
            requested_by=requested_by,
            requested_at=datetime.now(UTC),
        )

        try:
            result = handler(query)
            return True, result
        except Exception as e:
            logging.error(f"Query execution failed: {e}")
            return False, str(e)


__all__ = [
    "CQRSManager",
]
