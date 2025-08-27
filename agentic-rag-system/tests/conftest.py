"""
Test configuration and fixtures for the evaluation system tests.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import MagicMock
from datetime import datetime

import pytest
from loguru import logger

# Mock imports for testing
@pytest.fixture(scope="session")
def mock_agentic_rag():
    """Mock the agentic_rag package for testing."""
    
    class MockDocument:
        def __init__(self, doc_id: str, content: str, metadata: Dict = None):
            self.id = doc_id
            self.content = content
            self.metadata = metadata or {}
    
    class MockToolType:
        WEB_SEARCH = "web_search"
        CALCULATOR = "calculator"
        CODE_INTERPRETER = "code_interpreter"
        DOCUMENT_RETRIEVAL = "document_retrieval"
    
    class MockMultiTool:
        def __init__(self):
            self.tools = {}
            self.config = {}
        
        async def search(self, query: str, top_k: int = 5) -> List[MockDocument]:
            # Mock search results
            return [
                MockDocument(f"doc_{i}", f"Content for {query} - {i}", 
                           {"score": 0.9 - i*0.1}) 
                for i in range(top_k)
            ]
        
        async def process_query(self, query: str) -> Dict[str, Any]:
            # Mock query processing
            return {
                "response": f"Mock response for: {query}",
                "sources": ["doc_1", "doc_2"],
                "tools_used": [MockToolType.DOCUMENT_RETRIEVAL],
                "confidence": 0.85,
                "latency_ms": 250
            }
    
    return {
        "Document": MockDocument,
        "ToolType": MockToolType,
        "MultiTool": MockMultiTool
    }


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_queries():
    """Sample queries for testing."""
    return [
        {
            "query": "What are the latest trends in AI?",
            "domain": "technology",
            "expected_tools": ["web_search", "document_retrieval"],
            "ground_truth": ["doc_ai_trends", "doc_tech_news"]
        },
        {
            "query": "Calculate the ROI for this investment",
            "domain": "finance", 
            "expected_tools": ["calculator"],
            "ground_truth": ["doc_roi_formula"]
        },
        {
            "query": "How to implement OAuth2?",
            "domain": "software",
            "expected_tools": ["document_retrieval", "code_interpreter"],
            "ground_truth": ["doc_oauth2_guide", "doc_auth_examples"]
        }
    ]


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "id": "doc_ai_trends",
            "content": "Artificial Intelligence trends include LLMs, computer vision, and robotics...",
            "metadata": {"domain": "technology", "timestamp": "2024-01-01"}
        },
        {
            "id": "doc_tech_news",
            "content": "Latest technology news covers breakthroughs in quantum computing...",
            "metadata": {"domain": "technology", "timestamp": "2024-01-02"}
        },
        {
            "id": "doc_roi_formula",
            "content": "Return on Investment (ROI) = (Gain - Cost) / Cost * 100%",
            "metadata": {"domain": "finance", "timestamp": "2024-01-01"}
        },
        {
            "id": "doc_oauth2_guide",
            "content": "OAuth 2.0 is an authorization framework that enables applications...",
            "metadata": {"domain": "software", "timestamp": "2024-01-01"}
        }
    ]


@pytest.fixture
def sample_evaluation_results():
    """Sample evaluation results for testing."""
    return {
        "evaluation_id": "test_eval_001",
        "query_results": [
            {
                "query": "What are the latest trends in AI?",
                "retrieved_docs": ["doc_ai_trends", "doc_tech_news"],
                "relevant_docs": ["doc_ai_trends", "doc_tech_news"],
                "tools_used": ["document_retrieval"],
                "response_time_ms": 245,
                "confidence": 0.92
            },
            {
                "query": "Calculate ROI",
                "retrieved_docs": ["doc_roi_formula"],
                "relevant_docs": ["doc_roi_formula"],
                "tools_used": ["calculator"],
                "response_time_ms": 180,
                "confidence": 0.88
            }
        ],
        "system_metrics": {
            "overall_metrics": {
                "precision@5": 0.85,
                "recall@5": 0.80,
                "f1@5": 0.825,
                "mrr": 0.75,
                "ndcg@5": 0.82,
                "latency_ms": 212.5
            },
            "per_domain_metrics": {
                "technology": {
                    "precision@5": 0.90,
                    "recall@5": 0.85,
                    "f1@5": 0.875
                },
                "finance": {
                    "precision@5": 0.80,
                    "recall@5": 0.75,
                    "f1@5": 0.775
                }
            }
        }
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    class MockLLMClient:
        async def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
            return {
                "text": f"Generated response for: {prompt[:50]}...",
                "usage": {"tokens": 150},
                "model": "mock-llm-model"
            }
        
        async def embed(self, text: str) -> List[float]:
            # Mock embedding - simple hash-based vector
            return [hash(text[i:i+3]) % 100 / 100.0 for i in range(0, min(len(text), 384), 3)]
    
    return MockLLMClient()


@pytest.fixture
def evaluation_config():
    """Standard evaluation configuration for testing."""
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
        "evaluation_config": {
            "metrics": ["precision@5", "recall@5", "f1@5", "mrr", "ndcg@5"],
            "batch_size": 10,
            "timeout_seconds": 30
        }
    }


@pytest.fixture
def benchmark_config():
    """Benchmark configuration for testing."""
    return {
        "baseline_config": {
            "name": "baseline_v1",
            "retrieval_config": {"top_k": 5, "similarity_threshold": 0.7},
            "llm_config": {"model": "gpt-3.5-turbo", "temperature": 0.1}
        },
        "competitor_configs": [
            {
                "name": "improved_retrieval",
                "retrieval_config": {"top_k": 10, "similarity_threshold": 0.6},
                "llm_config": {"model": "gpt-3.5-turbo", "temperature": 0.1}
            },
            {
                "name": "better_llm",
                "retrieval_config": {"top_k": 5, "similarity_threshold": 0.7},
                "llm_config": {"model": "gpt-4", "temperature": 0.0}
            }
        ],
        "evaluation_queries": 50,
        "primary_metric": "f1@5"
    }


@pytest.fixture
def ab_test_config():
    """A/B test configuration for testing."""
    return {
        "name": "LLM Upgrade Test",
        "description": "Testing GPT-4 vs GPT-3.5 performance",
        "control_config": {
            "llm_config": {"model": "gpt-3.5-turbo", "temperature": 0.1}
        },
        "treatment_config": {
            "llm_config": {"model": "gpt-4", "temperature": 0.0}
        },
        "primary_metric": "f1@5",
        "secondary_metrics": ["precision@5", "recall@5", "mrr"],
        "minimum_detectable_effect": 0.05,
        "statistical_power": 0.8,
        "significance_level": 0.05
    }


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test utilities
def create_mock_query_result(query: str, retrieved_docs: List[str], 
                           relevant_docs: List[str], tools_used: List[str] = None):
    """Create a mock query result for testing."""
    return {
        "query": query,
        "retrieved_docs": retrieved_docs,
        "relevant_docs": relevant_docs,
        "tools_used": tools_used or ["document_retrieval"],
        "response_time_ms": 200,
        "confidence": 0.85
    }


def assert_metrics_valid(metrics: Dict[str, float]):
    """Assert that metrics are valid (between 0 and 1 for most metrics)."""
    for metric_name, value in metrics.items():
        if "latency" in metric_name or "time" in metric_name:
            assert value >= 0, f"{metric_name} should be non-negative"
        else:
            assert 0 <= value <= 1, f"{metric_name} should be between 0 and 1, got {value}"


def assert_evaluation_result_valid(result: Dict[str, Any]):
    """Assert that evaluation result structure is valid."""
    required_fields = ["evaluation_id", "query_results", "system_metrics"]
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
    
    # Check system metrics
    assert "overall_metrics" in result["system_metrics"]
    assert_metrics_valid(result["system_metrics"]["overall_metrics"])
    
    # Check query results structure
    for query_result in result["query_results"]:
        required_query_fields = ["query", "retrieved_docs", "relevant_docs"]
        for field in required_query_fields:
            assert field in query_result, f"Missing query result field: {field}"


# Logger setup for tests
logger.remove()  # Remove default handler
logger.add(
    "test_evaluation.log",
    level="DEBUG",
    format="{time} | {level} | {name}:{function}:{line} | {message}",
    rotation="10 MB"
)
