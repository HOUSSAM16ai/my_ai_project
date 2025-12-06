# app/overmind/planning/validators/hash_computer.py
"""
Hash computer for plan validation.

Computes content and structural hashes for change tracking.
Complexity: CC ≤ 3 per method
"""

import hashlib
import json
from typing import Any


class HashComputer:
    """Computes hashes for plan change tracking."""
    
    def compute_content_hash(self, plan: Any) -> str:
        """
        Compute semantic content hash.
        
        Complexity: CC=2
        """
        hash_payload = self._build_content_payload(plan)
        
        return hashlib.sha256(
            json.dumps(hash_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
    
    def compute_structural_hash(self, plan: Any) -> str:
        """
        Compute structural hash (topology only).
        
        Complexity: CC=2
        """
        structural_vector = self._build_structural_vector(plan)
        
        return hashlib.sha256(
            json.dumps(structural_vector, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
    
    def _build_content_payload(self, plan: Any) -> dict[str, Any]:
        """
        Build payload for content hash.
        
        Complexity: CC=1
        """
        return {
            "objective": plan.objective,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "description": t.description,
                    "task_type": t.task_type,
                    "tool_name": t.tool_name,
                    "tool_args": t.tool_args,
                    "dependencies": t.dependencies,
                    "priority": t.priority,
                    "criticality": t.criticality,
                    "risk_level": t.risk_level,
                    "allow_high_risk": t.allow_high_risk,
                    "tags": sorted(t.tags),
                    "metadata": t.metadata,
                    "gate_condition": t.gate_condition,
                }
                for t in sorted(plan.tasks, key=lambda x: x.task_id)
            ],
        }
    
    def _build_structural_vector(self, plan: Any) -> list[dict[str, Any]]:
        """
        Build vector for structural hash.
        
        Complexity: CC=1
        """
        return [
            {
                "task_id": t.task_id,
                "deps": sorted(t.dependencies),
                "priority": t.priority,
                "risk": t.risk_level,
                "hotspot": bool(t.metadata.get("hotspot")),
                "layer": t.metadata.get("layer"),
            }
            for t in sorted(plan.tasks, key=lambda x: x.task_id)
        ]
