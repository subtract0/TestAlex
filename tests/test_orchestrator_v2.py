#!/usr/bin/env python3
"""
Unit tests for Orchestrator v2 - Agent Registry and Capability-based Routing
Tests dynamic agent loading, capability tags, and orchestration rules.
"""

import asyncio
import json
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the orchestration directory to path for imports
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'orchestration'))

from agent_executor import AgentExecutor, ExecutionResult
from task_queue import TaskQueue, Task, Priority, TaskStatus, AgentRole


class TestAgentRegistryLoading:
    """Test agent registry loading functionality."""
    
    def test_load_agent_registry_success(self):
        """Test successful loading of agent registry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test registry
            registry_data = {
                "agents": {
                    "test_agent": {
                        "name": "Test Agent",
                        "prompt_path": "test/prompt.md",
                        "capabilities": ["test_capability"]
                    }
                },
                "routing_rules": {
                    "capability_tags": {
                        "test": ["test_agent"]
                    }
                }
            }
            
            registry_path = Path(temp_dir) / "agents" / "registry.json"
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f)
            
            executor = AgentExecutor(project_root=temp_dir)
            
            assert len(executor.agent_registry) == 1
            assert "test_agent" in executor.agent_registry
            assert executor.routing_rules["capability_tags"]["test"] == ["test_agent"]
    
    def test_load_agent_registry_missing_file(self):
        """Test handling of missing registry file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            assert executor.agent_registry == {}
            assert executor.routing_rules == {}
    
    def test_load_agent_registry_invalid_json(self):
        """Test handling of invalid JSON in registry."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_path = Path(temp_dir) / "agents" / "registry.json"
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(registry_path, 'w') as f:
                f.write("invalid json {")
            
            executor = AgentExecutor(project_root=temp_dir)
            
            assert executor.agent_registry == {}
            assert executor.routing_rules == {}


class TestNewAgentExecution:
    """Test execution of new agent types."""
    
    @pytest.mark.asyncio
    async def test_exa_searcher_execution(self):
        """Test ExaSearcher agent execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            task = Task(
                id="test_search",
                title="Test Code Search",
                description="Find TODO items in codebase",
                priority=Priority.MEDIUM,
                category="analysis",
                capability_tags=["search"]
            )
            
            result = await executor.execute_exa_searcher_task(task, {}, {})
            
            assert result.success is True
            assert "Static code analysis completed" in result.output
            assert "code_analysis_report.md" in result.artifacts
            assert "todos_found" in result.metrics
    
    @pytest.mark.asyncio
    async def test_playwright_tester_execution(self):
        """Test PlaywrightTester agent execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            task = Task(
                id="test_e2e",
                title="Test E2E Flows",
                description="Execute browser automation tests",
                priority=Priority.HIGH,
                category="testing",
                capability_tags=["playwright"]
            )
            
            result = await executor.execute_playwright_tester_task(task, {}, {})
            
            assert result.success is True
            assert "E2E testing completed" in result.output
            assert "e2e_test_results.html" in result.artifacts
            assert "tests_passed" in result.metrics
    
    @pytest.mark.asyncio
    async def test_revenue_analyst_execution(self):
        """Test RevenueAnalyst agent execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            task = Task(
                id="test_revenue",
                title="Analyze Revenue Funnel",
                description="Optimize conversion rates and pricing",
                priority=Priority.CRITICAL,
                category="business",
                capability_tags=["revenue"]
            )
            
            result = await executor.execute_revenue_analyst_task(task, {}, {})
            
            assert result.success is True
            assert "Revenue analysis completed" in result.output
            assert "funnel_analysis.pdf" in result.artifacts
            assert "conversion_improvement" in result.metrics
    
    @pytest.mark.asyncio
    async def test_generic_agent_execution(self):
        """Test generic agent execution for unknown agents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            task = Task(
                id="test_generic",
                title="Generic Task",
                description="Test unknown agent handling",
                priority=Priority.LOW,
                category="test"
            )
            
            # Mock AgentRole for unknown agent
            unknown_agent = Mock()
            unknown_agent.value = "unknown_agent"
            
            result = await executor.execute_generic_agent_task(task, {"prompt": "You are a helpful assistant."}, {}, unknown_agent)
            
            assert result.success is True
            assert "Successful" in result.output


class TestCapabilityRouting:
    """Test capability-based task routing."""
    
    def test_task_creation_with_capability_tags(self):
        """Test creating tasks with capability tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            queue = TaskQueue(
                storage_path=f"{temp_dir}/tasks.json",
                registry_path=f"{temp_dir}/registry.json"
            )
            
            task = queue.create_task(
                title="Search Code",
                description="Find patterns in codebase",
                priority=Priority.MEDIUM,
                category="analysis",
                capability_tags=["search", "static-analysis"]
            )
            
            assert task.capability_tags == ["search", "static-analysis"]
    
    def test_auto_route_task_with_registry(self):
        """Test automatic task routing based on capability tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test registry
            registry_data = {
                "routing_rules": {
                    "capability_tags": {
                        "search": ["exa_searcher"],
                        "playwright": ["playwright_tester"],
                        "revenue": ["revenue_analyst"]
                    },
                    "load_balancing": {
                        "strategy": "least_loaded"
                    }
                }
            }
            
            registry_path = Path(temp_dir) / "registry.json"
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f)
            
            queue = TaskQueue(
                storage_path=f"{temp_dir}/tasks.json",
                registry_path=str(registry_path)
            )
            
            # Test search task routing
            search_task = Task(
                id="search_test",
                title="Search Test",
                description="Test search routing",
                priority=Priority.MEDIUM,
                category="analysis",
                capability_tags=["search"]
            )
            
            routed_agent = queue.auto_route_task(search_task)
            assert routed_agent == AgentRole.EXA_SEARCHER
            
            # Test playwright task routing
            playwright_task = Task(
                id="playwright_test", 
                title="E2E Test",
                description="Test playwright routing",
                priority=Priority.HIGH,
                category="testing",
                capability_tags=["playwright"]
            )
            
            routed_agent = queue.auto_route_task(playwright_task)
            assert routed_agent == AgentRole.PLAYWRIGHT_TESTER
    
    def test_auto_route_task_load_balancing(self):
        """Test load balancing in task routing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_data = {
                "routing_rules": {
                    "capability_tags": {
                        "testing": ["qa_tester", "playwright_tester"]
                    },
                    "load_balancing": {
                        "strategy": "least_loaded"
                    }
                }
            }
            
            registry_path = Path(temp_dir) / "registry.json"
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f)
            
            queue = TaskQueue(
                storage_path=f"{temp_dir}/tasks.json",
                registry_path=str(registry_path)
            )
            
            # Set different workloads
            queue.agent_workload[AgentRole.QA_TESTER] = 5
            queue.agent_workload[AgentRole.PLAYWRIGHT_TESTER] = 2
            
            testing_task = Task(
                id="test_task",
                title="Testing Task",
                description="Test load balancing",
                priority=Priority.MEDIUM,
                category="testing",
                capability_tags=["testing"]
            )
            
            routed_agent = queue.auto_route_task(testing_task)
            # Should route to PlaywrightTester (lower workload)
            assert routed_agent == AgentRole.PLAYWRIGHT_TESTER
    
    def test_get_next_task_with_routing(self):
        """Test getting next task with capability routing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_data = {
                "routing_rules": {
                    "capability_tags": {
                        "search": ["exa_searcher"]
                    }
                }
            }
            
            registry_path = Path(temp_dir) / "registry.json"
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f)
            
            queue = TaskQueue(
                storage_path=f"{temp_dir}/tasks.json",
                registry_path=str(registry_path)
            )
            
            # Create tasks with capability tags
            search_task = queue.create_task(
                title="Search Task",
                description="Code search task",
                priority=Priority.HIGH,
                category="analysis",
                capability_tags=["search"]
            )
            
            regular_task = queue.create_task(
                title="Regular Task", 
                description="Regular task",
                priority=Priority.MEDIUM,
                category="general"
            )
            
            # Test routing to specific agent
            next_task = queue.get_next_task_with_routing(AgentRole.EXA_SEARCHER)
            assert next_task.id == search_task.id
            
            # Test general task retrieval
            next_task = queue.get_next_task_with_routing()
            assert next_task is not None


class TestOrchestrationRules:
    """Test orchestration rules and priority routing."""
    
    def test_priority_routing_critical_tasks(self):
        """Test routing of critical tasks to appropriate agents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_data = {
                "routing_rules": {
                    "priority_routing": {
                        "critical": ["acim_scholar", "devops_sre", "revenue_analyst"]
                    }
                }
            }
            
            registry_path = Path(temp_dir) / "registry.json"
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f)
            
            queue = TaskQueue(registry_path=str(registry_path))
            
            critical_task = queue.create_task(
                title="Critical ACIM Issue",
                description="Critical content validation issue",
                priority=Priority.CRITICAL,
                category="content",
                tags=["acim", "critical"]
            )
            
            assert critical_task.priority == Priority.CRITICAL
    
    def test_capability_tag_combinations(self):
        """Test tasks with multiple capability tags."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_data = {
                "routing_rules": {
                    "capability_tags": {
                        "search": ["exa_searcher"],
                        "testing": ["qa_tester", "playwright_tester"],
                        "static-analysis": ["exa_searcher"]
                    }
                }
            }
            
            registry_path = Path(temp_dir) / "registry.json"
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f)
            
            queue = TaskQueue(registry_path=str(registry_path))
            
            # Task with multiple capability tags
            multi_task = Task(
                id="multi_test",
                title="Multi-capability Task",
                description="Task requiring multiple capabilities",
                priority=Priority.MEDIUM,
                category="analysis",
                capability_tags=["search", "static-analysis"]
            )
            
            routed_agent = queue.auto_route_task(multi_task)
            # Should route to ExaSearcher (appears in both capabilities)
            assert routed_agent == AgentRole.EXA_SEARCHER


class TestBackwardCompatibility:
    """Test backward compatibility with existing functionality."""
    
    @pytest.mark.asyncio
    async def test_legacy_agent_execution_still_works(self):
        """Test that existing agents still execute correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            task = Task(
                id="legacy_test",
                title="Legacy ACIM Task",
                description="Test backward compatibility",
                priority=Priority.HIGH,
                category="content"
            )
            
            result = await executor.execute_acim_scholar_task(task, {"prompt": "You are an ACIM scholar focused on content integrity."}, {})
            
            assert result.success is True
            assert "Conclusion" in result.output
    
    def test_legacy_task_creation_without_capability_tags(self):
        """Test creating tasks without capability tags (legacy format)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            queue = TaskQueue(storage_path=f"{temp_dir}/tasks.json")
            
            task = queue.create_task(
                title="Legacy Task",
                description="Task without capability tags",
                priority=Priority.MEDIUM,
                category="general",
                tags=["legacy"]
            )
            
            assert task.capability_tags == []
            assert task.tags == ["legacy"]
    
    def test_legacy_agent_tools_fallback(self):
        """Test fallback to legacy agent tools when registry is empty."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            # Should fallback to legacy tools
            tools = executor.get_agent_tools(AgentRole.ACIM_SCHOLAR)
            
            expected_tools = [
                "text_validation", "citation_checker", "content_analyzer",
                "doctrinal_validator", "search_accuracy_tester"
            ]
            
            assert set(tools) == set(expected_tools)


