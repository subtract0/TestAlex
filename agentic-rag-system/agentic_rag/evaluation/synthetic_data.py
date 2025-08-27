"""
Synthetic query generation for RAG system evaluation.

This module provides comprehensive synthetic data generation capabilities
for creating realistic test queries and golden answer datasets.
"""

import random
import uuid
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from pydantic import BaseModel, Field


class QueryType(str, Enum):
    """Types of queries for categorization."""
    FACTUAL = "factual"
    DEFINITION = "definition"
    COMPARISON = "comparison"
    PROCEDURAL = "procedural"
    ANALYTICAL = "analytical"
    EXPLORATORY = "exploratory"
    CODE_SEARCH = "code_search"
    TROUBLESHOOTING = "troubleshooting"


class QueryComplexity(str, Enum):
    """Query complexity levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class QueryPattern:
    """Template pattern for generating synthetic queries."""
    template: str
    query_type: QueryType
    complexity: QueryComplexity
    domain: str
    variables: List[str]
    expected_tool: Optional[str] = None


class SyntheticQuery(BaseModel):
    """A synthetic query with associated metadata and golden answers."""
    
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query_text: str = Field(..., description="The generated query text")
    query_type: QueryType = Field(..., description="Type of query")
    complexity: QueryComplexity = Field(..., description="Complexity level")
    domain: str = Field(..., description="Domain/category")
    
    # Expected results
    relevant_documents: List[str] = Field(
        default_factory=list,
        description="Document IDs that should be relevant"
    )
    golden_answer: Optional[str] = Field(None, description="Expected answer text")
    expected_tool: Optional[str] = Field(None, description="Tool expected to perform best")
    
    # Generation metadata
    pattern_used: Optional[str] = Field(None, description="Template pattern used")
    generation_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters used during generation"
    )


class QueryGenerator:
    """Generates synthetic queries based on predefined patterns and templates."""
    
    def __init__(self):
        self.patterns = self._load_default_patterns()
        self.domain_vocabularies = self._load_domain_vocabularies()
    
    def _load_default_patterns(self) -> List[QueryPattern]:
        """Load default query patterns for different domains and types."""
        return [
            # Factual queries
            QueryPattern(
                template="What is {concept}?",
                query_type=QueryType.FACTUAL,
                complexity=QueryComplexity.SIMPLE,
                domain="general",
                variables=["concept"],
                expected_tool="vector_search"
            ),
            QueryPattern(
                template="How does {system} work?",
                query_type=QueryType.FACTUAL,
                complexity=QueryComplexity.MEDIUM,
                domain="technical",
                variables=["system"],
                expected_tool="vector_search"
            ),
            QueryPattern(
                template="What are the main differences between {item1} and {item2}?",
                query_type=QueryType.COMPARISON,
                complexity=QueryComplexity.MEDIUM,
                domain="general",
                variables=["item1", "item2"],
                expected_tool="vector_search"
            ),
            
            # Procedural queries
            QueryPattern(
                template="How to {action} in {context}?",
                query_type=QueryType.PROCEDURAL,
                complexity=QueryComplexity.MEDIUM,
                domain="how_to",
                variables=["action", "context"],
                expected_tool="vector_search"
            ),
            QueryPattern(
                template="Step by step guide to {task}",
                query_type=QueryType.PROCEDURAL,
                complexity=QueryComplexity.COMPLEX,
                domain="tutorial",
                variables=["task"],
                expected_tool="vector_search"
            ),
            
            # Code search queries
            QueryPattern(
                template="Find {function_type} function in {programming_language}",
                query_type=QueryType.CODE_SEARCH,
                complexity=QueryComplexity.SIMPLE,
                domain="programming",
                variables=["function_type", "programming_language"],
                expected_tool="grep_search"
            ),
            QueryPattern(
                template="Show me examples of {pattern} implementation",
                query_type=QueryType.CODE_SEARCH,
                complexity=QueryComplexity.MEDIUM,
                domain="programming",
                variables=["pattern"],
                expected_tool="grep_search"
            ),
            QueryPattern(
                template="class {class_name} definition",
                query_type=QueryType.CODE_SEARCH,
                complexity=QueryComplexity.SIMPLE,
                domain="programming",
                variables=["class_name"],
                expected_tool="grep_search"
            ),
            
            # Data queries
            QueryPattern(
                template="Find all {entity_type} where {attribute} is {value}",
                query_type=QueryType.ANALYTICAL,
                complexity=QueryComplexity.MEDIUM,
                domain="data",
                variables=["entity_type", "attribute", "value"],
                expected_tool="sql_query"
            ),
            QueryPattern(
                template="Count {entity_type} by {grouping_field}",
                query_type=QueryType.ANALYTICAL,
                complexity=QueryComplexity.MEDIUM,
                domain="data",
                variables=["entity_type", "grouping_field"],
                expected_tool="sql_query"
            ),
            QueryPattern(
                template="Show statistics for {metric} in {dataset}",
                query_type=QueryType.ANALYTICAL,
                complexity=QueryComplexity.COMPLEX,
                domain="data",
                variables=["metric", "dataset"],
                expected_tool="sql_query"
            ),
            
            # Troubleshooting queries
            QueryPattern(
                template="Why is {system} {problem_type}?",
                query_type=QueryType.TROUBLESHOOTING,
                complexity=QueryComplexity.COMPLEX,
                domain="technical",
                variables=["system", "problem_type"],
                expected_tool="vector_search"
            ),
            QueryPattern(
                template="How to fix {error_message}",
                query_type=QueryType.TROUBLESHOOTING,
                complexity=QueryComplexity.MEDIUM,
                domain="technical",
                variables=["error_message"],
                expected_tool="grep_search"
            ),
            
            # Definition queries
            QueryPattern(
                template="Define {technical_term} in {context}",
                query_type=QueryType.DEFINITION,
                complexity=QueryComplexity.SIMPLE,
                domain="technical",
                variables=["technical_term", "context"],
                expected_tool="vector_search"
            ),
            QueryPattern(
                template="Explain the concept of {concept} with examples",
                query_type=QueryType.DEFINITION,
                complexity=QueryComplexity.MEDIUM,
                domain="educational",
                variables=["concept"],
                expected_tool="vector_search"
            ),
        ]
    
    def _load_domain_vocabularies(self) -> Dict[str, Dict[str, List[str]]]:
        """Load vocabulary lists for different domains and variable types."""
        return {
            "technical": {
                "concept": ["machine learning", "neural networks", "databases", "algorithms", 
                           "data structures", "cloud computing", "microservices", "APIs"],
                "system": ["neural network", "database", "web server", "load balancer",
                          "authentication system", "cache", "message queue", "container"],
                "technical_term": ["recursion", "polymorphism", "encapsulation", "inheritance",
                                 "abstraction", "middleware", "scalability", "latency"],
                "context": ["software engineering", "web development", "data science",
                           "machine learning", "system design", "database management"],
                "problem_type": ["not responding", "throwing errors", "running slowly",
                               "using too much memory", "crashing", "timing out"],
                "error_message": ["connection refused", "out of memory", "null pointer exception",
                                "timeout error", "authentication failed", "file not found"]
            },
            "programming": {
                "function_type": ["sorting", "searching", "validation", "parsing",
                                "formatting", "conversion", "authentication", "encryption"],
                "programming_language": ["Python", "JavaScript", "Java", "Go", "Rust",
                                       "TypeScript", "C++", "SQL"],
                "pattern": ["singleton pattern", "factory pattern", "observer pattern",
                           "decorator pattern", "strategy pattern", "MVC pattern"],
                "class_name": ["UserManager", "DataProcessor", "RequestHandler", "Logger",
                             "ConfigManager", "CacheManager", "EventEmitter", "Validator"]
            },
            "data": {
                "entity_type": ["users", "orders", "products", "transactions", "customers",
                              "employees", "projects", "tasks", "events", "sessions"],
                "attribute": ["status", "category", "date", "price", "quantity", "type",
                            "priority", "department", "region", "active"],
                "value": ["active", "pending", "completed", "high", "low", "medium",
                        "true", "false", "null", "recent"],
                "grouping_field": ["department", "category", "status", "date", "region",
                                 "type", "priority", "month", "year", "user_id"],
                "metric": ["revenue", "count", "average", "total", "percentage",
                         "growth rate", "conversion rate", "response time"],
                "dataset": ["sales data", "user analytics", "performance metrics",
                          "transaction logs", "customer feedback", "system logs"]
            },
            "general": {
                "concept": ["artificial intelligence", "blockchain", "cybersecurity",
                           "data privacy", "sustainability", "remote work", "automation"],
                "item1": ["REST", "GraphQL", "SQL", "NoSQL", "Docker", "Kubernetes"],
                "item2": ["SOAP", "REST", "MongoDB", "PostgreSQL", "virtual machines", "containers"],
                "action": ["deploy", "configure", "optimize", "secure", "monitor",
                         "backup", "migrate", "integrate", "troubleshoot", "scale"],
                "context": ["production environment", "cloud platform", "local development",
                          "CI/CD pipeline", "staging environment", "microservices architecture"]
            },
            "how_to": {
                "action": ["set up", "configure", "deploy", "optimize", "secure", "monitor",
                         "backup", "migrate", "integrate", "debug"],
                "context": ["Docker container", "Kubernetes cluster", "AWS infrastructure",
                          "CI/CD pipeline", "database", "web application", "API"],
                "task": ["setting up a development environment", "deploying to production",
                        "configuring authentication", "implementing caching", "setting up monitoring",
                        "creating a backup strategy", "optimizing database performance"]
            },
            "educational": {
                "concept": ["machine learning", "data structures", "algorithms", "design patterns",
                           "system architecture", "database design", "security principles",
                           "performance optimization", "testing strategies"]
            }
        }
    
    def generate_query(self, 
                      pattern: Optional[QueryPattern] = None,
                      domain: Optional[str] = None,
                      query_type: Optional[QueryType] = None,
                      complexity: Optional[QueryComplexity] = None) -> SyntheticQuery:
        """Generate a single synthetic query based on constraints."""
        
        # Select pattern based on constraints
        if pattern is None:
            available_patterns = self.patterns
            
            if domain:
                available_patterns = [p for p in available_patterns if p.domain == domain]
            if query_type:
                available_patterns = [p for p in available_patterns if p.query_type == query_type]
            if complexity:
                available_patterns = [p for p in available_patterns if p.complexity == complexity]
            
            if not available_patterns:
                available_patterns = self.patterns
            
            pattern = random.choice(available_patterns)
        
        # Generate variable values
        variables = {}
        domain_vocab = self.domain_vocabularies.get(pattern.domain, {})
        
        for var in pattern.variables:
            if var in domain_vocab:
                variables[var] = random.choice(domain_vocab[var])
            else:
                # Fallback to generic values
                variables[var] = f"sample_{var}"
        
        # Generate query text
        query_text = pattern.template.format(**variables)
        
        # Create synthetic query
        synthetic_query = SyntheticQuery(
            query_text=query_text,
            query_type=pattern.query_type,
            complexity=pattern.complexity,
            domain=pattern.domain,
            expected_tool=pattern.expected_tool,
            pattern_used=pattern.template,
            generation_params=variables
        )
        
        return synthetic_query
    
    def generate_batch(self, 
                      count: int = 100,
                      domain_distribution: Optional[Dict[str, float]] = None,
                      complexity_distribution: Optional[Dict[QueryComplexity, float]] = None) -> List[SyntheticQuery]:
        """Generate a batch of synthetic queries with specified distributions."""
        
        # Default distributions
        if domain_distribution is None:
            domain_distribution = {
                "technical": 0.3,
                "programming": 0.2,
                "data": 0.2,
                "general": 0.15,
                "how_to": 0.1,
                "educational": 0.05
            }
        
        if complexity_distribution is None:
            complexity_distribution = {
                QueryComplexity.SIMPLE: 0.4,
                QueryComplexity.MEDIUM: 0.4,
                QueryComplexity.COMPLEX: 0.2
            }
        
        queries = []
        
        for _ in range(count):
            # Sample domain and complexity
            domain = self._sample_from_distribution(domain_distribution)
            complexity = self._sample_from_distribution(complexity_distribution)
            
            # Generate query
            query = self.generate_query(domain=domain, complexity=complexity)
            queries.append(query)
        
        return queries
    
    def _sample_from_distribution(self, distribution: Dict[Any, float]) -> Any:
        """Sample an item from a probability distribution."""
        items = list(distribution.keys())
        weights = list(distribution.values())
        return random.choices(items, weights=weights)[0]


class GoldenDatasetGenerator:
    """Generates golden answer datasets for evaluation."""
    
    def __init__(self):
        self.query_generator = QueryGenerator()
    
    def create_golden_dataset(self, 
                             queries: List[SyntheticQuery],
                             document_pool: List[str],
                             relevance_probability: float = 0.3) -> List[SyntheticQuery]:
        """Create golden dataset by assigning relevant documents to queries."""
        
        enhanced_queries = []
        
        for query in queries:
            # Copy the query
            enhanced_query = query.copy(deep=True)
            
            # Assign relevant documents based on query characteristics
            relevant_docs = self._assign_relevant_documents(
                query, document_pool, relevance_probability
            )
            enhanced_query.relevant_documents = relevant_docs
            
            # Generate golden answer if possible
            golden_answer = self._generate_golden_answer(query)
            enhanced_query.golden_answer = golden_answer
            
            enhanced_queries.append(enhanced_query)
        
        return enhanced_queries
    
    def _assign_relevant_documents(self, 
                                  query: SyntheticQuery, 
                                  document_pool: List[str],
                                  relevance_probability: float) -> List[str]:
        """Assign relevant documents to a query based on its characteristics."""
        
        # Determine number of relevant documents based on complexity
        if query.complexity == QueryComplexity.SIMPLE:
            num_relevant = random.randint(1, 3)
        elif query.complexity == QueryComplexity.MEDIUM:
            num_relevant = random.randint(2, 5)
        else:  # COMPLEX
            num_relevant = random.randint(3, 7)
        
        # Sample relevant documents
        num_relevant = min(num_relevant, len(document_pool))
        relevant_docs = random.sample(document_pool, num_relevant)
        
        return relevant_docs
    
    def _generate_golden_answer(self, query: SyntheticQuery) -> Optional[str]:
        """Generate a golden answer for a query when possible."""
        
        # Simple template-based answer generation
        if query.query_type == QueryType.DEFINITION:
            return f"{query.generation_params.get('concept', 'The concept')} is a fundamental concept in {query.domain}."
        
        elif query.query_type == QueryType.PROCEDURAL:
            action = query.generation_params.get('action', 'perform this task')
            return f"To {action}, follow these steps: 1. Prepare the environment, 2. Execute the action, 3. Verify the result."
        
        elif query.query_type == QueryType.COMPARISON:
            item1 = query.generation_params.get('item1', 'first item')
            item2 = query.generation_params.get('item2', 'second item')
            return f"The main differences between {item1} and {item2} are in their architecture, performance, and use cases."
        
        # For other query types, return None (would need more sophisticated generation)
        return None


# Utility functions for easy access

def create_synthetic_queries(count: int = 100, 
                           domain_distribution: Optional[Dict[str, float]] = None,
                           complexity_distribution: Optional[Dict[QueryComplexity, float]] = None) -> List[SyntheticQuery]:
    """Create a batch of synthetic queries with specified distributions."""
    generator = QueryGenerator()
    return generator.generate_batch(count, domain_distribution, complexity_distribution)


def create_golden_dataset(queries: List[SyntheticQuery],
                         document_pool: List[str],
                         relevance_probability: float = 0.3) -> List[SyntheticQuery]:
    """Create a golden dataset from synthetic queries and document pool."""
    generator = GoldenDatasetGenerator()
    return generator.create_golden_dataset(queries, document_pool, relevance_probability)


def save_synthetic_dataset(queries: List[SyntheticQuery], filepath: str):
    """Save synthetic dataset to JSON file."""
    data = [query.dict() for query in queries]
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_synthetic_dataset(filepath: str) -> List[SyntheticQuery]:
    """Load synthetic dataset from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return [SyntheticQuery(**item) for item in data]
