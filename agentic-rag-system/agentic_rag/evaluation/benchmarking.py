"""
Automated benchmarking system for RAG performance measurement.

This module provides comprehensive benchmarking capabilities including
performance baselines, regression detection, and comparative analysis.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from statistics import mean, stdev
import uuid

from loguru import logger
from pydantic import BaseModel, Field

from .models import EvaluationResult, BenchmarkResult
from .pipeline import EvaluationPipeline
from .synthetic_data import SyntheticQuery
from ..core.models import ToolType


@dataclass
class PerformanceBaseline:
    """Performance baseline for a specific configuration."""
    baseline_id: str
    configuration_name: str
    configuration_hash: str
    
    # Metrics
    metrics: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    
    # Metadata
    sample_size: int
    evaluation_date: datetime
    system_version: str
    
    # Quality indicators
    stability_score: float  # How stable these metrics are
    reliability_score: float  # How reliable the measurements are


class BaselineDatabase:
    """SQLite database for storing performance baselines."""
    
    def __init__(self, db_path: str = "evaluation_baselines.db"):
        """Initialize baseline database."""
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS baselines (
                    baseline_id TEXT PRIMARY KEY,
                    configuration_name TEXT NOT NULL,
                    configuration_hash TEXT NOT NULL,
                    metrics TEXT NOT NULL,  -- JSON
                    confidence_intervals TEXT,  -- JSON
                    sample_size INTEGER NOT NULL,
                    evaluation_date TEXT NOT NULL,
                    system_version TEXT NOT NULL,
                    stability_score REAL NOT NULL,
                    reliability_score REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    evaluation_id TEXT PRIMARY KEY,
                    baseline_id TEXT,
                    configuration_name TEXT NOT NULL,
                    metrics TEXT NOT NULL,  -- JSON
                    evaluation_date TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    query_count INTEGER NOT NULL,
                    system_version TEXT,
                    metadata TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (baseline_id) REFERENCES baselines (baseline_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS regressions (
                    regression_id TEXT PRIMARY KEY,
                    evaluation_id TEXT NOT NULL,
                    baseline_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    baseline_value REAL NOT NULL,
                    regression_percent REAL NOT NULL,
                    severity TEXT NOT NULL,  -- low, medium, high, critical
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'detected',  -- detected, acknowledged, resolved
                    FOREIGN KEY (evaluation_id) REFERENCES evaluations (evaluation_id),
                    FOREIGN KEY (baseline_id) REFERENCES baselines (baseline_id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_baselines_config ON baselines (configuration_name, configuration_hash);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_evaluations_date ON evaluations (evaluation_date);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_regressions_severity ON regressions (severity, detected_at);
            """)
    
    def save_baseline(self, baseline: PerformanceBaseline):
        """Save a performance baseline to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO baselines 
                (baseline_id, configuration_name, configuration_hash, metrics, 
                 confidence_intervals, sample_size, evaluation_date, system_version,
                 stability_score, reliability_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                baseline.baseline_id,
                baseline.configuration_name,
                baseline.configuration_hash,
                json.dumps(baseline.metrics),
                json.dumps({k: list(v) for k, v in baseline.confidence_intervals.items()}),
                baseline.sample_size,
                baseline.evaluation_date.isoformat(),
                baseline.system_version,
                baseline.stability_score,
                baseline.reliability_score
            ))
        
        logger.info(f"Saved baseline {baseline.baseline_id} for {baseline.configuration_name}")
    
    def load_baseline(self, baseline_id: str) -> Optional[PerformanceBaseline]:
        """Load a baseline by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM baselines WHERE baseline_id = ?
            """, (baseline_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            
            return PerformanceBaseline(
                baseline_id=data['baseline_id'],
                configuration_name=data['configuration_name'],
                configuration_hash=data['configuration_hash'],
                metrics=json.loads(data['metrics']),
                confidence_intervals={
                    k: tuple(v) for k, v in json.loads(data['confidence_intervals'] or '{}').items()
                },
                sample_size=data['sample_size'],
                evaluation_date=datetime.fromisoformat(data['evaluation_date']),
                system_version=data['system_version'],
                stability_score=data['stability_score'],
                reliability_score=data['reliability_score']
            )
    
    def find_baseline(self, configuration_name: str, configuration_hash: str) -> Optional[PerformanceBaseline]:
        """Find the most recent baseline for a configuration."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM baselines 
                WHERE configuration_name = ? AND configuration_hash = ?
                ORDER BY evaluation_date DESC 
                LIMIT 1
            """, (configuration_name, configuration_hash))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            
            return PerformanceBaseline(
                baseline_id=data['baseline_id'],
                configuration_name=data['configuration_name'],
                configuration_hash=data['configuration_hash'],
                metrics=json.loads(data['metrics']),
                confidence_intervals={
                    k: tuple(v) for k, v in json.loads(data['confidence_intervals'] or '{}').items()
                },
                sample_size=data['sample_size'],
                evaluation_date=datetime.fromisoformat(data['evaluation_date']),
                system_version=data['system_version'],
                stability_score=data['stability_score'],
                reliability_score=data['reliability_score']
            )
    
    def save_evaluation(self, evaluation_result: EvaluationResult, 
                       configuration_name: str, system_version: str = "1.0"):
        """Save evaluation result to database."""
        if not evaluation_result.system_metrics:
            logger.warning("Cannot save evaluation without system metrics")
            return
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO evaluations 
                (evaluation_id, configuration_name, metrics, evaluation_date, 
                 duration_seconds, query_count, system_version, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evaluation_result.evaluation_id,
                configuration_name,
                json.dumps(evaluation_result.system_metrics.overall_metrics),
                evaluation_result.start_time.isoformat(),
                evaluation_result.total_duration_seconds,
                len(evaluation_result.query_results),
                system_version,
                json.dumps(evaluation_result.config)
            ))
    
    def record_regression(self, evaluation_id: str, baseline_id: str, 
                         metric_name: str, current_value: float, 
                         baseline_value: float, severity: str):
        """Record a performance regression."""
        regression_id = str(uuid.uuid4())
        regression_percent = ((current_value - baseline_value) / baseline_value) * 100
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO regressions 
                (regression_id, evaluation_id, baseline_id, metric_name, 
                 current_value, baseline_value, regression_percent, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                regression_id, evaluation_id, baseline_id, metric_name,
                current_value, baseline_value, regression_percent, severity
            ))
        
        logger.warning(f"Regression detected: {metric_name} dropped {abs(regression_percent):.1f}%")
    
    def get_recent_evaluations(self, days: int = 30) -> List[Dict]:
        """Get recent evaluations for trending analysis."""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM evaluations 
                WHERE evaluation_date > ?
                ORDER BY evaluation_date DESC
            """, (cutoff_date,))
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_active_regressions(self) -> List[Dict]:
        """Get active regressions that haven't been resolved."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT r.*, b.configuration_name, e.evaluation_date
                FROM regressions r
                JOIN baselines b ON r.baseline_id = b.baseline_id
                JOIN evaluations e ON r.evaluation_id = e.evaluation_id
                WHERE r.status = 'detected'
                ORDER BY r.detected_at DESC
            """)
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


