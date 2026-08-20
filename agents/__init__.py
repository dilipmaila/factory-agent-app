"""
Agents Package for Factory AI Assistant.
Includes Contextual Bandit Router (UCB Algorithm), Gemini Chat Agent, and Shadow Observer Learning Evaluator.
"""

from .bandit_router import ContextualBandit
from .chat_agent import ManufacturingChatAgent
from .shadow_observer import ShadowObserver

__all__ = [
    "ContextualBandit",
    "ManufacturingChatAgent",
    "ShadowObserver",
]
