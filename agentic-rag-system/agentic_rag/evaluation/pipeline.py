"""
Evaluation pipeline orchestrator for RAG system performance measurement.

This module provides the main evaluation pipeline that coordinates
tool testing, metric calculation, and performance analysis.
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any, Callable, Union
from pathlib import Path
import json

from loguru import logger

from ..core.models import ToolType
from ..tools.base import MultiTool
from .models import (
    EvaluationResult,
    QueryMetrics,
    SystemMetrics,
    BenchmarkResult,
    RetrievalMetrics
)
from .synthetic_data import SyntheticQuery, create_synthetic_queries


class EvaluationPipeline:
    """Main evaluation pipeline orchestrator."""
    
    def __init__(self, multi_tool: MultiTool):
        """Initialize the evaluation pipeline with a multi-tool instance."""
        self.multi_tool = multi_tool
        self.evaluation_configs = {}
        self.results_cache = {}
    
    async def run_evaluation(self,
                           queries: List[SyntheticQuery],
                           evaluation_id: Optional[str] = None,
                           tools_to_test: Optional[List[ToolType]] = None,
                           config: Optional[Dict[str, Any]] = None) -> EvaluationResult:
        """Run comprehensive evaluation on a set of queries."""
        
        if evaluation_id is None:
            evaluation_id = f"eval_{uuid.uuid4().hex[:8]}"
        
        if config is None:
            config = {"default_evaluation": True}
        
        if tools_to_test is None:
            tools_to_test = list(self.multi_tool.get_available_tools())
        
        logger.info(f"Starting evaluation {evaluation_id} with {len(queries)} queries and {len(tools_to_test)} tools")
        
        # Initialize evaluation result
        evaluation_result = EvaluationResult(
            evaluation_id=evaluation_id,
            config=config
        )
        
        # Process queries sequentially or in batches
        batch_size = config.get("batch_size", 10)
        
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i+batch_size]
            batch_results = await self._process_query_batch(batch, tools_to_test)
            
            for query_metrics in batch_results:
                evaluation_result.add_query_result(query_metrics)
            
            # Log progress
            progress = min(i + batch_size, len(queries))
            logger.info(f"Processed {progress}/{len(queries)} queries ({progress/len(queries)*100:.1f}%)")
        
        # Finalize results
        evaluation_result.finalize()
        
        # Cache results
        self.results_cache[evaluation_id] = evaluation_result
        
        logger.info(f"Evaluation {evaluation_id} completed in {evaluation_result.total_duration_seconds:.2f}s")
        
        return evaluation_result
    
    async def _process_query_batch(self,
                                 queries: List[SyntheticQuery],
                                 tools_to_test: List[ToolType]) -> List[QueryMetrics]:
        """Process a batch of queries in parallel."""
        
        tasks = []
        for query in queries:
            task = self._evaluate_single_query(query, tools_to_test)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error evaluating query {queries[i].query_text}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _evaluate_single_query(self,
                                   query: SyntheticQuery,
                                   tools_to_test: List[ToolType]) -> QueryMetrics:
        """Evaluate a single query across multiple tools."""
        
        query_metrics = QueryMetrics(
            query=query.query_text,
            query_type=query.query_type.value,
            complexity=query.complexity.value
        )
        
        start_time = time.time()
        
        # Test each tool
        for tool_type in tools_to_test:
            try:
                # Execute tool
                tool_start = time.time()
                result = await self.multi_tool.execute_single(
                    tool_type,
                    query.query_text,
                    limit=10  # Standard limit for evaluation
                )
                tool_end = time.time()
                result.latency_ms = (tool_end - tool_start) * 1000
                
                # Add result and calculate metrics
                query_metrics.add_tool_result(
                    tool_type.value,
                    result,
                    query.relevant_documents
                )
                
            except Exception as e:
                logger.error(f"Tool {tool_type.value} failed for query '{query.query_text}': {e}")
                # Create empty result for failed tool
                from ..core.models import RetrievalResult
                empty_result = RetrievalResult(
                    tool_used=tool_type,
                    query=query.query_text,
                    content="",
                    citations=[],
                    confidence=0.0,
                    latency_ms=0.0,
                    metadata={"error": str(e)}
                )
                query_metrics.add_tool_result(
                    tool_type.value,
                    empty_result,
                    query.relevant_documents
                )
        
        query_metrics.total_latency_ms = (time.time() - start_time) * 1000
        
        return query_metrics
    
    async def run_quick_evaluation(self,
                                 num_queries: int = 50,
                                 tools_to_test: Optional[List[ToolType]] = None) -> EvaluationResult:
        """Run a quick evaluation with generated synthetic queries."""
        
        logger.info(f"Generating {num_queries} synthetic queries for quick evaluation")
        
        # Generate synthetic queries
        synthetic_queries = create_synthetic_queries(count=num_queries)
        
        # Create simple document pool for golden dataset
        document_pool = [
            f"doc_{i}" for i in range(100)  # Simple document IDs
        ]
        
        # Assign relevant documents
        from .synthetic_data import create_golden_dataset
        golden_queries = create_golden_dataset(synthetic_queries, document_pool)
        
        # Run evaluation
        return await self.run_evaluation(
            golden_queries,
            evaluation_id="quick_eval",
            tools_to_test=tools_to_test
        )
    
    def get_evaluation_summary(self, evaluation_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of a completed evaluation."""
        if evaluation_id not in self.results_cache:
            return None
        
        result = self.results_cache[evaluation_id]
        return result.get_summary_report()
    
    def save_evaluation(self, evaluation_id: str, filepath: str):
        """Save evaluation results to file."""
        if evaluation_id not in self.results_cache:
            raise ValueError(f"Evaluation {evaluation_id} not found in cache")
        
        result = self.results_cache[evaluation_id]
        
        # Convert to dict for JSON serialization
        data = result.dict()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Evaluation {evaluation_id} saved to {filepath}")
    
    def load_evaluation(self, filepath: str) -> str:
        """Load evaluation results from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        result = EvaluationResult(**data)
        evaluation_id = result.evaluation_id
        
        self.results_cache[evaluation_id] = result
        
        logger.info(f"Evaluation {evaluation_id} loaded from {filepath}")
        return evaluation_id


class BenchmarkRunner:
    """Runs benchmark comparisons between different configurations."""
    
    def __init__(self, multi_tool_factory: Callable[[], MultiTool]):
        """Initialize with a factory function that creates MultiTool instances."""
        self.multi_tool_factory = multi_tool_factory
        self.benchmark_results = {}
    
    async def run_ab_test(self,
                        config_a: Dict[str, Any],
                        config_b: Dict[str, Any],
                        queries: List[SyntheticQuery],
                        test_name: str,
                        num_iterations: int = 1) -> BenchmarkResult:
        """Run A/B test between two configurations."""
        
        benchmark_id = f"ab_test_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Starting A/B test {benchmark_id}: {test_name}")
        
        benchmark_result = BenchmarkResult(
            benchmark_id=benchmark_id,
            comparison_name=test_name
        )
        
        # Run evaluation for each configuration
        for config_name, config in [("config_a", config_a), ("config_b", config_b)]:
            # Create multi-tool instance with configuration
            multi_tool = self.multi_tool_factory()
            # Apply configuration (would need to implement config application)
            
            pipeline = EvaluationPipeline(multi_tool)
            
            # Run multiple iterations if specified
            iteration_results = []
            for i in range(num_iterations):
                eval_result = await pipeline.run_evaluation(
                    queries,
                    evaluation_id=f"{benchmark_id}_{config_name}_iter_{i}",
                    config=config
                )
                iteration_results.append(eval_result)
            
            # Combine results (for now, just use the first iteration)
            final_result = iteration_results[0]
            benchmark_result.add_result(config_name, final_result, config)
        
        # Determine winner
        benchmark_result.determine_winner("f1@5")
        
        # Calculate statistical significance (simplified)
        benchmark_result.statistical_significance = self._calculate_statistical_significance(
            benchmark_result.results["config_a"],
            benchmark_result.results["config_b"]
        )
        
        self.benchmark_results[benchmark_id] = benchmark_result
        
        logger.info(f"A/B test {benchmark_id} completed. Winner: {benchmark_result.winning_configuration}")
        
        return benchmark_result
    
    def _calculate_statistical_significance(self,
                                          result_a: EvaluationResult,
                                          result_b: EvaluationResult) -> Dict[str, Dict[str, float]]:
        """Calculate statistical significance between two results."""
        # Simplified p-value calculation (would need proper statistical testing)
        metrics = ["recall@5", "precision@5", "f1@5", "mrr", "ndcg@5"]
        
        significance = {}
        
        if result_a.system_metrics and result_b.system_metrics:
            for metric in metrics:
                value_a = result_a.system_metrics.overall_metrics.get(metric, 0.0)
                value_b = result_b.system_metrics.overall_metrics.get(metric, 0.0)
                
                # Simplified significance test (in practice, use proper statistical tests)
                if abs(value_a - value_b) > 0.05:  # 5% difference threshold
                    p_value = 0.01  # Assume significant
                else:
                    p_value = 0.5   # Assume not significant
                
                significance[metric] = {"p_value": p_value}
        
        return significance
    
    async def run_regression_test(self,
                                current_config: Dict[str, Any],
                                baseline_result: EvaluationResult,
                                queries: List[SyntheticQuery],
                                regression_threshold: float = 0.05) -> Dict[str, Any]:
        """Run regression test against a baseline."""
        
        logger.info("Running regression test against baseline")
        
        # Run current configuration
        multi_tool = self.multi_tool_factory()
        pipeline = EvaluationPipeline(multi_tool)
        
        current_result = await pipeline.run_evaluation(
            queries,
            evaluation_id="regression_test",
            config=current_config
        )
        
        # Compare metrics
        regression_report = {
            "test_passed": True,
            "regressions_detected": [],
            "improvements_detected": [],
            "current_metrics": current_result.system_metrics.overall_metrics,
            "baseline_metrics": baseline_result.system_metrics.overall_metrics
        }
        
        if current_result.system_metrics and baseline_result.system_metrics:
            metrics = ["recall@5", "precision@5", "f1@5", "mrr", "ndcg@5"]
            
            for metric in metrics:
                current_value = current_result.system_metrics.overall_metrics.get(metric, 0.0)
                baseline_value = baseline_result.system_metrics.overall_metrics.get(metric, 0.0)
                
                if baseline_value > 0:
                    change_percent = (current_value - baseline_value) / baseline_value
                    
                    if change_percent < -regression_threshold:
                        regression_report["regressions_detected"].append({
                            "metric": metric,
                            "current": current_value,
                            "baseline": baseline_value,
                            "change_percent": change_percent * 100
                        })
                        regression_report["test_passed"] = False
                    elif change_percent > regression_threshold:
                        regression_report["improvements_detected"].append({
                            "metric": metric,
                            "current": current_value,
                            "baseline": baseline_value,
                            "change_percent": change_percent * 100
                        })
        
        return regression_report


# Utility functions for easy access

async def run_evaluation(multi_tool: MultiTool,
                       queries: List[SyntheticQuery],
                       evaluation_id: Optional[str] = None,
                       tools_to_test: Optional[List[ToolType]] = None) -> EvaluationResult:
    """Quick utility to run evaluation."""
    pipeline = EvaluationPipeline(multi_tool)
    return await pipeline.run_evaluation(queries, evaluation_id, tools_to_test)


async def compare_tools(multi_tool: MultiTool,
                      num_queries: int = 100,
                      tools_to_test: Optional[List[ToolType]] = None) -> Dict[str, Any]:
    """Compare performance of different tools."""
    pipeline = EvaluationPipeline(multi_tool)
    result = await pipeline.run_quick_evaluation(num_queries, tools_to_test)
    
    return {
        "evaluation_id": result.evaluation_id,
        "tool_comparison": result.system_metrics.tool_performance,
        "best_tool_distribution": result.system_metrics.best_tool_distribution,
        "overall_metrics": result.system_metrics.overall_metrics
    }


def create_evaluation_report(evaluation_result: EvaluationResult) -> str:
    """Create a formatted evaluation report."""
    
    if not evaluation_result.system_metrics:
        return "No system metrics available"
    
    report_lines = [
        f"# Evaluation Report: {evaluation_result.evaluation_id}",
        f"Duration: {evaluation_result.total_duration_seconds:.2f}s",
        f"Total Queries: {len(evaluation_result.query_results)}",
        "",
        "## Overall Performance"
    ]
    
    # Overall metrics
    for metric, value in evaluation_result.system_metrics.overall_metrics.items():
        report_lines.append(f"- {metric}: {value:.3f}")
    
    report_lines.extend([
        "",
        "## Tool Performance"
    ])
    
    # Tool-specific metrics
    for tool_name, metrics in evaluation_result.system_metrics.tool_performance.items():
        report_lines.append(f"\n### {tool_name}")
        for metric, value in metrics.items():
            report_lines.append(f"- {metric}: {value:.3f}")
    
    report_lines.extend([
        "",
        "## Best Tool Distribution"
    ])
    
    # Best tool distribution
    for tool_name, count in evaluation_result.system_metrics.best_tool_distribution.items():
        percentage = (count / len(evaluation_result.query_results)) * 100
        report_lines.append(f"- {tool_name}: {count} queries ({percentage:.1f}%)")
    
    return "\n".join(report_lines)
