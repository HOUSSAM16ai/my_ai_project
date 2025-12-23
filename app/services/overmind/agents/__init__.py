"""
The Council of Agents (مجلس الحكماء).
Defines the specialized agents for the Overmind system.
"""
from .strategist import StrategistAgent
from .operator import OperatorAgent
from .auditor import AuditorAgent
from .architect import ArchitectAgent

__all__ = ["StrategistAgent", "OperatorAgent", "AuditorAgent", "ArchitectAgent"]
