#!/usr/bin/env python3
"""
ACIMguide Autonomous Improvement Pipeline - Task Queue Management
Handles task intake, prioritization, and distribution to specialized agents.
"""

import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Priority(Enum):
    CRITICAL = "critical"  # P0: Security, ACIM content corruption, outages
    HIGH = "high"         # P1: Performance, UX issues, cost overruns
    MEDIUM = "medium"     # P2: Feature enhancements, optimizations
    LOW = "low"          # P3: Nice-to-have improvements

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentRole(Enum):
    ACIM_SCHOLAR = "acim_scholar"
    PRODUCT_MANAGER = "product_manager"
    BACKEND_ENGINEER = "backend_engineer"
    ANDROID_ENGINEER = "android_engineer"
    DEVOPS_SRE = "devops_sre"
    QA_TESTER = "qa_tester"
    CLOUD_FUNCTIONS_ENGINEER = "cloud_functions_engineer"
    UI_UX_DESIGNER = "ui_ux_designer"
    TECHNICAL_WRITER = "technical_writer"
    # New dynamic agents from registry
    EXA_SEARCHER = "exa_searcher"
    PLAYWRIGHT_TESTER = "playwright_tester"
    REVENUE_ANALYST = "revenue_analyst"

@dataclass
class Task:
    """Represents a single improvement task in the pipeline."""
    id: str
    title: str
    description: str
    priority: Priority
    category: str
    assignee: Optional[AgentRole] = None
    dependencies: List[str] = None
    tags: List[str] = None
    capability_tags: List[str] = None  # New: capability-based routing tags
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []
        if self.capability_tags is None:
            self.capability_tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

