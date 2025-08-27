"""Query router using instructor for structured query understanding."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

import instructor
from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from .models import (
    ConfidenceLevel,
    ModelConfig,
    QueryIntent,
    QueryType,
    ToolType,
)


class QueryRouter:
    """Intelligent query router using structured outputs."""
    
    def __init__(self, model_config: ModelConfig):
        """Initialize the router with a model configuration."""
        self.model_config = model_config
        self.client = self._create_client()
        self.routing_history: List[QueryIntent] = []
    
    def _create_client(self):
        """Create instructor client based on provider."""
        if self.model_config.provider == "openai":
            base_client = AsyncOpenAI()
            return instructor.from_openai(base_client, mode=instructor.Mode.TOOLS)
        elif self.model_config.provider == "anthropic":
            # Add anthropic support
            raise NotImplementedError("Anthropic support coming soon")
        else:
            raise ValueError(f"Unsupported provider: {self.model_config.provider}")
    
    async def route_query(self, query: str) -> QueryIntent:
        """Route a query to determine intent and suggested tools."""
        
        logger.info(f"Routing query: {query[:100]}...")
        start_time = datetime.now()
        
        try:
            # Use instructor for structured query understanding
            intent = await self.client.chat.completions.create(
                model=self.model_config.model_name,
                response_model=QueryIntent,
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": f"Analyze this query: {query}"
                    }
                ],
                max_retries=3,
            )
            
            # Store in history for analysis
            self.routing_history.append(intent)
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(
                f"Routed query in {latency:.1f}ms: "
                f"type={intent.query_type.value}, "
                f"confidence={intent.confidence:.3f}, "
                f"tools={[t.value for t in intent.suggested_tools]}"
            )
            
            return intent
            
        except Exception as e:
            logger.error(f"Error routing query: {e}")
            # Return fallback intent
            return self._create_fallback_intent(query)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for query classification."""
        return """
You are an expert query analysis system. Your job is to understand user queries and recommend the best tools to answer them.

QUERY TYPES:
- SEARCH: General semantic search queries ("What is machine learning?", "How does RAG work?")
- CODE_LOOKUP: Exact code, function, or API lookups ("find function calculate_metrics", "show me the User class")
- DOCUMENT_RETRIEVAL: Specific document searches ("find the Q3 report", "get the user manual")
- COMPARISON: Compare/contrast queries ("difference between X and Y", "compare approaches")
- SUMMARIZATION: Requests to summarize content ("summarize the meeting notes", "what are the key points")
- STRUCTURED_QUERY: Data queries requiring filters/SQL ("users created after 2023", "sales by region")
- MULTI_HOP: Complex queries requiring multiple steps ("How did our sales compare to last year and what caused the difference?")

AVAILABLE TOOLS:
- VECTOR_SEARCH: Semantic similarity search, good for conceptual queries
- GREP_SEARCH: Exact text matching, perfect for code/function names, IDs, specific terms
- SQL_QUERY: Structured data queries with filters, aggregations
- DOCUMENT_PARSER: Extract content from PDFs, images, structured documents
- WEB_SEARCH: External web search when internal data is insufficient
- RERANKER: Improve results from other tools by reordering by relevance

ANALYSIS GUIDELINES:
1. Consider the query's structure and intent
2. Look for specific terms that suggest exact matching (function names, IDs, exact phrases)
3. Consider if multiple tools might be needed
4. Evaluate confidence based on query clarity and specificity
5. Provide clear reasoning for your classification

Be precise in your analysis and conservative with confidence scores.
"""
    
    def _create_fallback_intent(self, query: str) -> QueryIntent:
        """Create a fallback intent when routing fails."""
        return QueryIntent(
            query=query,
            query_type=QueryType.SEARCH,
            chain_of_thought="Fallback classification due to routing error",
            confidence=0.1,
            confidence_level=ConfidenceLevel.LOW,
            entities=[],
            filters={},
            suggested_tools=[ToolType.VECTOR_SEARCH]
        )
    
    def get_routing_stats(self) -> Dict[str, float]:
        """Get routing statistics for monitoring."""
        if not self.routing_history:
            return {}
        
        # Query type distribution
        type_counts = {}
        confidence_sum = 0
        high_confidence_count = 0
        
        for intent in self.routing_history:
            query_type = intent.query_type.value
            type_counts[query_type] = type_counts.get(query_type, 0) + 1
            confidence_sum += intent.confidence
            if intent.confidence_level == ConfidenceLevel.HIGH:
                high_confidence_count += 1
        
        total = len(self.routing_history)
        
        return {
            "total_queries": total,
            "avg_confidence": confidence_sum / total,
            "high_confidence_rate": high_confidence_count / total,
            "query_type_distribution": {
                k: v / total for k, v in type_counts.items()
            }
        }


