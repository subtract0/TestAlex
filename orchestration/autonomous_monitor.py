#!/usr/bin/env python3
"""
Autonomous ACIM Guide Monitoring System
Continuous monitoring and autonomous improvement orchestration
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from live_orchestrator import LiveOrchestrationSystem

# Configure logging (create logs directory first)
from pathlib import Path
Path('/home/am/TestAlex/orchestration/logs').mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/am/TestAlex/orchestration/logs/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutonomousMonitor:
    """Continuous monitoring system for ACIM Guide platform."""
    
    def __init__(self, project_root: str = "/home/am/TestAlex"):
        self.project_root = Path(project_root)
        self.orchestrator = LiveOrchestrationSystem(project_root)
        self.running = False
        self.cycle_count = 0
        self.last_cycle_time = None
        self.monitoring_config = self._load_monitoring_config()
        
        # Ensure logs directory exists
        logs_dir = self.project_root / "orchestration" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_monitoring_config(self) -> Dict:
        """Load monitoring configuration."""
        config_file = self.project_root / "orchestration" / "monitoring_config.json"
        
        default_config = {
            "cycle_interval_minutes": 30,
            "max_concurrent_tasks": 3,
            "min_time_between_cycles": 15,  # minutes
            "critical_priority_interval": 5,  # minutes for critical issues
            "health_check_interval": 5,  # minutes
            "metrics_retention_days": 7,
            "enable_email_alerts": False,
            "enable_slack_alerts": False,
            "thresholds": {
                "response_time_critical": 3.0,  # seconds
                "error_rate_critical": 0.01,   # 1%
                "conversion_rate_critical": 0.02,  # 2%
                "bounce_rate_critical": 0.40,  # 40%
                "citation_accuracy_critical": 0.85,  # 85%
                "uptime_critical": 0.95  # 95%
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"Failed to load monitoring config: {e}")
        
        # Save default config
        try:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default monitoring config at {config_file}")
        except Exception as e:
            logger.error(f"Failed to save default config: {e}")
            
        return default_config
    
    async def start_monitoring(self):
        """Start the continuous monitoring loop."""
        logger.info("🚀 Starting ACIM Guide Autonomous Monitor")
        logger.info("=" * 60)
        logger.info(f"📊 Monitoring interval: {self.monitoring_config['cycle_interval_minutes']} minutes")
        logger.info(f"🔍 Health checks every: {self.monitoring_config['health_check_interval']} minutes")
        logger.info(f"🎯 Max concurrent tasks: {self.monitoring_config['max_concurrent_tasks']}")
        logger.info("=" * 60)
        
        self.running = True
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Start monitoring tasks
            health_task = asyncio.create_task(self._health_check_loop())
            orchestration_task = asyncio.create_task(self._orchestration_loop())
            status_task = asyncio.create_task(self._status_reporting_loop())
            
            # Wait for tasks to complete
            await asyncio.gather(health_task, orchestration_task, status_task)
            
        except Exception as e:
            logger.error(f"❌ Monitoring failed: {e}")
        finally:
            logger.info("🛑 Autonomous monitoring stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def _health_check_loop(self):
        """Continuous health monitoring loop."""
        logger.info("💓 Starting health check loop")
        
        while self.running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.monitoring_config['health_check_interval'] * 60)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    async def _orchestration_loop(self):
        """Continuous orchestration loop."""
        logger.info("🤖 Starting orchestration loop")
        
        while self.running:
            try:
                # Check if enough time has passed since last cycle
                if self._should_run_cycle():
                    await self._run_orchestration_cycle()
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Orchestration loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _status_reporting_loop(self):
        """Periodic status reporting loop."""
        logger.info("📈 Starting status reporting loop")
        
        while self.running:
            try:
                await self._report_system_status()
                await asyncio.sleep(900)  # Report every 15 minutes
            except Exception as e:
                logger.error(f"Status reporting error: {e}")
                await asyncio.sleep(600)  # Retry after 10 minutes
    
    def _should_run_cycle(self) -> bool:
        """Determine if an orchestration cycle should run."""
        current_time = datetime.now()
        
        # Always run if this is the first cycle
        if self.last_cycle_time is None:
            return True
        
        # Calculate time since last cycle
        time_since_last = (current_time - self.last_cycle_time).total_seconds() / 60
        
        # Check minimum time between cycles
        if time_since_last < self.monitoring_config['min_time_between_cycles']:
            return False
        
        # Run regular cycles based on interval
        if time_since_last >= self.monitoring_config['cycle_interval_minutes']:
            return True
        
        # TODO: Add logic for critical issues that require immediate attention
        
        return False
    
    async def _perform_health_check(self):
        """Perform basic health checks on the system."""
        logger.debug("🔍 Performing health check")
        
        try:
            # Monitor production metrics
            metrics = await self.orchestrator.monitor_production_health()
            
            # Check for critical thresholds
            critical_issues = self._identify_critical_issues(metrics)
            
            if critical_issues:
                logger.warning(f"⚠️ Critical issues detected: {len(critical_issues)}")
                for issue in critical_issues:
                    logger.warning(f"   • {issue}")
                
                # TODO: Send alerts if configured
                await self._handle_critical_issues(critical_issues, metrics)
            
            # Log health status
            self._log_health_metrics(metrics)
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    def _identify_critical_issues(self, metrics: Dict) -> List[str]:
        """Identify critical issues from metrics."""
        issues = []
        thresholds = self.monitoring_config['thresholds']
        
        # Technical health checks
        tech_health = metrics.get('technical_health', {})
        if tech_health.get('response_time_avg', 0) > thresholds['response_time_critical']:
            issues.append(f"High response time: {tech_health['response_time_avg']:.1f}s")
        
        if tech_health.get('error_rate', 0) > thresholds['error_rate_critical']:
            issues.append(f"High error rate: {tech_health['error_rate']*100:.1f}%")
        
        if tech_health.get('uptime', 1) < thresholds['uptime_critical']:
            issues.append(f"Low uptime: {tech_health['uptime']*100:.1f}%")
        
        # User engagement checks
        user_engagement = metrics.get('user_engagement', {})
        if user_engagement.get('conversion_rate', 1) < thresholds['conversion_rate_critical']:
            issues.append(f"Low conversion rate: {user_engagement['conversion_rate']*100:.1f}%")
        
        if user_engagement.get('bounce_rate', 0) > thresholds['bounce_rate_critical']:
            issues.append(f"High bounce rate: {user_engagement['bounce_rate']*100:.1f}%")
        
        # Content quality checks
        content_quality = metrics.get('content_quality', {})
        if content_quality.get('citation_completeness', 1) < thresholds['citation_accuracy_critical']:
            issues.append(f"Low ACIM citation accuracy: {content_quality['citation_completeness']*100:.1f}%")
        
        return issues
    
    async def _handle_critical_issues(self, issues: List[str], metrics: Dict):
        """Handle critical issues by triggering immediate orchestration."""
        logger.warning("🚨 Handling critical issues immediately")
        
        # Force an orchestration cycle for critical issues
        if self._should_force_critical_cycle():
            await self._run_orchestration_cycle(force_critical=True)
    
    def _should_force_critical_cycle(self) -> bool:
        """Check if a critical cycle should be forced."""
        if self.last_cycle_time is None:
            return True
        
        time_since_last = (datetime.now() - self.last_cycle_time).total_seconds() / 60
        return time_since_last >= self.monitoring_config['critical_priority_interval']
    
    def _log_health_metrics(self, metrics: Dict):
        """Log key health metrics."""
        tech = metrics.get('technical_health', {})
        user = metrics.get('user_engagement', {})
        content = metrics.get('content_quality', {})
        
        logger.info(f"💓 Health: Response {tech.get('response_time_avg', 0):.1f}s, "
                   f"Uptime {tech.get('uptime', 0)*100:.1f}%, "
                   f"Conversion {user.get('conversion_rate', 0)*100:.1f}%, "
                   f"ACIM Accuracy {content.get('citation_completeness', 0)*100:.1f}%")
    
    async def _run_orchestration_cycle(self, force_critical: bool = False):
        """Run a full orchestration cycle."""
        self.cycle_count += 1
        logger.info(f"🔄 Running orchestration cycle #{self.cycle_count} "
                   f"{'(CRITICAL)' if force_critical else ''}")
        
        try:
            # Run the orchestration cycle
            cycle_result = await self.orchestrator.run_orchestration_cycle()
            
            # Save results
            await self.orchestrator.save_cycle_results(cycle_result)
            
            # Update last cycle time
            self.last_cycle_time = datetime.now()
            
            # Log cycle summary
            self._log_cycle_summary(cycle_result)
            
        except Exception as e:
            logger.error(f"❌ Orchestration cycle failed: {e}")
    
    def _log_cycle_summary(self, cycle_result: Dict):
        """Log orchestration cycle summary."""
        if cycle_result.get('success', True):
            logger.info(f"✅ Cycle completed: {cycle_result.get('opportunities_identified', 0)} opportunities, "
                       f"{cycle_result.get('tasks_executed', 0)} tasks executed, "
                       f"{cycle_result.get('success_rate', 0)*100:.0f}% success rate")
        else:
            logger.error(f"❌ Cycle failed: {cycle_result.get('error', 'Unknown error')}")
    
    async def _report_system_status(self):
        """Report comprehensive system status."""
        logger.info("📊 SYSTEM STATUS REPORT")
        logger.info(f"   🔄 Cycles completed: {self.cycle_count}")
        logger.info(f"   ⏰ Last cycle: {self.last_cycle_time.strftime('%H:%M:%S') if self.last_cycle_time else 'Never'}")
        logger.info(f"   💾 Config: {self.monitoring_config['cycle_interval_minutes']}min intervals")
        
        # Get recent metrics
        try:
            metrics = await self.orchestrator.monitor_production_health()
            
            logger.info("   📈 Current Metrics:")
            logger.info(f"      • Users: {metrics['user_engagement']['daily_active_users']}")
            logger.info(f"      • Response Time: {metrics['technical_health']['response_time_avg']:.1f}s")
            logger.info(f"      • Uptime: {metrics['technical_health']['uptime']*100:.1f}%")
            logger.info(f"      • ACIM Accuracy: {metrics['content_quality']['citation_completeness']*100:.0f}%")
            logger.info(f"      • Revenue: ${metrics['business_metrics']['monthly_revenue']}")
            
        except Exception as e:
            logger.error(f"   ❌ Failed to get current metrics: {e}")
    
    async def stop_monitoring(self):
        """Stop the monitoring system gracefully."""
        logger.info("🛑 Stopping autonomous monitoring...")
        self.running = False


async def main():
    """Run the autonomous monitoring system."""
    monitor = AutonomousMonitor()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("🔚 Monitoring interrupted by user")
    except Exception as e:
        logger.error(f"❌ Monitoring failed: {e}")
    finally:
        await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
