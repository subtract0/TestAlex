#!/usr/bin/env python3
"""Quick test script to validate the Agentic RAG system works."""

import asyncio
import os
from pathlib import Path

# Test imports
try:
    from agentic_rag import (
        create_default_router,
        create_vector_search_tool,
        QueryType,
        ToolType,
    )
    from agentic_rag.core.models import ModelConfig
    from agentic_rag.core.router import AdvancedQueryRouter
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)


async def test_query_routing():
    """Test the query routing functionality."""
    print("\n🧠 Testing Query Routing...")
    
    try:
        router = create_default_router()
        
        test_queries = [
            "How does machine learning work?",
            "find function calculate_metrics",  
            "What are the differences between Python and JavaScript?",
            "Summarize the meeting notes from yesterday"
        ]
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            intent = await router.route_query(query)
            print(f"   Type: {intent.query_type.value}")
            print(f"   Confidence: {intent.confidence:.3f}")
            print(f"   Tools: {[t.value for t in intent.suggested_tools]}")
            
        print("✅ Query routing tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Query routing failed: {e}")
        return False


async def test_vector_search_setup():
    """Test vector search tool setup (without API calls)."""
    print("\n🔍 Testing Vector Search Setup...")
    
    try:
        # Test tool creation
        tool = create_vector_search_tool("./test_db")
        print("✅ Vector search tool created")
        
        # Test sample data preparation
        sample_data = [
            {
                "id": "test1",
                "content": "This is a test document about artificial intelligence and machine learning.",
                "title": "AI Test Doc",
                "source": "test"
            }
        ]
        
        print("✅ Sample data prepared")
        print("⚠️  Note: Actual database creation requires OpenAI API key")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector search setup failed: {e}")
        return False


def test_model_validation():
    """Test Pydantic model validation."""
    print("\n📋 Testing Model Validation...")
    
    try:
        from agentic_rag.core.models import (
            QueryIntent, Citation, RetrievalResult, 
            ConfidenceLevel, QueryType, ToolType
        )
        
        # Test QueryIntent creation
        intent = QueryIntent(
            query="test query",
            query_type=QueryType.SEARCH,
            chain_of_thought="This is a test reasoning",
            confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            entities=["test"],
            filters={},
            suggested_tools=[ToolType.VECTOR_SEARCH]
        )
        print("✅ QueryIntent validation works")
        
        # Test Citation creation
        citation = Citation(
            source_id="test_source",
            relevance_score=0.9,
            snippet="This is a test snippet"
        )
        print("✅ Citation validation works")
        
        # Test RetrievalResult creation
        result = RetrievalResult(
            tool_used=ToolType.VECTOR_SEARCH,
            query="test",
            content="test content",
            citations=[citation],
            confidence=0.8,
            latency_ms=100.0
        )
        print("✅ RetrievalResult validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Model validation failed: {e}")
        return False


def test_cli_availability():
    """Test CLI command availability."""
    print("\n💻 Testing CLI Availability...")
    
    try:
        from agentic_rag.cli import app
        print("✅ CLI app imported successfully")
        
        # Test CLI help (without actually running it)
        print("✅ CLI should be available as 'rag' command after installation")
        
        return True
        
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Agentic RAG System - Quick Test Suite")
    print("=" * 50)
    
    tests = [
        ("Model Validation", test_model_validation),
        ("Query Routing", test_query_routing),
        ("Vector Search Setup", test_vector_search_setup),
        ("CLI Availability", test_cli_availability),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\n📋 Next steps:")
        print("1. Set your OPENAI_API_KEY environment variable")
        print("2. Run: rag init-db")
        print("3. Run: rag demo")
        print("4. Explore the full CLI with: rag --help")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
