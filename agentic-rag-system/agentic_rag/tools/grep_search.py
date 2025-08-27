"""Grep search tool for exact text matching in documents and code."""

import asyncio
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from .base import BaseTool, ToolConfig, create_citation
from ..core.models import RetrievalResult, ToolType


class GrepSearchTool(BaseTool):
    """Grep-based exact text search for code, documents, and structured content."""
    
    def __init__(self, config: ToolConfig, search_paths: List[str] = None):
        """Initialize the grep search tool."""
        super().__init__(config)
        
        self.search_paths = search_paths or ["."]
        self.file_extensions = config.settings.get(
            "file_extensions", 
            [".py", ".md", ".txt", ".json", ".yaml", ".yml", ".js", ".ts", ".go", ".java"]
        )
        self.max_results = config.settings.get("max_results", 100)
        self.context_lines = config.settings.get("context_lines", 3)
        
        # Validate search paths exist
        self._validate_search_paths()
    
    def _validate_search_paths(self):
        """Validate that search paths exist and are accessible."""
        valid_paths = []
        for path in self.search_paths:
            path_obj = Path(path)
            if path_obj.exists():
                valid_paths.append(str(path_obj.resolve()))
            else:
                logger.warning(f"Search path does not exist: {path}")
        
        self.search_paths = valid_paths or ["."]
        logger.info(f"Grep search configured for paths: {self.search_paths}")
    
    async def search(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> RetrievalResult:
        """Perform grep search for exact text matches."""
        
        try:
            # Build grep command
            grep_cmd = self._build_grep_command(query, filters)
            
            # Execute grep search
            results = await self._execute_grep(grep_cmd)
            
            # Process and rank results
            citations = self._process_grep_results(results, query, limit)
            
            # Calculate overall confidence based on exact matches
            confidence = self._calculate_confidence(citations, query)
            
            # Combine content from all citations
            combined_content = self._combine_content(citations)
            
            return RetrievalResult(
                tool_used=self.tool_type,
                query=query,
                content=combined_content,
                citations=citations,
                confidence=confidence,
                latency_ms=0.0,  # Will be set by parent class
                token_count=len(combined_content.split()),
                metadata={
                    "grep_command": " ".join(grep_cmd),
                    "search_paths": self.search_paths,
                    "file_extensions": self.file_extensions,
                    "total_matches": len(citations)
                }
            )
            
        except Exception as e:
            logger.error(f"Grep search failed: {e}")
            return RetrievalResult(
                tool_used=self.tool_type,
                query=query,
                content="",
                citations=[],
                confidence=0.0,
                latency_ms=0.0,
                metadata={"error": str(e)}
            )
    
    def _build_grep_command(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Build grep command with appropriate flags and filters."""
        
        cmd = ["grep", "-r", "-n", "-i"]  # recursive, line numbers, case-insensitive
        
        # Add context lines
        if self.context_lines > 0:
            cmd.extend(["-C", str(self.context_lines)])
        
        # Add file type filters
        if self.file_extensions:
            for ext in self.file_extensions:
                cmd.extend(["--include", f"*{ext}"])
        
        # Add filters if provided
        if filters:
            # File path filter
            if "path" in filters:
                path_filter = filters["path"]
                if isinstance(path_filter, str):
                    # Use only paths that match the filter
                    filtered_paths = [p for p in self.search_paths if path_filter in p]
                    if filtered_paths:
                        self.search_paths = filtered_paths
            
            # File extension filter
            if "extension" in filters:
                ext_filter = filters["extension"]
                if isinstance(ext_filter, str):
                    cmd.extend(["--include", f"*{ext_filter}"])
                elif isinstance(ext_filter, list):
                    for ext in ext_filter:
                        cmd.extend(["--include", f"*{ext}"])
        
        # Add the search pattern (escape special regex characters for literal search)
        escaped_query = re.escape(query)
        cmd.append(escaped_query)
        
        # Add search paths
        cmd.extend(self.search_paths)
        
        return cmd
    
    async def _execute_grep(self, cmd: List[str]) -> List[str]:
        """Execute grep command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Grep found matches
                return stdout.decode('utf-8', errors='ignore').strip().split('\n')
            elif process.returncode == 1:
                # No matches found (normal for grep)
                return []
            else:
                # Grep error
                error_msg = stderr.decode('utf-8', errors='ignore')
                logger.error(f"Grep command failed: {error_msg}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to execute grep command: {e}")
            return []
    
    def _process_grep_results(
        self, 
        results: List[str], 
        query: str, 
        limit: int
    ) -> List[Dict]:
        """Process grep output into structured citations."""
        
        citations = []
        seen_files = {}  # Track matches per file to avoid duplicates
        
        for line in results[:self.max_results]:
            if not line.strip():
                continue
            
            # Parse grep output: filename:line_number:content
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue
            
            file_path = parts[0]
            line_number = parts[1]
            content = parts[2]
            
            try:
                line_num = int(line_number)
            except ValueError:
                # Handle context lines that don't have line numbers
                continue
            
            # Calculate relevance based on exact match quality
            relevance_score = self._calculate_line_relevance(content, query)
            
            # Create unique source ID
            source_id = f"{file_path}:{line_num}"
            
            # Avoid duplicate entries from the same file/line
            if source_id in seen_files:
                continue
            
            seen_files[source_id] = True
            
            # Create citation
            citation = create_citation(
                source_id=source_id,
                content=content.strip(),
                relevance_score=relevance_score,
                title=Path(file_path).name,
                url=f"file://{os.path.abspath(file_path)}",
                page=line_num,
                chunk_id=f"line_{line_num}"
            )
            
            citations.append(citation)
            
            if len(citations) >= limit:
                break
        
        # Sort by relevance score (descending)
        citations.sort(key=lambda c: c.relevance_score, reverse=True)
        
        return citations
    
    def _calculate_line_relevance(self, content: str, query: str) -> float:
        """Calculate relevance score for a line match."""
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Base score for containing the query
        if query_lower not in content_lower:
            return 0.1  # Shouldn't happen with grep, but safety check
        
        # Calculate factors
        exact_match_bonus = 1.0 if query in content else 0.8
        length_penalty = max(0.1, 1.0 - len(content) / 1000)  # Prefer shorter, more focused lines
        position_bonus = 0.2 if content_lower.strip().startswith(query_lower) else 0.0
        
        # Check for code-specific patterns
        code_bonus = 0.0
        if any(pattern in content for pattern in ["def ", "class ", "function ", "const ", "let ", "var "]):
            code_bonus = 0.3  # Boost function/class definitions
        
        # Combine factors
        relevance_score = min(1.0, 0.5 + exact_match_bonus * 0.3 + length_penalty * 0.1 + position_bonus + code_bonus)
        
        return relevance_score
    
    def _calculate_confidence(self, citations: List[Dict], query: str) -> float:
        """Calculate overall confidence based on match quality."""
        if not citations:
            return 0.0
        
        # Average relevance of top results
        top_citations = citations[:3]  # Consider top 3 results
        avg_relevance = sum(c.relevance_score for c in top_citations) / len(top_citations)
        
        # Boost confidence if we have multiple good matches
        match_count_bonus = min(0.2, len(citations) * 0.05)
        
        return min(1.0, avg_relevance + match_count_bonus)
    
    def _combine_content(self, citations: List[Dict]) -> str:
        """Combine content from citations into readable format."""
        if not citations:
            return ""
        
        combined_parts = []
        for i, citation in enumerate(citations[:5]):  # Limit to top 5 for readability
            header = f"[{i+1}] {citation.title} (Line {citation.page}):"
            combined_parts.append(header)
            combined_parts.append(citation.snippet)
            combined_parts.append("")  # Empty line for separation
        
        return "\n".join(combined_parts).strip()


# Utility functions

def create_grep_search_tool(
    search_paths: List[str] = None,
    file_extensions: List[str] = None,
    context_lines: int = 3
) -> GrepSearchTool:
    """Create a grep search tool with default configuration."""
    
    settings = {
        "file_extensions": file_extensions or [
            ".py", ".md", ".txt", ".json", ".yaml", ".yml", 
            ".js", ".ts", ".go", ".java", ".cpp", ".h"
        ],
        "context_lines": context_lines,
        "max_results": 100
    }
    
    config = ToolConfig(
        tool_type=ToolType.GREP_SEARCH,
        enabled=True,
        timeout_seconds=15.0,
        max_retries=2,
        settings=settings
    )
    
    return GrepSearchTool(config, search_paths)


async def quick_grep_search(query: str, search_paths: List[str] = None, limit: int = 5) -> RetrievalResult:
    """Quick utility for grep search with default settings."""
    tool = create_grep_search_tool(search_paths)
    return await tool.search(query, limit)


# Export main classes
__all__ = [
    "GrepSearchTool",
    "create_grep_search_tool", 
    "quick_grep_search",
]