class TestErrorHandling:
    """Test error handling in orchestrator v2."""
    
    def test_invalid_agent_role_handling(self):
        """Test handling of invalid agent roles in routing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_data = {
                "routing_rules": {
                    "capability_tags": {
                        "invalid": ["non_existent_agent"]
                    }
                }
            }
            
            registry_path = Path(temp_dir) / "registry.json"
            with open(registry_path, 'w') as f:
                json.dump(registry_data, f)
            
            queue = TaskQueue(registry_path=str(registry_path))
            
            invalid_task = Task(
                id="invalid_test",
                title="Invalid Agent Task",
                description="Task with invalid agent reference",
                priority=Priority.MEDIUM,
                category="test",
                capability_tags=["invalid"]
            )
            
            # Should return None for invalid agent
            routed_agent = queue.auto_route_task(invalid_task)
            assert routed_agent is None
    
    @pytest.mark.asyncio
    async def test_agent_execution_error_handling(self):
        """Test error handling in agent execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            # Mock OpenAI client to raise an exception
            executor.openai_client = Mock()
            executor.openai_client.chat.completions.create.side_effect = Exception("API Error")
            
            task = Task(
                id="error_test",
                title="Error Test",
                description="Test error handling",
                priority=Priority.LOW,
                category="test"
            )
            
            # Test generic agent execution with error
            result = await executor.execute_generic_agent_task(
                task, {"prompt": "test"}, {}, Mock(value="test_agent")
            )
            
            assert result.success is False
            assert "OpenAI execution failed" in result.output


