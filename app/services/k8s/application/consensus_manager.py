# app/services/k8s/application/consensus_manager.py
"""Distributed consensus manager (Raft protocol)"""

from __future__ import annotations

import random
import threading
import time
from datetime import UTC, datetime
from typing import Any

from app.services.k8s.domain.models import ConsensusRole, RaftState


class ConsensusManager:
    """
    Consensus Manager - Raft protocol implementation

    Responsibilities:
    - Leader election
    - Log replication
    - Heartbeat management
    - Distributed decision making
    """

    def __init__(self, node_id: str):
        self._raft_state = RaftState(
            node_id=node_id,
            role=ConsensusRole.FOLLOWER,
        )
        self._lock = threading.RLock()
        self._running = False

    def get_raft_state(self) -> RaftState:
        """Get current Raft state"""
        with self._lock:
            return self._raft_state

    def append_log_entry(self, entry: dict[str, Any]) -> bool:
        """
        Append entry to Raft log

        Only leader can append entries
        """
        with self._lock:
            if self._raft_state.role != ConsensusRole.LEADER:
                return False

            # Add entry to log
            self._raft_state.log.append(entry)
            self._raft_state.commit_index = len(self._raft_state.log) - 1

            return True

    def start_consensus_protocol(self) -> None:
        """Start Raft consensus protocol"""
        if self._running:
            return

        self._running = True

        # Start heartbeat thread (for leader)
        def heartbeat_loop():
            while self._running:
                if self._raft_state.role == ConsensusRole.LEADER:
                    self.send_heartbeats()
                time.sleep(1)

        # Start election timeout checker (for followers)
        def election_loop():
            while self._running:
                if self._raft_state.role == ConsensusRole.FOLLOWER:
                    self._check_election_timeout()
                time.sleep(1)

        threading.Thread(target=heartbeat_loop, daemon=True).start()
        threading.Thread(target=election_loop, daemon=True).start()

    def stop_consensus_protocol(self) -> None:
        """Stop consensus protocol"""
        self._running = False

    def send_heartbeats(self) -> None:
        """Send heartbeats to followers (leader only)"""
        with self._lock:
            if self._raft_state.role != ConsensusRole.LEADER:
                return

            self._raft_state.last_heartbeat_time = datetime.now(UTC)

    def conduct_election(self) -> None:
        """
        Conduct leader election

        Raft election process:
        1. Increment term
        2. Vote for self
        3. Request votes from other nodes
        4. If majority votes received, become leader
        """
        with self._lock:
            # Become candidate
            self._raft_state.role = ConsensusRole.CANDIDATE
            self._raft_state.term += 1
            self._raft_state.voted_for = self._raft_state.node_id
            self._raft_state.votes_received = {self._raft_state.node_id}

            # Simulate receiving votes from other nodes
            # In real implementation, would send RequestVote RPCs
            num_nodes = 3  # Assume 3-node cluster
            votes_needed = (num_nodes // 2) + 1

            # Simulate random vote responses
            for i in range(1, num_nodes):
                if random.random() > 0.3:  # 70% chance of receiving vote
                    self._raft_state.votes_received.add(f"node-{i}")

            # Check if won election
            if len(self._raft_state.votes_received) >= votes_needed:
                self._raft_state.role = ConsensusRole.LEADER
                self._raft_state.last_heartbeat_time = datetime.now(UTC)
            else:
                # Lost election, become follower
                self._raft_state.role = ConsensusRole.FOLLOWER

    def _check_election_timeout(self) -> None:
        """Check if election timeout has occurred"""
        with self._lock:
            if self._raft_state.role != ConsensusRole.FOLLOWER:
                return

            time_since_heartbeat = (
                datetime.now(UTC) - self._raft_state.last_heartbeat_time
            ).total_seconds()

            if time_since_heartbeat > self._raft_state.election_timeout:
                # Start election
                self.conduct_election()
