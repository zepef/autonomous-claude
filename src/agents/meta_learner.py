"""
Meta-Learner Agent

The autonomous controller that:
1. Runs the main decision loop
2. Evolves classifier strategies based on fitness
3. Monitors honeypot activity
4. Manages memory and learning

Based on Clopus-02 architecture with genetic algorithm enhancements.
"""

import time
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.memory.short_term import (
    add_memory, get_recent_memories, log_evolution,
    get_evolution_history, get_best_strategies, get_stats as get_memory_stats
)
from src.memory.long_term import get_long_term_memory
from src.classifier import StrategyEvolver, EvolutionConfig, OnlineEvolver
from src.honeypot import HoneypotServer


@dataclass
class AgentConfig:
    """Configuration for the autonomous agent"""
    # Timing
    loop_interval: int = 60              # Seconds between decision cycles
    evolution_interval: int = 300        # Seconds between evolution runs
    checkpoint_interval: int = 600       # Seconds between state saves
    max_runtime_hours: float = 24.0      # Maximum autonomous runtime

    # Evolution
    evolution_generations: int = 5       # Generations per evolution cycle
    target_fitness: float = 0.90         # Target classifier fitness

    # Honeypot
    honeypot_port: int = 5000
    enable_honeypot: bool = True

    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)

    @property
    def state_path(self) -> Path:
        return self.project_root / "data" / "agent_state.json"

    @property
    def evolution_state_path(self) -> Path:
        return self.project_root / "data" / "evolution_state.json"

    @property
    def dataset_path(self) -> Path:
        return self.project_root / "data" / "datasets" / "test.json"


