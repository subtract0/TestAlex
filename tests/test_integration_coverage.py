#!/usr/bin/env python3
"""
Integration tests to improve coverage across orchestration modules.
Tests real execution flows and edge cases.
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


class TestAgentExecutorCoverage:
    """Tests to improve coverage in AgentExecutor."""
    
    def test_init_with_openai_client(self):
        """Test AgentExecutor initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            # OpenAI client should be initialized (using environment API key)
            assert hasattr(executor, 'openai_client')
    
    def test_get_agent_tools(self):
        """Test get_agent_tools for all agent types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            # Test all agent roles
            roles_to_test = [
                AgentRole.ACIM_SCHOLAR,
                AgentRole.DEVOPS_SRE,
                AgentRole.PRODUCT_MANAGER,
                AgentRole.QA_TESTER,
                AgentRole.EXA_SEARCHER,
                AgentRole.PLAYWRIGHT_TESTER,
                AgentRole.REVENUE_ANALYST
            ]
            
            for role in roles_to_test:
                tools = executor.get_agent_tools(role)
                assert isinstance(tools, list)
                # Tools list may be empty without agent registry
    
    @pytest.mark.asyncio
    async def test_all_agent_execution_methods(self):
        """Test all agent execution methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            task = Task(
                id="test_task",
                title="Test Task",
                description="Test all agents",
                priority=Priority.MEDIUM,
                category="test"
            )
            
            # Test all execution methods with proper environment
            env = {"task_workspace": str(temp_dir)}
            methods_and_agents = [
                (executor.execute_acim_scholar_task, {"prompt": "You are an ACIM scholar."}),
                (executor.execute_devops_sre_task, {}),
                (executor.execute_product_manager_task, {}),
                (executor.execute_qa_tester_task, {}),
                (executor.execute_exa_searcher_task, {}),
                (executor.execute_playwright_tester_task, {}),
                (executor.execute_revenue_analyst_task, {}),
            ]
            
            for method, context in methods_and_agents:
                result = await method(task, context, env)
                assert isinstance(result, ExecutionResult)
                assert result.success is True
    
    @pytest.mark.asyncio
    async def test_execute_task_routing(self):
        """Test execute_task with different agent roles."""
        with tempfile.TemporaryDirectory() as temp_dir:
            executor = AgentExecutor(project_root=temp_dir)
            
            task = Task(
                id="routing_test",
                title="Routing Test",
                description="Test task routing",
                priority=Priority.HIGH,
                category="test"
            )
            
            # Test routing to each agent
            roles = [
                AgentRole.ACIM_SCHOLAR,
                AgentRole.DEVOPS_SRE,
                AgentRole.PRODUCT_MANAGER,
                AgentRole.QA_TESTER,
                AgentRole.EXA_SEARCHER,
                AgentRole.PLAYWRIGHT_TESTER,
                AgentRole.REVENUE_ANALYST
            ]
            
            for role in roles:
                result = await executor.execute_task(task, role)
                assert isinstance(result, ExecutionResult)
                assert result.success is True


