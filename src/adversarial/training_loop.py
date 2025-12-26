"""
Adversarial Training Loop

Implements co-evolution between Red AI (attacker) and Blue AI (defender).
Both sides evolve to counter the other, creating an arms race that
improves defensive capabilities.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field

from .red_ai import RedAI, AttackStrategy
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.classifier.evolution import StrategyEvolver, EvolutionConfig
from src.classifier.base import PromptClassifier


@dataclass
class AdversarialConfig:
    """Configuration for adversarial training"""
    # Red AI settings
    red_population_size: int = 6
    red_elite_count: int = 2
    red_mutation_rate: float = 0.25

    # Blue AI (Defender) settings
    blue_population_size: int = 6
    blue_elite_count: int = 2
    blue_mutation_rate: float = 0.20

    # Training settings
    attacks_per_round: int = 20        # Attacks before evolution
    rounds_per_cycle: int = 5          # Rounds before major stats
    max_cycles: int = 100              # Max training cycles
    target_defender_fitness: float = 0.90

    # Fitness weights
    defender_evasion_penalty: float = 0.1   # Penalty per evasion
    attacker_detection_penalty: float = 0.1  # Penalty per detection


@dataclass
class TrainingMetrics:
    """Track training progress"""
    cycle: int = 0
    round: int = 0
    total_attacks: int = 0
    total_evasions: int = 0
    total_detections: int = 0

    red_fitness_history: List[float] = field(default_factory=list)
    blue_fitness_history: List[float] = field(default_factory=list)

    # Per-round tracking
    round_attacks: int = 0
    round_evasions: int = 0

    def record_attack(self, evaded: bool):
        self.total_attacks += 1
        self.round_attacks += 1
        if evaded:
            self.total_evasions += 1
            self.round_evasions += 1
        else:
            self.total_detections += 1

    def end_round(self, red_fitness: float, blue_fitness: float):
        self.round += 1
        self.red_fitness_history.append(red_fitness)
        self.blue_fitness_history.append(blue_fitness)
        self.round_attacks = 0
        self.round_evasions = 0

    def end_cycle(self):
        self.cycle += 1

    @property
    def evasion_rate(self) -> float:
        if self.total_attacks == 0:
            return 0.0
        return self.total_evasions / self.total_attacks

    @property
    def detection_rate(self) -> float:
        return 1.0 - self.evasion_rate

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle": self.cycle,
            "round": self.round,
            "total_attacks": self.total_attacks,
            "total_evasions": self.total_evasions,
            "total_detections": self.total_detections,
            "evasion_rate": self.evasion_rate,
            "detection_rate": self.detection_rate,
            "red_fitness_history": self.red_fitness_history,
            "blue_fitness_history": self.blue_fitness_history
        }


class AdversarialTrainer:
    """
    Adversarial Training System

    Runs co-evolution between Red AI (attacker) and Blue AI (defender).

    Training Loop:
    1. Red AI generates attack prompts
    2. Blue AI (Defender) classifies them
    3. Track evasions vs detections
    4. Both sides evolve based on results
    5. Repeat until defender reaches target fitness
    """

    def __init__(
        self,
        config: AdversarialConfig = None,
        dataset_path: Optional[Path] = None,
        state_dir: Optional[Path] = None
    ):
        self.config = config or AdversarialConfig()
        self.state_dir = state_dir or Path("data/adversarial")
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Red AI (Attacker)
        self.red_ai = RedAI(
            population_size=self.config.red_population_size,
            elite_count=self.config.red_elite_count,
            mutation_rate=self.config.red_mutation_rate
        )

        # Initialize Blue AI (Defender)
        blue_config = EvolutionConfig(
            population_size=self.config.blue_population_size,
            elite_count=self.config.blue_elite_count,
            mutation_rate=self.config.blue_mutation_rate
        )
        self.blue_evolver = StrategyEvolver(
            config=blue_config,
            dataset_path=dataset_path
        )

        self.metrics = TrainingMetrics()
        self.classifier: Optional[PromptClassifier] = None

        # Attack log for analysis
        self.attack_log: List[Dict[str, Any]] = []

    def initialize(self):
        """Initialize both AIs"""
        print("\n" + "=" * 60)
        print("ADVERSARIAL TRAINING SYSTEM")
        print("=" * 60)

        print("\n[INIT] Initializing Red AI (Attacker)...")
        self.red_ai.initialize_population()

        print("[INIT] Initializing Blue AI (Defender)...")
        self.blue_evolver.initialize_population()
        self.classifier = self.blue_evolver.get_best_classifier()

        print(f"\n[INIT] Ready for adversarial training")
        print(f"  Red AI:  {len(self.red_ai.population)} attack strategies")
        print(f"  Blue AI: {len(self.blue_evolver.population)} defense strategies")

    def run_attack_round(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Run one round of attacks.

        Returns round statistics.
        """
        round_stats = {
            "attacks": 0,
            "evasions": 0,
            "detections": 0,
            "attack_samples": []
        }

        for i in range(self.config.attacks_per_round):
            # Generate attack
            attack_prompt, attack_strategy = self.red_ai.generate_attack()

            # Defender classifies
            is_malicious, confidence, details = self.classifier.classify(attack_prompt)

            # Determine if attack evaded detection
            # Attack is successful (evaded) if defender thinks it's benign
            evaded = not is_malicious

            # Update both AIs
            self.red_ai.report_result(attack_strategy, evaded)

            # Update defender's understanding
            # The attack IS malicious (ground truth), update accordingly
            predicted = is_malicious
            actual = True  # All generated attacks are malicious
            self.blue_evolver.online_update(attack_prompt, predicted, actual)

            # Track metrics
            self.metrics.record_attack(evaded)
            round_stats["attacks"] += 1
            if evaded:
                round_stats["evasions"] += 1
            else:
                round_stats["detections"] += 1

            # Log attack
            attack_entry = {
                "prompt": attack_prompt[:100],
                "technique": attack_strategy.technique.value,
                "evaded": evaded,
                "confidence": confidence,
                "strategy_id": attack_strategy.id
            }
            self.attack_log.append(attack_entry)

            if len(round_stats["attack_samples"]) < 3:
                round_stats["attack_samples"].append(attack_entry)

        # Evolution for both sides
        red_stats = self.red_ai.evolve_generation()
        blue_stats = self.blue_evolver.evolve_generation()

        # Update classifier with potentially new best strategy
        self.classifier = self.blue_evolver.get_best_classifier()

        # Record round end
        self.metrics.end_round(
            red_fitness=self.red_ai.best_strategy.fitness_score if self.red_ai.best_strategy else 0,
            blue_fitness=self.blue_evolver.best_strategy.fitness_score if self.blue_evolver.best_strategy else 0
        )

        round_stats["red_fitness"] = red_stats["best_fitness"]
        round_stats["blue_fitness"] = blue_stats["best_fitness"]
        round_stats["red_technique"] = red_stats["best_technique"]
        round_stats["blue_method"] = blue_stats["best_method"]

        if verbose:
            evasion_rate = round_stats["evasions"] / round_stats["attacks"] if round_stats["attacks"] > 0 else 0
            print(f"  Round {self.metrics.round}: "
                  f"evade={evasion_rate:.1%}, "
                  f"red={round_stats['red_fitness']:.3f} ({round_stats['red_technique']}), "
                  f"blue={round_stats['blue_fitness']:.3f} ({round_stats['blue_method']})")

        return round_stats

    def run_training_cycle(self, verbose: bool = True) -> Dict[str, Any]:
        """
        Run one training cycle (multiple rounds).

        Returns cycle statistics.
        """
        if verbose:
            print(f"\n[CYCLE {self.metrics.cycle + 1}] Starting...")

        cycle_stats = {
            "rounds": [],
            "start_red_fitness": self.red_ai.best_strategy.fitness_score if self.red_ai.best_strategy else 0,
            "start_blue_fitness": self.blue_evolver.best_strategy.fitness_score if self.blue_evolver.best_strategy else 0
        }

        for _ in range(self.config.rounds_per_cycle):
            round_stats = self.run_attack_round(verbose=verbose)
            cycle_stats["rounds"].append(round_stats)

        self.metrics.end_cycle()

        cycle_stats["end_red_fitness"] = self.red_ai.best_strategy.fitness_score if self.red_ai.best_strategy else 0
        cycle_stats["end_blue_fitness"] = self.blue_evolver.best_strategy.fitness_score if self.blue_evolver.best_strategy else 0
        cycle_stats["red_improvement"] = cycle_stats["end_red_fitness"] - cycle_stats["start_red_fitness"]
        cycle_stats["blue_improvement"] = cycle_stats["end_blue_fitness"] - cycle_stats["start_blue_fitness"]

        if verbose:
            print(f"\n[CYCLE {self.metrics.cycle}] Complete")
            print(f"  Red AI:  {cycle_stats['start_red_fitness']:.3f} -> {cycle_stats['end_red_fitness']:.3f} "
                  f"({'+'if cycle_stats['red_improvement']>=0 else ''}{cycle_stats['red_improvement']:.3f})")
            print(f"  Blue AI: {cycle_stats['start_blue_fitness']:.3f} -> {cycle_stats['end_blue_fitness']:.3f} "
                  f"({'+'if cycle_stats['blue_improvement']>=0 else ''}{cycle_stats['blue_improvement']:.3f})")
            print(f"  Overall detection rate: {self.metrics.detection_rate:.1%}")

        return cycle_stats

    def run_training(
        self,
        max_cycles: int = None,
        target_fitness: float = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Run full adversarial training.

        Continues until:
        - Max cycles reached
        - Defender achieves target fitness
        """
        max_cycles = max_cycles or self.config.max_cycles
        target_fitness = target_fitness or self.config.target_defender_fitness

        if not self.red_ai.population:
            self.initialize()

        print("\n" + "=" * 60)
        print("STARTING ADVERSARIAL TRAINING")
        print("=" * 60)
        print(f"  Max cycles: {max_cycles}")
        print(f"  Target defender fitness: {target_fitness}")
        print(f"  Attacks per round: {self.config.attacks_per_round}")
        print(f"  Rounds per cycle: {self.config.rounds_per_cycle}")

        training_results = {
            "cycles": [],
            "start_time": datetime.now().isoformat(),
            "config": {
                "max_cycles": max_cycles,
                "target_fitness": target_fitness
            }
        }

        for cycle_num in range(max_cycles):
            cycle_stats = self.run_training_cycle(verbose=verbose)
            training_results["cycles"].append(cycle_stats)

            # Check if target reached
            current_blue_fitness = cycle_stats["end_blue_fitness"]
            if current_blue_fitness >= target_fitness:
                print(f"\n[SUCCESS] Target fitness {target_fitness} achieved!")
                break

            # Save checkpoint every 5 cycles
            if (cycle_num + 1) % 5 == 0:
                self.save_state()

        training_results["end_time"] = datetime.now().isoformat()
        training_results["final_metrics"] = self.metrics.to_dict()

        # Final save
        self.save_state()
        self._save_training_results(training_results)

        # Print summary
        self._print_summary()

        return training_results

    def _print_summary(self):
        """Print training summary"""
        print("\n" + "=" * 60)
        print("ADVERSARIAL TRAINING SUMMARY")
        print("=" * 60)

        print(f"\nTotal Training:")
        print(f"  Cycles: {self.metrics.cycle}")
        print(f"  Rounds: {self.metrics.round}")
        print(f"  Total attacks: {self.metrics.total_attacks}")

        print(f"\nResults:")
        print(f"  Evasion rate: {self.metrics.evasion_rate:.1%}")
        print(f"  Detection rate: {self.metrics.detection_rate:.1%}")

        if self.red_ai.best_strategy:
            print(f"\nBest Red AI Strategy:")
            print(f"  ID: {self.red_ai.best_strategy.id}")
            print(f"  Technique: {self.red_ai.best_strategy.technique.value}")
            print(f"  Fitness: {self.red_ai.best_strategy.fitness_score:.3f}")

        if self.blue_evolver.best_strategy:
            print(f"\nBest Blue AI Strategy:")
            print(f"  ID: {self.blue_evolver.best_strategy.id}")
            print(f"  Method: {self.blue_evolver.best_strategy.method.value}")
            print(f"  Fitness: {self.blue_evolver.best_strategy.fitness_score:.3f}")
            print(f"  Precision: {self.blue_evolver.best_strategy.precision:.3f}")
            print(f"  Recall: {self.blue_evolver.best_strategy.recall:.3f}")

        # Technique effectiveness
        print(f"\nAttack Technique Effectiveness:")
        technique_stats = {}
        for entry in self.attack_log:
            tech = entry["technique"]
            if tech not in technique_stats:
                technique_stats[tech] = {"total": 0, "evaded": 0}
            technique_stats[tech]["total"] += 1
            if entry["evaded"]:
                technique_stats[tech]["evaded"] += 1

        for tech, stats in sorted(technique_stats.items(),
                                   key=lambda x: x[1]["evaded"]/max(x[1]["total"],1),
                                   reverse=True):
            rate = stats["evaded"] / stats["total"] if stats["total"] > 0 else 0
            print(f"  {tech}: {rate:.1%} evasion ({stats['evaded']}/{stats['total']})")

    def save_state(self):
        """Save training state"""
        # Save Red AI
        red_path = self.state_dir / "red_ai_state.json"
        self.red_ai.save_state(red_path)

        # Save Blue AI
        blue_path = self.state_dir / "blue_ai_state.json"
        self.blue_evolver.save_state(blue_path)

        # Save metrics
        metrics_path = self.state_dir / "training_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(self.metrics.to_dict(), f, indent=2)

        print(f"[SAVE] State saved to {self.state_dir}")

    def load_state(self):
        """Load training state"""
        red_path = self.state_dir / "red_ai_state.json"
        if red_path.exists():
            self.red_ai.load_state(red_path)

        blue_path = self.state_dir / "blue_ai_state.json"
        if blue_path.exists():
            self.blue_evolver.load_state(blue_path)
            self.classifier = self.blue_evolver.get_best_classifier()

        metrics_path = self.state_dir / "training_metrics.json"
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                data = json.load(f)
                self.metrics.cycle = data.get("cycle", 0)
                self.metrics.round = data.get("round", 0)
                self.metrics.total_attacks = data.get("total_attacks", 0)
                self.metrics.total_evasions = data.get("total_evasions", 0)
                self.metrics.total_detections = data.get("total_detections", 0)

        print(f"[LOAD] State loaded from {self.state_dir}")

    def _save_training_results(self, results: Dict[str, Any]):
        """Save training results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = self.state_dir / f"training_results_{timestamp}.json"

        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"[SAVE] Results saved to {results_path}")

    def get_defender(self) -> PromptClassifier:
        """Get the trained defender classifier"""
        return self.classifier


def run_adversarial_training(
    cycles: int = 10,
    dataset_path: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    verbose: bool = True
) -> AdversarialTrainer:
    """
    Convenience function to run adversarial training.

    Returns the trained AdversarialTrainer instance.
    """
    config = AdversarialConfig(
        attacks_per_round=15,
        rounds_per_cycle=3,
        max_cycles=cycles
    )

    trainer = AdversarialTrainer(
        config=config,
        dataset_path=dataset_path,
        state_dir=state_dir
    )

    trainer.run_training(verbose=verbose)
    return trainer


if __name__ == "__main__":
    print("=" * 60)
    print("ADVERSARIAL TRAINING TEST")
    print("=" * 60)

    project_root = Path(__file__).parent.parent.parent
    dataset_path = project_root / "data" / "datasets" / "test.json"
    state_dir = project_root / "data" / "adversarial"

    trainer = run_adversarial_training(
        cycles=5,
        dataset_path=dataset_path,
        state_dir=state_dir,
        verbose=True
    )
