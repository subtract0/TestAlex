"""
Integration components for connecting the evaluation system with core RAG components.

This module provides seamless integration between the evaluation framework
and existing MultiTool, Router, and Vector Search components.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import uuid

from loguru import logger
from pydantic import BaseModel

from .models import RetrievalMetrics, SystemMetrics
from .pipeline import EvaluationPipeline
from ..core.models import AgentResponse as CoreQueryResult, ToolType


@dataclass
class EvaluationSession:
    """Manages evaluation context and session state."""
    session_id: str
    config: Dict[str, Any]
    start_time: datetime
    metrics_buffer: List[Dict[str, Any]]
    
    def __post_init__(self):
        if not hasattr(self, 'session_id') or not self.session_id:
            self.session_id = str(uuid.uuid4())
        if not hasattr(self, 'start_time') or not self.start_time:
            self.start_time = datetime.now()
        if not hasattr(self, 'metrics_buffer'):
            self.metrics_buffer = []
    
    def add_metrics(self, query: str, metrics: Dict[str, Any]):
        """Add metrics to the session buffer."""
        self.metrics_buffer.append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'metrics': metrics
        })
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of the evaluation session."""
        if not self.metrics_buffer:
            return {
                'session_id': self.session_id,
                'query_count': 0,
                'duration_seconds': 0,
                'average_metrics': {}
            }
        
        # Calculate averages
        metric_names = set()
        for entry in self.metrics_buffer:
            metric_names.update(entry['metrics'].keys())
        
        average_metrics = {}
        for metric in metric_names:
            values = [entry['metrics'].get(metric, 0) for entry in self.metrics_buffer if metric in entry['metrics']]
            if values:
                average_metrics[metric] = sum(values) / len(values)
        
        duration = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'session_id': self.session_id,
            'query_count': len(self.metrics_buffer),
            'duration_seconds': duration,
            'average_metrics': average_metrics,
            'queries_per_second': len(self.metrics_buffer) / max(duration, 1)
        }


@dataclass
class EvaluationAwareResult:
    """Result wrapper that includes evaluation metrics alongside core results."""
    core_result: CoreQueryResult
    evaluation_metrics: RetrievalMetrics
    processing_time_ms: float
    session_id: str
    query_metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'core_result': asdict(self.core_result),
            'evaluation_metrics': asdict(self.evaluation_metrics),
            'processing_time_ms': self.processing_time_ms,
            'session_id': self.session_id,
            'query_metadata': self.query_metadata or {}
        }