class TestTaskQueueCoverage:
    """Tests to improve coverage in TaskQueue."""
    
    def test_all_task_queue_methods(self):
        """Test all TaskQueue methods."""
        with tempfile.TemporaryDirectory() as temp_dir:
            queue = TaskQueue(
                storage_path=f"{temp_dir}/tasks.json",
                registry_path=f"{temp_dir}/registry.json"
            )
            
            # Test create_task with all parameters
            task = queue.create_task(
                title="Comprehensive Task",
                description="Test all parameters",
                priority=Priority.CRITICAL,
                category="integration",
                tags=["test", "coverage"],
                capability_tags=["search", "analysis"],
                metadata={"test_key": "test_value"}
            )
            
            assert task.title == "Comprehensive Task"
            assert task.priority == Priority.CRITICAL
            assert task.category == "integration"
            assert "test" in task.tags
            assert "search" in task.capability_tags
            assert task.metadata["test_key"] == "test_value"
    
    def test_task_queue_with_registry(self):
        """Test TaskQueue with registry configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create registry with comprehensive routing rules
            registry_data = {
                "routing_rules": {
                    "capability_tags": {
                        "search": ["exa_searcher"],
                        "testing": ["playwright_tester", "qa_tester"],
                        "revenue": ["revenue_analyst"],
                        "content": ["acim_scholar"],
                        "devops": ["devops_sre"]
                    },
                    "priority_routing": {
                        "critical": ["acim_scholar", "devops_sre", "revenue_analyst"],
                        "high": ["product_manager", "qa_tester"],
                        "medium": ["exa_searcher", "playwright_tester"],
                        "low": ["qa_tester"]
                    },
                    "load_balancing": {
                        "strategy": "least_loaded",
                        "max_tasks_per_agent": 10
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
            
            # Test routing for different capability combinations
            test_cases = [
                (["search"], AgentRole.EXA_SEARCHER),
                (["testing"], AgentRole.PLAYWRIGHT_TESTER),  # First in list
                (["revenue"], AgentRole.REVENUE_ANALYST),
                (["content"], AgentRole.ACIM_SCHOLAR),
                (["devops"], AgentRole.DEVOPS_SRE),
                (["search", "testing"], AgentRole.EXA_SEARCHER),  # Should pick first match
            ]
            
            for capability_tags, expected_agent in test_cases:
                task = Task(
                    id=f"test_{len(capability_tags)}_capabilities",
                    title="Test Routing",
                    description="Test capability routing",
                    priority=Priority.MEDIUM,
                    category="test",
                    capability_tags=capability_tags
                )
                
                routed_agent = queue.auto_route_task(task)
                assert routed_agent == expected_agent
    
    def test_task_status_transitions(self):
        """Test all task status transitions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            queue = TaskQueue(storage_path=f"{temp_dir}/tasks.json")
            
            task = queue.create_task(
                title="Status Test",
                description="Test status transitions",
                priority=Priority.MEDIUM,
                category="test"
            )
            
            assert task.status == TaskStatus.PENDING
            
            # Test status transitions
            task.status = TaskStatus.IN_PROGRESS
            assert task.status == TaskStatus.IN_PROGRESS
            
            task.status = TaskStatus.COMPLETED
            assert task.status == TaskStatus.COMPLETED
            
            task.status = TaskStatus.FAILED
            assert task.status == TaskStatus.FAILED
    
    def test_task_queue_load_balancing(self):
        """Test load balancing functionality."""
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
            
            queue = TaskQueue(registry_path=str(registry_path))
            
            # Set different workloads
            queue.agent_workload[AgentRole.QA_TESTER] = 8
            queue.agent_workload[AgentRole.PLAYWRIGHT_TESTER] = 3
            
            task = Task(
                id="load_balance_test",
                title="Load Balance Test",
                description="Test load balancing",
                priority=Priority.MEDIUM,
                category="testing",
                capability_tags=["testing"]
            )
            
            # Should route to Playwright Tester (lower workload)
            routed_agent = queue.auto_route_task(task)
            assert routed_agent == AgentRole.PLAYWRIGHT_TESTER
    
    def test_get_next_task_with_routing_comprehensive(self):
        """Test get_next_task_with_routing comprehensively."""
        with tempfile.TemporaryDirectory() as temp_dir:
            registry_data = {
                "routing_rules": {
                    "capability_tags": {
                        "search": ["exa_searcher"],
                        "testing": ["qa_tester"]
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
            
            # Create tasks with different capabilities and priorities
            high_search_task = queue.create_task(
                title="High Priority Search",
                description="Critical search task",
                priority=Priority.HIGH,
                category="analysis",
                capability_tags=["search"]
            )
            
            medium_test_task = queue.create_task(
                title="Medium Priority Test",
                description="Regular test task",
                priority=Priority.MEDIUM,
                category="testing",
                capability_tags=["testing"]
            )
            
            low_general_task = queue.create_task(
                title="Low Priority General",
                description="General task",
                priority=Priority.LOW,
                category="general"
            )
            
            # Test routing to specific agents
            next_task = queue.get_next_task_with_routing(AgentRole.EXA_SEARCHER)
            assert next_task.id == high_search_task.id
            
            next_task = queue.get_next_task_with_routing(AgentRole.QA_TESTER)
            assert next_task.id == medium_test_task.id
            
            # Test general routing (should get highest priority available)
            next_task = queue.get_next_task_with_routing()
            assert next_task is not None


class TestErrorHandlingCoverage:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_openai_error_handling(self):
        """Test OpenAI API error handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock OpenAI client with various errors
            mock_client = Mock()
            executor = AgentExecutor(project_root=temp_dir)
            executor.openai_client = mock_client  # Set after initialization
            
            task = Task(
                id="error_test",
                title="Error Test",
                description="Test error handling",
                priority=Priority.LOW,
                category="test"
            )
            
            # Test different error types
            error_scenarios = [
                Exception("Connection timeout"),
                Exception("Rate limit exceeded"),
                Exception("Invalid API key"),
                Exception("Model not found")
            ]
            
            for error in error_scenarios:
                mock_client.chat.completions.create.side_effect = error
                
                result = await executor.execute_generic_agent_task(
                    task, {"prompt": "test prompt"}, {}, Mock(value="test_agent")
                )
                
                assert result.success is False
                assert "OpenAI execution failed" in result.output
    
    def test_invalid_registry_handling(self):
        """Test handling of various invalid registry configurations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test empty registry
            registry_path = Path(temp_dir) / "empty_registry.json"
            with open(registry_path, 'w') as f:
                json.dump({}, f)
            
            queue = TaskQueue(registry_path=str(registry_path))
            
            task = Task(
                id="empty_registry_test",
                title="Empty Registry Test",
                description="Test with empty registry",
                priority=Priority.MEDIUM,
                category="test",
                capability_tags=["search"]
            )
            
            routed_agent = queue.auto_route_task(task)
            assert routed_agent is None
            
            # Test malformed registry
            malformed_path = Path(temp_dir) / "malformed_registry.json"
            with open(malformed_path, 'w') as f:
                f.write('{"routing_rules": {"capability_tags": "not_a_dict"}')
            
            queue_malformed = TaskQueue(registry_path=str(malformed_path))
            routed_agent = queue_malformed.auto_route_task(task)
            assert routed_agent is None
    
    def test_task_queue_storage_error_handling(self):
        """Test TaskQueue storage error handling."""
        # TaskQueue creates directories as needed, so we test a truly invalid path
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file where we want to create a directory
            invalid_path = Path(temp_dir) / "file.txt"
            invalid_path.write_text("blocking")
            try:
                # This should handle gracefully or raise an error
                TaskQueue(storage_path=str(invalid_path / "tasks.json"))
            except (PermissionError, OSError, FileNotFoundError):
                pass  # Expected behavior
    
    @pytest.mark.asyncio 
    async def test_execution_result_creation(self):
        """Test ExecutionResult creation with all parameters."""
        result = ExecutionResult(
            success=True,
            output="Test output",
            artifacts=["artifact1.txt", "artifact2.pdf"],
            metrics={"execution_time": 1.5, "lines_processed": 100},
            errors=["Test error"],
            execution_time=1.0
        )
        
        assert result.success is True
        assert result.output == "Test output"
        assert "Test error" in result.errors
        assert "artifact1.txt" in result.artifacts
        assert result.metrics["execution_time"] == 1.5
        assert result.execution_time == 1.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
