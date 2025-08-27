"""
Evaluation models for RAG system performance measurement.

This module defines Pydantic models for comprehensive evaluation metrics
following standard information retrieval practices.
"""

import math
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator

from ..core.models import RetrievalResult, Citation


class RetrievalMetrics(BaseModel):
    """Standard information retrieval metrics for a single query."""
    
    query: str = Field(..., description="The original query")
    
    # Core IR Metrics
    recall_at_k: Dict[int, float] = Field(
        default_factory=dict, 
        description="Recall@k for different k values (1, 3, 5, 10)"
    )
    precision_at_k: Dict[int, float] = Field(
        default_factory=dict,
        description="Precision@k for different k values (1, 3, 5, 10)"
    )
    mean_reciprocal_rank: float = Field(
        0.0,
        description="Mean Reciprocal Rank (MRR) - 1/rank of first relevant result"
    )
    ndcg_at_k: Dict[int, float] = Field(
        default_factory=dict,
        description="Normalized Discounted Cumulative Gain@k"
    )
    
    # Additional Metrics
    average_precision: float = Field(
        0.0,
        description="Average Precision across all relevant documents"
    )
    f1_at_k: Dict[int, float] = Field(
        default_factory=dict,
        description="F1 score@k combining precision and recall"
    )
    
    # Metadata
    total_retrieved: int = Field(0, description="Total documents retrieved")
    total_relevant: int = Field(0, description="Total relevant documents available")
    relevant_retrieved: int = Field(0, description="Relevant documents retrieved")
    
    @validator('recall_at_k', 'precision_at_k', 'ndcg_at_k', 'f1_at_k', pre=True)
    def ensure_dict(cls, v):
        """Ensure metric dictionaries have default k values."""
        if not isinstance(v, dict):
            v = {}
        
        # Ensure standard k values exist
        for k in [1, 3, 5, 10]:
            if k not in v:
                v[k] = 0.0
        
        return v
    
    @classmethod
    def calculate_metrics(
        cls,
        query: str,
        retrieved_results: List[Citation],
        relevant_doc_ids: List[str],
        max_k: int = 10
    ) -> "RetrievalMetrics":
        """Calculate all metrics for a query given retrieved results and relevant documents."""
        
        # Create binary relevance list
        retrieved_ids = [result.source_id for result in retrieved_results]
        relevance_scores = [1 if doc_id in relevant_doc_ids else 0 for doc_id in retrieved_ids]
        
        metrics = cls(query=query)
        
        # Basic counts
        metrics.total_retrieved = len(retrieved_results)
        metrics.total_relevant = len(relevant_doc_ids)
        metrics.relevant_retrieved = sum(relevance_scores)
        
        if not retrieved_results:
            return metrics
        
        # Calculate metrics for different k values
        k_values = [1, 3, 5, 10, max_k] if max_k > 10 else [1, 3, 5, 10]
        k_values = [k for k in k_values if k <= len(retrieved_results)]
        
        for k in k_values:
            if k > len(retrieved_results):
                continue
                
            # Recall@k and Precision@k
            relevant_at_k = sum(relevance_scores[:k])
            metrics.recall_at_k[k] = relevant_at_k / metrics.total_relevant if metrics.total_relevant > 0 else 0.0
            metrics.precision_at_k[k] = relevant_at_k / k if k > 0 else 0.0
            
            # F1@k
            if metrics.recall_at_k[k] + metrics.precision_at_k[k] > 0:
                metrics.f1_at_k[k] = 2 * (metrics.recall_at_k[k] * metrics.precision_at_k[k]) / \
                                   (metrics.recall_at_k[k] + metrics.precision_at_k[k])
            else:
                metrics.f1_at_k[k] = 0.0
            
            # NDCG@k
            metrics.ndcg_at_k[k] = cls._calculate_ndcg(relevance_scores[:k], k)
        
        # MRR
        for i, is_relevant in enumerate(relevance_scores):
            if is_relevant:
                metrics.mean_reciprocal_rank = 1.0 / (i + 1)
                break
        
        # Average Precision
        metrics.average_precision = cls._calculate_average_precision(relevance_scores)
        
        return metrics
    
    @staticmethod
    def _calculate_ndcg(relevance_scores: List[int], k: int) -> float:
        """Calculate Normalized Discounted Cumulative Gain@k."""
        if not relevance_scores or k <= 0:
            return 0.0
        
        # DCG@k
        dcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(relevance_scores[:k]))
        
        # IDCG@k (ideal DCG)
        ideal_relevance = sorted(relevance_scores[:k], reverse=True)
        idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal_relevance))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def _calculate_average_precision(relevance_scores: List[int]) -> float:
        """Calculate Average Precision."""
        if not relevance_scores:
            return 0.0
        
        relevant_count = 0
        precision_sum = 0.0
        
        for i, is_relevant in enumerate(relevance_scores):
            if is_relevant:
                relevant_count += 1
                precision_at_i = relevant_count / (i + 1)
                precision_sum += precision_at_i
        
        return precision_sum / sum(relevance_scores) if sum(relevance_scores) > 0 else 0.0