class EvaluationMultiTool:
    """
    Wrapper around existing MultiTool that adds evaluation capabilities.
    
    This class extends any MultiTool with automatic evaluation tracking,
    metrics collection, and performance monitoring without changing the
    core interface.
    """
    
    def __init__(self, base_multi_tool, evaluation_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the evaluation-aware MultiTool.
        
        Args:
            base_multi_tool: The original MultiTool instance to wrap
            evaluation_config: Configuration for evaluation behavior
        """
        self.base_tool = base_multi_tool
        self.config = evaluation_config or {}
        self.current_session: Optional[EvaluationSession] = None
        
        # Evaluation settings
        self.track_metrics = self.config.get('track_metrics', True)
        self.auto_evaluate = self.config.get('auto_evaluate', True)
        self.buffer_results = self.config.get('buffer_results', True)
        
        logger.info("EvaluationMultiTool initialized with automatic evaluation tracking")
    
    def start_evaluation_session(self, session_config: Optional[Dict[str, Any]] = None) -> str:
        """Start a new evaluation session."""
        config = {**self.config, **(session_config or {})}
        self.current_session = EvaluationSession(
            session_id=str(uuid.uuid4()),
            config=config,
            start_time=datetime.now(),
            metrics_buffer=[]
        )
        logger.info(f"Started evaluation session: {self.current_session.session_id}")
        return self.current_session.session_id
    
    def end_evaluation_session(self) -> Optional[Dict[str, Any]]:
        """End the current evaluation session and return summary."""
        if not self.current_session:
            return None
        
        summary = self.current_session.get_session_summary()
        logger.info(f"Ended evaluation session {self.current_session.session_id}: "
                   f"{summary['query_count']} queries processed")
        
        self.current_session = None
        return summary
    
    async def process_query(self, query: str, **kwargs) -> CoreQueryResult:
        """
        Process query with the base MultiTool (maintains compatibility).
        
        This method preserves the original interface while optionally
        collecting evaluation metrics in the background.
        """
        start_time = time.time()
        
        try:
            # Process with the base tool
            result = await self.base_tool.process_query(query, **kwargs)
            
            # Optionally collect metrics if evaluation is enabled
            if self.track_metrics and self.current_session:
                processing_time = (time.time() - start_time) * 1000  # Convert to ms
                
                # Create basic metrics (would be enhanced with actual relevance scoring)
                basic_metrics = {
                    'processing_time_ms': processing_time,
                    'tools_used': result.tools_used if hasattr(result, 'tools_used') else [],
                    'confidence': result.confidence if hasattr(result, 'confidence') else 0.0,
                    'source_count': len(result.sources) if hasattr(result, 'sources') else 0
                }
                
                self.current_session.add_metrics(query, basic_metrics)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query in EvaluationMultiTool: {e}")
            raise
    
    async def process_query_with_evaluation(self, query: str, 
                                          ground_truth: Optional[List[str]] = None,
                                          **kwargs) -> EvaluationAwareResult:
        """
        Process query with comprehensive evaluation metrics.
        
        This method provides enhanced evaluation capabilities including
        relevance scoring when ground truth is available.
        """
        start_time = time.time()
        
        # Ensure we have an active session
        if not self.current_session:
            self.start_evaluation_session()
        
        try:
            # Process with base tool
            core_result = await self.base_tool.process_query(query, **kwargs)
            processing_time = (time.time() - start_time) * 1000
            
            # Calculate evaluation metrics
            evaluation_metrics = self._calculate_evaluation_metrics(
                query, core_result, ground_truth, processing_time
            )
            
            # Create evaluation-aware result
            result = EvaluationAwareResult(
                core_result=core_result,
                evaluation_metrics=evaluation_metrics,
                processing_time_ms=processing_time,
                session_id=self.current_session.session_id,
                query_metadata={'ground_truth': ground_truth}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in process_query_with_evaluation: {e}")
            raise
    
    def _calculate_evaluation_metrics(self, query: str, result: CoreQueryResult,
                                    ground_truth: Optional[List[str]],
                                    processing_time: float) -> RetrievalMetrics:
        """Calculate evaluation metrics for a query result."""
        
        # Extract retrieved documents (implementation depends on result structure)
        retrieved_docs = []
        if hasattr(result, 'sources') and result.sources:
            retrieved_docs = [source.id if hasattr(source, 'id') else str(source) 
                            for source in result.sources]
        elif hasattr(result, 'citations') and result.citations:
            retrieved_docs = [citation.source_id for citation in result.citations]
        
        # Calculate metrics if we have ground truth
        if ground_truth:
            precision_at_k = self._calculate_precision_at_k(retrieved_docs, ground_truth, k=5)
            recall_at_k = self._calculate_recall_at_k(retrieved_docs, ground_truth, k=5)
            f1_at_k = self._calculate_f1_at_k(precision_at_k, recall_at_k)
            mrr = self._calculate_mrr(retrieved_docs, ground_truth)
            ndcg_at_k = self._calculate_ndcg_at_k(retrieved_docs, ground_truth, k=5)
        else:
            # Default values when no ground truth is available
            precision_at_k = recall_at_k = f1_at_k = mrr = ndcg_at_k = 0.0
        
        return RetrievalMetrics(
            query=query,
            precision_at_k={5: precision_at_k},
            recall_at_k={5: recall_at_k},
            f1_at_k={5: f1_at_k},
            mean_reciprocal_rank=mrr,
            ndcg_at_k={5: ndcg_at_k}
        )
    
    def _calculate_precision_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        """Calculate Precision@K."""
        if not retrieved:
            return 0.0
        
        retrieved_at_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc in retrieved_at_k if doc in relevant)
        return relevant_retrieved / len(retrieved_at_k)
    
    def _calculate_recall_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        """Calculate Recall@K."""
        if not relevant:
            return 0.0
        
        retrieved_at_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc in retrieved_at_k if doc in relevant)
        return relevant_retrieved / len(relevant)
    
    def _calculate_f1_at_k(self, precision: float, recall: float) -> float:
        """Calculate F1@K from precision and recall."""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    def _calculate_mrr(self, retrieved: List[str], relevant: List[str]) -> float:
        """Calculate Mean Reciprocal Rank."""
        for i, doc in enumerate(retrieved):
            if doc in relevant:
                return 1.0 / (i + 1)
        return 0.0
    
    def _calculate_ndcg_at_k(self, retrieved: List[str], relevant: List[str], k: int) -> float:
        """Calculate NDCG@K (simplified binary relevance version)."""
        if not relevant:
            return 0.0
        
        import math
        
        retrieved_at_k = retrieved[:k]
        
        # DCG calculation
        dcg = 0.0
        for i, doc in enumerate(retrieved_at_k):
            if doc in relevant:
                dcg += 1.0 / math.log2(i + 2)
        
        # IDCG calculation (ideal ranking)
        idcg = 0.0
        for i in range(min(len(relevant), k)):
            idcg += 1.0 / math.log2(i + 2)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    # Preserve all original MultiTool methods through delegation
    def __getattr__(self, name):
        """Delegate unknown methods to the base MultiTool."""
        return getattr(self.base_tool, name)


class EvaluationRouter:
    """
    Enhanced router that tracks routing decisions for evaluation.
    
    This wrapper adds evaluation tracking to the existing AdvancedQueryRouter
    without changing its interface.
    """
    
    def __init__(self, base_router, evaluation_config: Optional[Dict[str, Any]] = None):
        """Initialize evaluation-aware router."""
        self.base_router = base_router
        self.config = evaluation_config or {}
        self.routing_history: List[Dict[str, Any]] = []
        self.routing_analytics = {}  # Will be populated by get_routing_analytics()
        
        logger.info("EvaluationRouter initialized with routing decision tracking")
    
    async def route_query(self, query: str, **kwargs):
        """Route query with decision tracking."""
        start_time = time.time()
        
        try:
            # Route with base router
            intent = await self.base_router.route_query(query, **kwargs)
            
            # Track routing decision
            routing_time = (time.time() - start_time) * 1000
            self.routing_history.append({
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'intent': intent,
                'routing_time_ms': routing_time,
                'confidence': intent.confidence if hasattr(intent, 'confidence') else 0.0
            })
            
            return intent
            
        except Exception as e:
            logger.error(f"Error in EvaluationRouter.route_query: {e}")
            raise
    
    def get_routing_analytics(self) -> Dict[str, Any]:
        """Get analytics on routing decisions."""
        if not self.routing_history:
            return {'total_queries': 0, 'average_routing_time_ms': 0}
        
        total_time = sum(entry['routing_time_ms'] for entry in self.routing_history)
        avg_confidence = sum(entry['confidence'] for entry in self.routing_history) / len(self.routing_history)
        
        # Count query types
        query_types = {}
        for entry in self.routing_history:
            query_type = entry['intent'].query_type if hasattr(entry['intent'], 'query_type') else 'unknown'
            query_types[query_type] = query_types.get(query_type, 0) + 1
        
        return {
            'total_queries': len(self.routing_history),
            'average_routing_time_ms': total_time / len(self.routing_history),
            'average_confidence': avg_confidence,
            'query_type_distribution': query_types
        }
    
    # Delegate all other methods to base router
    def __getattr__(self, name):
        """Delegate unknown methods to the base router."""
        return getattr(self.base_router, name)


def create_evaluation_aware_system(multi_tool, router=None, evaluation_config: Optional[Dict[str, Any]] = None):
    """
    Factory function to create an evaluation-aware RAG system.
    
    Args:
        multi_tool: Base MultiTool instance
        router: Optional base router instance
        evaluation_config: Configuration for evaluation features
    
    Returns:
        Dictionary containing evaluation-enhanced components
    """
    eval_config = evaluation_config or {}
    
    # Create evaluation-aware components
    eval_multi_tool = EvaluationMultiTool(multi_tool, eval_config)
    
    eval_router = None
    if router:
        eval_router = EvaluationRouter(router, eval_config)
    
    logger.info("Created evaluation-aware RAG system")
    
    return {
        'multi_tool': eval_multi_tool,
        'router': eval_router,
        'config': eval_config
    }


# Utility functions for integration

def migrate_legacy_config(legacy_config: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate legacy configuration to evaluation-aware format."""
    
    # Start with the legacy config
    new_config = legacy_config.copy()
    
    # Add evaluation-specific settings
    evaluation_settings = {
        'track_metrics': True,
        'auto_evaluate': False,  # Conservative default
        'buffer_results': True,
        'metrics_to_track': ['precision@5', 'recall@5', 'f1@5', 'mrr', 'latency_ms']
    }
    
    new_config['evaluation'] = evaluation_settings
    
    logger.info("Migrated legacy configuration to evaluation-aware format")
    return new_config


def validate_integration_compatibility(multi_tool, router=None) -> Dict[str, Any]:
    """
    Validate that components are compatible with evaluation integration.
    
    Returns:
        Dictionary with validation results and any issues found
    """
    issues = []
    compatibility_score = 1.0
    
    # Check MultiTool compatibility
    required_methods = ['process_query']
    for method in required_methods:
        if not hasattr(multi_tool, method):
            issues.append(f"MultiTool missing required method: {method}")
            compatibility_score -= 0.3
    
    # Check if MultiTool is async
    if hasattr(multi_tool, 'process_query'):
        import inspect
        if not inspect.iscoroutinefunction(multi_tool.process_query):
            issues.append("MultiTool.process_query is not async - wrapping may be needed")
            compatibility_score -= 0.1
    
    # Check router compatibility if provided
    if router:
        if not hasattr(router, 'route_query'):
            issues.append("Router missing required method: route_query")
            compatibility_score -= 0.3
    
    return {
        'compatible': len(issues) == 0,
        'compatibility_score': max(0.0, compatibility_score),
        'issues': issues,
        'recommendations': [
            "Use EvaluationMultiTool wrapper for seamless integration",
            "Enable evaluation tracking gradually in production",
            "Monitor performance impact during initial deployment"
        ]
    }
