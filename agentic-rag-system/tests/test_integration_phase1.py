"""
Phase 1 Integration Tests for the Evaluation System.

Tests the integration between the new evaluation framework and 
existing core components like MultiTool and Router.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from typing import Dict, List, Any

# Test imports with fallbacks
try:
    from agentic_rag.evaluation.integration import (
        EvaluationMultiTool, EvaluationRouter, EvaluationSession,
        EvaluationAwareResult, create_evaluation_aware_system,
        validate_integration_compatibility, migrate_legacy_config
    )
    from agentic_rag.evaluation.models import RetrievalMetrics
    EVALUATION_AVAILABLE = True
except ImportError:
    EVALUATION_AVAILABLE = False


# Mock classes for testing
class MockMultiTool:
    """Mock MultiTool for testing integration."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.call_count = 0
    
    async def process_query(self, query: str, **kwargs):
        """Mock query processing."""
        self.call_count += 1
        
        # Simulate different response types based on query
        if "error" in query.lower():
            raise ValueError("Mock processing error")
        
        # Create mock result
        return MockQueryResult(
            response=f"Mock response for: {query}",
            sources=[f"source_{i}" for i in range(3)],
            tools_used=["document_retrieval"],
            confidence=0.85
        )
    
    def get_statistics(self):
        """Mock statistics method."""
        return {"queries_processed": self.call_count}


class MockQueryResult:
    """Mock query result for testing."""
    
    def __init__(self, response: str, sources: List[str], tools_used: List[str], confidence: float):
        self.response = response
        self.sources = sources
        self.tools_used = tools_used
        self.confidence = confidence


