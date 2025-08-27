"""
Demo script for the A/B testing infrastructure.

This script demonstrates how to:
1. Set up A/B tests for RAG system configurations
2. Run experiments with control and treatment groups
3. Perform statistical analysis of results
4. Interpret experiment outcomes
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List

from loguru import logger

# Assuming these would be imported from the actual package
try:
    from agentic_rag.evaluation.ab_testing import (
        ABTestingSystem, ExperimentStatus, create_ab_test,
        run_ab_test, analyze_ab_test
    )
    from agentic_rag.evaluation.synthetic_data import SyntheticDataGenerator, SyntheticQuery
    from agentic_rag.core.models import ToolType
except ImportError:
    logger.warning("Could not import agentic_rag modules. This is a demonstration.")
    
    # Mock classes for demonstration
    class SyntheticQuery:
        def __init__(self, query: str, domain: str):
            self.query = query
            self.domain = domain
            self.expected_tools = []
    
    class ABTestingSystem:
        def __init__(self, database_path: str = "ab_experiments.db"):
            self.database_path = database_path
        
        def create_experiment(self, **kwargs):
            return type('Config', (), {'experiment_id': 'demo-123'})()


def create_sample_queries() -> List[SyntheticQuery]:
    """Create sample queries for testing."""
    queries = [
        SyntheticQuery("What are the latest trends in AI research?", "technology"),
        SyntheticQuery("How do I optimize database performance?", "database"),
        SyntheticQuery("What are the best practices for microservices architecture?", "software"),
        SyntheticQuery("How does blockchain technology work?", "technology"),
        SyntheticQuery("What are the key metrics for evaluating ML models?", "machine_learning"),
        SyntheticQuery("How to implement OAuth2 authentication?", "security"),
        SyntheticQuery("What are the differences between SQL and NoSQL databases?", "database"),
        SyntheticQuery("How to set up CI/CD pipelines?", "devops"),
        SyntheticQuery("What are the principles of clean code?", "software"),
        SyntheticQuery("How to handle errors in distributed systems?", "distributed_systems"),
    ]
    
    return queries


def create_control_configuration() -> Dict[str, Any]:
    """Create baseline/control configuration."""
    return {
        "retrieval_config": {
            "top_k": 5,
            "similarity_threshold": 0.7,
            "reranking_enabled": False
        },
        "llm_config": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.1,
            "max_tokens": 500
        },
        "tool_selection": {
            "strategy": "basic",
            "confidence_threshold": 0.8
        },
        "caching": {
            "enabled": False
        }
    }


def create_treatment_configuration() -> Dict[str, Any]:
    """Create experimental/treatment configuration with improvements."""
    return {
        "retrieval_config": {
            "top_k": 10,
            "similarity_threshold": 0.6,
            "reranking_enabled": True,
            "reranking_model": "cross-encoder"
        },
        "llm_config": {
            "model": "gpt-4",
            "temperature": 0.0,
            "max_tokens": 750
        },
        "tool_selection": {
            "strategy": "adaptive",
            "confidence_threshold": 0.7,
            "context_aware": True
        },
        "caching": {
            "enabled": True,
            "cache_ttl": 3600
        }
    }


def mock_multi_tool_factory():
    """Mock factory for creating multi-tool instances."""
    class MockMultiTool:
        def __init__(self):
            self.config = {}
            
        def configure(self, config: Dict[str, Any]):
            self.config = config
            
    return MockMultiTool


async def demonstrate_ab_testing():
    """Demonstrate the A/B testing workflow."""
    
    logger.info("🧪 Starting A/B Testing Infrastructure Demo")
    
    # Initialize A/B testing system
    ab_system = ABTestingSystem("demo_ab_experiments.db")
    
    # Create sample queries
    queries = create_sample_queries()
    logger.info(f"Created {len(queries)} sample queries")
    
    # Define control and treatment configurations
    control_config = create_control_configuration()
    treatment_config = create_treatment_configuration()
    
    logger.info("📊 Control Configuration:")
    logger.info(json.dumps(control_config, indent=2))
    
    logger.info("🚀 Treatment Configuration:")
    logger.info(json.dumps(treatment_config, indent=2))
    
    # Create experiment
    experiment = ab_system.create_experiment(
        name="LLM Model Upgrade Experiment",
        description="Testing GPT-4 with improved retrieval vs baseline GPT-3.5",
        control_config=control_config,
        treatment_config=treatment_config,
        primary_metric="f1@5",
        secondary_metrics=["recall@10", "precision@5", "mrr", "latency_ms"],
        minimum_detectable_effect=0.10,  # 10% improvement
        statistical_power=0.8,
        significance_level=0.05
    )
    
    logger.info(f"✅ Created experiment: {experiment.experiment_id}")
    logger.info(f"Required sample size per group: {experiment.sample_size_per_group}")
    
    # List experiments
    experiments = ab_system.list_experiments()
    logger.info(f"📋 Total experiments in database: {len(experiments)}")
    
    # Simulate running the experiment (in real scenario, this would take time)
    logger.info("🔄 Simulating experiment execution...")
    
    # Note: In real usage, you would call:
    # benchmark_result = await ab_system.run_experiment(
    #     experiment.experiment_id, queries, mock_multi_tool_factory
    # )
    
    # Simulate some results data for analysis demonstration
    await simulate_experiment_results(ab_system, experiment.experiment_id)
    
    # Analyze results
    logger.info("📈 Analyzing experiment results...")
    analysis = ab_system.analyze_experiment(experiment.experiment_id)
    
    logger.info("Statistical Analysis Results:")
    for metric, result in analysis.items():
        logger.info(f"\n{metric.upper()}:")
        logger.info(f"  P-value: {result.p_value:.4f}")
        logger.info(f"  Effect size: {result.effect_size:.3f}")
        logger.info(f"  Significant: {result.is_significant}")
        logger.info(f"  Conclusion: {result.conclusion}")
        logger.info(f"  Recommendation: {result.recommendation}")
    
    # Get comprehensive summary
    summary = ab_system.get_experiment_summary(experiment.experiment_id)
    
    logger.info("\n📊 EXPERIMENT SUMMARY:")
    logger.info(f"Name: {summary['name']}")
    logger.info(f"Status: {summary['status']}")
    logger.info(f"Primary Metric: {summary['primary_metric']}")
    
    logger.info("\nSample Sizes:")
    for group, size in summary['sample_sizes'].items():
        logger.info(f"  {group}: {size}")
    
    logger.info("\nRecommendations:")
    for rec in summary['recommendations']:
        logger.info(f"  {rec}")
    
    return summary


async def simulate_experiment_results(ab_system: ABTestingSystem, experiment_id: str):
    """Simulate experiment results for demonstration."""
    
    # Mock evaluation results
    from datetime import datetime
    import uuid
    import random
    
    # Simulate control group results (baseline performance)
    control_metrics = []
    for i in range(50):  # 50 samples
        # Simulate realistic metrics with some variance
        metrics = {
            "f1@5": random.normalvariate(0.65, 0.1),
            "recall@10": random.normalvariate(0.72, 0.08),
            "precision@5": random.normalvariate(0.68, 0.12),
            "mrr": random.normalvariate(0.58, 0.1),
            "latency_ms": random.normalvariate(850, 100)
        }
        control_metrics.append(metrics)
    
    # Simulate treatment group results (improved performance)
    treatment_metrics = []
    for i in range(52):  # 52 samples (slightly different sample size)
        # Treatment shows improvement in most metrics
        metrics = {
            "f1@5": random.normalvariate(0.73, 0.09),  # 8% improvement
            "recall@10": random.normalvariate(0.78, 0.07),  # 6% improvement  
            "precision@5": random.normalvariate(0.75, 0.11),  # 7% improvement
            "mrr": random.normalvariate(0.62, 0.09),  # 4% improvement
            "latency_ms": random.normalvariate(920, 110)  # Slightly slower
        }
        treatment_metrics.append(metrics)
    
    # Save mock results to database
    import sqlite3
    
    with sqlite3.connect(ab_system.db.db_path) as conn:
        # Save control results
        for i, metrics in enumerate(control_metrics):
            result_id = str(uuid.uuid4())
            evaluation_id = f"{experiment_id}_control_{i}"
            
            conn.execute("""
                INSERT INTO experiment_results 
                (result_id, experiment_id, group_name, evaluation_id, metrics, 
                 sample_count, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id, experiment_id, "control", evaluation_id,
                json.dumps(metrics), 1, datetime.now().isoformat()
            ))
        
        # Save treatment results
        for i, metrics in enumerate(treatment_metrics):
            result_id = str(uuid.uuid4())
            evaluation_id = f"{experiment_id}_treatment_{i}"
            
            conn.execute("""
                INSERT INTO experiment_results 
                (result_id, experiment_id, group_name, evaluation_id, metrics, 
                 sample_count, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id, experiment_id, "treatment", evaluation_id,
                json.dumps(metrics), 1, datetime.now().isoformat()
            ))


def demonstrate_statistical_concepts():
    """Demonstrate key statistical concepts used in A/B testing."""
    
    logger.info("\n📚 Statistical Concepts in A/B Testing:")
    
    concepts = [
        {
            "concept": "Statistical Significance",
            "description": "Probability that observed difference is not due to chance",
            "threshold": "p < 0.05 (95% confidence)"
        },
        {
            "concept": "Effect Size",
            "description": "Magnitude of the difference between groups",
            "interpretation": "Cohen's d: 0.2=small, 0.5=medium, 0.8=large"
        },
        {
            "concept": "Statistical Power", 
            "description": "Probability of detecting a true effect",
            "target": "80% power (β = 0.2)"
        },
        {
            "concept": "Sample Size",
            "description": "Number of observations needed to detect effect",
            "factors": "Effect size, power, significance level"
        },
        {
            "concept": "Type I Error (α)",
            "description": "False positive - claiming effect when none exists",
            "control": "Set significance level (typically 0.05)"
        },
        {
            "concept": "Type II Error (β)",
            "description": "False negative - missing a true effect", 
            "control": "Increase power through larger sample sizes"
        }
    ]
    
    for concept in concepts:
        logger.info(f"\n{concept['concept']}:")
        logger.info(f"  {concept['description']}")
        for key, value in concept.items():
            if key not in ['concept', 'description']:
                logger.info(f"  {key.title()}: {value}")


def demonstrate_experiment_design_best_practices():
    """Show best practices for A/B test design."""
    
    logger.info("\n🎯 A/B Testing Best Practices:")
    
    practices = [
        "Define hypothesis and primary metric before running",
        "Calculate required sample size upfront", 
        "Randomize assignment to control/treatment groups",
        "Run experiments for sufficient duration",
        "Control for external factors and seasonality",
        "Monitor experiment health and data quality",
        "Avoid multiple comparisons without correction",
        "Consider practical significance, not just statistical",
        "Document assumptions and limitations",
        "Plan for follow-up experiments"
    ]
    
    for i, practice in enumerate(practices, 1):
        logger.info(f"{i:2d}. {practice}")
    
    logger.info("\n⚠️ Common Pitfalls to Avoid:")
    pitfalls = [
        "Stopping experiments early when results look good",
        "Running too many experiments simultaneously", 
        "Ignoring statistical power calculations",
        "Cherry-picking metrics after seeing results",
        "Not accounting for multiple testing",
        "Assuming correlation implies causation"
    ]
    
    for pitfall in pitfalls:
        logger.info(f"  • {pitfall}")


async def main():
    """Main demonstration function."""
    
    logger.info("🎯 A/B Testing Infrastructure Complete Demo")
    logger.info("=" * 50)
    
    # Core A/B testing demonstration
    summary = await demonstrate_ab_testing()
    
    # Educational content
    demonstrate_statistical_concepts()
    demonstrate_experiment_design_best_practices()
    
    logger.info("\n✅ Demo completed successfully!")
    logger.info("\n💡 Key Takeaways:")
    logger.info("  • A/B tests help validate RAG system improvements")
    logger.info("  • Statistical analysis prevents false conclusions")
    logger.info("  • Proper experiment design is crucial for reliable results")
    logger.info("  • Consider both statistical and practical significance")
    
    return summary


if __name__ == "__main__":
    # Set up logging
    logger.add("ab_testing_demo.log", level="INFO")
    
    # Run the demonstration
    asyncio.run(main())