@pytest.fixture
def sample_registry():
    """Fixture providing sample registry data."""
    return {
        "agents": {
            "exa_searcher": {
                "name": "ExaSearcher",
                "description": "Code search specialist",
                "prompt_path": "specialized/exa_searcher.md",
                "capabilities": ["code_search", "todo_detector"],
                "tags": ["search", "static-analysis"],
                "enabled": True
            },
            "playwright_tester": {
                "name": "PlaywrightTester", 
                "description": "E2E testing specialist",
                "prompt_path": "specialized/playwright_tester.md",
                "capabilities": ["e2e_tester", "browser_automator"],
                "tags": ["playwright", "testing"],
                "enabled": True
            },
            "revenue_analyst": {
                "name": "RevenueAnalyst",
                "description": "Revenue optimization specialist", 
                "prompt_path": "specialized/revenue_analyst.md",
                "capabilities": ["funnel_analyzer", "pricing_optimizer"],
                "tags": ["revenue", "analytics"],
                "enabled": True
            }
        },
        "routing_rules": {
            "capability_tags": {
                "search": ["exa_searcher"],
                "playwright": ["playwright_tester"],
                "revenue": ["revenue_analyst"]
            },
            "load_balancing": {
                "strategy": "least_loaded"
            }
        }
    }