class BenchmarkingSystem:
    """Comprehensive benchmarking system for RAG performance."""
    
    def __init__(self, database_path: str = "evaluation_baselines.db"):
        """Initialize benchmarking system."""
        self.db = BaselineDatabase(database_path)
        self.system_version = "1.0"  # Could be read from config
    
    def create_baseline(self, evaluation_results: List[EvaluationResult], 
                       configuration_name: str, 
                       configuration: Dict[str, Any]) -> PerformanceBaseline:
        """Create a performance baseline from multiple evaluation results."""
        
        if not evaluation_results:
            raise ValueError("Need at least one evaluation result to create baseline")
        
        # Calculate configuration hash for consistency
        import hashlib
        config_str = json.dumps(configuration, sort_keys=True)
        configuration_hash = hashlib.md5(config_str.encode()).hexdigest()
        
        # Aggregate metrics across evaluations
        all_metrics = []
        for result in evaluation_results:
            if result.system_metrics:
                all_metrics.append(result.system_metrics.overall_metrics)
        
        if not all_metrics:
            raise ValueError("No system metrics found in evaluation results")
        
        # Calculate mean and confidence intervals
        metrics = {}
        confidence_intervals = {}
        
        metric_names = set()
        for metric_dict in all_metrics:
            metric_names.update(metric_dict.keys())
        
        for metric_name in metric_names:
            values = [m.get(metric_name, 0.0) for m in all_metrics]
            values = [v for v in values if v is not None]
            
            if values:
                metrics[metric_name] = mean(values)
                
                # Calculate 95% confidence interval
                if len(values) > 1:
                    std_err = stdev(values) / (len(values) ** 0.5)
                    margin = 1.96 * std_err  # 95% CI
                    confidence_intervals[metric_name] = (
                        metrics[metric_name] - margin,
                        metrics[metric_name] + margin
                    )
                else:
                    confidence_intervals[metric_name] = (
                        metrics[metric_name],
                        metrics[metric_name]
                    )
        
        # Calculate stability and reliability scores
        stability_score = self._calculate_stability(all_metrics)
        reliability_score = self._calculate_reliability(evaluation_results)
        
        baseline = PerformanceBaseline(
            baseline_id=str(uuid.uuid4()),
            configuration_name=configuration_name,
            configuration_hash=configuration_hash,
            metrics=metrics,
            confidence_intervals=confidence_intervals,
            sample_size=len(evaluation_results),
            evaluation_date=datetime.now(),
            system_version=self.system_version,
            stability_score=stability_score,
            reliability_score=reliability_score
        )
        
        self.db.save_baseline(baseline)
        return baseline
    
    def _calculate_stability(self, all_metrics: List[Dict[str, float]]) -> float:
        """Calculate stability score based on metric variance."""
        if len(all_metrics) < 2:
            return 1.0
        
        stability_scores = []
        
        metric_names = set()
        for metrics in all_metrics:
            metric_names.update(metrics.keys())
        
        for metric_name in metric_names:
            values = [m.get(metric_name, 0.0) for m in all_metrics]
            values = [v for v in values if v is not None and v > 0]
            
            if len(values) > 1:
                avg = mean(values)
                if avg > 0:
                    cv = stdev(values) / avg  # Coefficient of variation
                    # Convert to stability (lower CV = higher stability)
                    stability = max(0.0, 1.0 - cv)
                    stability_scores.append(stability)
        
        return mean(stability_scores) if stability_scores else 0.5
    
    def _calculate_reliability(self, evaluation_results: List[EvaluationResult]) -> float:
        """Calculate reliability score based on evaluation success rates."""
        total_queries = sum(len(r.query_results) for r in evaluation_results)
        if total_queries == 0:
            return 0.0
        
        # Check for errors in results
        successful_queries = 0
        for result in evaluation_results:
            for query_result in result.query_results:
                # Check if at least one tool succeeded
                has_success = any(
                    tool_result.confidence > 0.0 
                    for tool_result in query_result.tool_results.values()
                )
                if has_success:
                    successful_queries += 1
        
        return successful_queries / total_queries if total_queries > 0 else 0.0
    
    def detect_regressions(self, evaluation_result: EvaluationResult, 
                          configuration_name: str,
                          configuration: Dict[str, Any],
                          regression_threshold: float = 0.05) -> List[Dict[str, Any]]:
        """Detect performance regressions against baseline."""
        
        # Find baseline for this configuration
        config_str = json.dumps(configuration, sort_keys=True)
        configuration_hash = hashlib.md5(config_str.encode()).hexdigest()
        
        baseline = self.db.find_baseline(configuration_name, configuration_hash)
        if not baseline:
            logger.info(f"No baseline found for {configuration_name}, cannot detect regressions")
            return []
        
        if not evaluation_result.system_metrics:
            logger.warning("Cannot detect regressions without system metrics")
            return []
        
        # Save current evaluation
        self.db.save_evaluation(evaluation_result, configuration_name, self.system_version)
        
        # Check for regressions
        regressions = []
        current_metrics = evaluation_result.system_metrics.overall_metrics
        
        for metric_name, current_value in current_metrics.items():
            baseline_value = baseline.metrics.get(metric_name)
            if baseline_value is None or baseline_value == 0:
                continue
            
            # Calculate percentage change
            change_percent = (current_value - baseline_value) / baseline_value
            
            # Check if it's a significant regression (negative change)
            if change_percent < -regression_threshold:
                # Determine severity
                if change_percent < -0.2:  # 20%+ drop
                    severity = "critical"
                elif change_percent < -0.1:  # 10%+ drop
                    severity = "high"
                elif change_percent < -0.05:  # 5%+ drop
                    severity = "medium"
                else:
                    severity = "low"
                
                regression = {
                    "metric_name": metric_name,
                    "current_value": current_value,
                    "baseline_value": baseline_value,
                    "change_percent": change_percent * 100,
                    "severity": severity,
                    "baseline_id": baseline.baseline_id
                }
                
                regressions.append(regression)
                
                # Record in database
                self.db.record_regression(
                    evaluation_result.evaluation_id,
                    baseline.baseline_id,
                    metric_name,
                    current_value,
                    baseline_value,
                    severity
                )
        
        return regressions
    
    def get_performance_trends(self, configuration_name: str, 
                             metric_name: str, days: int = 30) -> List[Dict]:
        """Get performance trends for a specific metric."""
        recent_evals = self.db.get_recent_evaluations(days)
        
        # Filter by configuration and extract metric
        trends = []
        for eval_data in recent_evals:
            if eval_data['configuration_name'] == configuration_name:
                metrics = json.loads(eval_data['metrics'])
                if metric_name in metrics:
                    trends.append({
                        'date': eval_data['evaluation_date'],
                        'value': metrics[metric_name],
                        'evaluation_id': eval_data['evaluation_id']
                    })
        
        return sorted(trends, key=lambda x: x['date'])
    
    def generate_benchmark_report(self, configuration_name: str) -> Dict[str, Any]:
        """Generate a comprehensive benchmark report."""
        # Get latest baseline
        recent_evals = self.db.get_recent_evaluations(7)  # Last week
        config_evals = [e for e in recent_evals if e['configuration_name'] == configuration_name]
        
        if not config_evals:
            return {"error": f"No recent evaluations found for {configuration_name}"}
        
        # Get baseline
        latest_eval = config_evals[0]
        config_str = json.dumps(json.loads(latest_eval['metadata']), sort_keys=True)
        configuration_hash = hashlib.md5(config_str.encode()).hexdigest()
        baseline = self.db.find_baseline(configuration_name, configuration_hash)
        
        # Get active regressions
        active_regressions = self.db.get_active_regressions()
        config_regressions = [r for r in active_regressions 
                            if r['configuration_name'] == configuration_name]
        
        report = {
            "configuration_name": configuration_name,
            "report_date": datetime.now().isoformat(),
            "baseline_info": {
                "exists": baseline is not None,
                "date": baseline.evaluation_date.isoformat() if baseline else None,
                "sample_size": baseline.sample_size if baseline else None,
                "stability_score": baseline.stability_score if baseline else None,
                "reliability_score": baseline.reliability_score if baseline else None
            },
            "recent_evaluations": len(config_evals),
            "active_regressions": len(config_regressions),
            "regression_details": config_regressions[:5],  # Top 5 most recent
            "performance_summary": {}
        }
        
        if baseline and config_evals:
            # Compare latest performance with baseline
            latest_metrics = json.loads(latest_eval['metrics'])
            performance_summary = {}
            
            for metric_name, baseline_value in baseline.metrics.items():
                current_value = latest_metrics.get(metric_name)
                if current_value is not None:
                    change_percent = ((current_value - baseline_value) / baseline_value * 100 
                                    if baseline_value != 0 else 0)
                    performance_summary[metric_name] = {
                        "current": current_value,
                        "baseline": baseline_value,
                        "change_percent": change_percent,
                        "trend": "improving" if change_percent > 1 else "stable" if abs(change_percent) <= 1 else "declining"
                    }
            
            report["performance_summary"] = performance_summary
        
        return report
    
    def create_performance_alert(self, regressions: List[Dict], 
                               configuration_name: str) -> Optional[str]:
        """Create a performance alert message for regressions."""
        if not regressions:
            return None
        
        critical = [r for r in regressions if r['severity'] == 'critical']
        high = [r for r in regressions if r['severity'] == 'high']
        medium = [r for r in regressions if r['severity'] == 'medium']
        
        alert_lines = [f"🚨 Performance Alert: {configuration_name}"]
        
        if critical:
            alert_lines.append(f"❌ CRITICAL: {len(critical)} metrics with >20% regression")
            for r in critical[:3]:  # Top 3
                alert_lines.append(f"   - {r['metric_name']}: {r['change_percent']:.1f}% drop")
        
        if high:
            alert_lines.append(f"⚠️  HIGH: {len(high)} metrics with >10% regression")
            
        if medium:
            alert_lines.append(f"📉 MEDIUM: {len(medium)} metrics with >5% regression")
        
        alert_lines.append(f"📊 Total metrics affected: {len(regressions)}")
        
        return "\n".join(alert_lines)


# Utility functions for easy access

def create_performance_baseline(evaluation_results: List[EvaluationResult],
                              configuration_name: str,
                              configuration: Dict[str, Any],
                              database_path: str = "evaluation_baselines.db") -> PerformanceBaseline:
    """Create a performance baseline from evaluation results."""
    benchmarking = BenchmarkingSystem(database_path)
    return benchmarking.create_baseline(evaluation_results, configuration_name, configuration)


def check_for_regressions(evaluation_result: EvaluationResult,
                        configuration_name: str,
                        configuration: Dict[str, Any],
                        database_path: str = "evaluation_baselines.db",
                        threshold: float = 0.05) -> List[Dict[str, Any]]:
    """Check for performance regressions in evaluation result."""
    benchmarking = BenchmarkingSystem(database_path)
    return benchmarking.detect_regressions(
        evaluation_result, configuration_name, configuration, threshold
    )


def generate_performance_report(configuration_name: str,
                              database_path: str = "evaluation_baselines.db") -> Dict[str, Any]:
    """Generate a comprehensive performance report."""
    benchmarking = BenchmarkingSystem(database_path)
    return benchmarking.generate_benchmark_report(configuration_name)
