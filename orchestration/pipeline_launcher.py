#!/usr/bin/env python3
"""
ACIMguide Autonomous Improvement Pipeline - Pipeline Launcher
Main entry point for starting and managing the autonomous improvement pipeline.
"""

import asyncio
import argparse
import signal
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from master_orchestrator import MasterOrchestrator
from monitoring_system import SystemMonitor
from task_queue import TaskQueue, Priority, AgentRole

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestration/pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PipelineLauncher:
    """Main launcher for the autonomous improvement pipeline."""
    
    def __init__(self):
        self.orchestrator: Optional[MasterOrchestrator] = None
        self.monitor: Optional[SystemMonitor] = None
        self.running = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    async def start_pipeline(self, mode: str = "full"):
        """Start the autonomous improvement pipeline."""
        logger.info("🚀 Starting ACIMguide Autonomous Improvement Pipeline")
        logger.info(f"📅 Start time: {datetime.now().isoformat()}")
        logger.info(f"🔧 Mode: {mode}")
        
        try:
            # Initialize components
            self.orchestrator = MasterOrchestrator()
            self.monitor = SystemMonitor()
            
            # Create initial tasks
            await self.create_initial_tasks()
            
            # Start components based on mode
            tasks = []
            
            if mode in ["full", "orchestrator"]:
                logger.info("🤖 Starting Master Orchestrator...")
                tasks.append(asyncio.create_task(self.orchestrator.start_autonomous_pipeline()))
            
            if mode in ["full", "monitor"]:
                logger.info("📊 Starting System Monitor...")
                tasks.append(asyncio.create_task(self.monitor.start_monitoring()))
            
            if mode == "demo":
                logger.info("🎭 Starting Demo Mode...")
                tasks.append(asyncio.create_task(self.run_demo_mode()))
            
            self.running = True
            
            # Run until shutdown signal
            while self.running and tasks:
                # Check if any tasks completed unexpectedly
                done, pending = await asyncio.wait(tasks, timeout=1.0, return_when=asyncio.FIRST_COMPLETED)
                
                for task in done:
                    try:
                        await task
                    except Exception as e:
                        logger.error(f"💥 Task failed: {e}")
                
                # Remove completed tasks
                tasks = list(pending)
            
            # Graceful shutdown
            logger.info("🛑 Shutting down pipeline...")
            for task in tasks:
                task.cancel()
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"💥 Pipeline error: {e}")
            raise
        finally:
            logger.info("✅ Pipeline shutdown complete")
    
    async def create_initial_tasks(self):
        """Create initial improvement tasks for the pipeline."""
        task_queue = TaskQueue()
        
        # Authentication fix task (based on our recent work)
        task_queue.create_task(
            title="Complete Firebase Anonymous Authentication Setup",
            description="Fully resolve Firebase Anonymous Authentication to eliminate login errors",
            priority=Priority.CRITICAL,
            category="security",
            assignee=AgentRole.DEVOPS_SRE,
            tags=["firebase", "authentication", "production"],
            estimated_hours=4
        )
        
        # Performance optimization task
        task_queue.create_task(
            title="Optimize OpenAI API Response Time",
            description="Improve AI response latency and implement caching strategies",
            priority=Priority.HIGH,
            category="performance",
            assignee=AgentRole.BACKEND_ENGINEER,
            tags=["openai", "performance", "caching"],
            estimated_hours=8
        )
        
        # Android development task
        task_queue.create_task(
            title="Implement Android App Foundation",
            description="Develop core Android application based on existing foundation",
            priority=Priority.MEDIUM,
            category="feature",
            assignee=AgentRole.ANDROID_ENGINEER,
            tags=["android", "mobile", "kotlin"],
            estimated_hours=40
        )
        
        # ACIM content validation task
        task_queue.create_task(
            title="Comprehensive ACIM Content Audit",
            description="Validate all ACIM content for accuracy and proper citations",
            priority=Priority.HIGH,
            category="content",
            assignee=AgentRole.ACIM_SCHOLAR,
            tags=["acim", "validation", "content", "citations"],
            estimated_hours=12
        )
        
        # Cost optimization task
        task_queue.create_task(
            title="Firebase Cost Optimization Analysis",
            description="Analyze and optimize Firebase usage to reduce operational costs",
            priority=Priority.MEDIUM,
            category="optimization",
            assignee=AgentRole.DEVOPS_SRE,
            tags=["firebase", "cost", "optimization"],
            estimated_hours=6
        )
        
        logger.info(f"📋 Created {len(task_queue.tasks)} initial tasks")
    
    async def run_demo_mode(self):
        """Run the pipeline in demonstration mode."""
        logger.info("🎭 Running Autonomous Pipeline Demo")
        
        task_queue = TaskQueue()
        
        # Simulate pipeline activity
        for i in range(10):
            if not self.running:
                break
            
            # Show pipeline metrics
            metrics = task_queue.get_pipeline_metrics()
            logger.info(f"📈 Pipeline Metrics: {metrics['completion_rate']:.1%} complete, "
                       f"{metrics['in_progress_tasks']} in progress")
            
            # Simulate task processing
            next_task = task_queue.get_next_task()
            if next_task:
                logger.info(f"🔄 Processing: {next_task.title}")
                task_queue.update_task_status(next_task.id, "completed")
            
            await asyncio.sleep(5)
        
        logger.info("🎭 Demo mode completed")
    
    def status(self):
        """Show pipeline status."""
        task_queue = TaskQueue()
        metrics = task_queue.get_pipeline_metrics()
        
        print("📊 ACIMguide Autonomous Pipeline Status")
        print("=" * 50)
        print(f"Total Tasks: {metrics['total_tasks']}")
        print(f"Completed: {metrics['completed_tasks']} ({metrics['completion_rate']:.1%})")
        print(f"In Progress: {metrics['in_progress_tasks']}")
        print(f"Failed: {metrics['failed_tasks']}")
        print(f"Average Completion Time: {metrics['avg_completion_hours']:.1f} hours")
        print(f"Overdue Tasks: {metrics['overdue_tasks']}")
        print()
        print("Agent Workloads:")
        for agent, workload in metrics['agent_workload'].items():
            print(f"  {agent.replace('_', ' ').title()}: {workload} tasks")
    
    def create_task(self, title: str, description: str, priority: str, category: str):
        """Create a new task via CLI."""
        task_queue = TaskQueue()
        
        priority_map = {
            "critical": Priority.CRITICAL,
            "high": Priority.HIGH,
            "medium": Priority.MEDIUM,
            "low": Priority.LOW
        }
        
        task = task_queue.create_task(
            title=title,
            description=description,
            priority=priority_map.get(priority.lower(), Priority.MEDIUM),
            category=category,
            tags=[category]
        )
        
        print(f"✅ Created task: {task.title} [{task.id}]")

async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="ACIMguide Autonomous Improvement Pipeline")
    parser.add_argument("command", choices=["start", "status", "create-task", "demo"], 
                       help="Command to execute")
    parser.add_argument("--mode", choices=["full", "orchestrator", "monitor", "demo"], 
                       default="full", help="Pipeline mode")
    parser.add_argument("--title", help="Task title (for create-task)")
    parser.add_argument("--description", help="Task description (for create-task)")
    parser.add_argument("--priority", choices=["critical", "high", "medium", "low"], 
                       default="medium", help="Task priority (for create-task)")
    parser.add_argument("--category", help="Task category (for create-task)")
    
    args = parser.parse_args()
    
    launcher = PipelineLauncher()
    
    try:
        if args.command == "start":
            await launcher.start_pipeline(args.mode)
        elif args.command == "demo":
            await launcher.start_pipeline("demo")
        elif args.command == "status":
            launcher.status()
        elif args.command == "create-task":
            if not all([args.title, args.description, args.category]):
                print("❌ Error: --title, --description, and --category are required for create-task")
                sys.exit(1)
            launcher.create_task(args.title, args.description, args.priority, args.category)
    
    except KeyboardInterrupt:
        logger.info("🛑 Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"💥 Pipeline error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
