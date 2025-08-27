"""
Evaluation framework for RAG system performance measurement.

This module provides comprehensive evaluation capabilities including:
- Standard information retrieval metrics (recall@k, MRR, NDCG, precision)
- Synthetic query generation for testing
- Automated benchmarking and regression detection
- A/B testing infrastructure
- Performance analysis and reporting
"""

from .models import (
    RetrievalMetrics,
    QueryMetrics, 
    SystemMetrics,
    EvaluationResult,
    BenchmarkResult
)

from .synthetic_data import (
    QueryGenerator,
    GoldenDatasetGenerator,
    create_synthetic_queries,
    create_golden_dataset
)

from .pipeline import (
    EvaluationPipeline,
    BenchmarkRunner,
    run_evaluation,
    compare_tools
)

__all__ = [
    # Models
    "RetrievalMetrics",
    "QueryMetrics", 
    "SystemMetrics",
    "EvaluationResult",
    "BenchmarkResult",
    
    # Synthetic Data
    "QueryGenerator",
    "GoldenDatasetGenerator", 
    "create_synthetic_queries",
    "create_golden_dataset",
    
    # Pipeline
    "EvaluationPipeline",
    "BenchmarkRunner",
    "run_evaluation",
    "compare_tools",
]
