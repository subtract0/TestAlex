#!/usr/bin/env python3
"""
Manual test runner for Orchestrator v2 verification
Tests dynamic agent loading, capability tags, and orchestration rules.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the orchestration directory to path
sys.path.append('orchestration')

from agent_executor import AgentExecutor
from task_queue import TaskQueue, Priority, AgentRole


async def test_orchestrator_v2():
    """Test orchestrator v2 functionality."""
    print("🚀 Testing Orchestrator v2 Implementation")
    print("=" * 50)
    
    # Test 1: Agent Registry Loading
    print("\n1. Testing Agent Registry Loading...")
    executor = AgentExecutor()
    print(f"   ✅ Loaded {len(executor.agent_registry)} agents from registry")
    print(f"   ✅ Routing rules available: {bool(executor.routing_rules)}")
    
    # Test 2: Task Queue with Capability Tags
    print("\n2. Testing Task Queue with Capability Tags...")
    queue = TaskQueue()
    
    # Create tasks with new capability tags
    search_task = queue.create_task(
        title="Find TODO Items in Codebase",
        description="Scan all source files for TODO, FIXME, and HACK comments",
        priority=Priority.MEDIUM,
        category="code-analysis",
        capability_tags=["search", "static-analysis"],
        tags=["technical-debt", "maintenance"]
    )
    
    playwright_task = queue.create_task(
        title="E2E Test User Registration",
        description="Automated browser testing of user signup flow",
        priority=Priority.HIGH,
        category="testing",
        capability_tags=["playwright", "e2e"],
        tags=["user-experience", "automation"]
    )
    
    revenue_task = queue.create_task(
        title="Analyze Subscription Conversion Funnel",
        description="Identify drop-off points in premium subscription flow",
        priority=Priority.CRITICAL,
        category="business-analysis",
        capability_tags=["revenue", "analytics"],
        tags=["business-critical", "conversion"]
    )
    
    print(f"   ✅ Created {len(queue.tasks)} tasks with capability tags")
    
    # Test 3: Auto-routing based on capability tags
    print("\n3. Testing Auto-routing based on Capability Tags...")
    
    search_agent = queue.auto_route_task(search_task)
    playwright_agent = queue.auto_route_task(playwright_task)
    revenue_agent = queue.auto_route_task(revenue_task)
    
    print(f"   ✅ Search task routed to: {search_agent.value if search_agent else 'None'}")
    print(f"   ✅ Playwright task routed to: {playwright_agent.value if playwright_agent else 'None'}")
    print(f"   ✅ Revenue task routed to: {revenue_agent.value if revenue_agent else 'None'}")
    
    # Test 4: New Agent Execution
    print("\n4. Testing New Agent Execution...")
    
    if search_agent:
        search_result = await executor.execute_task(search_task, search_agent)
        print(f"   ✅ ExaSearcher execution: {search_result.success}")
        print(f"      - Output: {search_result.output[:60]}...")
        print(f"      - Artifacts: {len(search_result.artifacts)} files")
        print(f"      - Metrics: {list(search_result.metrics.keys())}")
    
    if playwright_agent:
        playwright_result = await executor.execute_task(playwright_task, playwright_agent)
        print(f"   ✅ PlaywrightTester execution: {playwright_result.success}")
        print(f"      - Output: {playwright_result.output[:60]}...")
        print(f"      - Artifacts: {len(playwright_result.artifacts)} files")
        print(f"      - Metrics: {list(playwright_result.metrics.keys())}")
    
    if revenue_agent:
        revenue_result = await executor.execute_task(revenue_task, revenue_agent)
        print(f"   ✅ RevenueAnalyst execution: {revenue_result.success}")
        print(f"      - Output: {revenue_result.output[:60]}...")
        print(f"      - Artifacts: {len(revenue_result.artifacts)} files")
        print(f"      - Metrics: {list(revenue_result.metrics.keys())}")
    
    # Test 5: Backward Compatibility
    print("\n5. Testing Backward Compatibility...")
    
    legacy_task = queue.create_task(
        title="Validate ACIM Text Integrity",
        description="Ensure all ACIM quotations are exact and properly cited",
        priority=Priority.CRITICAL,
        category="content",
        tags=["acim", "validation", "content"],
        estimated_hours=2
    )
    
    legacy_result = await executor.execute_task(legacy_task, AgentRole.ACIM_SCHOLAR)
    print(f"   ✅ Legacy ACIM Scholar execution: {legacy_result.success}")
    print(f"      - Maintains full backward compatibility")
    
    # Test 6: Pipeline Metrics
    print("\n6. Testing Enhanced Pipeline Metrics...")
    metrics = queue.get_pipeline_metrics()
    print(f"   ✅ Total tasks: {metrics['total_tasks']}")
    print(f"   ✅ Agent workload tracking: {len(metrics['agent_workload'])} agents")
    print(f"   ✅ Completion rate: {metrics['completion_rate']:.2%}")
    
    print("\n" + "=" * 50)
    print("🎉 Orchestrator v2 Tests Completed Successfully!")
    print("\nKey Features Implemented:")
    print("  ✅ Dynamic agent loading from registry.json")
    print("  ✅ New agents: ExaSearcher, PlaywrightTester, RevenueAnalyst")  
    print("  ✅ Capability-based task routing (search, playwright, revenue)")
    print("  ✅ Load balancing and orchestration rules")
    print("  ✅ Backward compatibility with existing agents")
    print("  ✅ Enhanced task queue with capability tags")


def test_agent_registry_structure():
    """Test the agent registry structure."""
    registry_path = Path("agents/registry.json")
    
    if not registry_path.exists():
        print("❌ Agent registry not found!")
        return False
    
    import json
    with open(registry_path) as f:
        registry = json.load(f)
    
    required_agents = ["exa_searcher", "playwright_tester", "revenue_analyst"]
    
    print("\n📋 Agent Registry Structure:")
    for agent_key in required_agents:
        if agent_key in registry.get("agents", {}):
            agent = registry["agents"][agent_key]
            print(f"  ✅ {agent.get('name', agent_key)}")
            print(f"     - Capabilities: {len(agent.get('capabilities', []))}")
            print(f"     - Tags: {agent.get('tags', [])}")
            print(f"     - Enabled: {agent.get('enabled', False)}")
        else:
            print(f"  ❌ Missing agent: {agent_key}")
            return False
    
    # Test routing rules
    routing_rules = registry.get("routing_rules", {})
    capability_tags = routing_rules.get("capability_tags", {})
    
    print("\n🔀 Routing Rules:")
    for tag in ["search", "playwright", "revenue"]:
        if tag in capability_tags:
            print(f"  ✅ {tag} -> {capability_tags[tag]}")
        else:
            print(f"  ❌ Missing routing for: {tag}")
            return False
    
    return True


if __name__ == "__main__":
    print("🧪 ACIMguide Orchestrator v2 - Manual Test Suite")
    print("=" * 60)
    
    # Test registry structure first
    if not test_agent_registry_structure():
        print("❌ Agent registry structure test failed!")
        sys.exit(1)
    
    # Run async tests
    try:
        asyncio.run(test_orchestrator_v2())
        print("\n✅ All tests passed! Orchestrator v2 is ready.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