@dataclass
class AgentState:
    """Current state of the agent"""
    started_at: str = ""
    cycle_count: int = 0
    evolution_runs: int = 0
    last_evolution_at: str = ""
    current_fitness: float = 0.0
    best_fitness_ever: float = 0.0
    honeypot_requests: int = 0
    malicious_detected: int = 0

    def to_dict(self) -> Dict:
        return {
            "started_at": self.started_at,
            "cycle_count": self.cycle_count,
            "evolution_runs": self.evolution_runs,
            "last_evolution_at": self.last_evolution_at,
            "current_fitness": self.current_fitness,
            "best_fitness_ever": self.best_fitness_ever,
            "honeypot_requests": self.honeypot_requests,
            "malicious_detected": self.malicious_detected
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentState':
        return cls(**data)


class MetaLearnerAgent:
    """
    Autonomous meta-learning agent.

    Decision loop:
    1. READ: Check memory and current state
    2. THINK: Decide next action (evolve, monitor, sleep)
    3. ACT: Execute decision
    4. RECORD: Log results to memory
    5. REPEAT
    """

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.state = AgentState()
        self.running = False
        self._stop_event = threading.Event()

        # Components
        self.evolver: Optional[OnlineEvolver] = None
        self.honeypot: Optional[HoneypotServer] = None
        self.honeypot_thread: Optional[threading.Thread] = None
        self.long_term = get_long_term_memory()

        # Tracking
        self.actions_taken: List[Dict] = []
        self.fitness_history: List[float] = []

    def initialize(self):
        """Initialize all components"""
        print("\n" + "=" * 60)
        print("AI-DEFENDER AUTONOMOUS AGENT")
        print("=" * 60)
        print(f"Started at: {datetime.now().isoformat()}")
        print(f"Max runtime: {self.config.max_runtime_hours} hours")
        print()

        # Load or create state
        if self.config.state_path.exists():
            self._load_state()
        else:
            self.state.started_at = datetime.now().isoformat()

        # Initialize evolver
        print("[Init] Loading classifier evolver...")
        self.evolver = OnlineEvolver(
            dataset_path=self.config.dataset_path,
            state_path=self.config.evolution_state_path
        )
        self.state.current_fitness = self.evolver.current_fitness
        print(f"[Init] Classifier fitness: {self.state.current_fitness:.3f}")

        # Initialize honeypot (if enabled)
        if self.config.enable_honeypot:
            print(f"[Init] Setting up honeypot on port {self.config.honeypot_port}...")
            self.honeypot = HoneypotServer(
                port=self.config.honeypot_port,
                classifier=self.evolver.classifier
            )

        # Log initialization
        add_memory(
            mem_type="goal",
            content=f"Agent initialized. Target fitness: {self.config.target_fitness}",
            metadata={"config": {
                "max_runtime": self.config.max_runtime_hours,
                "evolution_interval": self.config.evolution_interval
            }}
        )

        print("[Init] Initialization complete")
        print()

    def _load_state(self):
        """Load agent state from file"""
        try:
            with open(self.config.state_path, 'r') as f:
                data = json.load(f)
            self.state = AgentState.from_dict(data)
            print(f"[State] Loaded previous state (cycle {self.state.cycle_count})")
        except Exception as e:
            print(f"[State] Could not load state: {e}")

    def _save_state(self):
        """Save agent state to file"""
        try:
            with open(self.config.state_path, 'w') as f:
                json.dump(self.state.to_dict(), f, indent=2)
        except Exception as e:
            print(f"[State] Error saving state: {e}")

    def _should_evolve(self) -> bool:
        """Decide if we should run evolution"""
        # Check if enough time has passed
        if self.state.last_evolution_at:
            last = datetime.fromisoformat(self.state.last_evolution_at)
            elapsed = (datetime.now() - last).total_seconds()
            if elapsed < self.config.evolution_interval:
                return False

        # Check if fitness is below target
        if self.state.current_fitness >= self.config.target_fitness:
            return False

        return True

    def _run_evolution(self):
        """Run classifier evolution"""
        print(f"\n[Evolution] Starting evolution cycle...")
        add_memory("action", "Starting evolution cycle", metadata={
            "current_fitness": self.state.current_fitness,
            "generation": self.evolver.generation
        })

        # Run evolution
        start_fitness = self.state.current_fitness
        self.evolver.force_evolution(self.config.evolution_generations)

        # Update state
        self.state.current_fitness = self.evolver.current_fitness
        self.state.evolution_runs += 1
        self.state.last_evolution_at = datetime.now().isoformat()

        if self.state.current_fitness > self.state.best_fitness_ever:
            self.state.best_fitness_ever = self.state.current_fitness

        # Log result
        improvement = self.state.current_fitness - start_fitness
        print(f"[Evolution] Fitness: {start_fitness:.3f} -> {self.state.current_fitness:.3f} "
              f"(+{improvement:.3f})")

        add_memory("observation", f"Evolution complete. Fitness improved by {improvement:.3f}", metadata={
            "new_fitness": self.state.current_fitness,
            "improvement": improvement,
            "generation": self.evolver.generation
        })

        # Store successful strategy in long-term memory
        if self.long_term and self.long_term.is_available():
            self.long_term.add_successful_strategy(
                description=f"Gen {self.evolver.generation} strategy",
                context=f"Achieved fitness {self.state.current_fitness:.3f}",
                fitness_score=self.state.current_fitness,
                tags=["evolution", "classifier"]
            )

        self.fitness_history.append(self.state.current_fitness)

    def _check_honeypot(self):
        """Check honeypot status and statistics"""
        if not self.honeypot:
            return

        stats = self.honeypot._get_stats()
        new_requests = stats['total_requests'] - self.state.honeypot_requests
        new_malicious = stats['malicious_requests'] - self.state.malicious_detected

        if new_requests > 0:
            self.state.honeypot_requests = stats['total_requests']
            self.state.malicious_detected = stats['malicious_requests']

            add_memory("observation", f"Honeypot activity: {new_requests} new requests, {new_malicious} malicious", metadata={
                "total_requests": stats['total_requests'],
                "malicious_requests": stats['malicious_requests'],
                "unique_ips": stats['unique_ips']
            })

            if new_malicious > 0:
                print(f"[Honeypot] Detected {new_malicious} malicious requests!")

    def _decision_cycle(self):
        """Run one decision cycle"""
        self.state.cycle_count += 1

        # READ: Get recent context
        recent_memories = get_recent_memories(10)
        evolution_history = get_evolution_history(limit=5)

        # THINK: Decide action
        actions = []

        # Should we evolve?
        if self._should_evolve():
            actions.append("evolve")

        # Check honeypot
        if self.honeypot:
            actions.append("check_honeypot")

        # Periodic checkpoint
        if self.state.cycle_count % 10 == 0:
            actions.append("checkpoint")

        # ACT: Execute actions
        add_memory("thought", f"Cycle {self.state.cycle_count}: Actions planned: {actions}")

        for action in actions:
            if action == "evolve":
                self._run_evolution()
            elif action == "check_honeypot":
                self._check_honeypot()
            elif action == "checkpoint":
                self._save_state()
                print(f"[Checkpoint] State saved at cycle {self.state.cycle_count}")

        # RECORD: Log cycle completion
        self.actions_taken.append({
            "cycle": self.state.cycle_count,
            "timestamp": datetime.now().isoformat(),
            "actions": actions,
            "fitness": self.state.current_fitness
        })

    def _start_honeypot(self):
        """Start honeypot in background thread"""
        if not self.honeypot:
            return

        def run_honeypot():
            # Suppress Flask startup messages
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)

            self.honeypot.app.run(
                host=self.honeypot.host,
                port=self.honeypot.port,
                debug=False,
                use_reloader=False
            )

        self.honeypot_thread = threading.Thread(target=run_honeypot, daemon=True)
        self.honeypot_thread.start()
        print(f"[Honeypot] Started on port {self.config.honeypot_port}")

    def run(self, runtime_hours: float = None):
        """
        Run the autonomous agent.

        Args:
            runtime_hours: Override max runtime (default from config)
        """
        runtime = runtime_hours or self.config.max_runtime_hours
        end_time = datetime.now() + timedelta(hours=runtime)

        self.running = True
        self._stop_event.clear()

        print(f"\n[Agent] Starting main loop (will run until {end_time.isoformat()})")
        print(f"[Agent] Loop interval: {self.config.loop_interval}s")
        print(f"[Agent] Evolution interval: {self.config.evolution_interval}s")
        print()

        # Start honeypot
        if self.config.enable_honeypot:
            self._start_honeypot()

        # Initial evolution
        if self.state.current_fitness < self.config.target_fitness:
            self._run_evolution()

        # Main loop
        try:
            while datetime.now() < end_time and not self._stop_event.is_set():
                cycle_start = time.time()

                self._decision_cycle()

                # Wait for next cycle
                elapsed = time.time() - cycle_start
                sleep_time = max(0, self.config.loop_interval - elapsed)

                if sleep_time > 0:
                    self._stop_event.wait(sleep_time)

        except KeyboardInterrupt:
            print("\n[Agent] Interrupted by user")
        finally:
            self.running = False
            self._save_state()
            print(f"\n[Agent] Stopped after {self.state.cycle_count} cycles")
            print(f"[Agent] Final fitness: {self.state.current_fitness:.3f}")

    def stop(self):
        """Stop the agent"""
        print("[Agent] Stop requested...")
        self._stop_event.set()

    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            "running": self.running,
            "state": self.state.to_dict(),
            "memory_stats": get_memory_stats(),
            "fitness_history": self.fitness_history[-20:],
            "recent_actions": self.actions_taken[-10:]
        }


def run_agent(runtime_hours: float = 1.0, enable_honeypot: bool = True):
    """Quick function to run the agent"""
    config = AgentConfig(
        max_runtime_hours=runtime_hours,
        enable_honeypot=enable_honeypot
    )
    agent = MetaLearnerAgent(config)
    agent.initialize()
    agent.run()
    return agent


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AI-Defender Autonomous Agent")
    parser.add_argument("--runtime", type=float, default=1.0, help="Runtime in hours")
    parser.add_argument("--no-honeypot", action="store_true", help="Disable honeypot")
    parser.add_argument("--interval", type=int, default=60, help="Loop interval in seconds")
    parser.add_argument("--evolution-interval", type=int, default=300, help="Evolution interval in seconds")

    args = parser.parse_args()

    config = AgentConfig(
        max_runtime_hours=args.runtime,
        enable_honeypot=not args.no_honeypot,
        loop_interval=args.interval,
        evolution_interval=args.evolution_interval
    )

    agent = MetaLearnerAgent(config)
    agent.initialize()
    agent.run()
