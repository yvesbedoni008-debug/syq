"""Agent Orchestrator: coordinates multiple agents and synthesizes their insights."""

from typing import Dict, Any, List, Optional
import asyncio
import logging
from app.agents.base_agent import BaseAgent
from app.agents.discovery_agent import DiscoveryAgent
from app.agents.market_agent import MarketAgent
from app.agents.price_agent import PriceAgent
from app.agents.trust_agent import TrustAgent
from app.agents.risk_agent import RiskAgent
from app.agents.personal_agent import PersonalAgent
from app.agents.strategy_agent import StrategyAgent
from app.agents.negotiation_agent import NegotiationAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates the execution of multiple SYQ agents and aggregates their results."""

    def __init__(self):
        self.logger = logger
        # Initialize agents
        self.agents: List[BaseAgent] = [
            DiscoveryAgent(),
            MarketAgent(),
            PriceAgent(),
            TrustAgent(),
            RiskAgent(),
            PersonalAgent(),
            StrategyAgent(),
            NegotiationAgent()
        ]
        self.logger.info(f"Initialized Orchestrator with {[agent.agent_name for agent in self.agents]}")

    async def run_agents(
        self,
        opportunity_data: dict,
        user_context: Optional[dict] = None,
        selected_agents: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run selected agents on the opportunity data and return aggregated insights.

        Args:
            opportunity_data: Dictionary containing opportunity details
            user_context: Optional dict with user profile, preferences, etc.
            selected_agents: Optional list of agent names to run; if None, run all

        Returns:
            Dictionary containing each agent's output and a synthesized summary.
        """
        self.logger.info(f"Starting agent orchestration for opportunity {opportunity_data.get('id', 'unknown')}")

        # Determine which agents to run
        if selected_agents is None:
            agents_to_run = self.agents
        else:
            agents_to_run = [agent for agent in self.agents if agent.agent_name in selected_agents]
            if not agents_to_run:
                self.logger.warning("No matching agents found for selected_agents; running all")

        # Prepare context for each agent (including user context for personal agent)
        agent_results = {}
        tasks = []

        for agent in agents_to_run:
            # Personal agent expects user_profile in context
            agent_context = user_context.copy() if user_context else {}
            # For simplicity, we pass same context to all; agents ignore what they don't need
            task = asyncio.create_task(self._run_single_agent(agent, opportunity_data, agent_context))
            tasks.append((agent.agent_name, task))

        # Wait for all agents to complete
        for name, task in tasks:
            try:
                result = await task
                agent_results[name] = result
                self.logger.debug(f"Agent {name} completed")
            except Exception as e:
                self.logger.error(f"Agent {name} failed: {e}", exc_info=True)
                agent_results[name] = {
                    "agent": name,
                    "error": str(e),
                    "status": "failed"
                }

        # Synthesize results (could be more advanced)
        synthesis = self._synthesize_results(agent_results)

        return {
            "agent_results": agent_results,
            "synthesis": synthesis,
            "opportunity_id": opportunity_data.get("id"),
            "timestamp": None  # could add datetime
        }

    async def _run_single_agent(self, agent: BaseAgent, opportunity_data: dict, context: dict) -> dict:
        """Run a single agent and return its result."""
        self.logger.debug(f"Running agent {agent.agent_name}")
        return await agent.process(opportunity_data, context)

    def _synthesize_results(self, agent_results: dict) -> dict:
        """Create a high-level summary from individual agent outputs."""
        # Extract key scores if available
        scores = {}
        for agent_name, result in agent_results.items():
            if isinstance(result, dict) and "error" not in result:
                # Common score fields
                if "price_score" in result:
                    scores["price"] = result["price_score"]
                if "trust_score" in result:
                    scores["trust"] = result["trust_score"]
                if "risk_score" in result:
                    # risk score inverted for convenience (lower is better risk)
                    scores["risk_inverse"] = 100 - result["risk_score"]
                if "personal_score" in result:
                    scores["personal"] = result["personal_score"]
                if "market_score" in result:
                    scores["market"] = result["market_score"]
                if "discovery_score" in result:
                    scores["discovery"] = result["discovery_score"]

        # Compute simple weighted average (weights can be tuned)
        weights = {
            "price": 0.25,
            "trust": 0.20,
            "risk_inverse": 0.15,
            "personal": 0.20,
            "market": 0.20,
            "discovery": 0.0  # discovery is more informational
        }

        total_weight = 0
        weighted_sum = 0
        for key, weight in weights.items():
            if key in scores:
                weighted_sum += scores[key] * weight
                total_weight += weight

        composite_score = weighted_sum / total_weight if total_weight > 0 else 50

        # Determine overall recommendation based on strategy agent if present
        recommendation = "hold"
        strategy_result = agent_results.get("StrategyAgent", {})
        if isinstance(strategy_result, dict) and "recommendation" in strategy_result:
            recommendation = strategy_result["recommendation"]

        negotiation_result = agent_results.get("NegotiationAgent", {})
        suggested_price_range = None
        if isinstance(negotiation_result, dict):
            suggested_price_range = negotiation_result.get("suggested_price_range")

        return {
            "composite_score": round(composite_score, 1),
            "individual_scores": scores,
            "recommendation": recommendation,
            "suggested_price_range": suggested_price_range,
            "notes": "Synthesis based on weighted agent scores; see agent_results for details."
        }