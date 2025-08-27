"""
Golden dataset utilities and ground truth annotation helpers.

This module provides utilities for creating and managing golden datasets
for evaluation, including document indexing and relevance annotation.
"""

import json
import csv
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass
import uuid

from .synthetic_data import SyntheticQuery


@dataclass
class DocumentReference:
    """Reference to a document with metadata."""
    doc_id: str
    title: str
    content: str
    source_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class RelevanceAnnotation:
    """Relevance annotation for query-document pair."""
    query_id: str
    doc_id: str
    relevance_score: int  # 0=not relevant, 1=somewhat relevant, 2=highly relevant
    annotator: str = "system"
    confidence: float = 1.0
    notes: str = ""


class GoldenDatasetManager:
    """Manages golden datasets for evaluation."""
    
    def __init__(self, dataset_path: Optional[str] = None):
        """Initialize with optional dataset path."""
        self.dataset_path = Path(dataset_path) if dataset_path else Path("./evaluation_data")
        self.dataset_path.mkdir(exist_ok=True)
        
        self.documents: Dict[str, DocumentReference] = {}
        self.queries: Dict[str, SyntheticQuery] = {}
        self.annotations: List[RelevanceAnnotation] = []
    
    def add_document(self, 
                    doc_id: str, 
                    title: str, 
                    content: str,
                    source_path: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> DocumentReference:
        """Add a document to the dataset."""
        
        doc_ref = DocumentReference(
            doc_id=doc_id,
            title=title,
            content=content,
            source_path=source_path,
            metadata=metadata or {}
        )
        
        self.documents[doc_id] = doc_ref
        return doc_ref
    
    def add_documents_from_directory(self, 
                                   directory: str, 
                                   file_patterns: List[str] = ["*.txt", "*.md"],
                                   content_extractors: Dict[str, callable] = None) -> int:
        """Add documents from a directory."""
        
        if content_extractors is None:
            content_extractors = {
                ".txt": lambda p: p.read_text(encoding='utf-8'),
                ".md": lambda p: p.read_text(encoding='utf-8'),
            }
        
        directory_path = Path(directory)
        added_count = 0
        
        for pattern in file_patterns:
            for file_path in directory_path.rglob(pattern):
                if file_path.is_file():
                    try:
                        # Extract content based on file extension
                        extractor = content_extractors.get(file_path.suffix)
                        if extractor:
                            content = extractor(file_path)
                        else:
                            content = file_path.read_text(encoding='utf-8')
                        
                        # Generate document ID from file path hash
                        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()
                        
                        # Add document
                        self.add_document(
                            doc_id=doc_id,
                            title=file_path.name,
                            content=content,
                            source_path=str(file_path),
                            metadata={
                                "file_extension": file_path.suffix,
                                "file_size": file_path.stat().st_size,
                                "relative_path": str(file_path.relative_to(directory_path))
                            }
                        )
                        added_count += 1
                        
                    except Exception as e:
                        print(f"Warning: Could not process {file_path}: {e}")
        
        return added_count
    
    def add_query(self, query: SyntheticQuery):
        """Add a synthetic query to the dataset."""
        self.queries[query.query_id] = query
    
    def add_queries(self, queries: List[SyntheticQuery]):
        """Add multiple queries to the dataset."""
        for query in queries:
            self.add_query(query)
    
    def annotate_relevance(self,
                         query_id: str,
                         doc_id: str,
                         relevance_score: int,
                         annotator: str = "system",
                         confidence: float = 1.0,
                         notes: str = "") -> RelevanceAnnotation:
        """Annotate relevance between a query and document."""
        
        annotation = RelevanceAnnotation(
            query_id=query_id,
            doc_id=doc_id,
            relevance_score=relevance_score,
            annotator=annotator,
            confidence=confidence,
            notes=notes
        )
        
        self.annotations.append(annotation)
        return annotation
    
    def auto_annotate_relevance(self, 
                              use_content_similarity: bool = True,
                              use_keyword_matching: bool = True,
                              similarity_threshold: float = 0.3) -> int:
        """Automatically annotate relevance using heuristics."""
        
        annotated_count = 0
        
        for query_id, query in self.queries.items():
            relevant_docs = set()
            
            # Use existing relevant documents from query if available
            if query.relevant_documents:
                for doc_id in query.relevant_documents:
                    if doc_id in self.documents:
                        self.annotate_relevance(query_id, doc_id, 2, "synthetic")
                        annotated_count += 1
                        relevant_docs.add(doc_id)
            
            # Auto-annotate based on content similarity and keyword matching
            for doc_id, document in self.documents.items():
                if doc_id in relevant_docs:
                    continue  # Already annotated
                
                relevance_score = self._calculate_relevance_score(
                    query, document, use_content_similarity, use_keyword_matching
                )
                
                if relevance_score >= similarity_threshold:
                    # Map continuous score to discrete relevance levels
                    if relevance_score >= 0.7:
                        discrete_score = 2  # Highly relevant
                    elif relevance_score >= 0.4:
                        discrete_score = 1  # Somewhat relevant
                    else:
                        discrete_score = 0  # Not relevant
                    
                    if discrete_score > 0:
                        self.annotate_relevance(
                            query_id, 
                            doc_id, 
                            discrete_score, 
                            "auto_heuristic",
                            confidence=relevance_score,
                            notes=f"Auto-annotated with score {relevance_score:.3f}"
                        )
                        annotated_count += 1
        
        return annotated_count
    
    def _calculate_relevance_score(self,
                                 query: SyntheticQuery,
                                 document: DocumentReference,
                                 use_content_similarity: bool,
                                 use_keyword_matching: bool) -> float:
        """Calculate relevance score using various heuristics."""
        
        scores = []
        
        if use_keyword_matching:
            # Simple keyword matching score
            query_terms = set(query.query_text.lower().split())
            doc_terms = set(document.content.lower().split())
            title_terms = set(document.title.lower().split())
            
            # Calculate overlap
            content_overlap = len(query_terms & doc_terms) / len(query_terms) if query_terms else 0
            title_overlap = len(query_terms & title_terms) / len(query_terms) if query_terms else 0
            
            # Boost title matches
            keyword_score = max(content_overlap, title_overlap * 1.5)
            scores.append(keyword_score)
        
        if use_content_similarity:
            # Simple content similarity (could be enhanced with embeddings)
            similarity_score = self._simple_text_similarity(query.query_text, document.content)
            scores.append(similarity_score)
        
        # Domain-specific scoring
        domain_score = self._domain_specific_scoring(query, document)
        if domain_score > 0:
            scores.append(domain_score)
        
        return max(scores) if scores else 0.0
    
    def _simple_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity using term overlap."""
        
        terms1 = set(text1.lower().split())
        terms2 = set(text2.lower().split())
        
        if not terms1 or not terms2:
            return 0.0
        
        intersection = terms1 & terms2
        union = terms1 | terms2
        
        return len(intersection) / len(union)  # Jaccard similarity
    
    def _domain_specific_scoring(self, query: SyntheticQuery, document: DocumentReference) -> float:
        """Apply domain-specific scoring rules."""
        
        score_boost = 0.0
        
        # Code search queries should match code files
        if query.query_type.value == "code_search":
            code_extensions = {".py", ".js", ".java", ".cpp", ".go", ".rs", ".ts"}
            if document.metadata.get("file_extension") in code_extensions:
                score_boost += 0.3
        
        # Data queries should match structured data
        elif query.query_type.value == "analytical":
            data_extensions = {".csv", ".json", ".sql", ".db"}
            if document.metadata.get("file_extension") in data_extensions:
                score_boost += 0.3
        
        # Documentation queries should match documentation files
        elif query.query_type.value in ["definition", "procedural"]:
            doc_extensions = {".md", ".txt", ".rst", ".doc"}
            if document.metadata.get("file_extension") in doc_extensions:
                score_boost += 0.2
        
        return score_boost
    
    def get_relevant_documents(self, query_id: str, min_relevance: int = 1) -> List[str]:
        """Get list of relevant document IDs for a query."""
        
        relevant_docs = []
        for annotation in self.annotations:
            if (annotation.query_id == query_id and 
                annotation.relevance_score >= min_relevance):
                relevant_docs.append(annotation.doc_id)
        
        return relevant_docs
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get statistics about the dataset."""
        
        stats = {
            "total_queries": len(self.queries),
            "total_documents": len(self.documents),
            "total_annotations": len(self.annotations),
            "query_types": {},
            "relevance_distribution": {0: 0, 1: 0, 2: 0},
            "annotator_distribution": {}
        }
        
        # Query type distribution
        for query in self.queries.values():
            query_type = query.query_type.value
            stats["query_types"][query_type] = stats["query_types"].get(query_type, 0) + 1
        
        # Relevance and annotator distribution
        for annotation in self.annotations:
            stats["relevance_distribution"][annotation.relevance_score] += 1
            annotator = annotation.annotator
            stats["annotator_distribution"][annotator] = stats["annotator_distribution"].get(annotator, 0) + 1
        
        return stats
    
    def save_dataset(self, name: str = "golden_dataset"):
        """Save the complete dataset to files."""
        
        dataset_dir = self.dataset_path / name
        dataset_dir.mkdir(exist_ok=True)
        
        # Save documents
        docs_data = {
            doc_id: {
                "title": doc.title,
                "content": doc.content,
                "source_path": doc.source_path,
                "metadata": doc.metadata
            }
            for doc_id, doc in self.documents.items()
        }
        
        with open(dataset_dir / "documents.json", 'w') as f:
            json.dump(docs_data, f, indent=2)
        
        # Save queries
        queries_data = [query.dict() for query in self.queries.values()]
        
        with open(dataset_dir / "queries.json", 'w') as f:
            json.dump(queries_data, f, indent=2, default=str)
        
        # Save annotations
        annotations_data = [
            {
                "query_id": ann.query_id,
                "doc_id": ann.doc_id,
                "relevance_score": ann.relevance_score,
                "annotator": ann.annotator,
                "confidence": ann.confidence,
                "notes": ann.notes
            }
            for ann in self.annotations
        ]
        
        with open(dataset_dir / "annotations.json", 'w') as f:
            json.dump(annotations_data, f, indent=2)
        
        # Save statistics
        stats = self.get_query_statistics()
        with open(dataset_dir / "statistics.json", 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Dataset saved to {dataset_dir}")
        return str(dataset_dir)
    
    def load_dataset(self, name: str = "golden_dataset"):
        """Load a dataset from files."""
        
        dataset_dir = self.dataset_path / name
        
        if not dataset_dir.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")
        
        # Load documents
        with open(dataset_dir / "documents.json", 'r') as f:
            docs_data = json.load(f)
        
        self.documents = {}
        for doc_id, doc_data in docs_data.items():
            self.documents[doc_id] = DocumentReference(
                doc_id=doc_id,
                title=doc_data["title"],
                content=doc_data["content"],
                source_path=doc_data.get("source_path"),
                metadata=doc_data.get("metadata", {})
            )
        
        # Load queries
        with open(dataset_dir / "queries.json", 'r') as f:
            queries_data = json.load(f)
        
        self.queries = {}
        for query_data in queries_data:
            query = SyntheticQuery(**query_data)
            self.queries[query.query_id] = query
        
        # Load annotations
        with open(dataset_dir / "annotations.json", 'r') as f:
            annotations_data = json.load(f)
        
        self.annotations = [
            RelevanceAnnotation(**ann_data) for ann_data in annotations_data
        ]
        
        print(f"Dataset loaded from {dataset_dir}")
    
    def export_for_evaluation(self) -> Tuple[List[SyntheticQuery], Dict[str, str]]:
        """Export queries with updated relevant documents for evaluation."""
        
        # Update queries with relevant documents from annotations
        updated_queries = []
        document_content = {}
        
        for query_id, query in self.queries.items():
            # Get relevant documents from annotations
            relevant_docs = self.get_relevant_documents(query_id, min_relevance=1)
            
            # Update query
            updated_query = query.copy(deep=True)
            updated_query.relevant_documents = relevant_docs
            updated_queries.append(updated_query)
        
        # Create document content mapping
        for doc_id, document in self.documents.items():
            document_content[doc_id] = document.content
        
        return updated_queries, document_content


# Utility functions

def create_golden_dataset_from_directory(directory_path: str,
                                       query_count: int = 100,
                                       dataset_name: str = "generated_dataset") -> str:
    """Create a golden dataset from a directory of documents."""
    
    from .synthetic_data import create_synthetic_queries
    
    # Initialize dataset manager
    manager = GoldenDatasetManager()
    
    # Add documents from directory
    doc_count = manager.add_documents_from_directory(directory_path)
    print(f"Added {doc_count} documents from {directory_path}")
    
    # Generate synthetic queries
    queries = create_synthetic_queries(count=query_count)
    manager.add_queries(queries)
    print(f"Generated {len(queries)} synthetic queries")
    
    # Auto-annotate relevance
    annotation_count = manager.auto_annotate_relevance()
    print(f"Created {annotation_count} relevance annotations")
    
    # Save dataset
    dataset_path = manager.save_dataset(dataset_name)
    
    # Print statistics
    stats = manager.get_query_statistics()
    print(f"\nDataset Statistics:")
    print(f"- Queries: {stats['total_queries']}")
    print(f"- Documents: {stats['total_documents']}")
    print(f"- Annotations: {stats['total_annotations']}")
    print(f"- Query Types: {stats['query_types']}")
    print(f"- Relevance Distribution: {stats['relevance_distribution']}")
    
    return dataset_path


def load_golden_dataset(dataset_name: str, dataset_path: Optional[str] = None) -> GoldenDatasetManager:
    """Load a golden dataset."""
    manager = GoldenDatasetManager(dataset_path)
    manager.load_dataset(dataset_name)
    return manager
