"""SQL query tool for structured data queries."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from loguru import logger
from sqlmodel import Session, create_engine, text

from .base import BaseTool, ToolConfig, create_citation
from ..core.models import RetrievalResult, ToolType


class SQLQueryTool(BaseTool):
    """SQL-based search tool for structured data queries."""
    
    def __init__(self, config: ToolConfig, database_path: str = ":memory:"):
        """Initialize the SQL query tool."""
        super().__init__(config)
        
        self.database_path = database_path
        self.engine = create_engine(f"sqlite:///{database_path}")
        self.max_results = config.settings.get("max_results", 100)
        self.safe_mode = config.settings.get("safe_mode", True)  # Prevent dangerous queries
        
        # Initialize database if needed
        self._setup_database()
    
    def _setup_database(self):
        """Setup database and load initial data if configured."""
        try:
            # Create connection to test
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"SQL query tool connected to database: {self.database_path}")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> RetrievalResult:
        """Execute SQL query and return structured results."""
        
        try:
            # Validate and sanitize query
            if self.safe_mode and not self._is_safe_query(query):
                return RetrievalResult(
                    tool_used=self.tool_type,
                    query=query,
                    content="",
                    citations=[],
                    confidence=0.0,
                    latency_ms=0.0,
                    metadata={"error": "Unsafe query rejected by safety filter"}
                )
            
            # Build final query with filters
            final_query = self._build_query(query, filters, limit)
            
            # Execute query
            results = await self._execute_query(final_query)
            
            # Process results into citations
            citations = self._process_sql_results(results, final_query)
            
            # Calculate confidence based on result quality
            confidence = self._calculate_confidence(citations, results)
            
            # Combine content
            combined_content = self._combine_content(citations, results)
            
            return RetrievalResult(
                tool_used=self.tool_type,
                query=query,
                content=combined_content,
                citations=citations,
                confidence=confidence,
                latency_ms=0.0,  # Will be set by parent class
                token_count=len(combined_content.split()),
                metadata={
                    "final_query": final_query,
                    "row_count": len(results) if results else 0,
                    "database_path": self.database_path
                }
            )
            
        except Exception as e:
            logger.error(f"SQL query failed: {e}")
            return RetrievalResult(
                tool_used=self.tool_type,
                query=query,
                content="",
                citations=[],
                confidence=0.0,
                latency_ms=0.0,
                metadata={"error": str(e)}
            )
    
    def _is_safe_query(self, query: str) -> bool:
        """Check if query is safe to execute."""
        query_upper = query.upper().strip()
        
        # Allow only SELECT statements
        if not query_upper.startswith("SELECT"):
            return False
        
        # Dangerous keywords to avoid
        dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
            "TRUNCATE", "REPLACE", "MERGE", "EXEC", "EXECUTE"
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        return True
    
    def _build_query(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]], 
        limit: int
    ) -> str:
        """Build final query with filters and limits."""
        
        final_query = query.strip()
        
        # Add WHERE clause from filters if provided
        if filters and "where" in filters:
            where_clause = filters["where"]
            if " WHERE " not in final_query.upper():
                final_query += f" WHERE {where_clause}"
            else:
                final_query += f" AND {where_clause}"
        
        # Add LIMIT if not already present
        if " LIMIT " not in final_query.upper():
            final_query += f" LIMIT {min(limit, self.max_results)}"
        
        return final_query
    
    async def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        try:
            with Session(self.engine) as session:
                result = session.execute(text(query))
                
                # Convert to list of dictionaries
                columns = result.keys()
                rows = []
                for row in result.fetchall():
                    row_dict = dict(zip(columns, row))
                    rows.append(row_dict)
                
                return rows
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def _process_sql_results(
        self, 
        results: List[Dict[str, Any]], 
        query: str
    ) -> List[Any]:
        """Process SQL results into structured citations."""
        
        if not results:
            return []
        
        citations = []
        
        for i, row in enumerate(results):
            # Create a readable representation of the row
            row_content = json.dumps(row, indent=2, default=str)
            
            # Calculate relevance (simple heuristic based on data completeness)
            non_null_fields = sum(1 for v in row.values() if v is not None)
            total_fields = len(row)
            relevance_score = non_null_fields / total_fields if total_fields > 0 else 0.5
            
            # Create citation
            citation = create_citation(
                source_id=f"query_result_{i+1}",
                content=row_content,
                relevance_score=relevance_score,
                title=f"Query Result {i+1}",
                chunk_id=f"row_{i+1}"
            )
            
            citations.append(citation)
        
        return citations
    
    def _calculate_confidence(
        self, 
        citations: List[Any], 
        results: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence based on query results."""
        
        if not results:
            return 0.0
        
        # Base confidence on having results
        base_confidence = 0.7
        
        # Boost for complete data (fewer null values)
        total_values = sum(len(row) for row in results)
        null_values = sum(1 for row in results for v in row.values() if v is None)
        completeness = 1.0 - (null_values / max(total_values, 1))
        
        # Boost for reasonable result count
        result_count_factor = min(1.0, len(results) / 10)  # Optimal around 10 results
        
        confidence = base_confidence + completeness * 0.2 + result_count_factor * 0.1
        return min(1.0, confidence)
    
    def _combine_content(
        self, 
        citations: List[Any], 
        results: List[Dict[str, Any]]
    ) -> str:
        """Combine SQL results into readable content."""
        
        if not results:
            return "No results found."
        
        # Create a summary
        summary_parts = [f"Query returned {len(results)} result(s):"]
        
        # If results are tabular, create a simple table view
        if results:
            # Get column names
            columns = list(results[0].keys())
            
            # Add header
            summary_parts.append("")
            summary_parts.append(" | ".join(columns))
            summary_parts.append("-" * (len(" | ".join(columns))))
            
            # Add rows (limit to first 5 for readability)
            for row in results[:5]:
                row_values = [str(row.get(col, "")) for col in columns]
                summary_parts.append(" | ".join(row_values))
            
            if len(results) > 5:
                summary_parts.append(f"... and {len(results) - 5} more rows")
        
        return "\n".join(summary_parts)
    
    def load_csv(self, csv_path: str, table_name: str) -> bool:
        """Load CSV data into a table for querying."""
        try:
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, self.engine, if_exists="replace", index=False)
            logger.info(f"Loaded CSV {csv_path} into table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return False
    
    def load_json(self, json_path: str, table_name: str) -> bool:
        """Load JSON data into a table for querying."""
        try:
            with open(json_path) as f:
                data = json.load(f)
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                raise ValueError("JSON must be object or array")
            
            df.to_sql(table_name, self.engine, if_exists="replace", index=False)
            logger.info(f"Loaded JSON {json_path} into table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            return False
    
    def get_tables(self) -> List[str]:
        """Get list of available tables."""
        try:
            with Session(self.engine) as session:
                result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get tables: {e}")
            return []
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a table."""
        try:
            with Session(self.engine) as session:
                result = session.execute(text(f"PRAGMA table_info({table_name})"))
                columns = []
                for row in result.fetchall():
                    columns.append({
                        "name": row[1],
                        "type": row[2],
                        "not_null": bool(row[3]),
                        "default": row[4],
                        "primary_key": bool(row[5])
                    })
                return {
                    "table_name": table_name,
                    "columns": columns
                }
        except Exception as e:
            logger.error(f"Failed to get schema for {table_name}: {e}")
            return {}


# Utility functions

def create_sql_query_tool(database_path: str = ":memory:", safe_mode: bool = True) -> SQLQueryTool:
    """Create a SQL query tool with default configuration."""
    
    config = ToolConfig(
        tool_type=ToolType.SQL_QUERY,
        enabled=True,
        timeout_seconds=30.0,
        max_retries=2,
        settings={
            "safe_mode": safe_mode,
            "max_results": 100
        }
    )
    
    return SQLQueryTool(config, database_path)


async def quick_sql_query(query: str, database_path: str = ":memory:", limit: int = 5) -> RetrievalResult:
    """Quick utility for SQL queries with default settings."""
    tool = create_sql_query_tool(database_path)
    return await tool.search(query, limit)


# Export main classes
__all__ = [
    "SQLQueryTool",
    "create_sql_query_tool",
    "quick_sql_query",
]
