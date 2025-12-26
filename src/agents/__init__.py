"""
Agents Module

Autonomous agents for AI-Defender system.

Components:
- meta_learner: Main autonomous controller with decision loop

Usage:
    # Quick start (1 hour runtime)
    python -m src.agents.meta_learner --runtime 1

    # Programmatic
    from src.agents import MetaLearnerAgent, AgentConfig
    config = AgentConfig(max_runtime_hours=24)
    agent = MetaLearnerAgent(config)
    agent.initialize()
    agent.run()
"""

from .meta_learner import (
    MetaLearnerAgent,
    AgentConfig,
    AgentState,
    run_agent
)

__all__ = [
    'MetaLearnerAgent',
    'AgentConfig',
    'AgentState',
    'run_agent'
]