class QueryMetrics(BaseModel):
    """Comprehensive metrics for a single query evaluation."""
    
    query: str = Field(..., description="The query text")
    query_type: str = Field("unknown", description="Type/category of query")
    complexity: str = Field("medium", description="Query complexity (simple/medium/complex)")
    
    # Tool-specific results
    tool_results: Dict[str, RetrievalResult] = Field(
        default_factory=dict,
        description="Results from different tools"
    )
    
    # Tool-specific metrics
    tool_metrics: Dict[str, RetrievalMetrics] = Field(
        default_factory=dict,
        description="Metrics for each tool"
    )
    
    # Best performing tool
    best_tool: Optional[str] = Field(None, description="Tool with highest performance")
    best_metric_value: float = Field(0.0, description="Best metric value achieved")
    
    # Timing
    evaluation_time: datetime = Field(default_factory=datetime.now)
    total_latency_ms: float = Field(0.0, description="Total evaluation time")
    
    def add_tool_result(self, tool_name: str, result: RetrievalResult, relevant_docs: List[str]):
        """Add result from a tool and calculate metrics."""
        self.tool_results[tool_name] = result
        self.tool_metrics[tool_name] = RetrievalMetrics.calculate_metrics(
            self.query, result.citations, relevant_docs
        )
        
        # Update best tool based on F1@5
        f1_5 = self.tool_metrics[tool_name].f1_at_k.get(5, 0.0)
        if f1_5 > self.best_metric_value:
            self.best_tool = tool_name
            self.best_metric_value = f1_5
    
    def get_comparative_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get comparative metrics across all tools."""
        comparison = {}
        
        for tool_name, metrics in self.tool_metrics.items():
            comparison[tool_name] = {
                "recall@5": metrics.recall_at_k.get(5, 0.0),
                "precision@5": metrics.precision_at_k.get(5, 0.0),
                "f1@5": metrics.f1_at_k.get(5, 0.0),
                "mrr": metrics.mean_reciprocal_rank,
                "ndcg@5": metrics.ndcg_at_k.get(5, 0.0),
                "latency_ms": self.tool_results[tool_name].latency_ms
            }
        
        return comparison


class SystemMetrics(BaseModel):
    """Aggregate metrics across multiple queries and tools."""
    
    evaluation_id: str = Field(..., description="Unique evaluation identifier")
    evaluation_time: datetime = Field(default_factory=datetime.now)
    
    # Query statistics
    total_queries: int = Field(0, description="Total number of queries evaluated")
    query_types: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of queries by type"
    )
    
    # Tool performance
    tool_performance: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Average metrics per tool"
    )
    
    # Overall system metrics
    overall_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="System-wide average metrics"
    )
    
    # Performance analysis
    best_tool_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="How often each tool performed best"
    )
    
    # Latency statistics
    latency_stats: Dict[str, float] = Field(
        default_factory=dict,
        description="Latency statistics (mean, median, p95, p99)"
    )
    
    def add_query_metrics(self, query_metrics: QueryMetrics):
        """Add metrics from a single query evaluation."""
        self.total_queries += 1
        
        # Update query type counts
        query_type = query_metrics.query_type
        self.query_types[query_type] = self.query_types.get(query_type, 0) + 1
        
        # Update best tool distribution
        if query_metrics.best_tool:
            best_tool = query_metrics.best_tool
            self.best_tool_distribution[best_tool] = self.best_tool_distribution.get(best_tool, 0) + 1
        
        # Update tool performance (running averages)
        for tool_name, metrics in query_metrics.tool_metrics.items():
            if tool_name not in self.tool_performance:
                self.tool_performance[tool_name] = {
                    "recall@5": 0.0, "precision@5": 0.0, "f1@5": 0.0,
                    "mrr": 0.0, "ndcg@5": 0.0, "latency_ms": 0.0
                }
            
            # Running average update
            n = self.total_queries
            current = self.tool_performance[tool_name]
            current["recall@5"] = ((n-1) * current["recall@5"] + metrics.recall_at_k.get(5, 0.0)) / n
            current["precision@5"] = ((n-1) * current["precision@5"] + metrics.precision_at_k.get(5, 0.0)) / n
            current["f1@5"] = ((n-1) * current["f1@5"] + metrics.f1_at_k.get(5, 0.0)) / n
            current["mrr"] = ((n-1) * current["mrr"] + metrics.mean_reciprocal_rank) / n
            current["ndcg@5"] = ((n-1) * current["ndcg@5"] + metrics.ndcg_at_k.get(5, 0.0)) / n
            
            # Update latency
            tool_latency = query_metrics.tool_results[tool_name].latency_ms
            current["latency_ms"] = ((n-1) * current["latency_ms"] + tool_latency) / n
    
    def finalize_metrics(self):
        """Calculate final system-wide metrics."""
        if not self.tool_performance:
            return
        
        # Calculate overall system metrics (average across tools)
        metrics_to_average = ["recall@5", "precision@5", "f1@5", "mrr", "ndcg@5", "latency_ms"]
        
        for metric in metrics_to_average:
            values = [tool_metrics[metric] for tool_metrics in self.tool_performance.values()]
            self.overall_metrics[metric] = sum(values) / len(values) if values else 0.0


class EvaluationResult(BaseModel):
    """Complete evaluation result for a set of queries."""
    
    evaluation_id: str = Field(..., description="Unique evaluation identifier")
    config: Dict[str, Any] = Field(default_factory=dict, description="Evaluation configuration")
    
    # Results
    query_results: List[QueryMetrics] = Field(default_factory=list)
    system_metrics: Optional[SystemMetrics] = None
    
    # Metadata
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_duration_seconds: float = Field(0.0)
    
    def add_query_result(self, query_metrics: QueryMetrics):
        """Add results from a single query evaluation."""
        self.query_results.append(query_metrics)
        
        if not self.system_metrics:
            self.system_metrics = SystemMetrics(evaluation_id=self.evaluation_id)
        
        self.system_metrics.add_query_metrics(query_metrics)
    
    def finalize(self):
        """Finalize the evaluation and calculate summary statistics."""
        self.end_time = datetime.now()
        self.total_duration_seconds = (self.end_time - self.start_time).total_seconds()
        
        if self.system_metrics:
            self.system_metrics.finalize_metrics()
    
    def get_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of the evaluation."""
        if not self.system_metrics:
            return {"error": "No system metrics available"}
        
        return {
            "evaluation_id": self.evaluation_id,
            "total_queries": len(self.query_results),
            "duration_seconds": self.total_duration_seconds,
            "overall_performance": self.system_metrics.overall_metrics,
            "tool_performance": self.system_metrics.tool_performance,
            "best_tool_distribution": self.system_metrics.best_tool_distribution,
            "query_type_distribution": self.system_metrics.query_types,
        }