class MockRouter:
    """Mock Router for testing integration."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.route_count = 0
    
    async def route_query(self, query: str, **kwargs):
        """Mock query routing."""
        self.route_count += 1
        
        return MockIntent(
            query_type="information_retrieval",
            confidence=0.9,
            suggested_tools=["document_retrieval"]
        )


class MockIntent:
    """Mock routing intent."""
    
    def __init__(self, query_type: str, confidence: float, suggested_tools: List[str]):
        self.query_type = query_type
        self.confidence = confidence
        self.suggested_tools = suggested_tools


@pytest.mark.skipif(not EVALUATION_AVAILABLE, reason="Evaluation system not available")
class TestEvaluationMultiTool:
    """Test EvaluationMultiTool integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.base_tool = MockMultiTool()
        self.eval_config = {
            'track_metrics': True,
            'auto_evaluate': True,
            'buffer_results': True
        }
        self.eval_tool = EvaluationMultiTool(self.base_tool, self.eval_config)
    
    @pytest.mark.asyncio
    async def test_basic_query_processing(self):
        """Test basic query processing maintains compatibility."""
        
        # Process query through evaluation wrapper
        result = await self.eval_tool.process_query("What is machine learning?")
        
        # Verify result structure matches original
        assert hasattr(result, 'response')
        assert hasattr(result, 'sources')
        assert hasattr(result, 'tools_used')
        assert hasattr(result, 'confidence')
        
        # Verify base tool was called
        assert self.base_tool.call_count == 1
    
    @pytest.mark.asyncio
    async def test_evaluation_session_management(self):
        """Test evaluation session lifecycle."""
        
        # Start evaluation session
        session_id = self.eval_tool.start_evaluation_session()
        assert session_id is not None
        assert self.eval_tool.current_session is not None
        
        # Process queries with session active
        await self.eval_tool.process_query("Query 1")
        await self.eval_tool.process_query("Query 2")
        
        # End session and get summary
        summary = self.eval_tool.end_evaluation_session()
        assert summary is not None
        assert summary['query_count'] == 2
        assert summary['session_id'] == session_id
        assert 'average_metrics' in summary
    
    @pytest.mark.asyncio 
    async def test_evaluation_aware_processing(self):
        """Test enhanced evaluation processing with ground truth."""
        
        # Start session
        self.eval_tool.start_evaluation_session()
        
        # Process query with ground truth
        ground_truth = ["source_0", "source_1"]
        result = await self.eval_tool.process_query_with_evaluation(
            "Test query",
            ground_truth=ground_truth
        )
        
        # Verify evaluation-aware result structure
        assert isinstance(result, EvaluationAwareResult)
        assert hasattr(result, 'core_result')
        assert hasattr(result, 'evaluation_metrics')
        assert hasattr(result, 'processing_time_ms')
        assert hasattr(result, 'session_id')
        
        # Verify evaluation metrics
        metrics = result.evaluation_metrics
        assert hasattr(metrics, 'precision_at_k')
        assert hasattr(metrics, 'recall_at_k')
        assert hasattr(metrics, 'f1_at_k')
        assert hasattr(metrics, 'mrr')
        assert hasattr(metrics, 'ndcg_at_k')
        assert hasattr(metrics, 'latency_ms')
    
    @pytest.mark.asyncio
    async def test_metric_calculations(self):
        """Test evaluation metric calculations."""
        
        self.eval_tool.start_evaluation_session()
        
        # Test with perfect relevance
        perfect_ground_truth = ["source_0", "source_1", "source_2"]
        result = await self.eval_tool.process_query_with_evaluation(
            "Perfect match query",
            ground_truth=perfect_ground_truth
        )
        
        # Should have high precision/recall for perfect match
        metrics = result.evaluation_metrics
        assert metrics.precision_at_k[5] == 1.0  # All retrieved are relevant
        assert metrics.recall_at_k[5] == 1.0     # All relevant are retrieved
        assert metrics.f1_at_k[5] == 1.0         # Perfect F1
        assert metrics.mrr == 1.0                # First result is relevant
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in evaluation wrapper."""
        
        self.eval_tool.start_evaluation_session()
        
        # Test that errors are properly propagated
        with pytest.raises(ValueError):
            await self.eval_tool.process_query("error query")
    
    def test_method_delegation(self):
        """Test that unknown methods are delegated to base tool."""
        
        # Access method that exists on base tool but not wrapper
        stats = self.eval_tool.get_statistics()
        assert stats is not None
        assert "queries_processed" in stats


@pytest.mark.skipif(not EVALUATION_AVAILABLE, reason="Evaluation system not available")
class TestEvaluationRouter:
    """Test EvaluationRouter integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.base_router = MockRouter()
        self.eval_config = {'track_routing': True}
        self.eval_router = EvaluationRouter(self.base_router, self.eval_config)
    
    @pytest.mark.asyncio
    async def test_basic_routing(self):
        """Test basic routing functionality."""
        
        # Route query
        intent = await self.eval_router.route_query("What is AI?")
        
        # Verify intent structure
        assert hasattr(intent, 'query_type')
        assert hasattr(intent, 'confidence')
        assert hasattr(intent, 'suggested_tools')
        
        # Verify base router was called
        assert self.base_router.route_count == 1
    
    @pytest.mark.asyncio
    async def test_routing_analytics(self):
        """Test routing decision tracking and analytics."""
        
        # Route multiple queries
        queries = [
            "What is machine learning?",
            "How does deep learning work?",
            "Explain neural networks"
        ]
        
        for query in queries:
            await self.eval_router.route_query(query)
        
        # Get analytics
        analytics = self.eval_router.get_routing_analytics()
        
        # Verify analytics structure
        assert analytics['total_queries'] == 3
        assert 'average_routing_time_ms' in analytics
        assert 'average_confidence' in analytics
        assert 'query_type_distribution' in analytics
        
        # Verify confidence tracking
        assert 0 <= analytics['average_confidence'] <= 1


