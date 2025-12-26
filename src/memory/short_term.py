"""
Short-Term Memory Module (SQLite)
Maintains recent context with auto-pruning to last N entries

Based on Clopus-02 architecture but enhanced for evolution tracking.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

# Configuration
DB_PATH = Path(__file__).parent.parent.parent / "data" / "memory" / "short_term.db"
MAX_ENTRIES = 50


@contextmanager
def get_connection():
    """Thread-safe database connection context manager"""
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize the short-term memory database"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        c = conn.cursor()

        # Main memories table
        c.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                agent_id TEXT,
                fitness_score REAL
            )
        ''')

        # Index for faster queries
        c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_type ON memories(type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_agent ON memories(agent_id)')

        # Evolution tracking table
        c.execute('''
            CREATE TABLE IF NOT EXISTS evolution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                generation INTEGER NOT NULL,
                strategy_id TEXT NOT NULL,
                fitness_score REAL NOT NULL,
                action TEXT,
                outcome TEXT
            )
        ''')

    print(f"[ShortTerm] Database initialized at {DB_PATH}")


def add_memory(
    mem_type: str,
    content: str,
    metadata: Optional[Dict] = None,
    agent_id: Optional[str] = None,
    fitness_score: Optional[float] = None
) -> int:
    """
    Add a memory entry.

    Types: thought, action, observation, goal, error, evolution

    Returns the ID of the inserted memory.
    """
    with get_connection() as conn:
        c = conn.cursor()

        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else None

        c.execute('''
            INSERT INTO memories (timestamp, type, content, metadata, agent_id, fitness_score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, mem_type, content, metadata_json, agent_id, fitness_score))

        memory_id = c.lastrowid

        # Prune old entries beyond MAX_ENTRIES
        c.execute('''
            DELETE FROM memories
            WHERE id NOT IN (
                SELECT id FROM memories ORDER BY id DESC LIMIT ?
            )
        ''', (MAX_ENTRIES,))

        return memory_id


def get_recent_memories(limit: int = MAX_ENTRIES, mem_type: Optional[str] = None) -> List[Dict]:
    """
    Get recent memories, optionally filtered by type.

    Returns list of memory dicts with parsed metadata.
    """
    with get_connection() as conn:
        c = conn.cursor()

        if mem_type:
            c.execute('''
                SELECT * FROM memories
                WHERE type = ?
                ORDER BY id DESC LIMIT ?
            ''', (mem_type, limit))
        else:
            c.execute('''
                SELECT * FROM memories
                ORDER BY id DESC LIMIT ?
            ''', (limit,))

        rows = c.fetchall()

        memories = []
        for row in rows:
            memory = dict(row)
            if memory['metadata']:
                memory['metadata'] = json.loads(memory['metadata'])
            memories.append(memory)

        return memories


def get_memories_by_agent(agent_id: str, limit: int = 20) -> List[Dict]:
    """Get memories for a specific agent"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT * FROM memories
            WHERE agent_id = ?
            ORDER BY id DESC LIMIT ?
        ''', (agent_id, limit))

        rows = c.fetchall()
        return [dict(row) for row in rows]


def log_evolution(
    generation: int,
    strategy_id: str,
    fitness_score: float,
    action: Optional[str] = None,
    outcome: Optional[str] = None
):
    """Log an evolution event for tracking strategy fitness over time"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO evolution_log (timestamp, generation, strategy_id, fitness_score, action, outcome)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), generation, strategy_id, fitness_score, action, outcome))


def get_evolution_history(strategy_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
    """Get evolution history, optionally filtered by strategy"""
    with get_connection() as conn:
        c = conn.cursor()

        if strategy_id:
            c.execute('''
                SELECT * FROM evolution_log
                WHERE strategy_id = ?
                ORDER BY id DESC LIMIT ?
            ''', (strategy_id, limit))
        else:
            c.execute('''
                SELECT * FROM evolution_log
                ORDER BY id DESC LIMIT ?
            ''', (limit,))

        return [dict(row) for row in c.fetchall()]


def get_best_strategies(limit: int = 10) -> List[Dict]:
    """Get top performing strategies by average fitness"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT strategy_id, AVG(fitness_score) as avg_fitness, COUNT(*) as runs
            FROM evolution_log
            GROUP BY strategy_id
            ORDER BY avg_fitness DESC
            LIMIT ?
        ''', (limit,))

        return [dict(row) for row in c.fetchall()]


def clear_all():
    """Clear all memories (use with caution)"""
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM memories')
        c.execute('DELETE FROM evolution_log')


def get_stats() -> Dict:
    """Get memory statistics"""
    with get_connection() as conn:
        c = conn.cursor()

        c.execute('SELECT COUNT(*) as count FROM memories')
        memory_count = c.fetchone()['count']

        c.execute('SELECT COUNT(*) as count FROM evolution_log')
        evolution_count = c.fetchone()['count']

        c.execute('''
            SELECT type, COUNT(*) as count
            FROM memories
            GROUP BY type
        ''')
        type_counts = {row['type']: row['count'] for row in c.fetchall()}

        return {
            "total_memories": memory_count,
            "evolution_events": evolution_count,
            "by_type": type_counts,
            "max_entries": MAX_ENTRIES
        }


# Initialize on import
if not DB_PATH.exists():
    init_database()


if __name__ == "__main__":
    # Test the module
    init_database()

    # Add some test memories
    add_memory("thought", "Testing short-term memory system")
    add_memory("action", "Initialized database", metadata={"test": True})
    add_memory("observation", "System working correctly")

    # Log evolution event
    log_evolution(
        generation=1,
        strategy_id="test-strategy-001",
        fitness_score=0.85,
        action="classify_prompt",
        outcome="correct"
    )

    # Print stats
    print("\nMemory Stats:")
    print(json.dumps(get_stats(), indent=2))

    print("\nRecent Memories:")
    for m in get_recent_memories(5):
        print(f"  [{m['type']}] {m['content'][:50]}...")

    print("\nEvolution History:")
    for e in get_evolution_history(limit=5):
        print(f"  Gen {e['generation']}: {e['strategy_id']} = {e['fitness_score']}")
