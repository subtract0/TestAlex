"""Vector search tool using LanceDB for semantic similarity search."""

import os
from typing import Any, Dict, List, Optional

import lancedb
import numpy as np
from openai import AsyncOpenAI
from loguru import logger

from .base import BaseTool, ToolConfig, create_citation
from ..core.models import RetrievalResult, ToolType


class VectorSearchTool(BaseTool):
    """Vector-based semantic search using LanceDB and OpenAI embeddings."""
    
    def __init__(self, config: ToolConfig, db_path: str = "./data/lancedb"):
        """Initialize the vector search tool."""
        super().__init__(config)
        
        self.db_path = db_path
        self.embedding_model = config.settings.get("embedding_model", "text-embedding-3-small")
        self.table_name = config.settings.get("table_name", "documents")
        
        # Initialize clients
        self.openai_client = AsyncOpenAI()
        self.db = None
        self.table = None
        
        # Initialize database connection
        self._init_db()
    
    def _init_db(self):
        """Initialize LanceDB connection."""
        try:
            self.db = lancedb.connect(self.db_path)
            
            # Try to open existing table
            if self.table_name in self.db.table_names():
                self.table = self.db.open_table(self.table_name)
                logger.info(f"Connected to existing table: {self.table_name}")
            else:
                logger.warning(f"Table {self.table_name} not found. Call create_table() first.")
                
        except Exception as e:
            logger.error(f"Failed to initialize LanceDB: {e}")
            self.table = None
    
    async def create_table(self, sample_data: List[Dict[str, Any]]) -> bool:
        """Create a new table with sample data structure."""
        try:
            if not sample_data:
                raise ValueError("Sample data is required to create table schema")
            
            # Ensure required fields exist
            for item in sample_data:
                if 'vector' not in item:
                    # Generate embedding for content
                    content = item.get('content', '')
                    if content:
                        embedding = await self._get_embedding(content)
                        item['vector'] = embedding
            
            self.table = self.db.create_table(self.table_name, sample_data, mode="overwrite")
            logger.info(f"Created table {self.table_name} with {len(sample_data)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            return False
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector database."""
        if not self.table:
            logger.error("Table not initialized")
            return False
        
        try:
            # Generate embeddings for documents that don't have them
            for doc in documents:
                if 'vector' not in doc:
                    content = doc.get('content', '')
                    if content:
                        doc['vector'] = await self._get_embedding(content)
            
            self.table.add(documents)
            logger.info(f"Added {len(documents)} documents to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI."""
        try:
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text.replace("\n", " ")
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return []
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> RetrievalResult:
        """Perform vector similarity search."""
        
        if not self.table:
            return RetrievalResult(
                tool_used=self.tool_type,
                query=query,
                content="",
                citations=[],
                confidence=0.0,
                latency_ms=0.0,
                metadata={"error": "Vector database not initialized"}
            )
        
        try:
            # Get query embedding
            query_embedding = await self._get_embedding(query)
            if not query_embedding:
                raise ValueError("Failed to generate query embedding")
            
            # Build search query
            search_builder = self.table.search(query_embedding).limit(limit)
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        # Handle list filters (IN operator)
                        search_builder = search_builder.where(f"{key} IN {value}")
                    else:
                        # Handle equality filters
                        search_builder = search_builder.where(f"{key} = '{value}'")
            
            # Execute search
            results = search_builder.to_pandas()
            
            if results.empty:
                return RetrievalResult(
                    tool_used=self.tool_type,
                    query=query,
                    content="",
                    citations=[],
                    confidence=0.0,
                    latency_ms=0.0,
                    metadata={"results_count": 0}
                )
            
            # Process results
            citations = []
            all_content = []
            
            for _, row in results.iterrows():
                # Calculate confidence from distance (lower distance = higher confidence)
                distance = row.get('_distance', 1.0)
                confidence = max(0.0, 1.0 - distance) if distance <= 1.0 else 1.0 / (1.0 + distance)
                
                citation = create_citation(
                    source_id=str(row.get('id', row.get('source_id', 'unknown'))),
                    content=str(row.get('content', '')),
                    relevance_score=confidence,
                    title=str(row.get('title', None)) if row.get('title') else None,
                    url=str(row.get('url', None)) if row.get('url') else None,
                    page=int(row.get('page', 0)) if row.get('page') else None,
                    chunk_id=str(row.get('chunk_id', None)) if row.get('chunk_id') else None
                )
                
                citations.append(citation)
                all_content.append(str(row.get('content', '')))
            
            # Combine all content
            combined_content = "\n\n".join(all_content)
            
            # Calculate overall confidence (average of top results)
            overall_confidence = sum(c.relevance_score for c in citations) / len(citations)
            
            return RetrievalResult(
                tool_used=self.tool_type,
                query=query,
                content=combined_content,
                citations=citations,
                confidence=overall_confidence,
                latency_ms=0.0,  # Will be set by parent class
                token_count=len(combined_content.split()),
                metadata={
                    "results_count": len(results),
                    "embedding_model": self.embedding_model,
                    "filters_applied": filters or {}
                }
            )
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return RetrievalResult(
                tool_used=self.tool_type,
                query=query,
                content="",
                citations=[],
                confidence=0.0,
                latency_ms=0.0,
                metadata={"error": str(e)}
            )
    
    def get_table_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database table."""
        if not self.table:
            return {"error": "Table not initialized"}
        
        try:
            # Get table schema and count
            count_result = self.table.count_rows()
            schema = self.table.schema
            
            return {
                "table_name": self.table_name,
                "document_count": count_result,
                "schema": str(schema),
                "embedding_model": self.embedding_model
            }
            
        except Exception as e:
            return {"error": str(e)}


# Utility functions

def create_vector_search_tool(db_path: str = "./data/lancedb", 
                              embedding_model: str = "text-embedding-3-small",
                              table_name: str = "documents") -> VectorSearchTool:
    """Create a vector search tool with default configuration."""
    
    config = ToolConfig(
        tool_type=ToolType.VECTOR_SEARCH,
        enabled=True,
        timeout_seconds=30.0,
        max_retries=2,
        settings={
            "embedding_model": embedding_model,
            "table_name": table_name
        }
    )
    
    return VectorSearchTool(config, db_path)


async def quick_vector_search(query: str, limit: int = 5) -> RetrievalResult:
    """Quick utility for vector search with default settings."""
    tool = create_vector_search_tool()
    return await tool.search(query, limit)


# Export main classes
__all__ = [
    "VectorSearchTool",
    "create_vector_search_tool",
    "quick_vector_search",
]