class AdvancedQueryRouter(QueryRouter):
    """Advanced router with multi-step reasoning and fallback strategies."""
    
    def __init__(self, model_config: ModelConfig, fallback_threshold: float = 0.3):
        """Initialize with fallback threshold."""
        super().__init__(model_config)
        self.fallback_threshold = fallback_threshold
    
    async def route_with_fallback(self, query: str) -> QueryIntent:
        """Route with automatic fallback to simpler strategies."""
        
        primary_intent = await self.route_query(query)
        
        # If confidence is too low, try fallback strategies
        if primary_intent.confidence < self.fallback_threshold:
            logger.warning(
                f"Low confidence ({primary_intent.confidence:.3f}) for query: {query[:50]}..."
                ", attempting fallback strategies"
            )
            
            fallback_intent = await self._fallback_routing(query, primary_intent)
            return fallback_intent
        
        return primary_intent
    
    async def _fallback_routing(self, query: str, primary_intent: QueryIntent) -> QueryIntent:
        """Try fallback routing strategies."""
        
        # Strategy 1: Rule-based classification
        rule_based_intent = self._rule_based_classification(query)
        if rule_based_intent.confidence > primary_intent.confidence:
            logger.info("Using rule-based classification as fallback")
            return rule_based_intent
        
        # Strategy 2: Multi-tool approach for uncertain queries
        logger.info("Using multi-tool approach for uncertain query")
        return self._create_multi_tool_intent(query, primary_intent)
    
    def _rule_based_classification(self, query: str) -> QueryIntent:
        """Simple rule-based classification as fallback."""
        
        query_lower = query.lower()
        confidence = 0.6  # Medium confidence for rule-based
        
        # Code lookup patterns
        code_patterns = ["function", "class", "method", "def ", "import", "from ", ".py"]
        if any(pattern in query_lower for pattern in code_patterns):
            return QueryIntent(
                query=query,
                query_type=QueryType.CODE_LOOKUP,
                chain_of_thought=f"Rule-based: detected code-related terms in query",
                confidence=confidence,
                confidence_level=ConfidenceLevel.MEDIUM,
                entities=[],
                filters={},
                suggested_tools=[ToolType.GREP_SEARCH, ToolType.VECTOR_SEARCH]
            )
        
        # Comparison patterns
        comparison_patterns = ["vs", "versus", "compare", "difference", "different"]
        if any(pattern in query_lower for pattern in comparison_patterns):
            return QueryIntent(
                query=query,
                query_type=QueryType.COMPARISON,
                chain_of_thought="Rule-based: detected comparison terms",
                confidence=confidence,
                confidence_level=ConfidenceLevel.MEDIUM,
                entities=[],
                filters={},
                suggested_tools=[ToolType.VECTOR_SEARCH]
            )
        
        # Summarization patterns
        summary_patterns = ["summarize", "summary", "key points", "overview"]
        if any(pattern in query_lower for pattern in summary_patterns):
            return QueryIntent(
                query=query,
                query_type=QueryType.SUMMARIZATION,
                chain_of_thought="Rule-based: detected summarization terms",
                confidence=confidence,
                confidence_level=ConfidenceLevel.MEDIUM,
                entities=[],
                filters={},
                suggested_tools=[ToolType.DOCUMENT_PARSER, ToolType.VECTOR_SEARCH]
            )
        
        # Default to search
        return QueryIntent(
            query=query,
            query_type=QueryType.SEARCH,
            chain_of_thought="Rule-based: no specific patterns detected, defaulting to search",
            confidence=0.4,
            confidence_level=ConfidenceLevel.LOW,
            entities=[],
            filters={},
            suggested_tools=[ToolType.VECTOR_SEARCH]
        )
    
    def _create_multi_tool_intent(self, query: str, primary_intent: QueryIntent) -> QueryIntent:
        """Create an intent that uses multiple tools for better coverage."""
        
        # Use multiple tools to increase chance of finding relevant content
        multi_tools = [
            ToolType.VECTOR_SEARCH,  # Always include semantic search
            ToolType.GREP_SEARCH,    # Include exact matching
        ]
        
        # Add specific tools based on query characteristics
        if any(term in query.lower() for term in ["data", "count", "number", "total"]):
            multi_tools.append(ToolType.SQL_QUERY)
        
        if any(term in query.lower() for term in ["document", "pdf", "file"]):
            multi_tools.append(ToolType.DOCUMENT_PARSER)
        
        return QueryIntent(
            query=query,
            query_type=primary_intent.query_type,  # Keep original classification
            chain_of_thought=(
                f"Multi-tool fallback: Original confidence was {primary_intent.confidence:.3f}, "
                f"using multiple tools to improve coverage"
            ),
            confidence=0.5,  # Medium confidence for multi-tool
            confidence_level=ConfidenceLevel.MEDIUM,
            entities=primary_intent.entities,
            filters=primary_intent.filters,
            suggested_tools=multi_tools
        )


# Utility functions

def create_default_router() -> QueryRouter:
    """Create a router with default OpenAI configuration."""
    config = ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.1,
        max_tokens=1000,
        input_cost_per_1k_tokens=0.00015,
        output_cost_per_1k_tokens=0.0006,
    )
    return QueryRouter(config)


async def quick_route(query: str) -> QueryIntent:
    """Quick utility function for routing a single query."""
    router = create_default_router()
    return await router.route_query(query)


# Export main classes
__all__ = [
    "QueryRouter",
    "AdvancedQueryRouter", 
    "create_default_router",
    "quick_route",
]
