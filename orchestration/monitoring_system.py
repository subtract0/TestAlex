#!/usr/bin/env python3
"""
ACIMguide Autonomous Improvement Pipeline - Monitoring System
Continuous monitoring of system health, performance, and improvement opportunities.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import subprocess
import requests
import psutil
from dataclasses import dataclass, asdict

from task_queue import TaskQueue, Priority, AgentRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MetricThreshold:
    """Defines thresholds for monitoring metrics."""
    name: str
    warning_threshold: float
    critical_threshold: float
    unit: str
    description: str

@dataclass
class MonitoringAlert:
    """Represents a monitoring alert."""
    id: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str  # warning, critical
    timestamp: datetime
    description: str
    suggested_actions: List[str]

class SystemMonitor:
    """Monitors system health and performance metrics."""
    
    def __init__(self, project_root: str = "/home/am/TestAlex"):
        self.project_root = Path(project_root)
        self.task_queue = TaskQueue()
        self.metrics_history = {}
        self.active_alerts = {}
        self.thresholds = self._initialize_thresholds()
        self.monitoring_config = self._load_monitoring_config()
    
    def _initialize_thresholds(self) -> Dict[str, MetricThreshold]:
        """Initialize monitoring thresholds for various metrics."""
        return {
            "api_response_time": MetricThreshold(
                name="api_response_time",
                warning_threshold=500,  # 500ms
                critical_threshold=1000,  # 1s
                unit="ms",
                description="Average API response time"
            ),
            "error_rate": MetricThreshold(
                name="error_rate",
                warning_threshold=0.05,  # 5%
                critical_threshold=0.10,  # 10%
                unit="%",
                description="Error rate percentage"
            ),
            "firebase_costs": MetricThreshold(
                name="firebase_costs",
                warning_threshold=400,  # $400/month
                critical_threshold=500,  # $500/month
                unit="USD",
                description="Monthly Firebase costs"
            ),
            "user_satisfaction": MetricThreshold(
                name="user_satisfaction",
                warning_threshold=4.5,  # Below 4.5 stars
                critical_threshold=4.0,  # Below 4.0 stars
                unit="stars",
                description="User satisfaction rating"
            ),
            "acim_content_accuracy": MetricThreshold(
                name="acim_content_accuracy",
                warning_threshold=0.98,  # 98%
                critical_threshold=0.95,  # 95%
                unit="%",
                description="ACIM content accuracy percentage"
            ),
            "system_uptime": MetricThreshold(
                name="system_uptime",
                warning_threshold=0.999,  # 99.9%
                critical_threshold=0.995,  # 99.5%
                unit="%",
                description="System uptime percentage"
            )
        }
    
    def _load_monitoring_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        config_file = self.project_root / "orchestration" / "monitoring_config.json"
        
        default_config = {
            "monitoring_interval": 300,  # 5 minutes
            "alert_cooldown": 3600,  # 1 hour
            "metrics_retention_days": 30,
            "firebase_project_id": "acim-guide-test",
            "endpoints_to_monitor": [
                "https://acim-guide-test.web.app/",
                "https://us-central1-acim-guide-test.cloudfunctions.net/chatWithAssistant"
            ]
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                return {**default_config, **config}
            except Exception as e:
                logger.error(f"Error loading monitoring config: {e}")
        
        # Save default config
        config_file.parent.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    async def start_monitoring(self):
        """Start the continuous monitoring system."""
        logger.info("🔍 Starting ACIMguide monitoring system")
        
        while True:
            try:
                # Collect all metrics
                metrics = await self.collect_all_metrics()
                
                # Store metrics history
                self._store_metrics(metrics)
                
                # Check thresholds and generate alerts
                alerts = self._check_thresholds(metrics)
                
                # Process alerts and generate improvement tasks
                await self._process_alerts(alerts)
                
                # Generate improvement opportunities
                await self._generate_improvement_opportunities(metrics)
                
                # Log monitoring status
                logger.info(f"📊 Monitoring cycle completed - {len(metrics)} metrics, {len(alerts)} alerts")
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_config["monitoring_interval"])
                
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry
    
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all system metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system_performance": await self._collect_system_performance(),
            "api_performance": await self._collect_api_performance(),
            "firebase_metrics": await self._collect_firebase_metrics(),
            "user_experience": await self._collect_user_experience_metrics(),
            "acim_content": await self._collect_acim_content_metrics(),
            "cost_metrics": await self._collect_cost_metrics()
        }
        
        return metrics
    
    async def _collect_system_performance(self) -> Dict[str, Any]:
        """Collect system performance metrics."""
        try:
            return {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            }
        except Exception as e:
            logger.error(f"Error collecting system performance: {e}")
            return {}
    
    async def _collect_api_performance(self) -> Dict[str, Any]:
        """Collect API performance metrics."""
        metrics = {
            "endpoints": {},
            "average_response_time": 0,
            "error_rate": 0,
            "uptime": 1.0
        }
        
        total_response_time = 0
        total_requests = 0
        errors = 0
        
        for endpoint in self.monitoring_config["endpoints_to_monitor"]:
            try:
                start_time = time.time()
                response = requests.get(endpoint, timeout=10)
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                
                metrics["endpoints"][endpoint] = {
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "success": response.status_code < 400
                }
                
                total_response_time += response_time
                total_requests += 1
                
                if response.status_code >= 400:
                    errors += 1
                
            except Exception as e:
                logger.error(f"Error monitoring endpoint {endpoint}: {e}")
                metrics["endpoints"][endpoint] = {
                    "response_time": 0,
                    "status_code": 0,
                    "success": False,
                    "error": str(e)
                }
                errors += 1
                total_requests += 1
        
        if total_requests > 0:
            metrics["average_response_time"] = total_response_time / total_requests
            metrics["error_rate"] = errors / total_requests
            metrics["uptime"] = (total_requests - errors) / total_requests
        
        return metrics
    
    async def _collect_firebase_metrics(self) -> Dict[str, Any]:
        """Collect Firebase-specific metrics."""
        # In a real implementation, this would use Firebase Admin SDK
        # to collect metrics from Firebase Console
        return {
            "functions_invocations": 1250,  # Simulated
            "firestore_reads": 8500,
            "firestore_writes": 1200,
            "hosting_bandwidth": "2.5GB",
            "authentication_users": 150
        }
    
    async def _collect_user_experience_metrics(self) -> Dict[str, Any]:
        """Collect user experience metrics."""
        # In a real implementation, this would integrate with analytics
        return {
            "user_satisfaction": 4.7,  # Simulated app store rating
            "session_duration": 12.5,  # Average minutes
            "bounce_rate": 0.15,
            "feature_usage": {
                "search": 0.85,
                "quick_actions": 0.72,
                "chat": 0.91
            }
        }
    
    async def _collect_acim_content_metrics(self) -> Dict[str, Any]:
        """Collect ACIM content integrity metrics."""
        # In a real implementation, this would validate ACIM content
        return {
            "content_accuracy": 0.999,  # 99.9% accuracy
            "citation_accuracy": 0.995,
            "search_precision": 0.92,
            "search_recall": 0.88,
            "content_completeness": 1.0
        }
    
    async def _collect_cost_metrics(self) -> Dict[str, Any]:
        """Collect cost and resource utilization metrics."""
        # In a real implementation, this would use cloud billing APIs
        return {
            "monthly_cost": 285,  # USD
            "cost_per_user": 1.90,
            "resource_utilization": {
                "functions": 0.65,
                "firestore": 0.45,
                "hosting": 0.30
            },
            "cost_trend": "stable"
        }
    
    def _store_metrics(self, metrics: Dict[str, Any]):
        """Store metrics in history for trend analysis."""
        timestamp = metrics["timestamp"]
        
        # Store in memory (in production, use proper time-series database)
        if "history" not in self.metrics_history:
            self.metrics_history["history"] = []
        
        self.metrics_history["history"].append(metrics)
        
        # Keep only recent history
        retention_days = self.monitoring_config["metrics_retention_days"]
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        self.metrics_history["history"] = [
            m for m in self.metrics_history["history"]
            if datetime.fromisoformat(m["timestamp"]) > cutoff_date
        ]
    
    def _check_thresholds(self, metrics: Dict[str, Any]) -> List[MonitoringAlert]:
        """Check metrics against thresholds and generate alerts."""
        alerts = []
        
        # Check API response time
        avg_response_time = metrics.get("api_performance", {}).get("average_response_time", 0)
        alert = self._check_metric_threshold("api_response_time", avg_response_time)
        if alert:
            alerts.append(alert)
        
        # Check error rate
        error_rate = metrics.get("api_performance", {}).get("error_rate", 0)
        alert = self._check_metric_threshold("error_rate", error_rate)
        if alert:
            alerts.append(alert)
        
        # Check Firebase costs
        monthly_cost = metrics.get("cost_metrics", {}).get("monthly_cost", 0)
        alert = self._check_metric_threshold("firebase_costs", monthly_cost)
        if alert:
            alerts.append(alert)
        
        # Check user satisfaction
        satisfaction = metrics.get("user_experience", {}).get("user_satisfaction", 5.0)
        alert = self._check_metric_threshold("user_satisfaction", satisfaction, reverse=True)
        if alert:
            alerts.append(alert)
        
        # Check ACIM content accuracy
        content_accuracy = metrics.get("acim_content", {}).get("content_accuracy", 1.0)
        alert = self._check_metric_threshold("acim_content_accuracy", content_accuracy, reverse=True)
        if alert:
            alerts.append(alert)
        
        # Check system uptime
        uptime = metrics.get("api_performance", {}).get("uptime", 1.0)
        alert = self._check_metric_threshold("system_uptime", uptime, reverse=True)
        if alert:
            alerts.append(alert)
        
        return alerts
    
    def _check_metric_threshold(
        self, 
        metric_name: str, 
        value: float, 
        reverse: bool = False
    ) -> Optional[MonitoringAlert]:
        """Check a single metric against its threshold."""
        threshold = self.thresholds.get(metric_name)
        if not threshold:
            return None
        
        # Determine if threshold is exceeded
        if reverse:
            # For metrics where lower is worse (e.g., satisfaction, uptime)
            critical_exceeded = value < threshold.critical_threshold
            warning_exceeded = value < threshold.warning_threshold and not critical_exceeded
        else:
            # For metrics where higher is worse (e.g., response time, error rate)
            critical_exceeded = value > threshold.critical_threshold
            warning_exceeded = value > threshold.warning_threshold and not critical_exceeded
        
        if critical_exceeded:
            severity = "critical"
            threshold_value = threshold.critical_threshold
        elif warning_exceeded:
            severity = "warning"
            threshold_value = threshold.warning_threshold
        else:
            return None
        
        # Check alert cooldown
        alert_key = f"{metric_name}_{severity}"
        if alert_key in self.active_alerts:
            last_alert = self.active_alerts[alert_key]
            cooldown = timedelta(seconds=self.monitoring_config["alert_cooldown"])
            if datetime.now() - last_alert < cooldown:
                return None
        
        # Create alert
        alert = MonitoringAlert(
            id=f"alert_{int(time.time())}",
            metric_name=metric_name,
            current_value=value,
            threshold_value=threshold_value,
            severity=severity,
            timestamp=datetime.now(),
            description=f"{threshold.description} is {severity}: {value}{threshold.unit}",
            suggested_actions=self._get_suggested_actions(metric_name, severity)
        )
        
        # Record alert time
        self.active_alerts[alert_key] = datetime.now()
        
        return alert
    
    def _get_suggested_actions(self, metric_name: str, severity: str) -> List[str]:
        """Get suggested actions for specific metric alerts."""
        actions = {
            "api_response_time": [
                "Optimize database queries",
                "Implement caching",
                "Scale Firebase Functions",
                "Review OpenAI API usage"
            ],
            "error_rate": [
                "Review error logs",
                "Implement better error handling",
                "Check Firebase Functions health",
                "Validate API endpoints"
            ],
            "firebase_costs": [
                "Optimize Firebase Functions usage",
                "Implement request caching",
                "Review Firestore query patterns",
                "Consider usage limits"
            ],
            "user_satisfaction": [
                "Analyze user feedback",
                "Improve app performance",
                "Enhance user experience",
                "Fix reported bugs"
            ],
            "acim_content_accuracy": [
                "Run ACIM content validation",
                "Review search algorithms",
                "Check citation accuracy",
                "Validate content sources"
            ],
            "system_uptime": [
                "Investigate system outages",
                "Implement health checks",
                "Review deployment process",
                "Set up redundancy"
            ]
        }
        
        return actions.get(metric_name, ["Investigate and resolve issue"])
    
    async def _process_alerts(self, alerts: List[MonitoringAlert]):
        """Process alerts and generate improvement tasks."""
        for alert in alerts:
            logger.warning(f"🚨 {alert.severity.upper()} ALERT: {alert.description}")
            
            # Generate improvement task for critical alerts
            if alert.severity == "critical":
                await self._create_alert_task(alert)
    
    async def _create_alert_task(self, alert: MonitoringAlert):
        """Create an improvement task based on an alert."""
        priority = Priority.CRITICAL if alert.severity == "critical" else Priority.HIGH
        
        # Determine appropriate agent based on metric
        agent_mapping = {
            "api_response_time": AgentRole.BACKEND_ENGINEER,
            "error_rate": AgentRole.DEVOPS_SRE,
            "firebase_costs": AgentRole.DEVOPS_SRE,
            "user_satisfaction": AgentRole.PRODUCT_MANAGER,
            "acim_content_accuracy": AgentRole.ACIM_SCHOLAR,
            "system_uptime": AgentRole.DEVOPS_SRE
        }
        
        assignee = agent_mapping.get(alert.metric_name)
        
        task = self.task_queue.create_task(
            title=f"Resolve {alert.metric_name} Alert",
            description=f"{alert.description}\n\nSuggested actions:\n" + 
                       "\n".join(f"- {action}" for action in alert.suggested_actions),
            priority=priority,
            category="alert_response",
            assignee=assignee,
            tags=[alert.metric_name, "alert", alert.severity],
            estimated_hours=4 if alert.severity == "critical" else 8,
            metadata={
                "alert_id": alert.id,
                "metric_value": alert.current_value,
                "threshold_value": alert.threshold_value
            }
        )
        
        logger.info(f"📋 Created alert task: {task.title} [{task.id}]")
    
    async def _generate_improvement_opportunities(self, metrics: Dict[str, Any]):
        """Generate improvement opportunities based on metric trends."""
        # Analyze trends and generate proactive improvement tasks
        
        # Example: If response time is trending upward, suggest optimization
        if self._is_metric_trending_up("api_response_time"):
            existing_tasks = [
                task for task in self.task_queue.tasks.values()
                if "performance" in task.tags and task.status.value in ["pending", "in_progress"]
            ]
            
            if not existing_tasks:
                self.task_queue.create_task(
                    title="Proactive Performance Optimization",
                    description="Optimize system performance based on trending metrics",
                    priority=Priority.MEDIUM,
                    category="optimization",
                    tags=["performance", "proactive"],
                    estimated_hours=12
                )
    
    def _is_metric_trending_up(self, metric_name: str) -> bool:
        """Check if a metric is trending upward."""
        # Simple trend analysis (in production, use proper statistical methods)
        if len(self.metrics_history.get("history", [])) < 3:
            return False
        
        recent_values = []
        for record in self.metrics_history["history"][-3:]:
            if metric_name == "api_response_time":
                value = record.get("api_performance", {}).get("average_response_time", 0)
                recent_values.append(value)
        
        if len(recent_values) >= 3:
            return recent_values[-1] > recent_values[0]
        
        return False
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        latest_metrics = self.metrics_history.get("history", [])[-1] if self.metrics_history.get("history") else {}
        
        return {
            "current_metrics": latest_metrics,
            "active_alerts": len(self.active_alerts),
            "system_health": "healthy" if not self.active_alerts else "degraded",
            "pipeline_metrics": self.task_queue.get_pipeline_metrics(),
            "uptime": latest_metrics.get("api_performance", {}).get("uptime", 1.0),
            "response_time": latest_metrics.get("api_performance", {}).get("average_response_time", 0),
            "cost": latest_metrics.get("cost_metrics", {}).get("monthly_cost", 0)
        }

# Example usage and testing
async def main():
    """Test the monitoring system."""
    monitor = SystemMonitor()
    
    print("🔍 Testing ACIMguide Monitoring System")
    
    # Collect metrics once
    metrics = await monitor.collect_all_metrics()
    print(f"📊 Collected metrics: {json.dumps(metrics, indent=2)}")
    
    # Check thresholds
    alerts = monitor._check_thresholds(metrics)
    print(f"🚨 Generated {len(alerts)} alerts")
    
    for alert in alerts:
        print(f"  - {alert.severity}: {alert.description}")
    
    # Get dashboard data
    dashboard = monitor.get_monitoring_dashboard_data()
    print(f"📈 Dashboard data: {json.dumps(dashboard, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
