"""
حزمة مبادئ الوكلاء الأذكياء.

تجمع المبادئ المعيارية والواجهات الداعمة لبناء وكلاء مستقلين ومتعاونين.
"""

from app.core.agents.principles import AgentPrinciple, get_agent_principles, resolve_autonomy_namespace

__all__ = [
    "AgentPrinciple",
    "get_agent_principles",
    "resolve_autonomy_namespace",
]
