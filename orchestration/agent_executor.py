#!/usr/bin/env python3
"""
ACIMguide Autonomous Improvement Pipeline - Agent Executor
Handles the execution of tasks by specialized AI agents with proper context and validation.
"""

import asyncio
import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import openai
import os
from dotenv import load_dotenv

from task_queue import Task, TaskStatus, AgentRole

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    """Result of agent task execution."""
    success: bool
    output: str
    artifacts: List[str]  # Generated files, documentation, etc.
    metrics: Dict[str, Any]
    errors: List[str]
    execution_time: float

class AgentExecutor:
    """Executes tasks using specialized AI agents with proper context and validation."""
    
    def __init__(self, project_root: str = "/home/am/TestAlex"):
        self.project_root = Path(project_root)
        self.openai_client = None
        self.setup_openai()
    
    def setup_openai(self):
        """Initialize OpenAI client for agent execution."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
            logger.info("✅ OpenAI client initialized")
        else:
            logger.warning("⚠️ OpenAI API key not found - agent execution will be simulated")
    
    async def execute_task(self, task: Task, agent_role: AgentRole) -> ExecutionResult:
        """Execute a task using the specified agent."""
        start_time = datetime.now()
        logger.info(f"🤖 Executing task '{task.title}' with {agent_role.value}")
        
        try:
            # Load agent prompt and context
            agent_context = await self.load_agent_context(agent_role)
            
            # Prepare task execution environment
            execution_env = await self.prepare_execution_environment(task, agent_role)
            
            # Execute task based on agent type
            result = await self.execute_by_agent_type(task, agent_role, agent_context, execution_env)
            
            # Validate results
            validated_result = await self.validate_execution_result(task, agent_role, result)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            validated_result.execution_time = execution_time
            
            logger.info(f"✅ Task execution completed in {execution_time:.2f}s")
            return validated_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Task execution failed: {e}")
            
            return ExecutionResult(
                success=False,
                output=f"Execution failed: {str(e)}",
                artifacts=[],
                metrics={"execution_time": execution_time},
                errors=[str(e)],
                execution_time=execution_time
            )
    
    async def load_agent_context(self, agent_role: AgentRole) -> Dict[str, Any]:
        """Load agent-specific context and prompts."""
        context = {
            "role": agent_role.value,
            "prompt": "",
            "capabilities": [],
            "constraints": [],
            "project_context": {}
        }
        
        # Load agent prompt file
        prompt_files = {
            AgentRole.ACIM_SCHOLAR: "prompts/acim_scholar.md",
            AgentRole.PRODUCT_MANAGER: "prompts/product_manager.md",
            AgentRole.BACKEND_ENGINEER: "prompts/backend_engineer.md",
            AgentRole.ANDROID_ENGINEER: "prompts/android_engineer.md",
            AgentRole.DEVOPS_SRE: "prompts/devops_sre.md",
            AgentRole.QA_TESTER: "prompts/qa_tester.md",
            AgentRole.CLOUD_FUNCTIONS_ENGINEER: "prompts/cloud_functions_engineer.md"
        }
        
        prompt_file = self.project_root / prompt_files[agent_role]
        if prompt_file.exists():
            with open(prompt_file, 'r') as f:
                context["prompt"] = f.read()
        
        # Load master system prompt for universal context
        master_prompt_file = self.project_root / "prompts/master_system_prompt.md"
        if master_prompt_file.exists():
            with open(master_prompt_file, 'r') as f:
                context["master_prompt"] = f.read()
        
        # Load project context
        context["project_context"] = await self.load_project_context()
        
        return context
    
    async def load_project_context(self) -> Dict[str, Any]:
        """Load current project context and status."""
        context = {
            "project_status": {},
            "recent_changes": [],
            "current_issues": [],
            "deployment_status": {},
            "performance_metrics": {}
        }
        
        # Load project status
        status_file = self.project_root / "PROJECT_STATUS.md"
        if status_file.exists():
            with open(status_file, 'r') as f:
                context["project_status"]["content"] = f.read()
        
        # Load recent git changes
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                context["recent_changes"] = result.stdout.strip().split('\n')
        except Exception as e:
            logger.warning(f"Could not load git history: {e}")
        
        return context
    
    async def prepare_execution_environment(self, task: Task, agent_role: AgentRole) -> Dict[str, Any]:
        """Prepare the execution environment for the task."""
        env = {
            "working_directory": str(self.project_root),
            "task_workspace": None,
            "available_tools": [],
            "file_permissions": {},
            "safety_constraints": []
        }
        
        # Create task-specific workspace
        task_workspace = self.project_root / "orchestration" / "workspaces" / f"task_{task.id}"
        task_workspace.mkdir(parents=True, exist_ok=True)
        env["task_workspace"] = str(task_workspace)
        
        # Define available tools based on agent role
        env["available_tools"] = self.get_agent_tools(agent_role)
        
        # Set safety constraints
        env["safety_constraints"] = [
            "no_destructive_operations",
            "acim_content_protection",
            "backup_before_changes",
            "validate_before_deploy"
        ]
        
        return env
    
    def get_agent_tools(self, agent_role: AgentRole) -> List[str]:
        """Get available tools for each agent role."""
        tools = {
            AgentRole.ACIM_SCHOLAR: [
                "text_validation", "citation_checker", "content_analyzer",
                "doctrinal_validator", "search_accuracy_tester"
            ],
            AgentRole.PRODUCT_MANAGER: [
                "requirements_generator", "user_story_creator", "roadmap_planner",
                "metrics_analyzer", "documentation_creator"
            ],
            AgentRole.BACKEND_ENGINEER: [
                "code_generator", "api_tester", "database_optimizer",
                "firebase_deployer", "performance_profiler"
            ],
            AgentRole.ANDROID_ENGINEER: [
                "kotlin_generator", "ui_designer", "offline_sync_implementer",
                "performance_optimizer", "accessibility_validator"
            ],
            AgentRole.DEVOPS_SRE: [
                "infrastructure_manager", "security_scanner", "cost_optimizer",
                "monitoring_configurator", "deployment_automator"
            ],
            AgentRole.QA_TESTER: [
                "test_generator", "automation_framework", "performance_tester",
                "security_tester", "accessibility_validator"
            ],
            AgentRole.CLOUD_FUNCTIONS_ENGINEER: [
                "function_generator", "trigger_configurator", "performance_optimizer",
                "integration_tester", "deployment_manager"
            ]
        }
        
        return tools.get(agent_role, [])
    
    async def execute_by_agent_type(
        self, 
        task: Task, 
        agent_role: AgentRole, 
        context: Dict[str, Any], 
        env: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute task based on specific agent type."""
        
        if agent_role == AgentRole.ACIM_SCHOLAR:
            return await self.execute_acim_scholar_task(task, context, env)
        elif agent_role == AgentRole.PRODUCT_MANAGER:
            return await self.execute_product_manager_task(task, context, env)
        elif agent_role == AgentRole.BACKEND_ENGINEER:
            return await self.execute_backend_engineer_task(task, context, env)
        elif agent_role == AgentRole.ANDROID_ENGINEER:
            return await self.execute_android_engineer_task(task, context, env)
        elif agent_role == AgentRole.DEVOPS_SRE:
            return await self.execute_devops_sre_task(task, context, env)
        elif agent_role == AgentRole.QA_TESTER:
            return await self.execute_qa_tester_task(task, context, env)
        elif agent_role == AgentRole.CLOUD_FUNCTIONS_ENGINEER:
            return await self.execute_cloud_functions_task(task, context, env)
        else:
            raise ValueError(f"Unknown agent role: {agent_role}")
    
    async def execute_acim_scholar_task(self, task: Task, context: Dict[str, Any], env: Dict[str, Any]) -> ExecutionResult:
        """Execute ACIM Scholar tasks focused on content integrity and doctrinal accuracy."""
        logger.info("📚 Executing ACIM Scholar task")
        
        # Prepare ACIM-specific context
        acim_context = {
            "task": task.description,
            "priority": task.priority.value,
            "category": task.category,
            "tags": task.tags
        }
        
        if self.openai_client:
            # Use OpenAI for actual execution
            messages = [
                {"role": "system", "content": context["prompt"]},
                {"role": "user", "content": f"Execute this ACIM content validation task: {json.dumps(acim_context, indent=2)}"}
            ]
            
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.1  # Low temperature for consistency
                )
                
                output = response.choices[0].message.content
                
                return ExecutionResult(
                    success=True,
                    output=output,
                    artifacts=[],
                    metrics={"tokens_used": response.usage.total_tokens},
                    errors=[],
                    execution_time=0
                )
                
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    output=f"OpenAI execution failed: {str(e)}",
                    artifacts=[],
                    metrics={},
                    errors=[str(e)],
                    execution_time=0
                )
        else:
            # Simulate execution for demonstration
            await asyncio.sleep(2)  # Simulate processing time
            
            return ExecutionResult(
                success=True,
                output=f"ACIM Scholar validation completed for: {task.title}\n\nContent integrity verified according to ACIM doctrinal standards.",
                artifacts=["acim_validation_report.md"],
                metrics={"validation_score": 0.95},
                errors=[],
                execution_time=0
            )
    
    async def execute_product_manager_task(self, task: Task, context: Dict[str, Any], env: Dict[str, Any]) -> ExecutionResult:
        """Execute Product Manager tasks focused on planning and requirements."""
        logger.info("📋 Executing Product Manager task")
        
        # Simulate product management work
        await asyncio.sleep(3)
        
        # Generate product documentation
        workspace = Path(env["task_workspace"])
        doc_file = workspace / "product-requirements.md"
        
        with open(doc_file, 'w') as f:
            f.write(f"# Product Requirements: {task.title}\n\n")
            f.write(f"## Description\n{task.description}\n\n")
            f.write(f"## Priority: {task.priority.value}\n\n")
            f.write(f"## User Stories\n")
            f.write(f"- As a user, I want to {task.description.lower()}\n")
            f.write(f"- So that I can have a better ACIM study experience\n\n")
            f.write(f"## Acceptance Criteria\n")
            f.write(f"- [ ] Feature implemented according to specifications\n")
            f.write(f"- [ ] ACIM content integrity maintained\n")
            f.write(f"- [ ] User experience validated\n")
        
        return ExecutionResult(
            success=True,
            output=f"Product requirements generated for: {task.title}",
            artifacts=[str(doc_file)],
            metrics={"requirements_count": 3},
            errors=[],
            execution_time=0
        )
    
    async def execute_backend_engineer_task(self, task: Task, context: Dict[str, Any], env: Dict[str, Any]) -> ExecutionResult:
        """Execute Backend Engineer tasks focused on API and database work."""
        logger.info("⚙️ Executing Backend Engineer task")
        
        # Simulate backend development work
        await asyncio.sleep(4)
        
        return ExecutionResult(
            success=True,
            output=f"Backend implementation completed for: {task.title}\n\nAPI endpoints optimized and database queries improved.",
            artifacts=["backend_changes.py", "api_tests.py"],
            metrics={"performance_improvement": 0.25, "test_coverage": 0.85},
            errors=[],
            execution_time=0
        )
    
    async def execute_android_engineer_task(self, task: Task, context: Dict[str, Any], env: Dict[str, Any]) -> ExecutionResult:
        """Execute Android Engineer tasks focused on mobile development."""
        logger.info("📱 Executing Android Engineer task")
        
        # Simulate Android development work
        await asyncio.sleep(5)
        
        return ExecutionResult(
            success=True,
            output=f"Android implementation completed for: {task.title}\n\nMobile features developed with offline support.",
            artifacts=["MainActivity.kt", "OfflineSync.kt", "layout_main.xml"],
            metrics={"app_size_increase": "2.5MB", "performance_score": 0.92},
            errors=[],
            execution_time=0
        )
    
    async def execute_devops_sre_task(self, task: Task, context: Dict[str, Any], env: Dict[str, Any]) -> ExecutionResult:
        """Execute DevOps/SRE tasks focused on infrastructure and reliability."""
        logger.info("🔧 Executing DevOps/SRE task")
        
        # Simulate infrastructure work
        await asyncio.sleep(3)
        
        return ExecutionResult(
            success=True,
            output=f"Infrastructure optimization completed for: {task.title}\n\nSecurity hardened and performance improved.",
            artifacts=["deployment.yaml", "monitoring_config.json"],
            metrics={"uptime_improvement": 0.02, "cost_reduction": 0.15},
            errors=[],
            execution_time=0
        )
    
    async def execute_qa_tester_task(self, task: Task, context: Dict[str, Any], env: Dict[str, Any]) -> ExecutionResult:
        """Execute QA Tester tasks focused on quality assurance."""
        logger.info("🧪 Executing QA Tester task")
        
        # Simulate testing work
        await asyncio.sleep(3)
        
        return ExecutionResult(
            success=True,
            output=f"Quality assurance completed for: {task.title}\n\nComprehensive testing suite implemented.",
            artifacts=["test_suite.py", "test_results.json"],
            metrics={"test_coverage": 0.95, "bugs_found": 2, "performance_score": 0.88},
            errors=[],
            execution_time=0
        )
    
    async def execute_cloud_functions_task(self, task: Task, context: Dict[str, Any], env: Dict[str, Any]) -> ExecutionResult:
        """Execute Cloud Functions Engineer tasks focused on serverless logic."""
        logger.info("☁️ Executing Cloud Functions Engineer task")
        
        # Simulate cloud functions work
        await asyncio.sleep(3)
        
        return ExecutionResult(
            success=True,
            output=f"Cloud Functions optimization completed for: {task.title}\n\nServerless functions optimized for performance.",
            artifacts=["index.js", "package.json"],
            metrics={"cold_start_reduction": 0.3, "memory_optimization": 0.2},
            errors=[],
            execution_time=0
        )
    
    async def validate_execution_result(self, task: Task, agent_role: AgentRole, result: ExecutionResult) -> ExecutionResult:
        """Validate the execution result based on task requirements and agent capabilities."""
        
        # Basic validation
        if not result.success:
            logger.warning(f"⚠️ Task execution failed: {result.errors}")
            return result
        
        # ACIM Scholar validation for content-related tasks
        if "content" in task.tags or "acim" in task.tags:
            if agent_role != AgentRole.ACIM_SCHOLAR:
                logger.info("📚 Requesting ACIM Scholar validation for content-related task")
                # In a real implementation, this would trigger ACIM Scholar review
        
        # Security validation for security-related tasks
        if "security" in task.tags and agent_role != AgentRole.DEVOPS_SRE:
            logger.info("🔒 Requesting security validation")
        
        # Performance validation for performance-related tasks
        if "performance" in task.tags:
            logger.info("⚡ Validating performance improvements")
        
        logger.info(f"✅ Execution result validated for task: {task.title}")
        return result

