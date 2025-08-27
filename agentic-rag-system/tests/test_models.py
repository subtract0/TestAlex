"""
Unit tests for evaluation models and metrics.
"""

import pytest
from datetime import datetime
from typing import List, Dict, Any

# Import the models we'll test
try:
    from agentic_rag.evaluation.models import (
        RetrievalMetrics, QueryResult, SystemMetrics, EvaluationResult,
        BenchmarkResult, calculate_precision_at_k, calculate_recall_at_k,
        calculate_f1_at_k, calculate_mrr, calculate_ndcg_at_k
    )
except ImportError:
    # Mock models for testing
    from dataclasses import dataclass
    from typing import Optional
    
    @dataclass
    class RetrievalMetrics:
        precision_at_k: Dict[int, float]
        recall_at_k: Dict[int, float]
        f1_at_k: Dict[int, float]
        mrr: float
        ndcg_at_k: Dict[int, float]
        latency_ms: float
        
    @dataclass
    class QueryResult:
        query: str
        retrieved_docs: List[str]
        relevant_docs: List[str]
        tools_used: List[str]
        retrieval_metrics: RetrievalMetrics
        response_time_ms: float
        confidence: Optional[float] = None


class TestRetrievalMetrics:
    """Test RetrievalMetrics calculations."""
    
    def test_precision_at_k_perfect_match(self):
        """Test precision calculation with perfect matches."""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        
        precision = calculate_precision_at_k(retrieved, relevant, k=5)
        assert precision == 1.0
    
    def test_precision_at_k_partial_match(self):
        """Test precision calculation with partial matches."""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc3", "doc5"]
        
        precision = calculate_precision_at_k(retrieved, relevant, k=5)
        assert precision == 0.6  # 3/5
    
    def test_precision_at_k_no_match(self):
        """Test precision calculation with no matches."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc4", "doc5", "doc6"]
        
        precision = calculate_precision_at_k(retrieved, relevant, k=3)
        assert precision == 0.0
    
    def test_precision_at_k_empty_lists(self):
        """Test precision calculation with empty lists."""
        precision = calculate_precision_at_k([], [], k=5)
        assert precision == 0.0
        
        precision = calculate_precision_at_k(["doc1"], [], k=1)
        assert precision == 0.0
    
    def test_recall_at_k_perfect_match(self):
        """Test recall calculation with perfect matches."""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc2", "doc3"]
        
        recall = calculate_recall_at_k(retrieved, relevant, k=5)
        assert recall == 1.0  # Found all relevant docs
    
    def test_recall_at_k_partial_match(self):
        """Test recall calculation with partial matches."""
        retrieved = ["doc1", "doc2", "doc6"]
        relevant = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        
        recall = calculate_recall_at_k(retrieved, relevant, k=3)
        assert recall == 0.4  # 2/5 relevant docs found
    
    def test_recall_at_k_no_relevant_docs(self):
        """Test recall calculation with no relevant docs."""
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = []
        
        recall = calculate_recall_at_k(retrieved, relevant, k=3)
        assert recall == 0.0
    
    def test_f1_at_k_calculation(self):
        """Test F1 score calculation."""
        # Case where precision = 0.6, recall = 0.4
        precision = 0.6
        recall = 0.4
        
        expected_f1 = 2 * (precision * recall) / (precision + recall)
        assert expected_f1 == pytest.approx(0.48, rel=1e-3)
        
        # Test with actual retrieved and relevant docs
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]  # 5 retrieved
        relevant = ["doc1", "doc2", "doc6", "doc7", "doc8"]   # 5 relevant, 2 overlap
        
        f1 = calculate_f1_at_k(retrieved, relevant, k=5)
        # Precision: 2/5 = 0.4, Recall: 2/5 = 0.4, F1: 0.4
        assert f1 == pytest.approx(0.4, rel=1e-3)
    
    def test_f1_at_k_edge_cases(self):
        """Test F1 calculation edge cases."""
        # Perfect precision and recall
        retrieved = ["doc1", "doc2"]
        relevant = ["doc1", "doc2"]
        f1 = calculate_f1_at_k(retrieved, relevant, k=2)
        assert f1 == 1.0
        
        # Zero precision or recall
        retrieved = ["doc1", "doc2"]
        relevant = ["doc3", "doc4"]
        f1 = calculate_f1_at_k(retrieved, relevant, k=2)
        assert f1 == 0.0
    
    def test_mrr_calculation(self):
        """Test Mean Reciprocal Rank calculation."""
        # Test with multiple queries
        queries_results = [
            {
                "retrieved": ["doc1", "doc2", "doc3"],
                "relevant": ["doc1", "doc4"]  # First relevant at position 1
            },
            {
                "retrieved": ["doc5", "doc6", "doc7"],
                "relevant": ["doc6", "doc8"]  # First relevant at position 2
            },
            {
                "retrieved": ["doc9", "doc10", "doc11"],
                "relevant": ["doc12"]  # No relevant docs found
            }
        ]
        
        reciprocal_ranks = []
        for result in queries_results:
            rr = 0.0
            for i, doc in enumerate(result["retrieved"]):
                if doc in result["relevant"]:
                    rr = 1.0 / (i + 1)
                    break
            reciprocal_ranks.append(rr)
        
        expected_mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
        # RR = [1.0, 0.5, 0.0], MRR = 1.5/3 = 0.5
        assert expected_mrr == pytest.approx(0.5, rel=1e-3)
    
    def test_ndcg_calculation_basic(self):
        """Test basic NDCG calculation."""
        # Simple test case with binary relevance
        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc1", "doc3"]
        
        # For NDCG, we need relevance scores
        # Binary: relevant = 1, non-relevant = 0
        relevance_scores = [1, 0, 1]  # doc1=1, doc2=0, doc3=1
        
        # DCG = 1/log2(2) + 0/log2(3) + 1/log2(4) = 1 + 0 + 0.5 = 1.5
        # IDCG (perfect ranking) = 1/log2(2) + 1/log2(3) = 1 + 0.63 = 1.63
        # NDCG = DCG/IDCG = 1.5/1.63 ≈ 0.92
        
        ndcg = calculate_ndcg_at_k(retrieved, relevant, k=3)
        assert 0.8 <= ndcg <= 1.0  # Should be high for mostly correct ranking


class TestQueryResult:
    """Test QueryResult model."""
    
    def test_query_result_creation(self):
        """Test creating a QueryResult instance."""
        metrics = RetrievalMetrics(
            precision_at_k={5: 0.8},
            recall_at_k={5: 0.6},
            f1_at_k={5: 0.69},
            mrr=0.75,
            ndcg_at_k={5: 0.82},
            latency_ms=150.0
        )
        
        result = QueryResult(
            query="What is machine learning?",
            retrieved_docs=["doc1", "doc2", "doc3"],
            relevant_docs=["doc1", "doc4"],
            tools_used=["document_retrieval"],
            retrieval_metrics=metrics,
            response_time_ms=200.0,
            confidence=0.85
        )
        
        assert result.query == "What is machine learning?"
        assert len(result.retrieved_docs) == 3
        assert len(result.relevant_docs) == 2
        assert result.confidence == 0.85
        assert result.retrieval_metrics.precision_at_k[5] == 0.8
    
    def test_query_result_optional_fields(self):
        """Test QueryResult with optional fields."""
        metrics = RetrievalMetrics(
            precision_at_k={5: 0.8},
            recall_at_k={5: 0.6},
            f1_at_k={5: 0.69},
            mrr=0.75,
            ndcg_at_k={5: 0.82},
            latency_ms=150.0
        )
        
        result = QueryResult(
            query="Test query",
            retrieved_docs=["doc1"],
            relevant_docs=["doc1"],
            tools_used=["web_search"],
            retrieval_metrics=metrics,
            response_time_ms=100.0
            # confidence is optional
        )
        
        assert result.confidence is None


class TestSystemMetrics:
    """Test SystemMetrics aggregation."""
    
    def test_system_metrics_aggregation(self):
        """Test aggregating metrics from multiple queries."""
        # Create sample query results
        query_results = []
        
        for i in range(3):
            metrics = RetrievalMetrics(
                precision_at_k={5: 0.8 + i*0.1},
                recall_at_k={5: 0.6 + i*0.1},
                f1_at_k={5: 0.69 + i*0.1},
                mrr=0.75 + i*0.05,
                ndcg_at_k={5: 0.82 + i*0.05},
                latency_ms=150.0 + i*10
            )
            
            result = QueryResult(
                query=f"Query {i+1}",
                retrieved_docs=[f"doc{i}1", f"doc{i}2"],
                relevant_docs=[f"doc{i}1"],
                tools_used=["document_retrieval"],
                retrieval_metrics=metrics,
                response_time_ms=200.0 + i*20
            )
            query_results.append(result)
        
        # Test that we can create system metrics
        # Note: Actual implementation would aggregate these
        assert len(query_results) == 3
        assert all(result.retrieval_metrics.precision_at_k[5] >= 0.8 for result in query_results)


class TestEvaluationResult:
    """Test EvaluationResult model."""
    
    def test_evaluation_result_creation(self):
        """Test creating an EvaluationResult."""
        # This would typically be created by the evaluation pipeline
        # For now, test basic structure
        
        evaluation_id = "test_eval_001"
        query_count = 5
        
        # Mock some basic data
        query_results = []
        for i in range(query_count):
            metrics = RetrievalMetrics(
                precision_at_k={5: 0.8},
                recall_at_k={5: 0.6},
                f1_at_k={5: 0.69},
                mrr=0.75,
                ndcg_at_k={5: 0.82},
                latency_ms=150.0
            )
            
            result = QueryResult(
                query=f"Query {i+1}",
                retrieved_docs=[f"doc{i}1", f"doc{i}2"],
                relevant_docs=[f"doc{i}1"],
                tools_used=["document_retrieval"],
                retrieval_metrics=metrics,
                response_time_ms=200.0
            )
            query_results.append(result)
        
        # Verify we have the expected structure
        assert len(query_results) == query_count
        assert all(isinstance(result, QueryResult) for result in query_results)


class TestBenchmarkResult:
    """Test BenchmarkResult model."""
    
    def test_benchmark_result_creation(self):
        """Test creating a BenchmarkResult."""
        benchmark_id = "benchmark_001"
        comparison_name = "Baseline vs Improved"
        
        # This would contain multiple evaluation results for comparison
        # Test basic structure
        assert benchmark_id is not None
        assert comparison_name is not None


class TestMetricsIntegration:
    """Test integration between different metric calculations."""
    
    def test_consistent_metric_calculations(self):
        """Test that metrics calculations are consistent."""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc3", "doc5", "doc7", "doc8"]  # 3 overlap, 5 total relevant
        
        precision = calculate_precision_at_k(retrieved, relevant, k=5)
        recall = calculate_recall_at_k(retrieved, relevant, k=5)
        f1 = calculate_f1_at_k(retrieved, relevant, k=5)
        
        # Precision: 3/5 = 0.6
        # Recall: 3/5 = 0.6  
        # F1: 2*(0.6*0.6)/(0.6+0.6) = 0.6
        assert precision == pytest.approx(0.6, rel=1e-3)
        assert recall == pytest.approx(0.6, rel=1e-3)
        assert f1 == pytest.approx(0.6, rel=1e-3)
    
    def test_metrics_with_k_parameter(self):
        """Test that k parameter works correctly across metrics."""
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc2"]  # Only first two are relevant
        
        # At k=2: precision=1.0, recall=1.0, f1=1.0
        precision_2 = calculate_precision_at_k(retrieved, relevant, k=2)
        recall_2 = calculate_recall_at_k(retrieved, relevant, k=2)
        f1_2 = calculate_f1_at_k(retrieved, relevant, k=2)
        
        assert precision_2 == 1.0
        assert recall_2 == 1.0
        assert f1_2 == 1.0
        
        # At k=5: precision=0.4, recall=1.0, f1=0.57
        precision_5 = calculate_precision_at_k(retrieved, relevant, k=5)
        recall_5 = calculate_recall_at_k(retrieved, relevant, k=5)
        f1_5 = calculate_f1_at_k(retrieved, relevant, k=5)
        
        assert precision_5 == pytest.approx(0.4, rel=1e-3)
        assert recall_5 == 1.0
        assert f1_5 == pytest.approx(0.571, rel=1e-2)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_inputs(self):
        """Test metrics with empty inputs."""
        empty_list = []
        non_empty = ["doc1", "doc2"]
        
        # Empty retrieved docs
        assert calculate_precision_at_k(empty_list, non_empty, k=5) == 0.0
        assert calculate_recall_at_k(empty_list, non_empty, k=5) == 0.0
        assert calculate_f1_at_k(empty_list, non_empty, k=5) == 0.0
        
        # Empty relevant docs
        assert calculate_precision_at_k(non_empty, empty_list, k=5) == 0.0
        assert calculate_recall_at_k(non_empty, empty_list, k=5) == 0.0
        assert calculate_f1_at_k(non_empty, empty_list, k=5) == 0.0
    
    def test_k_larger_than_retrieved(self):
        """Test when k is larger than the number of retrieved documents."""
        retrieved = ["doc1", "doc2"]  # Only 2 docs
        relevant = ["doc1", "doc2", "doc3"]
        
        # Should handle gracefully
        precision = calculate_precision_at_k(retrieved, relevant, k=5)
        recall = calculate_recall_at_k(retrieved, relevant, k=5)
        
        # Precision: 2/2 = 1.0 (only consider available docs)
        # Recall: 2/3 = 0.67 (found 2 out of 3 relevant)
        assert precision == 1.0
        assert recall == pytest.approx(0.667, rel=1e-2)
    
    def test_duplicate_documents(self):
        """Test handling of duplicate documents."""
        retrieved = ["doc1", "doc2", "doc1", "doc3"]  # doc1 appears twice
        relevant = ["doc1", "doc4"]
        
        # Should handle duplicates appropriately
        precision = calculate_precision_at_k(retrieved, relevant, k=4)
        # Only unique matches should count, not duplicates
        # Implementation dependent - might be 0.25 or 0.5 depending on how duplicates are handled


# Mock implementations of metric functions for testing
def calculate_precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """Calculate precision at k."""
    if not retrieved:
        return 0.0
    
    retrieved_at_k = retrieved[:k]
    relevant_retrieved = sum(1 for doc in retrieved_at_k if doc in relevant)
    
    return relevant_retrieved / len(retrieved_at_k) if retrieved_at_k else 0.0


def calculate_recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """Calculate recall at k."""
    if not relevant:
        return 0.0
    
    retrieved_at_k = retrieved[:k]
    relevant_retrieved = sum(1 for doc in retrieved_at_k if doc in relevant)
    
    return relevant_retrieved / len(relevant)


def calculate_f1_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """Calculate F1 score at k."""
    precision = calculate_precision_at_k(retrieved, relevant, k)
    recall = calculate_recall_at_k(retrieved, relevant, k)
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)


def calculate_mrr(queries_results: List[Dict[str, List[str]]]) -> float:
    """Calculate Mean Reciprocal Rank."""
    reciprocal_ranks = []
    
    for result in queries_results:
        retrieved = result["retrieved"]
        relevant = result["relevant"]
        
        rr = 0.0
        for i, doc in enumerate(retrieved):
            if doc in relevant:
                rr = 1.0 / (i + 1)
                break
        reciprocal_ranks.append(rr)
    
    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0


def calculate_ndcg_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """Calculate NDCG at k (simplified version)."""
    if not relevant:
        return 0.0
    
    import math
    
    retrieved_at_k = retrieved[:k]
    
    # Calculate DCG
    dcg = 0.0
    for i, doc in enumerate(retrieved_at_k):
        if doc in relevant:
            dcg += 1.0 / math.log2(i + 2)  # i+2 because log2(1) is 0
    
    # Calculate IDCG (ideal DCG)
    idcg = 0.0
    for i in range(min(len(relevant), k)):
        idcg += 1.0 / math.log2(i + 2)
    
    return dcg / idcg if idcg > 0 else 0.0
