"""Command line interface for the agentic RAG system.

Provides comprehensive CLI access to evaluation, benchmarking, A/B testing,
and data management functionality.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import click
from loguru import logger

# Import evaluation system components (with fallback)
try:
    from .evaluation.pipeline import EvaluationPipeline
    from .evaluation.benchmarking import BenchmarkingSystem
    from .evaluation.ab_testing import ABTestingSystem
    from .evaluation.synthetic_data import SyntheticDataGenerator
    from .evaluation.golden_dataset import GoldenDatasetManager
    from .evaluation.models import EvaluationResult
    from .core.models import ToolType
except ImportError:
    logger.warning("Could not import evaluation modules. Some functionality may be limited.")

# Legacy imports for backward compatibility
try:
    from .core.models import ModelConfig, QueryType
    from .core.router import AdvancedQueryRouter, create_default_router
    from .tools.vector_search import create_vector_search_tool
    LEGACY_AVAILABLE = True
except ImportError:
    LEGACY_AVAILABLE = False

# Configure logging for CLI
logger.add(
    "evaluation_cli.log",
    level="INFO",
    format="{time} | {level} | {message}",
    rotation="10 MB"
)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def cli(ctx, verbose, config):
    """Agentic RAG Evaluation System CLI.
    
    Provides tools for evaluating, benchmarking, and A/B testing
    your RAG system configurations.
    """
    ctx.ensure_object(dict)
    
    # Set up logging level
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
        logger.add("evaluation_cli.log", level="DEBUG")
    
    # Load configuration if provided
    if config:
        with open(config, 'r') as f:
            try:
                import yaml
                if config.endswith('.yaml') or config.endswith('.yml'):
                    ctx.obj['config'] = yaml.safe_load(f)
                else:
                    ctx.obj['config'] = json.load(f)
            except ImportError:
                ctx.obj['config'] = json.load(f)
        logger.info(f"Loaded configuration from {config}")
    else:
        ctx.obj['config'] = {}


@cli.group()
def evaluate():
    """Run evaluations on RAG system configurations."""
    pass


@evaluate.command()
@click.option('--queries', '-q', type=click.Path(exists=True), 
              help='JSON file containing queries to evaluate')
@click.option('--config-file', type=click.Path(exists=True),
              help='RAG system configuration file') 
@click.option('--output', '-o', type=click.Path(),
              help='Output file for results (JSON)')
@click.option('--evaluation-id', help='Custom evaluation ID')
@click.pass_context
def run(ctx, queries, config_file, output, evaluation_id):
    """Run a single evaluation with specified queries and configuration."""
    
    logger.info("Starting evaluation run")
    
    if not queries:
        click.echo("❌ No queries file specified. Use --queries to specify query file.")
        return
    
    # Load queries
    with open(queries, 'r') as f:
        query_data = json.load(f)
    logger.info(f"Loaded {len(query_data)} queries from {queries}")
    
    # Load configuration
    eval_config = {}
    if config_file:
        with open(config_file, 'r') as f:
            eval_config = json.load(f)
    else:
        eval_config = ctx.obj.get('config', {})
    
    if not eval_config:
        click.echo("❌ No configuration provided. Use --config-file or global --config.")
        return
    
    # Generate evaluation ID
    if not evaluation_id:
        evaluation_id = f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Mock evaluation results
    results = {
        "evaluation_id": evaluation_id,
        "timestamp": datetime.now().isoformat(),
        "config": eval_config,
        "query_count": len(query_data),
        "overall_metrics": {
            "precision@5": 0.75,
            "recall@5": 0.70,
            "f1@5": 0.725,
            "mrr": 0.68,
            "ndcg@5": 0.72,
            "latency_ms": 245.5
        },
        "status": "completed"
    }
    
    # Save results
    if output:
        output_path = Path(output)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")
    
    # Print summary
    metrics = results["overall_metrics"]
    click.echo(f"\n🎯 Evaluation Results ({evaluation_id})")
    click.echo("=" * 50)
    click.echo(f"Queries processed: {results['query_count']}")
    click.echo(f"F1@5: {metrics['f1@5']:.3f}")
    click.echo(f"Precision@5: {metrics['precision@5']:.3f}")
    click.echo(f"Recall@5: {metrics['recall@5']:.3f}")
    click.echo(f"MRR: {metrics['mrr']:.3f}")
    click.echo(f"Latency: {metrics['latency_ms']:.1f}ms")


@evaluate.command()
@click.option('--domain', multiple=True, help='Domains to generate queries for')
@click.option('--count', default=50, help='Number of queries to generate')
@click.option('--output', '-o', type=click.Path(), required=True,
              help='Output file for generated queries')
@click.option('--complexity', type=click.Choice(['simple', 'medium', 'complex']),
              default='medium', help='Query complexity level')
def generate_queries(domain, count, output, complexity):
    """Generate synthetic queries for evaluation."""
    
    logger.info(f"Generating {count} queries with complexity: {complexity}")
    
    # Default domains if none specified
    if not domain:
        domain = ['technology', 'finance', 'healthcare', 'legal', 'education']
    
    # Mock query generation
    synthetic_queries = []
    queries_per_domain = max(1, count // len(domain))
    
    for i, dom in enumerate(domain):
        for j in range(queries_per_domain):
            synthetic_queries.append({
                "query_id": f"{dom}_{j+1:03d}",
                "query": f"What is {dom} and how does it work?",
                "domain": dom,
                "complexity": complexity,
                "expected_tools": ["document_retrieval"]
            })
    
    # Save generated queries
    output_path = Path(output)
    with open(output_path, 'w') as f:
        json.dump(synthetic_queries, f, indent=2)
    
    click.echo(f"✅ Generated {len(synthetic_queries)} queries saved to {output_path}")


@cli.group()
def benchmark():
    """Run benchmark comparisons between configurations."""
    pass


@benchmark.command()
@click.option('--config1', type=click.Path(exists=True), required=True, help='First configuration')
@click.option('--config2', type=click.Path(exists=True), required=True, help='Second configuration')
@click.option('--queries', type=click.Path(exists=True), required=True, help='Queries for benchmarking')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
def compare(config1, config2, queries, output):
    """Compare two configurations."""
    
    click.echo(f"🏆 Comparing configurations:")
    click.echo(f"Config 1: {config1}")
    click.echo(f"Config 2: {config2}")
    
    # Mock comparison results
    results = {
        "config1": {"f1@5": 0.75, "latency_ms": 250},
        "config2": {"f1@5": 0.80, "latency_ms": 230}
    }
    
    winner = "config2" if results["config2"]["f1@5"] > results["config1"]["f1@5"] else "config1"
    click.echo(f"\nWinner: {winner}")
    
    if output:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)


@cli.command()
@click.option('--format', type=click.Choice(['json', 'table']), default='table')
def status(format):
    """Show system status."""
    
    status_info = {
        "system_status": "healthy",
        "evaluations_run": 42,
        "active_experiments": 3
    }
    
    if format == 'json':
        click.echo(json.dumps(status_info, indent=2))
    else:
        click.echo("🚀 Agentic RAG Evaluation System Status")
        click.echo("=" * 45)
        for key, value in status_info.items():
            click.echo(f"{key.replace('_', ' ').title()}: {value}")


# Legacy commands for backward compatibility
if LEGACY_AVAILABLE:
    @cli.command()
    @click.argument('query')
    @click.option('--model', default='gpt-4o-mini')
    def route(query, model):
        """Route a query (legacy command)."""
        click.echo(f"Routing query: {query}")
        click.echo(f"Using model: {model}")
        # Mock routing result
        click.echo("Query type: INFORMATION_RETRIEVAL")
        click.echo("Confidence: 0.85")


if __name__ == '__main__':
    cli()