class TestIntegration:
    """Integration tests for the complete orchestrator v2 system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_task_routing_and_execution(self, sample_registry):
        """Test complete flow from task creation to execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup registry
            registry_path = Path(temp_dir) / "agents" / "registry.json"
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(registry_path, 'w') as f:
                json.dump(sample_registry, f)
            
            # Initialize components
            queue = TaskQueue(
                storage_path=f"{temp_dir}/tasks.json",
                registry_path=str(registry_path)
            )
            executor = AgentExecutor(project_root=temp_dir)
            
            # Create tasks with different capability tags
            search_task = queue.create_task(
                title="Find TODO Items",
                description="Scan codebase for TODO comments",
                priority=Priority.MEDIUM,
                category="analysis",
                capability_tags=["search"]
            )
            
            e2e_task = queue.create_task(
                title="Test Login Flow",
                description="E2E test for user authentication",
                priority=Priority.HIGH,
                category="testing",
                capability_tags=["playwright"]
            )
            
            revenue_task = queue.create_task(
                title="Analyze Conversion Funnel",
                description="Optimize pricing and conversion rates",
                priority=Priority.CRITICAL,
                category="business",
                capability_tags=["revenue"]
            )
            
            # Test auto-routing
            search_agent = queue.auto_route_task(search_task)
            e2e_agent = queue.auto_route_task(e2e_task)
            revenue_agent = queue.auto_route_task(revenue_task)
            
            assert search_agent == AgentRole.EXA_SEARCHER
            assert e2e_agent == AgentRole.PLAYWRIGHT_TESTER
            assert revenue_agent == AgentRole.REVENUE_ANALYST
            
            # Test task execution
            search_result = await executor.execute_task(search_task, search_agent)
            e2e_result = await executor.execute_task(e2e_task, e2e_agent)
            revenue_result = await executor.execute_task(revenue_task, revenue_agent)
            
            assert all(result.success for result in [search_result, e2e_result, revenue_result])
            assert "Static code analysis completed" in search_result.output
            assert "E2E testing completed" in e2e_result.output
            assert "Revenue analysis completed" in revenue_result.output


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
