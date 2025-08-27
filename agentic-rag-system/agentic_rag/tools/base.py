"""Base tool interface and common utilities for RAG tools."""

import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from ..core.models import Citation, RetrievalResult, ToolType


class ToolConfig(BaseModel):
    """Configuration for a retrieval tool."""
    
    tool_type: ToolType
    enabled: bool = Field(default=True)
    timeout_seconds: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=2, ge=0)
    
    # Tool-specific settings
    settings: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for all retrieval tools."""
    
    def __init__(self, config: ToolConfig):
        """Initialize the tool with configuration."""
        self.config = config
        self.tool_type = config.tool_type
        self.call_count = 0
        self.total_latency = 0.0
        self.error_count = 0
        
        if not config.enabled:
            logger.warning(f"Tool {self.tool_type.value} is disabled")
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> RetrievalResult:
        """
        Perform search with the tool.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            filters: Optional filters to apply
            **kwargs: Tool-specific parameters
            
        Returns:
            RetrievalResult with found content and metadata
        """
        pass
    
    async def search_with_retry(
        self,
        query: str,
        limit: int = 5, 
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> RetrievalResult:
        """Search with automatic retry logic."""
        
        if not self.config.enabled:
            raise RuntimeError(f"Tool {self.tool_type.value} is disabled")
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Add timeout
                result = await asyncio.wait_for(
                    self.search(query, limit, filters, **kwargs),
                    timeout=self.config.timeout_seconds
                )
                
                # Update metrics
                latency = (time.time() - start_time) * 1000
                self.call_count += 1
                self.total_latency += latency
                
                result.latency_ms = latency
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.config.timeout_seconds}s"
                logger.warning(f"Tool {self.tool_type.value} timeout on attempt {attempt + 1}")
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Tool {self.tool_type.value} error on attempt {attempt + 1}: {e}")
                
                if attempt < self.config.max_retries:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
        
        # All retries failed
        self.error_count += 1
        latency = (time.time() - start_time) * 1000
        
        # Return empty result with error info
        return RetrievalResult(
            tool_used=self.tool_type,
            query=query,
            content="",
            citations=[],
            confidence=0.0,
            latency_ms=latency,
            metadata={"error": last_error, "retries": self.config.max_retries}
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get tool performance metrics."""
        avg_latency = self.total_latency / max(self.call_count, 1)
        error_rate = self.error_count / max(self.call_count, 1)
        
        return {
            "tool_type": self.tool_type.value,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "avg_latency_ms": avg_latency,
            "total_latency_ms": self.total_latency,
        }
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self.call_count = 0
        self.total_latency = 0.0
        self.error_count = 0


