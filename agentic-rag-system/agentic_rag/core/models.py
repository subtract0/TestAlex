"""Core Pydantic models for the agentic RAG system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class QueryType(str, Enum):
    """Types of queries the system can handle."""
    
    SEARCH = "search"  # General semantic search
    CODE_LOOKUP = "code_lookup"  # Exact code/function search  
    DOCUMENT_RETRIEVAL = "document_retrieval"  # Document-specific search
    COMPARISON = "comparison"  # Compare/contrast queries
    SUMMARIZATION = "summarization"  # Summarize content
    STRUCTURED_QUERY = "structured_query"  # SQL-like queries
    MULTI_HOP = "multi_hop"  # Complex multi-step queries


class ToolType(str, Enum):
    """Available tools for retrieval."""
    
    VECTOR_SEARCH = "vector_search"
    GREP_SEARCH = "grep_search" 
    SQL_QUERY = "sql_query"
    DOCUMENT_PARSER = "document_parser"
    WEB_SEARCH = "web_search"
    RERANKER = "reranker"


class ConfidenceLevel(str, Enum):
    """Confidence levels for predictions."""
    
    HIGH = "high"  # > 0.8
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"  # < 0.5


# Query Processing Models

class QueryIntent(BaseModel):
    """Structured representation of query understanding."""
    
    query: str = Field(..., description="Original user query")
    query_type: QueryType = Field(..., description="Classified query type")
    
    # Chain of thought reasoning (instructor pattern)
    chain_of_thought: str = Field(
        ..., 
        description="Step-by-step reasoning for classification"
    )
    
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score for classification"
    )
    
    confidence_level: ConfidenceLevel = Field(..., description="Confidence category")
    
    # Extracted entities and parameters
    entities: List[str] = Field(default_factory=list, description="Named entities")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Query filters")
    
    # Suggested tools to use
    suggested_tools: List[ToolType] = Field(
        ..., 
        description="Recommended tools for this query type"
    )
    
    @field_validator("confidence_level", mode="before")
    @classmethod
    def set_confidence_level(cls, v, info):
        """Automatically set confidence level based on score."""
        if "confidence" in info.data:
            score = info.data["confidence"]
            if score > 0.8:
                return ConfidenceLevel.HIGH
            elif score > 0.5:
                return ConfidenceLevel.MEDIUM
            else:
                return ConfidenceLevel.LOW
        return v


class Citation(BaseModel):
    """Source citation with structured metadata."""
    
    source_id: str = Field(..., description="Unique identifier for source")
    title: Optional[str] = Field(None, description="Document/chunk title")
    url: Optional[str] = Field(None, description="Source URL if available")
    page: Optional[int] = Field(None, description="Page number for documents")
    chunk_id: Optional[str] = Field(None, description="Specific chunk identifier")
    relevance_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Relevance to query"
    )
    snippet: str = Field(..., description="Relevant excerpt from source")


class RetrievalResult(BaseModel):
    """Structured result from any retrieval tool."""
    
    tool_used: ToolType = Field(..., description="Tool that generated this result")
    query: str = Field(..., description="Query that was executed")
    
    # Results
    content: str = Field(..., description="Retrieved content")
    citations: List[Citation] = Field(
        default_factory=list, 
        description="Source citations"
    )
    
    # Metadata
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence in result quality"
    )
    
    latency_ms: float = Field(..., description="Time taken for retrieval")
    token_count: int = Field(default=0, description="Approximate token count")
    
    # Tool-specific metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Tool-specific metadata"
    )


class ToolCall(BaseModel):
    """Structured representation of a tool execution."""
    
    call_id: UUID = Field(default_factory=uuid4, description="Unique call ID")
    tool_type: ToolType = Field(..., description="Type of tool called")
    
    # Input parameters
    function_name: str = Field(..., description="Function/method called")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Parameters passed to tool"
    )
    
    # Execution results
    success: bool = Field(..., description="Whether call succeeded")
    result: Optional[RetrievalResult] = Field(
        None, 
        description="Structured result if successful"
    )
    error_message: Optional[str] = Field(
        None, 
        description="Error message if failed"
    )
    
    # Timing and metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    latency_ms: float = Field(..., description="Execution time")
    retries: int = Field(default=0, description="Number of retries attempted")


# Agent Response Models

class AgentResponse(BaseModel):
    """Complete structured response from the RAG agent."""
    
    query: str = Field(..., description="Original user query")
    query_intent: QueryIntent = Field(..., description="Parsed query intent")
    
    # Response content
    answer: str = Field(..., description="Generated answer")
    
    # Chain of reasoning (for transparency)
    reasoning_steps: List[str] = Field(
        default_factory=list,
        description="Step-by-step reasoning process"
    )
    
    # Tool execution history
    tool_calls: List[ToolCall] = Field(
        default_factory=list,
        description="All tools executed for this query"
    )
    
    # Source attribution
    citations: List[Citation] = Field(
        default_factory=list,
        description="All sources used in response"
    )
    
    # Quality metrics
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Overall response confidence"
    )
    
    completeness_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="How complete the answer is"
    )
    
    # Metadata
    total_latency_ms: float = Field(..., description="Total response time")
    cost_estimate: Optional[float] = Field(
        None, 
        description="Estimated cost in USD"
    )
    
    session_id: UUID = Field(default_factory=uuid4, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.now)


# Evaluation Models

class EvaluationMetric(BaseModel):
    """Structured evaluation results."""
    
    metric_name: str = Field(..., description="Name of the metric")
    value: float = Field(..., description="Metric value")
    
    # Context
    query_type: Optional[QueryType] = Field(
        None, 
        description="Query type this metric applies to"
    )
    tool_type: Optional[ToolType] = Field(
        None, 
        description="Tool type this metric applies to"
    )
    
    # Metadata
    sample_size: int = Field(..., description="Number of samples evaluated")
    confidence_interval: Optional[tuple[float, float]] = Field(
        None, 
        description="95% confidence interval"
    )
    
    timestamp: datetime = Field(default_factory=datetime.now)


class RelevanceJudgment(BaseModel):
    """Structured relevance assessment."""
    
    query: str = Field(..., description="Query being judged")
    document: str = Field(..., description="Document/chunk being judged")
    
    # Judgment
    relevance_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Relevance score (0 = not relevant, 1 = highly relevant)"
    )
    
    reasoning: str = Field(
        ..., 
        description="Explanation for the relevance score"
    )
    
    # Categories
    is_exact_match: bool = Field(..., description="Is this an exact answer?")
    is_partial_match: bool = Field(..., description="Is this partially relevant?")
    is_context: bool = Field(..., description="Provides useful context?")
    
    # Metadata
    judge_type: str = Field(
        default="llm", 
        description="Type of judge (human, llm, automatic)"
    )
    
    timestamp: datetime = Field(default_factory=datetime.now)


# Feedback and Learning Models

class UserFeedback(BaseModel):
    """Structured user feedback."""
    
    response_id: UUID = Field(..., description="ID of response being rated")
    
    # Feedback scores
    helpful_score: int = Field(
        ..., 
        ge=1, 
        le=5, 
        description="How helpful (1-5)"
    )
    
    accuracy_score: int = Field(
        ..., 
        ge=1, 
        le=5, 
        description="How accurate (1-5)"
    )
    
    # Text feedback
    feedback_text: Optional[str] = Field(
        None, 
        description="Free-form feedback"
    )
    
    # Specific issues
    issues: List[str] = Field(
        default_factory=list,
        description="Specific issues identified"
    )
    
    # Corrections
    corrected_answer: Optional[str] = Field(
        None,
        description="User-provided correction"
    )
    
    timestamp: datetime = Field(default_factory=datetime.now)


# Configuration Models

class ModelConfig(BaseModel):
    """Configuration for LLM models."""
    
    provider: str = Field(..., description="Provider (openai, anthropic, etc.)")
    model_name: str = Field(..., description="Model identifier")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, gt=0)
    
    # Cost tracking
    input_cost_per_1k_tokens: float = Field(default=0.0, ge=0.0)
    output_cost_per_1k_tokens: float = Field(default=0.0, ge=0.0)


class RAGConfig(BaseModel):
    """Configuration for the RAG system."""
    
    # Models
    router_model: ModelConfig = Field(..., description="Model for query routing")
    generator_model: ModelConfig = Field(..., description="Model for answer generation")
    evaluator_model: ModelConfig = Field(..., description="Model for evaluation")
    
    # Retrieval settings
    max_chunks: int = Field(default=5, gt=0, description="Max chunks to retrieve")
    similarity_threshold: float = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0, 
        description="Minimum similarity for relevance"
    )
    
    # Tool settings
    enable_reranking: bool = Field(default=True)
    enable_multi_tool: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=0)
    
    # Evaluation
    enable_auto_evaluation: bool = Field(default=True)
    evaluation_sample_rate: float = Field(
        default=0.1, 
        ge=0.0, 
        le=1.0,
        description="Fraction of queries to auto-evaluate"
    )


# Export all models
__all__ = [
    # Enums
    "QueryType",
    "ToolType", 
    "ConfidenceLevel",
    
    # Core models
    "QueryIntent",
    "Citation",
    "RetrievalResult",
    "ToolCall",
    "AgentResponse",
    
    # Evaluation
    "EvaluationMetric",
    "RelevanceJudgment",
    "UserFeedback",
    
    # Configuration
    "ModelConfig",
    "RAGConfig",
]
