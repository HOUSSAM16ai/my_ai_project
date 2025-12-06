# app/overmind/planning/validators/stats_computer.py
"""
Statistics computer for plan validation.

Computes various statistics about the plan.
Complexity: CC ≤ 4 per method
"""

from typing import Any

from .graph_builder import GraphData


class StatsComputer:
    """Computes statistics about the plan."""
    
    def compute(
        self, plan: Any, graph_data: GraphData, depth_map: dict[str, int]
    ) -> dict[str, Any]:
        """
        Compute plan statistics.
        
        Complexity: CC=2
        """
        risk_counts = self._compute_risk_counts(plan)
        risk_score = self._compute_risk_score(risk_counts)
        fanout_stats = self._compute_fanout_stats(graph_data)
        
        orphan_tasks = self._find_orphan_tasks(graph_data)
        
        stats = {
            "tasks": graph_data.task_count,
            "roots": len(graph_data.roots),
            "longest_path": max(depth_map.values()) if depth_map else 0,
            "avg_out_degree": fanout_stats["avg"],
            "max_out_degree": fanout_stats["max"],
            "risk_counts": risk_counts,
            "risk_score": risk_score,
            "orphan_tasks": orphan_tasks,
        }
        
        return stats
    
    def _compute_risk_counts(self, plan: Any) -> dict[str, int]:
        """
        Compute risk level counts.
        
        Complexity: CC=4
        """
        from ..schemas import RiskLevel
        
        risk_counts = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
        }
        
        for task in plan.tasks:
            if task.risk_level == RiskLevel.LOW:
                risk_counts["LOW"] += 1
            elif task.risk_level == RiskLevel.MEDIUM:
                risk_counts["MEDIUM"] += 1
            elif task.risk_level == RiskLevel.HIGH:
                risk_counts["HIGH"] += 1
        
        return risk_counts
    
    def _compute_risk_score(self, risk_counts: dict[str, int]) -> int:
        """
        Compute weighted risk score.
        
        Complexity: CC=1
        """
        return (
            risk_counts["LOW"] * 1
            + risk_counts["MEDIUM"] * 3
            + risk_counts["HIGH"] * 7
        )
    
    def _compute_fanout_stats(self, graph_data: GraphData) -> dict[str, float]:
        """
        Compute fan-out statistics.
        
        Complexity: CC=3
        """
        out_degrees = graph_data.out_degrees
        
        if not out_degrees:
            return {"avg": 0.0, "max": 0}
        
        avg_fanout = round(sum(out_degrees) / len(out_degrees), 4)
        max_fanout = max(out_degrees)
        
        return {"avg": avg_fanout, "max": max_fanout}
    
    def _find_orphan_tasks(self, graph_data: GraphData) -> list[str]:
        """
        Find orphan tasks (isolated tasks).
        
        Complexity: CC=3
        """
        orphans = []
        
        for tid in graph_data.id_map:
            is_root = graph_data.indegree[tid] == 0
            has_no_children = not graph_data.adjacency[tid]
            
            if is_root and has_no_children and graph_data.task_count > 1:
                orphans.append(tid)
        
        return orphans
