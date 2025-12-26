"""
Classifier Module with Genetic Evolution

This module provides malicious prompt detection with evolving strategies.

Components:
- strategies: Strategy genomes (genes, mutation, crossover)
- base: Core classification logic (keyword, pattern, semantic, LLM, ensemble)
- evolution: Genetic algorithm for strategy optimization

Usage:
    from src.classifier import OnlineEvolver, PromptClassifier

    # Quick classification with default strategy
    classifier = PromptClassifier(ClassificationStrategy())
    is_malicious, confidence, details = classifier.classify("some prompt")

    # Evolving classifier that improves over time
    evolver = OnlineEvolver(dataset_path=Path("data/datasets/test.json"))
    is_malicious, confidence, details = evolver.classify("some prompt")
    evolver.feedback("some prompt", was_correct=True, actual_label="benign")
"""

from .strategies import (
    ClassificationStrategy,
    DetectionMethod,
    StrategyGene,
    create_initial_population
)

from .base import (
    PromptClassifier,
    load_dataset
)

from .evolution import (
    EvolutionConfig,
    StrategyEvolver,
    OnlineEvolver
)

__all__ = [
    # Strategies
    'ClassificationStrategy',
    'DetectionMethod',
    'StrategyGene',
    'create_initial_population',
    # Classifier
    'PromptClassifier',
    'load_dataset',
    # Evolution
    'EvolutionConfig',
    'StrategyEvolver',
    'OnlineEvolver'
]
