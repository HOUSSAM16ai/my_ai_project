# app/services/orchestration/application/raft_consensus.py
"""
Raft Consensus Service
=======================
Single Responsibility: Distributed consensus protocol (Raft).
"""

from __future__ import annotations

import random
import threading
import time
from datetime import datetime
from typing import Any

from app.services.orchestration.domain.models import ConsensusRole, RaftState


class RaftConsensusEngine:
    """
    Raft distributed consensus protocol implementation.

    Responsibilities:
    - Leader election
    - Log replication
    - Heartbeat management
    """

    def __init__(self, node_id: str, cluster_nodes: list[str]):
        self._node_id = node_id
        self._cluster_nodes = cluster_nodes
        self._state = RaftState(
            node_id=node_id,
            role=ConsensusRole.FOLLOWER,
        )
        self._lock = threading.RLock()
        self._running = False
        self._consensus_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start consensus protocol"""
        self._running = True
        self._consensus_thread = threading.Thread(
            target=self._run_consensus_loop,
            daemon=True,
        )
        self._consensus_thread.start()

    def stop(self) -> None:
        """Stop consensus protocol"""
        self._running = False
        if self._consensus_thread:
            self._consensus_thread.join(timeout=5)

    def append_log_entry(self, entry: dict[str, Any]) -> bool:
        """Append entry to distributed log (Leader only)"""
        with self._lock:
            if self._state.role != ConsensusRole.LEADER:
                return False

            log_entry = {
                "term": self._state.term,
                "index": len(self._state.log),
                "data": entry,
            }
            self._state.log.append(log_entry)
            return True

    def get_state(self) -> RaftState:
        """Get current Raft state"""
        with self._lock:
            return self._state

    def is_leader(self) -> bool:
        """Check if this node is the leader"""
        with self._lock:
            return self._state.role == ConsensusRole.LEADER

    def _run_consensus_loop(self) -> None:
        """Main consensus loop"""
        while self._running:
            try:
                with self._lock:
                    if self._state.role == ConsensusRole.LEADER:
                        self._send_heartbeats()
                        time.sleep(1)
                    elif self._state.role == ConsensusRole.FOLLOWER:
                        self._check_election_timeout()
                        time.sleep(0.5)
                    elif self._state.role == ConsensusRole.CANDIDATE:
                        self._conduct_election()
                        time.sleep(0.5)
            except Exception:
                pass

    def _send_heartbeats(self) -> None:
        """Send heartbeats to followers"""
        self._state.last_heartbeat_time = datetime.utcnow()
        # In production: send RPCs to all followers

    def _check_election_timeout(self) -> None:
        """Check if election timeout exceeded"""
        elapsed = (datetime.utcnow() - self._state.last_heartbeat_time).total_seconds()
        timeout = self._state.election_timeout + random.uniform(0, 2)

        if elapsed > timeout:
            # Start election
            self._state.role = ConsensusRole.CANDIDATE
            self._state.term += 1
            self._state.voted_for = self._node_id
            self._state.votes_received = {self._node_id}

    def _conduct_election(self) -> None:
        """Conduct leader election"""
        majority = (len(self._cluster_nodes) // 2) + 1

        # Simulate receiving votes from other nodes
        for node_id in self._cluster_nodes:
            if node_id != self._node_id and random.random() > 0.3:
                self._state.votes_received.add(node_id)

        # Check if won election
        if len(self._state.votes_received) >= majority:
            self._state.role = ConsensusRole.LEADER
            self._send_heartbeats()
        else:
            # Election failed, revert to follower
            self._state.role = ConsensusRole.FOLLOWER
            self._state.voted_for = None
            self._state.votes_received.clear()