class BenchmarkResult(BaseModel):
    """Result of a benchmark comparison between different configurations."""
    
    benchmark_id: str = Field(..., description="Unique benchmark identifier")
    comparison_name: str = Field(..., description="Name describing what's being compared")
    
    # Configurations being compared
    configurations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Configuration details for each variant"
    )
    
    # Evaluation results
    results: Dict[str, EvaluationResult] = Field(
        default_factory=dict,
        description="Evaluation results for each configuration"
    )
    
    # Statistical analysis
    statistical_significance: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="P-values for pairwise comparisons"
    )
    
    # Winner determination
    winning_configuration: Optional[str] = Field(None, description="Best performing configuration")
    winning_metric: str = Field("f1@5", description="Metric used to determine winner")
    improvement_percentage: float = Field(0.0, description="Improvement over baseline")
    
    # Metadata
    benchmark_time: datetime = Field(default_factory=datetime.now)
    
    def add_result(self, config_name: str, result: EvaluationResult, config: Dict[str, Any]):
        """Add evaluation result for a configuration."""
        self.configurations[config_name] = config
        self.results[config_name] = result
    
    def determine_winner(self, metric: str = "f1@5"):
        """Determine the winning configuration based on specified metric."""
        self.winning_metric = metric
        
        best_score = -1.0
        best_config = None
        
        for config_name, result in self.results.items():
            if result.system_metrics and metric in result.system_metrics.overall_metrics:
                score = result.system_metrics.overall_metrics[metric]
                if score > best_score:
                    best_score = score
                    best_config = config_name
        
        self.winning_configuration = best_config
        
        # Calculate improvement over first (baseline) configuration
        if len(self.results) >= 2:
            baseline_name = list(self.results.keys())[0]
            baseline_score = self.results[baseline_name].system_metrics.overall_metrics.get(metric, 0.0)
            if baseline_score > 0:
                self.improvement_percentage = ((best_score - baseline_score) / baseline_score) * 100
    
    def get_comparison_report(self) -> Dict[str, Any]:
        """Generate a detailed comparison report."""
        return {
            "benchmark_id": self.benchmark_id,
            "comparison_name": self.comparison_name,
            "winning_configuration": self.winning_configuration,
            "winning_metric": self.winning_metric,
            "improvement_percentage": self.improvement_percentage,
            "configurations": list(self.configurations.keys()),
            "detailed_results": {
                name: result.get_summary_report() 
                for name, result in self.results.items()
            }
        }
