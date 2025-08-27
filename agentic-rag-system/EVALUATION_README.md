# Agentic RAG Evaluation System

A comprehensive evaluation framework for Retrieval-Augmented Generation (RAG) systems with advanced benchmarking, A/B testing, and statistical analysis capabilities.

## 🎯 Overview

The Agentic RAG Evaluation System provides a complete toolkit for evaluating, benchmarking, and optimizing RAG systems through:

- **Comprehensive Metrics**: Standard IR metrics (Precision@K, Recall@K, F1@K, MRR, NDCG)
- **Automated Benchmarking**: Performance baseline establishment and regression detection
- **A/B Testing Infrastructure**: Statistical significance testing with proper experimental design
- **Synthetic Data Generation**: Scalable query generation for evaluation datasets
- **Golden Dataset Management**: Ground truth annotation and validation tools
- **CLI Interface**: Easy-to-use command-line tools for all evaluation workflows

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
- [Usage Examples](#usage-examples)
- [CLI Commands](#cli-commands)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)
- [Contributing](#contributing)

## 🚀 Installation

```bash
# Install the package
pip install -e .

# Install with evaluation dependencies
pip install -e ".[evaluation]"

# For development
pip install -e ".[dev]"
```

### Dependencies

- **Core**: `pydantic`, `loguru`, `click`
- **Statistical Analysis**: `scipy`, `numpy`
- **Data Processing**: `pandas` (optional)
- **Testing**: `pytest`, `pytest-asyncio`

## ⚡ Quick Start

### 1. Basic Evaluation

```python
import asyncio
from agentic_rag.evaluation.pipeline import EvaluationPipeline
from agentic_rag.evaluation.synthetic_data import SyntheticDataGenerator

# Generate synthetic queries
generator = SyntheticDataGenerator()
queries = generator.generate_domain_queries("technology", count=10)

# Initialize evaluation pipeline
# (assumes you have a multi-tool instance)
pipeline = EvaluationPipeline(multi_tool_instance)

# Run evaluation
results = await pipeline.run_evaluation(queries)

print(f"F1@5: {results.system_metrics.overall_metrics['f1@5']:.3f}")
print(f"MRR: {results.system_metrics.overall_metrics['mrr']:.3f}")
```

### 2. CLI Usage

```bash
# Generate test queries
agentic-rag evaluate generate-queries --domain technology --count 50 --output queries.json

# Run evaluation
agentic-rag evaluate run --queries queries.json --config config.json --output results.json

# Check system status
agentic-rag status
```

### 3. A/B Testing

```python
from agentic_rag.evaluation.ab_testing import ABTestingSystem

# Create A/B test
ab_system = ABTestingSystem()

experiment = ab_system.create_experiment(
    name="LLM Upgrade Test",
    description="Testing GPT-4 vs GPT-3.5 performance",
    control_config=baseline_config,
    treatment_config=improved_config,
    primary_metric="f1@5"
)

# Run experiment and get results
benchmark_result = await ab_system.run_experiment(
    experiment.experiment_id, 
    queries, 
    multi_tool_factory
)

# Analyze statistical significance
analysis = ab_system.analyze_experiment(experiment.experiment_id)
```

## 🏗️ Core Components

### 1. Evaluation Models (`evaluation/models.py`)

**Key Classes:**
- `RetrievalMetrics`: Standard IR metrics (Precision@K, Recall@K, F1@K, MRR, NDCG)
- `QueryResult`: Individual query evaluation results
- `SystemMetrics`: Aggregated system performance metrics
- `EvaluationResult`: Complete evaluation session results

**Supported Metrics:**
- **Precision@K**: Fraction of retrieved documents that are relevant
- **Recall@K**: Fraction of relevant documents that are retrieved
- **F1@K**: Harmonic mean of precision and recall
- **MRR**: Mean Reciprocal Rank
- **NDCG@K**: Normalized Discounted Cumulative Gain

### 2. Synthetic Data Generation (`evaluation/synthetic_data.py`)

```python
from agentic_rag.evaluation.synthetic_data import SyntheticDataGenerator

generator = SyntheticDataGenerator()

# Generate domain-specific queries
tech_queries = generator.generate_domain_queries(
    domain="technology",
    count=100,
    complexity_distribution={"simple": 0.3, "medium": 0.5, "complex": 0.2}
)

# Generate with specific patterns
custom_queries = generator.generate_queries_from_templates([
    "What are the benefits of {technology}?",
    "How does {system} compare to {alternative}?"
], domains=["software", "hardware"])
```

### 3. Automated Benchmarking (`evaluation/benchmarking.py`)

```python
from agentic_rag.evaluation.benchmarking import BenchmarkingSystem

benchmark_system = BenchmarkingSystem()

# Compare multiple configurations
benchmark_result = await benchmark_system.run_comprehensive_benchmark(
    baseline_config=config1,
    competitor_configs=[config2, config3, config4],
    queries=test_queries,
    primary_metric="f1@5"
)

# Automatic winner determination
winner = benchmark_result.get_winner("f1@5")
print(f"Winner: {winner.config_name} with {winner.score:.3f}")

# Regression detection
regression_detected = benchmark_system.detect_regression(
    current_results, historical_baselines, threshold=0.05
)
```

### 4. A/B Testing Infrastructure (`evaluation/ab_testing.py`)

```python
from agentic_rag.evaluation.ab_testing import ABTestingSystem

ab_system = ABTestingSystem()

# Create statistically rigorous experiment
experiment = ab_system.create_experiment(
    name="Retrieval Strategy Test",
    description="Dense vs Hybrid retrieval comparison", 
    control_config=dense_retrieval_config,
    treatment_config=hybrid_retrieval_config,
    primary_metric="f1@5",
    minimum_detectable_effect=0.05,  # 5% improvement
    statistical_power=0.8,           # 80% power
    significance_level=0.05          # 95% confidence
)

print(f"Required sample size: {experiment.sample_size_per_group} per group")

# Run experiment with proper randomization
results = await ab_system.run_experiment(experiment.experiment_id, queries, factory)

# Statistical analysis
analysis = ab_system.analyze_experiment(experiment.experiment_id)
for metric, stats in analysis.items():
    print(f"{metric}: p={stats.p_value:.4f}, effect_size={stats.effect_size:.3f}")
```

### 5. Golden Dataset Management (`evaluation/golden_dataset.py`)

```python
from agentic_rag.evaluation.golden_dataset import GoldenDatasetManager

manager = GoldenDatasetManager()

# Create golden dataset
dataset = manager.create_dataset(
    name="Tech Eval v1.0",
    documents=document_collection,
    queries=annotated_queries
)

# Validate annotations
validation_report = manager.validate_annotations(dataset)
if validation_report.is_valid:
    manager.save_dataset(dataset, "tech_eval_v1.json")

# Load and use
golden_dataset = manager.load_dataset("tech_eval_v1.json")
```

## 💻 CLI Commands

### Evaluation Commands

```bash
# Generate synthetic queries
agentic-rag evaluate generate-queries \\
    --domain technology \\
    --domain finance \\
    --count 100 \\
    --complexity medium \\
    --output queries.json

# Run evaluation
agentic-rag evaluate run \\
    --queries queries.json \\
    --config-file config.json \\
    --output results.json \\
    --evaluation-id "experiment_001"
```

### Benchmarking Commands

```bash
# Compare configurations
agentic-rag benchmark compare \\
    --config1 baseline.json \\
    --config2 improved.json \\
    --queries test_queries.json \\
    --output benchmark_results.json
```

### A/B Testing Commands

```bash
# Create experiment
agentic-rag ab-test create-experiment \\
    --name "LLM Upgrade Test" \\
    --description "Testing GPT-4 vs GPT-3.5" \\
    --control-config baseline.json \\
    --treatment-config improved.json \\
    --primary-metric f1@5 \\
    --min-effect 0.05

# Run experiment
agentic-rag ab-test run-experiment exp_20241201_143022 \\
    --queries experiment_queries.json

# List experiments
agentic-rag ab-test list-experiments
```

### Dataset Management Commands

```bash
# Create golden dataset
agentic-rag dataset create-golden \\
    --name "Tech Evaluation Dataset" \\
    --documents documents.json \\
    --queries annotated_queries.json \\
    --output golden_dataset.json
```

### System Commands

```bash
# System status
agentic-rag status
agentic-rag status --format json

# Help
agentic-rag --help
agentic-rag evaluate --help
```

## 🔬 Advanced Features

### 1. Statistical Rigor

- **Power Analysis**: Automatic sample size calculation
- **Multiple Testing Correction**: Bonferroni and FDR methods
- **Effect Size Calculation**: Cohen's d and practical significance
- **Confidence Intervals**: Bootstrap and parametric methods

### 2. Regression Detection

```python
from agentic_rag.evaluation.benchmarking import RegressionDetector

detector = RegressionDetector(
    baseline_window=7,      # Days of baseline data
    sensitivity=0.05,       # 5% regression threshold
    confidence_level=0.95   # Statistical confidence
)

# Continuous monitoring
is_regression = detector.detect_performance_regression(
    current_metrics=today_results,
    historical_metrics=past_week_results
)

if is_regression:
    detector.send_alert("Performance regression detected in F1@5 metric")
```

### 3. Multi-Domain Evaluation

```python
# Domain-specific evaluation
domain_results = await pipeline.run_domain_evaluation({
    "technology": tech_queries,
    "finance": finance_queries,
    "healthcare": healthcare_queries
})

# Cross-domain analysis
cross_domain_report = pipeline.analyze_cross_domain_performance(domain_results)
```

### 4. Batch Processing

```python
# Large-scale batch evaluation
batch_processor = BatchEvaluationProcessor(
    batch_size=50,
    parallel_workers=4,
    timeout_per_query=30
)

results = await batch_processor.process_large_dataset(
    queries=large_query_set,
    multi_tool=rag_system
)
```

## 📚 API Reference

### Core Classes

#### `EvaluationPipeline`

Main orchestrator for evaluation workflows.

```python
class EvaluationPipeline:
    def __init__(self, multi_tool: MultiTool, config: Optional[Dict] = None)
    
    async def run_evaluation(
        self,
        queries: List[SyntheticQuery],
        evaluation_id: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> EvaluationResult
    
    async def run_batch_evaluation(
        self,
        query_batches: List[List[SyntheticQuery]],
        config: Optional[Dict] = None
    ) -> List[EvaluationResult]
```

#### `BenchmarkingSystem`

Automated benchmarking and comparison.

```python
class BenchmarkingSystem:
    async def run_comprehensive_benchmark(
        self,
        baseline_config: Dict[str, Any],
        competitor_configs: List[Dict[str, Any]],
        queries: List[SyntheticQuery],
        primary_metric: str = "f1@5"
    ) -> BenchmarkResult
    
    def detect_regression(
        self,
        current_results: Dict[str, float],
        historical_results: List[Dict[str, float]],
        threshold: float = 0.05
    ) -> bool
```

#### `ABTestingSystem`

Statistical A/B testing framework.

```python
class ABTestingSystem:
    def create_experiment(
        self,
        name: str,
        description: str,
        control_config: Dict[str, Any],
        treatment_config: Dict[str, Any],
        primary_metric: str = "f1@5",
        minimum_detectable_effect: float = 0.05,
        statistical_power: float = 0.8,
        significance_level: float = 0.05
    ) -> ExperimentConfiguration
    
    async def run_experiment(
        self,
        experiment_id: str,
        queries: List[SyntheticQuery],
        multi_tool_factory: callable
    ) -> BenchmarkResult
    
    def analyze_experiment(
        self,
        experiment_id: str
    ) -> Dict[str, StatisticalResult]
```

### Statistical Functions

```python
# Available statistical tests
from agentic_rag.evaluation.ab_testing import StatisticalAnalyzer

# Welch's t-test (unequal variances)
result = StatisticalAnalyzer.welch_t_test(control_values, treatment_values)

# Bootstrap test (non-parametric)
result = StatisticalAnalyzer.bootstrap_test(control_values, treatment_values)

# Sample size calculation
required_size = StatisticalAnalyzer.calculate_sample_size(
    effect_size=0.05, power=0.8, alpha=0.05
)
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_models.py          # Model tests
pytest tests/test_integration.py    # Integration tests
pytest tests/test_cli_basic.py      # CLI tests

# Run with coverage
pytest --cov=agentic_rag/evaluation --cov-report=html
```

### Test Categories

1. **Unit Tests**: Individual component functionality
2. **Integration Tests**: End-to-end workflow testing  
3. **Statistical Tests**: Verification of statistical calculations
4. **CLI Tests**: Command-line interface testing
5. **Performance Tests**: Scalability and performance validation

## 📊 Examples and Demos

### Complete Evaluation Workflow

```python
import asyncio
from agentic_rag.evaluation import *

async def complete_evaluation_demo():
    # 1. Generate synthetic data
    generator = SyntheticDataGenerator()
    queries = generator.generate_mixed_complexity_queries(
        domains=["technology", "finance"], 
        count=100
    )
    
    # 2. Run baseline evaluation
    pipeline = EvaluationPipeline(your_rag_system)
    baseline_results = await pipeline.run_evaluation(queries)
    
    # 3. Run A/B test
    ab_system = ABTestingSystem()
    experiment = ab_system.create_experiment(
        name="Performance Optimization Test",
        control_config=baseline_config,
        treatment_config=optimized_config,
        primary_metric="f1@5"
    )
    
    ab_results = await ab_system.run_experiment(
        experiment.experiment_id, queries, rag_factory
    )
    
    # 4. Statistical analysis
    analysis = ab_system.analyze_experiment(experiment.experiment_id)
    
    # 5. Generate report
    print(f"Baseline F1@5: {baseline_results.system_metrics.overall_metrics['f1@5']:.3f}")
    print(f"A/B Test Winner: {ab_results.winner}")
    print(f"Statistical Significance: {analysis['f1@5'].is_significant}")
    
    return {
        "baseline": baseline_results,
        "ab_test": ab_results,
        "statistical_analysis": analysis
    }

# Run the demo
results = asyncio.run(complete_evaluation_demo())
```

### Benchmarking Demo

See `examples/benchmarking_demo.py` for a comprehensive benchmarking example.

### A/B Testing Demo

See `examples/ab_testing_demo.py` for detailed A/B testing workflows.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/agentic-rag-system.git
cd agentic-rag-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
flake8 agentic_rag/
black agentic_rag/
```

### Code Standards

- **Type Hints**: All functions must have type annotations
- **Documentation**: Comprehensive docstrings for all public APIs
- **Testing**: Minimum 80% test coverage for new code
- **Formatting**: Use `black` for code formatting
- **Imports**: Use `isort` for import organization

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🆘 Support

- **Documentation**: [Full Documentation](https://docs.agentic-rag.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/agentic-rag-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/agentic-rag-system/discussions)
- **Email**: support@agentic-rag.com

## 🙏 Acknowledgments

- Built with inspiration from modern RAG research and best practices
- Statistical methods based on established A/B testing frameworks
- IR metrics implementation follows TREC evaluation standards

---

**Happy Evaluating! 🚀**
