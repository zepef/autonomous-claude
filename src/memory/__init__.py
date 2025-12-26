"""
Memory modules for AI-Defender autonomous agent.

Short-term: SQLite-based recent context (last 50 entries)
Long-term: Qdrant vector database for semantic search
"""

from .short_term import (
    init_database,
    add_memory,
    get_recent_memories,
    get_memories_by_agent,
    log_evolution,
    get_evolution_history,
    get_best_strategies,
    get_stats as get_short_term_stats,
    clear_all as clear_short_term
)

from .long_term import (
    LongTermMemory,
    get_long_term_memory
)

__all__ = [
    # Short-term
    'init_database',
    'add_memory',
    'get_recent_memories',
    'get_memories_by_agent',
    'log_evolution',
    'get_evolution_history',
    'get_best_strategies',
    'get_short_term_stats',
    'clear_short_term',
    # Long-term
    'LongTermMemory',
    'get_long_term_memory'
]