class MultiTool:
    """Manages multiple retrieval tools and orchestrates their execution."""
    
    def __init__(self, tools: Dict[ToolType, BaseTool]):
        """Initialize with a dictionary of tools."""
        self.tools = tools
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute_single(
        self, 
        tool_type: ToolType,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> RetrievalResult:
        """Execute a single tool."""
        
        if tool_type not in self.tools:
            raise ValueError(f"Tool {tool_type.value} not available")
        
        tool = self.tools[tool_type]
        
        logger.info(f"Executing {tool_type.value} for query: {query[:50]}...")
        result = await tool.search_with_retry(query, limit, filters, **kwargs)
        
        # Log execution
        self.execution_history.append({
            "tool_type": tool_type.value,
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "success": result.confidence > 0,
            "latency_ms": result.latency_ms,
            "result_count": len(result.citations),
        })
        
        return result
    
    async def execute_parallel(
        self,
        tool_types: List[ToolType],
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[RetrievalResult]:
        """Execute multiple tools in parallel."""
        
        logger.info(f"Executing {len(tool_types)} tools in parallel for query: {query[:50]}...")
        
        # Create tasks for each tool
        tasks = []
        for tool_type in tool_types:
            if tool_type in self.tools:
                task = self.execute_single(tool_type, query, limit, filters, **kwargs)
                tasks.append(task)
            else:
                logger.warning(f"Tool {tool_type.value} not available, skipping")
        
        if not tasks:
            logger.error("No available tools to execute")
            return []
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Tool execution failed: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def execute_sequential(
        self,
        tool_types: List[ToolType], 
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        early_stop_threshold: float = 0.8,
        **kwargs
    ) -> List[RetrievalResult]:
        """Execute tools sequentially with early stopping."""
        
        logger.info(f"Executing {len(tool_types)} tools sequentially for query: {query[:50]}...")
        
        results = []
        
        for tool_type in tool_types:
            if tool_type not in self.tools:
                logger.warning(f"Tool {tool_type.value} not available, skipping")
                continue
            
            result = await self.execute_single(tool_type, query, limit, filters, **kwargs)
            results.append(result)
            
            # Early stopping if we get high-confidence result
            if result.confidence >= early_stop_threshold:
                logger.info(
                    f"Early stopping: {tool_type.value} returned high confidence "
                    f"({result.confidence:.3f})"
                )
                break
        
        return results
    
    def merge_results(
        self, 
        results: List[RetrievalResult],
        max_citations: int = 10
    ) -> RetrievalResult:
        """Merge results from multiple tools into a single result."""
        
        if not results:
            return RetrievalResult(
                tool_used=ToolType.VECTOR_SEARCH,  # Default
                query="",
                content="",
                citations=[],
                confidence=0.0,
                latency_ms=0.0
            )
        
        # Combine content and citations
        all_citations = []
        all_content = []
        total_latency = 0.0
        max_confidence = 0.0
        
        for result in results:
            if result.content.strip():
                all_content.append(result.content)
            
            all_citations.extend(result.citations)
            total_latency += result.latency_ms
            max_confidence = max(max_confidence, result.confidence)
        
        # Sort citations by relevance and deduplicate
        all_citations.sort(key=lambda c: c.relevance_score, reverse=True)
        unique_citations = []
        seen_sources = set()
        
        for citation in all_citations:
            if citation.source_id not in seen_sources:
                unique_citations.append(citation)
                seen_sources.add(citation.source_id)
                
                if len(unique_citations) >= max_citations:
                    break
        
        # Combine content
        combined_content = "\n\n".join(all_content) if all_content else ""
        
        # Tool used is the first successful tool
        tool_used = results[0].tool_used if results else ToolType.VECTOR_SEARCH
        query = results[0].query if results else ""
        
        return RetrievalResult(
            tool_used=tool_used,
            query=query,
            content=combined_content,
            citations=unique_citations,
            confidence=max_confidence,
            latency_ms=total_latency,
            metadata={
                "merged_from": [r.tool_used.value for r in results],
                "source_count": len(results)
            }
        )
    
    def get_overall_metrics(self) -> Dict[str, Any]:
        """Get metrics for all tools."""
        tool_metrics = {}
        for tool_type, tool in self.tools.items():
            tool_metrics[tool_type.value] = tool.get_metrics()
        
        # Execution history stats
        total_executions = len(self.execution_history)
        successful_executions = sum(
            1 for exec in self.execution_history if exec["success"]
        )
        
        return {
            "tool_metrics": tool_metrics,
            "total_executions": total_executions,
            "success_rate": successful_executions / max(total_executions, 1),
            "execution_history_size": total_executions
        }
    
    def get_available_tools(self) -> List[ToolType]:
        """Get list of available tool types."""
        return [
            tool_type for tool_type, tool in self.tools.items() 
            if tool.config.enabled
        ]


# Utility functions

def create_citation(
    source_id: str,
    content: str,
    relevance_score: float,
    title: Optional[str] = None,
    url: Optional[str] = None,
    page: Optional[int] = None,
    chunk_id: Optional[str] = None
) -> Citation:
    """Helper function to create citation objects."""
    
    # Create a snippet from the content (first 200 chars)
    snippet = content[:200] + "..." if len(content) > 200 else content
    
    return Citation(
        source_id=source_id,
        title=title,
        url=url,
        page=page,
        chunk_id=chunk_id,
        relevance_score=relevance_score,
        snippet=snippet
    )


# Export main classes
__all__ = [
    "ToolConfig",
    "BaseTool", 
    "MultiTool",
    "create_citation",
]