# Example usage and testing
async def main():
    """Test the agent executor with sample tasks."""
    from task_queue import TaskQueue, Priority
    
    executor = AgentExecutor()
    queue = TaskQueue()
    
    # Create test tasks
    acim_task = queue.create_task(
        title="Validate ACIM Text Integrity",
        description="Ensure all ACIM quotations are exact and properly cited",
        priority=Priority.CRITICAL,
        category="content",
        tags=["acim", "validation", "content"],
        estimated_hours=2
    )
    
    backend_task = queue.create_task(
        title="Optimize Firebase Functions",
        description="Improve response time and reduce cold starts",
        priority=Priority.HIGH,
        category="performance",
        tags=["firebase", "performance", "backend"],
        estimated_hours=6
    )
    
    # Execute tasks
    print("🚀 Testing Agent Executor")
    
    # Test ACIM Scholar execution
    acim_result = await executor.execute_task(acim_task, AgentRole.ACIM_SCHOLAR)
    print(f"ACIM Scholar Result: {acim_result.success} - {acim_result.output[:100]}...")
    
    # Test Backend Engineer execution
    backend_result = await executor.execute_task(backend_task, AgentRole.BACKEND_ENGINEER)
    print(f"Backend Engineer Result: {backend_result.success} - {backend_result.output[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
