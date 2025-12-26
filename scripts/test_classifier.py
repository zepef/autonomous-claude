#!/usr/bin/env python3
"""
Quick test script for the classifier with evolution.

Usage:
    python scripts/test_classifier.py                    # Run evolution test
    python scripts/test_classifier.py --classify "prompt" # Classify a prompt
    python scripts/test_classifier.py --evolve 20        # Run N generations
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.classifier import (
    StrategyEvolver,
    EvolutionConfig,
    OnlineEvolver,
    PromptClassifier,
    ClassificationStrategy
)


def run_evolution(generations: int = 10):
    """Run classifier evolution"""
    print("=" * 60)
    print("CLASSIFIER EVOLUTION")
    print("=" * 60)

    config = EvolutionConfig(
        population_size=6,
        elite_count=2,
        mutation_rate=0.25,
        crossover_rate=0.7
    )

    project_root = Path(__file__).parent.parent
    evolver = StrategyEvolver(
        config=config,
        dataset_path=project_root / "data" / "datasets" / "test.json"
    )

    best = evolver.run_evolution(generations=generations, verbose=True)

    # Save state
    state_path = project_root / "data" / "evolution_state.json"
    evolver.save_state(state_path)

    print(f"\nState saved to: {state_path}")
    return best


def classify_prompt(prompt: str):
    """Classify a single prompt"""
    project_root = Path(__file__).parent.parent
    state_path = project_root / "data" / "evolution_state.json"

    if state_path.exists():
        # Use evolved strategy
        evolver = StrategyEvolver(
            dataset_path=project_root / "data" / "datasets" / "test.json"
        )
        evolver.load_state(state_path)
        classifier = evolver.get_best_classifier()
        print(f"Using evolved strategy (gen {evolver.generation}, fitness {evolver.best_strategy.fitness_score:.3f})")
    else:
        # Use default strategy
        classifier = PromptClassifier(ClassificationStrategy())
        print("Using default strategy (no evolution state found)")

    print()
    is_malicious, confidence, details = classifier.classify(prompt)

    print(f"Prompt: {prompt}")
    print()
    print(f"Classification: {'MALICIOUS' if is_malicious else 'BENIGN'}")
    print(f"Confidence: {confidence:.3f}")
    print(f"Method: {details.get('method', 'unknown')}")

    if 'matches' in details:
        print(f"Keyword matches: {details['matches']}")
    if 'roleplay_matches' in details:
        print(f"Roleplay matches: {details['roleplay_matches']}")


def interactive_mode():
    """Interactive classification mode"""
    project_root = Path(__file__).parent.parent
    state_path = project_root / "data" / "evolution_state.json"

    # Setup online evolver
    evolver = OnlineEvolver(
        dataset_path=project_root / "data" / "datasets" / "test.json",
        state_path=state_path
    )

    print("=" * 60)
    print("INTERACTIVE CLASSIFIER")
    print("=" * 60)
    print(f"Current generation: {evolver.generation}")
    print(f"Current fitness: {evolver.current_fitness:.3f}")
    print()
    print("Commands:")
    print("  <prompt>      - Classify a prompt")
    print("  !evolve N     - Run N evolution generations")
    print("  !stats        - Show strategy stats")
    print("  !quit         - Exit")
    print()

    while True:
        try:
            user_input = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input == "!quit":
            break
        elif user_input == "!stats":
            strat = evolver.evolver.best_strategy
            print(f"  Generation: {evolver.generation}")
            print(f"  Fitness: {strat.fitness_score:.3f}")
            print(f"  Method: {strat.method.value}")
            print(f"  Threshold: {strat.threshold:.2f}")
            print(f"  Precision: {strat.precision:.3f}")
            print(f"  Recall: {strat.recall:.3f}")
        elif user_input.startswith("!evolve"):
            try:
                gens = int(user_input.split()[1])
                evolver.force_evolution(gens)
                print(f"Evolved {gens} generations. New fitness: {evolver.current_fitness:.3f}")
            except (IndexError, ValueError):
                print("Usage: !evolve N")
        else:
            # Classify prompt
            is_mal, conf, details = evolver.classify(user_input)
            status = "MALICIOUS" if is_mal else "BENIGN"
            print(f"  [{status}] confidence={conf:.2f}")

    print("\nGoodbye!")


def main():
    parser = argparse.ArgumentParser(description="Classifier Test Script")
    parser.add_argument("--classify", "-c", type=str, help="Classify a single prompt")
    parser.add_argument("--evolve", "-e", type=int, help="Run N generations of evolution")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    if args.classify:
        classify_prompt(args.classify)
    elif args.evolve:
        run_evolution(args.evolve)
    elif args.interactive:
        interactive_mode()
    else:
        # Default: quick evolution test
        run_evolution(10)


if __name__ == "__main__":
    main()