@pytest.mark.skipif(not EVALUATION_AVAILABLE, reason="Evaluation system not available")
class TestEvaluationSession:
    """Test EvaluationSession functionality."""
    
    def test_session_creation(self):
        """Test evaluation session creation."""
        
        config = {'test': True}
        session = EvaluationSession(
            session_id="test-session",
            config=config,
            start_time=datetime.now(),
            metrics_buffer=[]
        )
        
        assert session.session_id == "test-session"
        assert session.config == config
        assert len(session.metrics_buffer) == 0
    
    def test_metrics_addition(self):
        """Test adding metrics to session."""
        
        session = EvaluationSession(
            session_id="test",
            config={},
            start_time=datetime.now(),
            metrics_buffer=[]
        )
        
        # Add metrics
        metrics = {'precision@5': 0.8, 'recall@5': 0.7}
        session.add_metrics("test query", metrics)
        
        assert len(session.metrics_buffer) == 1
        assert session.metrics_buffer[0]['query'] == "test query"
        assert session.metrics_buffer[0]['metrics'] == metrics
    
    def test_session_summary(self):
        """Test session summary generation."""
        
        session = EvaluationSession(
            session_id="test",
            config={},
            start_time=datetime.now(),
            metrics_buffer=[]
        )
        
        # Add sample metrics
        session.add_metrics("query1", {'precision@5': 0.8, 'latency_ms': 100})
        session.add_metrics("query2", {'precision@5': 0.6, 'latency_ms': 150})
        
        summary = session.get_session_summary()
        
        # Verify summary structure
        assert summary['session_id'] == "test"
        assert summary['query_count'] == 2
        assert 'duration_seconds' in summary
        assert 'average_metrics' in summary
        assert 'queries_per_second' in summary
        
        # Verify average calculations
        assert summary['average_metrics']['precision@5'] == 0.7  # (0.8 + 0.6) / 2
        assert summary['average_metrics']['latency_ms'] == 125   # (100 + 150) / 2


@pytest.mark.skipif(not EVALUATION_AVAILABLE, reason="Evaluation system not available")
class TestSystemIntegration:
    """Test complete system integration."""
    
    def test_create_evaluation_aware_system(self):
        """Test factory function for creating evaluation-aware system."""
        
        base_tool = MockMultiTool()
        base_router = MockRouter()
        config = {'evaluation_enabled': True}
        
        # Create evaluation-aware system
        system = create_evaluation_aware_system(
            base_tool, base_router, config
        )
        
        # Verify system structure
        assert 'multi_tool' in system
        assert 'router' in system
        assert 'config' in system
        
        # Verify component types
        assert isinstance(system['multi_tool'], EvaluationMultiTool)
        assert isinstance(system['router'], EvaluationRouter)
        assert system['config'] == config
    
    def test_compatibility_validation(self):
        """Test component compatibility validation."""
        
        # Test with compatible components
        compatible_tool = MockMultiTool()
        compatible_router = MockRouter()
        
        result = validate_integration_compatibility(compatible_tool, compatible_router)
        
        assert result['compatible'] == True
        assert result['compatibility_score'] >= 0.9
        assert len(result['issues']) == 0
        assert 'recommendations' in result
    
    def test_compatibility_validation_issues(self):
        """Test compatibility validation with problematic components."""
        
        # Create tool missing required methods
        class IncompatibleTool:
            pass
        
        incompatible_tool = IncompatibleTool()
        
        result = validate_integration_compatibility(incompatible_tool)
        
        assert result['compatible'] == False
        assert result['compatibility_score'] < 1.0
        assert len(result['issues']) > 0
        assert any("missing required method" in issue for issue in result['issues'])
    
    def test_legacy_config_migration(self):
        """Test migration of legacy configurations."""
        
        legacy_config = {
            'llm_model': 'gpt-3.5-turbo',
            'retrieval_top_k': 5,
            'temperature': 0.1
        }
        
        migrated_config = migrate_legacy_config(legacy_config)
        
        # Verify original config is preserved
        assert migrated_config['llm_model'] == 'gpt-3.5-turbo'
        assert migrated_config['retrieval_top_k'] == 5
        assert migrated_config['temperature'] == 0.1
        
        # Verify evaluation settings are added
        assert 'evaluation' in migrated_config
        assert migrated_config['evaluation']['track_metrics'] == True
        assert 'metrics_to_track' in migrated_config['evaluation']