class TaskQueue:
    """Manages the autonomous improvement task queue with intelligent prioritization."""
    
    def __init__(self, storage_path: str = "orchestration/tasks.json", registry_path: str = "agents/registry.json"):
        self.storage_path = Path(storage_path)
        self.registry_path = Path(registry_path)
        self.tasks: Dict[str, Task] = {}
        self.agent_workload: Dict[AgentRole, int] = {role: 0 for role in AgentRole}
        self.routing_rules = {}
        self.load_agent_registry()
        self.load_tasks()
    
    def load_agent_registry(self):
        """Load agent registry for capability-based routing."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    registry_data = json.load(f)
                    self.routing_rules = registry_data.get('routing_rules', {})
                logger.info(f"✅ Loaded routing rules from agent registry")
            except Exception as e:
                logger.error(f"❌ Failed to load agent registry: {e}")
                self.routing_rules = {}
        else:
            logger.warning(f"⚠️ Agent registry not found at {self.registry_path}")
            self.routing_rules = {}
    
    def generate_task_id(self) -> str:
        """Generate a unique task identifier."""
        return f"task_{uuid.uuid4().hex[:8]}"
    
    def create_task(
        self,
        title: str,
        description: str,
        priority: Priority,
        category: str,
        assignee: Optional[AgentRole] = None,
        dependencies: List[str] = None,
        tags: List[str] = None,
        capability_tags: List[str] = None,
        estimated_hours: Optional[int] = None,
        metadata: Dict[str, Any] = None
    ) -> Task:
        """Create a new improvement task."""
        task = Task(
            id=self.generate_task_id(),
            title=title,
            description=description,
            priority=priority,
            category=category,
            assignee=assignee,
            dependencies=dependencies or [],
            tags=tags or [],
            capability_tags=capability_tags or [],
            estimated_hours=estimated_hours,
            metadata=metadata or {}
        )
        
        self.tasks[task.id] = task
        self.save_tasks()
        
        logger.info(f"Created task {task.id}: {task.title} [{task.priority.value}]")
        return task
    
    def assign_task(self, task_id: str, agent: AgentRole) -> bool:
        """Assign a task to a specific agent."""
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        task = self.tasks[task_id]
        if task.status != TaskStatus.PENDING:
            logger.error(f"Task {task_id} is not in pending status")
            return False
        
        # Check dependencies
        if not self.are_dependencies_met(task):
            logger.warning(f"Dependencies not met for task {task_id}")
            return False
        
        task.assignee = agent
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.now()
        self.agent_workload[agent] += 1
        
        self.save_tasks()
        logger.info(f"Assigned task {task_id} to {agent.value}")
        return True
    
    def update_task_status(self, task_id: str, status: TaskStatus, actual_hours: Optional[int] = None) -> bool:
        """Update task status and completion metrics."""
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return False
        
        task = self.tasks[task_id]
        old_status = task.status
        task.status = status
        
        if actual_hours:
            task.actual_hours = actual_hours
        
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            if task.assignee:
                self.agent_workload[task.assignee] = max(0, self.agent_workload[task.assignee] - 1)
        
        self.save_tasks()
        logger.info(f"Updated task {task_id} status: {old_status.value} -> {status.value}")
        return True
    
    def are_dependencies_met(self, task: Task) -> bool:
        """Check if all task dependencies are completed."""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                logger.warning(f"Dependency {dep_id} not found for task {task.id}")
                return False
            
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        
        return True
    
    def get_next_task(self, agent: Optional[AgentRole] = None) -> Optional[Task]:
        """Get the next highest priority task that can be executed."""
        available_tasks = []
        
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            if agent and task.assignee and task.assignee != agent:
                continue
            
            if not self.are_dependencies_met(task):
                continue
            
            available_tasks.append(task)
        
        if not available_tasks:
            return None
        
        # Sort by priority (critical first) then by creation time
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        available_tasks.sort(key=lambda t: (priority_order[t.priority], t.created_at))
        
        return available_tasks[0]
    
    def auto_route_task(self, task: Task) -> Optional[AgentRole]:
        """Auto-route task based on capability tags using registry rules."""
        if not task.capability_tags or not self.routing_rules:
            return None
        
        capability_routing = self.routing_rules.get('capability_tags', {})
        
        # Find agents that can handle the task's capability tags
        suitable_agents = set()
        for cap_tag in task.capability_tags:
            if cap_tag in capability_routing:
                agent_keys = capability_routing[cap_tag]
                for agent_key in agent_keys:
                    # Convert agent key to AgentRole enum if it exists
                    try:
                        agent_role = AgentRole(agent_key)
                        suitable_agents.add(agent_role)
                    except ValueError:
                        # Skip unknown agent roles
                        continue
        
        if not suitable_agents:
            return None
        
        # Apply load balancing strategy
        load_balancing = self.routing_rules.get('load_balancing', {})
        strategy = load_balancing.get('strategy', 'least_loaded')
        
        if strategy == 'least_loaded':
            # Choose agent with lowest workload
            return min(suitable_agents, key=lambda agent: self.agent_workload[agent])
        else:
            # Fallback to first suitable agent
            return list(suitable_agents)[0]
    
    def get_next_task_with_routing(self, agent: Optional[AgentRole] = None) -> Optional[Task]:
        """Get the next task with intelligent capability-based routing."""
        available_tasks = []
        
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            if not self.are_dependencies_met(task):
                continue
            
            # If requesting for specific agent
            if agent:
                # Check if task is already assigned to this agent
                if task.assignee and task.assignee == agent:
                    available_tasks.append(task)
                # Check if agent can handle task capabilities
                elif task.capability_tags:
                    auto_assigned = self.auto_route_task(task)
                    if auto_assigned == agent:
                        available_tasks.append(task)
                # Fallback to existing logic
                elif not task.assignee:
                    available_tasks.append(task)
            else:
                # General task retrieval
                available_tasks.append(task)
        
        if not available_tasks:
            return None
        
        # Sort by priority and creation time
        priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        available_tasks.sort(key=lambda t: (priority_order[t.priority], t.created_at))
        
        return available_tasks[0]
    
    def get_agent_workload(self) -> Dict[AgentRole, int]:
        """Get current workload for each agent."""
        return self.agent_workload.copy()
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status."""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_tasks_by_priority(self, priority: Priority) -> List[Task]:
        """Get all tasks with a specific priority."""
        return [task for task in self.tasks.values() if task.priority == priority]
    
    def get_overdue_tasks(self, hours_threshold: int = 48) -> List[Task]:
        """Get tasks that are overdue based on priority thresholds."""
        overdue = []
        now = datetime.now()
        
        for task in self.tasks.values():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                continue
            
            # Define SLA based on priority
            sla_hours = {
                Priority.CRITICAL: 4,   # 4 hours for critical issues
                Priority.HIGH: 24,      # 24 hours for high priority
                Priority.MEDIUM: 168,   # 1 week for medium priority
                Priority.LOW: 720       # 1 month for low priority
            }
            
            threshold = sla_hours.get(task.priority, hours_threshold)
            if (now - task.created_at).total_seconds() / 3600 > threshold:
                overdue.append(task)
        
        return overdue
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline performance metrics."""
        total_tasks = len(self.tasks)
        completed_tasks = len(self.get_tasks_by_status(TaskStatus.COMPLETED))
        failed_tasks = len(self.get_tasks_by_status(TaskStatus.FAILED))
        in_progress_tasks = len(self.get_tasks_by_status(TaskStatus.IN_PROGRESS))
        
        # Calculate average completion time
        completed = self.get_tasks_by_status(TaskStatus.COMPLETED)
        avg_completion_hours = 0
        if completed:
            total_hours = sum(
                (task.completed_at - task.created_at).total_seconds() / 3600
                for task in completed
                if task.completed_at
            )
            avg_completion_hours = total_hours / len(completed)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "failure_rate": failed_tasks / total_tasks if total_tasks > 0 else 0,
            "avg_completion_hours": round(avg_completion_hours, 2),
            "agent_workload": self.agent_workload,
            "overdue_tasks": len(self.get_overdue_tasks())
        }
    
    def save_tasks(self):
        """Persist tasks to storage."""
        self.storage_path.parent.mkdir(exist_ok=True)
        
        # Convert tasks to serializable format
        serializable_tasks = {}
        for task_id, task in self.tasks.items():
            task_dict = asdict(task)
            # Convert datetime objects to ISO strings
            for field in ['created_at', 'assigned_at', 'completed_at']:
                if task_dict[field]:
                    task_dict[field] = task_dict[field].isoformat()
            # Convert enums to strings
            task_dict['priority'] = task_dict['priority'].value
            task_dict['status'] = task_dict['status'].value
            if task_dict['assignee']:
                task_dict['assignee'] = task_dict['assignee'].value
            
            serializable_tasks[task_id] = task_dict
        
        with open(self.storage_path, 'w') as f:
            json.dump(serializable_tasks, f, indent=2)
    
    def load_tasks(self):
        """Load tasks from storage."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            for task_id, task_dict in data.items():
                # Convert strings back to datetime objects
                for field in ['created_at', 'assigned_at', 'completed_at']:
                    if task_dict[field]:
                        task_dict[field] = datetime.fromisoformat(task_dict[field])
                
                # Convert strings back to enums
                task_dict['priority'] = Priority(task_dict['priority'])
                task_dict['status'] = TaskStatus(task_dict['status'])
                if task_dict['assignee']:
                    task_dict['assignee'] = AgentRole(task_dict['assignee'])
                
                task = Task(**task_dict)
                self.tasks[task_id] = task
                
                # Update agent workload
                if task.assignee and task.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                    self.agent_workload[task.assignee] += 1
        
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize task queue
    queue = TaskQueue()
    
    # Create sample tasks
    task1 = queue.create_task(
        title="Fix Firebase Authentication Error",
        description="Resolve the persistent authentication failure in production web UI",
        priority=Priority.CRITICAL,
        category="security",
        tags=["firebase", "authentication", "production"],
        estimated_hours=4
    )
    
    task2 = queue.create_task(
        title="Optimize OpenAI Response Time",
        description="Improve AI response latency for better user experience",
        priority=Priority.HIGH,
        category="performance",
        tags=["openai", "performance", "backend"],
        estimated_hours=8
    )
    
    task3 = queue.create_task(
        title="Implement Android Offline Mode",
        description="Add offline ACIM text access for mobile users",
        priority=Priority.MEDIUM,
        category="feature",
        tags=["android", "offline", "mobile"],
        estimated_hours=24,
        dependencies=[task2.id]  # Depends on backend optimization
    )
    
    # Demonstrate task assignment and management
    print("=== ACIMguide Autonomous Task Queue Demo ===")
    print(f"Created {len(queue.tasks)} tasks")
    
    # Get next task
    next_task = queue.get_next_task()
    if next_task:
        print(f"Next task: {next_task.title} [{next_task.priority.value}]")
        
        # Assign to appropriate agent
        if "authentication" in next_task.tags:
            queue.assign_task(next_task.id, AgentRole.DEVOPS_SRE)
    
    # Show pipeline metrics
    metrics = queue.get_pipeline_metrics()
    print(f"Pipeline metrics: {json.dumps(metrics, indent=2)}")
