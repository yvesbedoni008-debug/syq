"""Base agent class for all SYQ agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all specialized agents in the SYQ system."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")

    @abstractmethod
    async def process(self, opportunity_data: dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process opportunity data and return agent-specific insights.

        Args:
            opportunity_data: Dictionary containing opportunity information
            context: Optional context such as user preferences, market data, etc.

        Returns:
            Dictionary containing agent's analysis, insights, and confidence score.
        """
        pass

    def _log_info(self, message: str):
        self.logger.info(f"[{self.agent_name}] {message}")

    def _log_error(self, message: str):
        self.logger.error(f"[{self.agent_name}] {message}")

    def _log_debug(self, message: str):
        self.logger.debug(f"[{self.agent_name}] {message}")