@pytest.mark.skipif(not EVALUATION_AVAILABLE, reason="Evaluation system not available")
class TestEndToEndIntegration:
    """Test complete end-to-end integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_evaluation_workflow(self):
        """Test complete workflow from query to evaluation results."""
        
        # Set up components
        base_tool = MockMultiTool()
        base_router = MockRouter()
        
        # Create evaluation-aware system
        system = create_evaluation_aware_system(base_tool, base_router)
        eval_tool = system['multi_tool']
        eval_router = system['router']
        
        # Start evaluation session
        session_id = eval_tool.start_evaluation_session()
        
        # Route and process queries
        queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "Explain deep learning algorithms"
        ]
        
        results = []
        for query in queries:
            # Route query
            intent = await eval_router.route_query(query)
            
            # Process with evaluation
            ground_truth = [f"relevant_doc_{i}" for i in range(2)]
            result = await eval_tool.process_query_with_evaluation(
                query, ground_truth=ground_truth
            )
            results.append(result)
        
        # End session and get summary
        session_summary = eval_tool.end_evaluation_session()
        routing_analytics = eval_router.get_routing_analytics()
        
        # Verify end-to-end results
        assert len(results) == 3
        assert session_summary['query_count'] == 3
        assert routing_analytics['total_queries'] == 3
        
        # Verify all results have evaluation metrics
        for result in results:
            assert isinstance(result, EvaluationAwareResult)
            assert result.session_id == session_id
            assert hasattr(result.evaluation_metrics, 'precision_at_k')
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self):
        """Test performance monitoring during integration."""
        
        base_tool = MockMultiTool()
        eval_tool = EvaluationMultiTool(base_tool)
        
        # Process queries and monitor performance
        eval_tool.start_evaluation_session()
        
        # Process multiple queries
        for i in range(10):
            await eval_tool.process_query(f"Test query {i}")
        
        summary = eval_tool.end_evaluation_session()
        
        # Verify performance metrics are tracked
        assert summary['query_count'] == 10
        assert summary['queries_per_second'] > 0
        assert 'average_metrics' in summary
        
        # Verify latency tracking
        if 'processing_time_ms' in summary['average_metrics']:
            assert summary['average_metrics']['processing_time_ms'] >= 0
    
    @pytest.mark.asyncio
    async def test_error_resilience(self):
        """Test system resilience to errors during integration."""
        
        base_tool = MockMultiTool()
        eval_tool = EvaluationMultiTool(base_tool)
        
        eval_tool.start_evaluation_session()
        
        # Process mix of successful and failing queries
        queries = [
            "successful query 1",
            "error query",  # This should fail
            "successful query 2"
        ]
        
        successful_count = 0
        error_count = 0
        
        for query in queries:
            try:
                await eval_tool.process_query(query)
                successful_count += 1
            except Exception:
                error_count += 1
        
        # Verify partial success
        assert successful_count == 2
        assert error_count == 1
        
        # Verify session still works after errors
        summary = eval_tool.end_evaluation_session()
        assert summary['query_count'] == 2  # Only successful queries tracked


# Mock-based tests when evaluation system is not available
@pytest.mark.skipif(EVALUATION_AVAILABLE, reason="Evaluation system is available")
class TestMockIntegration:
    """Mock tests for when evaluation system is not available."""
    
    def test_mock_integration_concept(self):
        """Test the concept of integration with mocks."""
        
        # Mock the integration concept
        def mock_evaluate_query(query: str, tool) -> dict:
            # Simulate evaluation
            return {
                'query': query,
                'precision@5': 0.8,
                'recall@5': 0.7,
                'processing_time_ms': 150
            }
        
        # Test mock integration
        mock_tool = MockMultiTool()
        result = mock_evaluate_query("test query", mock_tool)
        
        assert result['query'] == "test query"
        assert 'precision@5' in result
        assert 'recall@5' in result
        assert 'processing_time_ms' in result
    
    def test_mock_session_management(self):
        """Test mock session management concept."""
        
        class MockEvaluationSession:
            def __init__(self):
                self.metrics = []
                self.active = False
            
            def start(self):
                self.active = True
                return "mock-session-id"
            
            def add_metrics(self, metrics):
                if self.active:
                    self.metrics.append(metrics)
            
            def end(self):
                self.active = False
                return {
                    'query_count': len(self.metrics),
                    'session_id': 'mock-session-id'
                }
        
        # Test mock session
        session = MockEvaluationSession()
        session_id = session.start()
        
        session.add_metrics({'precision@5': 0.8})
        session.add_metrics({'precision@5': 0.6})
        
        summary = session.end()
        
        assert session_id == "mock-session-id"
        assert summary['query_count'] == 2
