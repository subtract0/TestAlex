"""Agentic RAG System - State-of-the-art RAG with structured outputs."""

__version__ = "0.1.0"
__author__ = "Alex"
__description__ = "State-of-the-art RAG system with agentic capabilities using structured outputs"

# Core imports
from .core.models import (
    AgentResponse,
    Citation,
    QueryIntent,
    QueryType,
    RetrievalResult,
    ToolCall,
    ToolType,
)

from .core.router import (
    AdvancedQueryRouter,
    QueryRouter,
    create_default_router,
)

# Tool imports
from .tools.base import MultiTool
from .tools.vector_search import VectorSearchTool, create_vector_search_tool

__all__ = [
    # Version info
    "__version__",
    "__author__", 
    "__description__",
    
    # Core models
    "AgentResponse",
    "Citation", 
    "QueryIntent",
    "QueryType",
    "RetrievalResult",
    "ToolCall",
    "ToolType",
    
    # Router
    "AdvancedQueryRouter",
    "QueryRouter",
    "create_default_router",
    
    # Tools
    "MultiTool",
    "VectorSearchTool",
    "create_vector_search_tool",
]
