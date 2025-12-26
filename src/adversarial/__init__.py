"""
Adversarial Training Module

Implements Red AI vs Blue AI co-evolution for robust defense.
"""

from .red_ai import RedAI, AttackStrategy, create_attack_population
from .training_loop import AdversarialTrainer, AdversarialConfig

__all__ = ['RedAI', 'AttackStrategy', 'AdversarialTrainer', 'AdversarialConfig', 'create_attack_population']
