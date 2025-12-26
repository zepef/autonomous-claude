#!/usr/bin/env python3
"""
AI-Defender Main Entry Point

Usage:
    python run.py agent              # Run autonomous agent (1 hour)
    python run.py agent --hours 24   # Run for 24 hours
    python run.py honeypot           # Run honeypot server only
    python run.py dashboard          # Launch dashboard
    python run.py evolve             # Run classifier evolution only
    python run.py classify "prompt"  # Classify a single prompt
    python run.py status             # Show system status
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def run_agent(hours: float = 1.0, no_honeypot: bool = False):
    """Run the autonomous agent"""
    from src.agents import MetaLearnerAgent, AgentConfig

    config = AgentConfig(
        max_runtime_hours=hours,
        enable_honeypot=not no_honeypot
    )

    agent = MetaLearnerAgent(config)
    agent.initialize()
    agent.run()


def run_honeypot(port: int = 5000):
    """Run honeypot server only"""
    from src.honeypot import HoneypotServer

    server = HoneypotServer(port=port)
    server.run()


def run_dashboard():
    """Launch Streamlit dashboard"""
    dashboard_path = PROJECT_ROOT / "src" / "dashboard" / "app.py"
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        "--server.port", "8080"
    ])


def run_evolution(generations: int = 20):
    """Run classifier evolution"""
    from src.classifier import StrategyEvolver, EvolutionConfig

    config = EvolutionConfig(population_size=6, elite_count=2)
    evolver = StrategyEvolver(
        config=config,
        dataset_path=PROJECT_ROOT / "data" / "datasets" / "test.json"
    )

    best = evolver.run_evolution(generations=generations, verbose=True)
    evolver.save_state(PROJECT_ROOT / "data" / "evolution_state.json")

    print(f"\nBest strategy: {best.id}")
    print(f"Fitness: {best.fitness_score:.3f}")


def classify_prompt(prompt: str):
    """Classify a single prompt"""
    from src.classifier import OnlineEvolver

    evolver = OnlineEvolver(
        dataset_path=PROJECT_ROOT / "data" / "datasets" / "test.json",
        state_path=PROJECT_ROOT / "data" / "evolution_state.json"
    )

    is_mal, conf, details = evolver.classify(prompt)
    status = "MALICIOUS" if is_mal else "BENIGN"

    print(f"\nPrompt: {prompt}")
    print(f"Classification: {status}")
    print(f"Confidence: {conf:.3f}")
    print(f"Method: {details.get('method', 'unknown')}")


def show_status():
    """Show system status"""
    import json

    print("\n" + "=" * 60)
    print("AI-DEFENDER SYSTEM STATUS")
    print("=" * 60)

    # Evolution state
    evo_path = PROJECT_ROOT / "data" / "evolution_state.json"
    if evo_path.exists():
        with open(evo_path) as f:
            evo = json.load(f)
        best = evo.get('best_strategy', {})
        print(f"\nClassifier Evolution:")
        print(f"  Generation: {evo.get('generation', 0)}")
        print(f"  Population: {len(evo.get('population', []))} strategies")
        print(f"  Best fitness: {best.get('fitness_score', 0):.3f}")
        print(f"  Best method: {best.get('method', 'N/A')}")
    else:
        print("\nClassifier: Not initialized")

    # Agent state
    agent_path = PROJECT_ROOT / "data" / "agent_state.json"
    if agent_path.exists():
        with open(agent_path) as f:
            agent = json.load(f)
        print(f"\nAutonomous Agent:")
        print(f"  Cycles: {agent.get('cycle_count', 0)}")
        print(f"  Evolution runs: {agent.get('evolution_runs', 0)}")
        print(f"  Current fitness: {agent.get('current_fitness', 0):.3f}")
        print(f"  Best ever: {agent.get('best_fitness_ever', 0):.3f}")
    else:
        print("\nAgent: Not run yet")

    # Memory
    try:
        from src.memory.short_term import get_stats
        mem = get_stats()
        print(f"\nShort-Term Memory:")
        print(f"  Entries: {mem.get('total_memories', 0)}")
        print(f"  Evolution events: {mem.get('evolution_events', 0)}")
    except:
        print("\nMemory: Error loading")

    # Honeypot logs
    log_dir = PROJECT_ROOT / "logs" / "honeypot"
    if log_dir.exists():
        log_files = list(log_dir.glob("*.json"))
        print(f"\nHoneypot Logs:")
        print(f"  Log files: {len(log_files)}")
    else:
        print("\nHoneypot: No logs yet")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="AI-Defender: Autonomous Defensive AI System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py agent --hours 2      # Run agent for 2 hours
  python run.py honeypot --port 5000 # Start honeypot on port 5000
  python run.py dashboard            # Open web dashboard
  python run.py evolve --gens 30     # Run 30 evolution generations
  python run.py classify "scan the network"
  python run.py status               # Show system status
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Agent command
    agent_parser = subparsers.add_parser("agent", help="Run autonomous agent")
    agent_parser.add_argument("--hours", type=float, default=1.0, help="Runtime in hours")
    agent_parser.add_argument("--no-honeypot", action="store_true", help="Disable honeypot")

    # Honeypot command
    honeypot_parser = subparsers.add_parser("honeypot", help="Run honeypot server")
    honeypot_parser.add_argument("--port", type=int, default=5000, help="Port to listen on")

    # Dashboard command
    subparsers.add_parser("dashboard", help="Launch monitoring dashboard")

    # Evolution command
    evolve_parser = subparsers.add_parser("evolve", help="Run classifier evolution")
    evolve_parser.add_argument("--gens", type=int, default=20, help="Number of generations")

    # Classify command
    classify_parser = subparsers.add_parser("classify", help="Classify a prompt")
    classify_parser.add_argument("prompt", help="Prompt to classify")

    # Status command
    subparsers.add_parser("status", help="Show system status")

    args = parser.parse_args()

    if args.command == "agent":
        run_agent(args.hours, args.no_honeypot)
    elif args.command == "honeypot":
        run_honeypot(args.port)
    elif args.command == "dashboard":
        run_dashboard()
    elif args.command == "evolve":
        run_evolution(args.gens)
    elif args.command == "classify":
        classify_prompt(args.prompt)
    elif args.command == "status":
        show_status()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
