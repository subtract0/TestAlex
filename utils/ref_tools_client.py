#!/usr/bin/env python3
"""
Ref-Tools MCP Client for ACIMguide Agent System
Provides token-efficient access to technical documentation for all agents
"""

import os
import json
import logging
import requests
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RefToolsConfig:
    """Configuration for Ref-Tools MCP client"""
    base_url: str
    port: int = 4102
    transport: str = 'http'
    timeout: int = 20
    max_retries: int = 3
    fallback_urls: List[str] = None

    def __post_init__(self):
        if self.fallback_urls is None:
            self.fallback_urls = [
                "https://ref-tools-mcp.acimguide.com",
                "http://localhost:8080"  # alternative local port
            ]

class RefToolsClient:
    """
    High-level client for Ref-Tools MCP service
    Provides token-efficient documentation access for agents
    """
    
    def __init__(self, config: Optional[RefToolsConfig] = None):
        if config is None:
            port = int(os.getenv('REF_MCP_PORT', 4102))
            host = os.getenv('REF_MCP_HOST', 'localhost')
            base_url = os.getenv('REF_MCP_URL', f'http://{host}:{port}')
            
            config = RefToolsConfig(
                base_url=base_url,
                port=port
            )
        
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ACIMguide-Agent-System/1.0'
        })

    def _make_request(self, endpoint: str, payload: Optional[Dict] = None, method: str = 'POST') -> Dict[str, Any]:
        """
        Make HTTP request to MCP server with fallback support
        """
        urls_to_try = [self.config.base_url] + self.config.fallback_urls
        
        for attempt, base_url in enumerate(urls_to_try):
            try:
                url = urljoin(base_url, endpoint)
                logger.debug(f"Attempting {method} {url} (attempt {attempt + 1})")
                
                if method.upper() == 'POST':
                    response = self.session.post(
                        url,
                        json=payload,
                        timeout=self.config.timeout
                    )
                else:
                    response = self.session.get(
                        url,
                        timeout=self.config.timeout
                    )
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request to {base_url} failed: {e}")
                if attempt == len(urls_to_try) - 1:
                    raise RefToolsConnectionError(f"Failed to connect to Ref-Tools MCP service after trying {len(urls_to_try)} endpoints")
                continue
            except Exception as e:
                logger.error(f"Unexpected error with {base_url}: {e}")
                continue

    def health_check(self) -> Dict[str, Any]:
        """Check if the MCP service is healthy and responsive"""
        try:
            return self._make_request('/health', method='GET')
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }

    def get_docs(self, library: str, query: str = "", max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Get documentation for a specific library or API
        
        Args:
            library: Name of the library/API (e.g., 'firebase', 'openai', 'react')
            query: Specific search query within the documentation
            max_tokens: Maximum tokens to return (helps with cost optimization)
            
        Returns:
            Dictionary containing relevant documentation snippets
        """
        payload = {
            'library': library,
            'query': query,
            'max_tokens': max_tokens,
            'format': 'json'
        }
        
        return self._make_request('/docs', payload)

    def search_api(self, api_name: str, endpoint_pattern: str = "", method: str = "") -> Dict[str, Any]:
        """
        Search for specific API endpoints and usage patterns
        
        Args:
            api_name: Name of the API (e.g., 'Firebase Admin', 'OpenAI')
            endpoint_pattern: Pattern to search for (e.g., '/users', 'chat/completions')
            method: HTTP method filter (GET, POST, etc.)
            
        Returns:
            API documentation and examples
        """
        payload = {
            'api': api_name,
            'endpoint': endpoint_pattern,
            'method': method.upper() if method else "",
            'include_examples': True
        }
        
        return self._make_request('/api', payload)

    def get_examples(self, technology: str, use_case: str = "") -> Dict[str, Any]:
        """
        Get code examples for specific technologies and use cases
        
        Args:
            technology: Technology name (e.g., 'typescript', 'python', 'react')
            use_case: Specific use case (e.g., 'authentication', 'database-query')
            
        Returns:
            Code examples and best practices
        """
        payload = {
            'technology': technology,
            'use_case': use_case,
            'format': 'code_snippets'
        }
        
        return self._make_request('/examples', payload)

    def get_best_practices(self, domain: str, framework: str = "") -> Dict[str, Any]:
        """
        Get best practices for a specific domain or framework
        
        Args:
            domain: Domain area (e.g., 'security', 'performance', 'testing')
            framework: Specific framework (e.g., 'firebase', 'react', 'nodejs')
            
        Returns:
            Best practices and guidelines
        """
        payload = {
            'domain': domain,
            'framework': framework,
            'include_antipatterns': True
        }
        
        return self._make_request('/best-practices', payload)

    def search_errors(self, error_message: str, technology: str = "") -> Dict[str, Any]:
        """
        Search for solutions to specific error messages
        
        Args:
            error_message: The error message or pattern
            technology: Technology context (e.g., 'firebase', 'typescript')
            
        Returns:
            Common solutions and troubleshooting steps
        """
        payload = {
            'error': error_message,
            'technology': technology,
            'include_solutions': True,
            'include_prevention': True
        }
        
        return self._make_request('/errors', payload)

# Convenience functions for direct usage
def query_ref(endpoint: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Simple function for direct MCP queries
    """
    client = RefToolsClient()
    return client._make_request(endpoint, payload)

def get_docs(library: str, query: str = "", max_tokens: int = 2000) -> Dict[str, Any]:
    """Convenience function for documentation lookup"""
    client = RefToolsClient()
    return client.get_docs(library, query, max_tokens)

def search_api(api_name: str, endpoint_pattern: str = "", method: str = "") -> Dict[str, Any]:
    """Convenience function for API search"""
    client = RefToolsClient()
    return client.search_api(api_name, endpoint_pattern, method)

def get_examples(technology: str, use_case: str = "") -> Dict[str, Any]:
    """Convenience function for code examples"""
    client = RefToolsClient()
    return client.get_examples(technology, use_case)

def get_best_practices(domain: str, framework: str = "") -> Dict[str, Any]:
    """Convenience function for best practices"""
    client = RefToolsClient()
    return client.get_best_practices(domain, framework)

def search_errors(error_message: str, technology: str = "") -> Dict[str, Any]:
    """Convenience function for error resolution"""
    client = RefToolsClient()
    return client.search_errors(error_message, technology)

# Exception classes
class RefToolsConnectionError(Exception):
    """Raised when unable to connect to Ref-Tools MCP service"""
    pass

class RefToolsAPIError(Exception):
    """Raised when MCP service returns an API error"""
    pass

# Global client instance for easy access
_default_client = None

def get_default_client() -> RefToolsClient:
    """Get or create the default client instance"""
    global _default_client
    if _default_client is None:
        _default_client = RefToolsClient()
    return _default_client

# Agent integration helpers
class AgentRefToolsHelper:
    """
    Helper class for integrating Ref-Tools into agent workflows
    """
    
    def __init__(self, agent_name: str = "unknown"):
        self.agent_name = agent_name
        self.client = RefToolsClient()
    
    def lookup_for_task(self, task_description: str, technologies: List[str] = None) -> Dict[str, Any]:
        """
        Intelligent lookup based on agent task and required technologies
        """
        if not technologies:
            technologies = self._extract_technologies(task_description)
        
        results = {
            'task': task_description,
            'agent': self.agent_name,
            'technologies': technologies,
            'documentation': {},
            'examples': {},
            'best_practices': {}
        }
        
        for tech in technologies:
            try:
                # Get docs for each technology
                results['documentation'][tech] = self.client.get_docs(tech, task_description)
                
                # Get relevant examples
                results['examples'][tech] = self.client.get_examples(tech, task_description)
                
                # Get best practices
                results['best_practices'][tech] = self.client.get_best_practices(tech)
                
            except Exception as e:
                logger.warning(f"Failed to get info for {tech}: {e}")
                results['documentation'][tech] = {'error': str(e)}
        
        return results
    
    def _extract_technologies(self, task_description: str) -> List[str]:
        """Extract likely technologies from task description"""
        tech_keywords = {
            'firebase': ['firebase', 'firestore', 'functions'],
            'typescript': ['typescript', 'ts', 'type'],
            'python': ['python', 'py', 'django', 'flask'],
            'react': ['react', 'jsx', 'component'],
            'nodejs': ['node', 'express', 'npm'],
            'openai': ['openai', 'gpt', 'ai', 'llm']
        }
        
        found_techs = []
        task_lower = task_description.lower()
        
        for tech, keywords in tech_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                found_techs.append(tech)
        
        return found_techs or ['general']

if __name__ == "__main__":
    # Quick test of the client
    try:
        client = RefToolsClient()
        health = client.health_check()
        print(f"Ref-Tools MCP Health: {health}")
        
        # Example usage
        docs = get_docs('firebase', 'authentication')
        print(f"Firebase auth docs: {docs.get('summary', 'No summary available')}")
        
    except Exception as e:
        print(f"Error testing Ref-Tools client: {e}")
