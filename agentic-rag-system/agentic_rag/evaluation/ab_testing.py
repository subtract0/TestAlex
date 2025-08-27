"""
A/B testing infrastructure for RAG system experiments.

This module provides comprehensive A/B testing capabilities including
experiment design, statistical significance testing, and result analysis.
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import math
from statistics import mean, stdev

import sqlite3
from loguru import logger
from pydantic import BaseModel, Field

from .models import EvaluationResult, BenchmarkResult
from .pipeline import EvaluationPipeline
from .synthetic_data import SyntheticQuery
from .benchmarking import BenchmarkingSystem
from ..core.models import ToolType


class ExperimentStatus(str, Enum):
    """Status of an A/B test experiment."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StatisticalTest(str, Enum):
    """Types of statistical tests available."""
    WELCH_T_TEST = "welch_t_test"
    MANN_WHITNEY_U = "mann_whitney_u"
    CHI_SQUARE = "chi_square"
    BOOTSTRAP = "bootstrap"


@dataclass
class ExperimentConfiguration:
    """Configuration for an A/B test experiment."""
    experiment_id: str
    name: str
    description: str
    
    # Experiment design
    control_config: Dict[str, Any]
    treatment_config: Dict[str, Any]
    
    # Statistical parameters
    primary_metric: str
    secondary_metrics: List[str]
    minimum_detectable_effect: float  # e.g., 0.05 for 5%
    statistical_power: float  # e.g., 0.8 for 80%
    significance_level: float  # e.g., 0.05 for 95% confidence
    
    # Experiment parameters
    sample_size_per_group: Optional[int] = None
    max_duration_days: int = 30
    
    # Metadata
    created_by: str = "system"
    created_at: datetime = None
    status: ExperimentStatus = ExperimentStatus.DRAFT
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class StatisticalResult:
    """Result of a statistical significance test."""
    test_type: StatisticalTest
    statistic: float
    p_value: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    power: float
    
    # Interpretation
    conclusion: str
    recommendation: str


class ExperimentDatabase:
    """SQLite database for storing A/B test experiments."""
    
    def __init__(self, db_path: str = "ab_experiments.db"):
        """Initialize experiment database."""
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    control_config TEXT NOT NULL,  -- JSON
                    treatment_config TEXT NOT NULL,  -- JSON
                    primary_metric TEXT NOT NULL,
                    secondary_metrics TEXT,  -- JSON array
                    minimum_detectable_effect REAL NOT NULL,
                    statistical_power REAL NOT NULL,
                    significance_level REAL NOT NULL,
                    sample_size_per_group INTEGER,
                    max_duration_days INTEGER NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS experiment_results (
                    result_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    group_name TEXT NOT NULL,  -- 'control' or 'treatment'
                    evaluation_id TEXT NOT NULL,
                    metrics TEXT NOT NULL,  -- JSON
                    sample_count INTEGER NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS statistical_tests (
                    test_id TEXT PRIMARY KEY,
                    experiment_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    test_type TEXT NOT NULL,
                    statistic REAL NOT NULL,
                    p_value REAL NOT NULL,
                    effect_size REAL NOT NULL,
                    confidence_interval_lower REAL NOT NULL,
                    confidence_interval_upper REAL NOT NULL,
                    is_significant BOOLEAN NOT NULL,
                    power REAL NOT NULL,
                    conclusion TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    computed_at TEXT NOT NULL,
                    FOREIGN KEY (experiment_id) REFERENCES experiments (experiment_id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments (status, created_at);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_results_experiment ON experiment_results (experiment_id, group_name);
            """)
    
    def save_experiment(self, config: ExperimentConfiguration):
        """Save experiment configuration."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO experiments 
                (experiment_id, name, description, control_config, treatment_config,
                 primary_metric, secondary_metrics, minimum_detectable_effect, 
                 statistical_power, significance_level, sample_size_per_group,
                 max_duration_days, created_by, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config.experiment_id,
                config.name,
                config.description,
                json.dumps(config.control_config),
                json.dumps(config.treatment_config),
                config.primary_metric,
                json.dumps(config.secondary_metrics),
                config.minimum_detectable_effect,
                config.statistical_power,
                config.significance_level,
                config.sample_size_per_group,
                config.max_duration_days,
                config.created_by,
                config.created_at.isoformat(),
                config.status.value
            ))
    
    def load_experiment(self, experiment_id: str) -> Optional[ExperimentConfiguration]:
        """Load experiment configuration."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM experiments WHERE experiment_id = ?
            """, (experiment_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            
            return ExperimentConfiguration(
                experiment_id=data['experiment_id'],
                name=data['name'],
                description=data['description'],
                control_config=json.loads(data['control_config']),
                treatment_config=json.loads(data['treatment_config']),
                primary_metric=data['primary_metric'],
                secondary_metrics=json.loads(data['secondary_metrics']),
                minimum_detectable_effect=data['minimum_detectable_effect'],
                statistical_power=data['statistical_power'],
                significance_level=data['significance_level'],
                sample_size_per_group=data['sample_size_per_group'],
                max_duration_days=data['max_duration_days'],
                created_by=data['created_by'],
                created_at=datetime.fromisoformat(data['created_at']),
                status=ExperimentStatus(data['status'])
            )
    
    def save_experiment_result(self, experiment_id: str, group_name: str,
                             evaluation_result: EvaluationResult):
        """Save results from an experiment group."""
        if not evaluation_result.system_metrics:
            logger.warning("Cannot save experiment result without system metrics")
            return
        
        result_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO experiment_results 
                (result_id, experiment_id, group_name, evaluation_id, metrics, 
                 sample_count, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result_id,
                experiment_id,
                group_name,
                evaluation_result.evaluation_id,
                json.dumps(evaluation_result.system_metrics.overall_metrics),
                len(evaluation_result.query_results),
                datetime.now().isoformat()
            ))
    
    def get_experiment_results(self, experiment_id: str) -> Dict[str, List[Dict]]:
        """Get all results for an experiment grouped by control/treatment."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM experiment_results 
                WHERE experiment_id = ?
                ORDER BY recorded_at
            """, (experiment_id,))
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        grouped = {"control": [], "treatment": []}
        for result in results:
            group = result['group_name']
            if group in grouped:
                result['metrics'] = json.loads(result['metrics'])
                grouped[group].append(result)
        
        return grouped
    
    def save_statistical_test(self, experiment_id: str, metric_name: str, 
                            result: StatisticalResult):
        """Save statistical test result."""
        test_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO statistical_tests 
                (test_id, experiment_id, metric_name, test_type, statistic, p_value,
                 effect_size, confidence_interval_lower, confidence_interval_upper,
                 is_significant, power, conclusion, recommendation, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                test_id, experiment_id, metric_name, result.test_type.value,
                result.statistic, result.p_value, result.effect_size,
                result.confidence_interval[0], result.confidence_interval[1],
                result.is_significant, result.power, result.conclusion,
                result.recommendation, datetime.now().isoformat()
            ))


class StatisticalAnalyzer:
    """Statistical analysis for A/B test results."""
    
    @staticmethod
    def calculate_sample_size(effect_size: float, power: float = 0.8, 
                            alpha: float = 0.05) -> int:
        """Calculate required sample size for detecting effect."""
        # Simplified sample size calculation (assumes normal distribution)
        # For more precise calculations, would need specific distribution assumptions
        
        from scipy import stats
        
        # Two-tailed test
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = stats.norm.ppf(power)
        
        # Cohen's formula for two-sample t-test
        n_per_group = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        
        return math.ceil(n_per_group)
    
    @staticmethod
    def welch_t_test(control_values: List[float], 
                    treatment_values: List[float],
                    alpha: float = 0.05) -> StatisticalResult:
        """Perform Welch's t-test (assumes unequal variances)."""
        
        if len(control_values) < 2 or len(treatment_values) < 2:
            return StatisticalResult(
                test_type=StatisticalTest.WELCH_T_TEST,
                statistic=0.0,
                p_value=1.0,
                effect_size=0.0,
                confidence_interval=(0.0, 0.0),
                is_significant=False,
                power=0.0,
                conclusion="Insufficient data for statistical test",
                recommendation="Collect more samples"
            )
        
        # Calculate statistics
        mean_c, mean_t = mean(control_values), mean(treatment_values)
        var_c, var_t = stdev(control_values)**2, stdev(treatment_values)**2
        n_c, n_t = len(control_values), len(treatment_values)
        
        # Effect size (Cohen's d)
        pooled_std = math.sqrt(((n_c - 1) * var_c + (n_t - 1) * var_t) / (n_c + n_t - 2))
        cohens_d = (mean_t - mean_c) / pooled_std if pooled_std > 0 else 0.0
        
        # Welch's t-statistic
        se_diff = math.sqrt(var_c/n_c + var_t/n_t)
        t_stat = (mean_t - mean_c) / se_diff if se_diff > 0 else 0.0
        
        # Degrees of freedom (Welch-Satterthwaite equation)
        if var_c > 0 and var_t > 0:
            df = (var_c/n_c + var_t/n_t)**2 / ((var_c/n_c)**2/(n_c-1) + (var_t/n_t)**2/(n_t-1))
        else:
            df = n_c + n_t - 2
        
        # P-value (two-tailed)
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
        
        # Confidence interval for difference of means
        t_critical = stats.t.ppf(1 - alpha/2, df)
        margin = t_critical * se_diff
        ci_lower = (mean_t - mean_c) - margin
        ci_upper = (mean_t - mean_c) + margin
        
        # Statistical power (approximate)
        effect_size_observed = abs(cohens_d)
        power = StatisticalAnalyzer._calculate_power(effect_size_observed, n_c, n_t, alpha)
        
        is_significant = p_value < alpha
        
        # Interpretation
        if is_significant:
            direction = "higher" if mean_t > mean_c else "lower"
            conclusion = f"Treatment shows significantly {direction} performance (p={p_value:.4f})"
            if abs(cohens_d) > 0.8:
                effect_desc = "large"
            elif abs(cohens_d) > 0.5:
                effect_desc = "medium"
            elif abs(cohens_d) > 0.2:
                effect_desc = "small"
            else:
                effect_desc = "negligible"
            recommendation = f"Effect size is {effect_desc} (Cohen's d={cohens_d:.3f}). Consider practical significance."
        else:
            conclusion = f"No significant difference detected (p={p_value:.4f})"
            recommendation = "Continue experiment or increase sample size if higher power needed."
        
        return StatisticalResult(
            test_type=StatisticalTest.WELCH_T_TEST,
            statistic=t_stat,
            p_value=p_value,
            effect_size=cohens_d,
            confidence_interval=(ci_lower, ci_upper),
            is_significant=is_significant,
            power=power,
            conclusion=conclusion,
            recommendation=recommendation
        )
    
    @staticmethod
    def _calculate_power(effect_size: float, n1: int, n2: int, alpha: float) -> float:
        """Calculate statistical power (approximate)."""
        # Simplified power calculation
        from scipy import stats
        
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = z_alpha - effect_size * math.sqrt(n1 * n2 / (n1 + n2))
        
        return 1 - stats.norm.cdf(z_beta)
    
    @staticmethod
    def bootstrap_test(control_values: List[float], 
                      treatment_values: List[float],
                      n_bootstrap: int = 10000,
                      alpha: float = 0.05) -> StatisticalResult:
        """Perform bootstrap significance test."""
        
        import random
        
        # Original difference
        original_diff = mean(treatment_values) - mean(control_values)
        
        # Bootstrap resampling
        all_values = control_values + treatment_values
        n_control = len(control_values)
        n_treatment = len(treatment_values)
        
        bootstrap_diffs = []
        for _ in range(n_bootstrap):
            # Resample with replacement
            resampled = random.choices(all_values, k=len(all_values))
            bootstrap_control = resampled[:n_control]
            bootstrap_treatment = resampled[n_control:n_control+n_treatment]
            
            diff = mean(bootstrap_treatment) - mean(bootstrap_control)
            bootstrap_diffs.append(diff)
        
        # Calculate p-value
        extreme_count = sum(1 for d in bootstrap_diffs if abs(d) >= abs(original_diff))
        p_value = extreme_count / n_bootstrap
        
        # Effect size
        pooled_std = math.sqrt((stdev(control_values)**2 + stdev(treatment_values)**2) / 2)
        cohens_d = original_diff / pooled_std if pooled_std > 0 else 0.0
        
        # Confidence interval
        bootstrap_diffs.sort()
        ci_lower_idx = int(n_bootstrap * alpha/2)
        ci_upper_idx = int(n_bootstrap * (1 - alpha/2))
        ci_lower = bootstrap_diffs[ci_lower_idx]
        ci_upper = bootstrap_diffs[ci_upper_idx]
        
        is_significant = p_value < alpha
        
        conclusion = ("Significant difference detected" if is_significant 
                     else "No significant difference detected")
        conclusion += f" (bootstrap p={p_value:.4f})"
        
        recommendation = ("Effect is statistically significant" if is_significant
                         else "Consider increasing sample size or effect may be negligible")
        
        return StatisticalResult(
            test_type=StatisticalTest.BOOTSTRAP,
            statistic=original_diff,
            p_value=p_value,
            effect_size=cohens_d,
            confidence_interval=(ci_lower, ci_upper),
            is_significant=is_significant,
            power=0.8,  # Placeholder - power calculation for bootstrap is complex
            conclusion=conclusion,
            recommendation=recommendation
        )


class ABTestingSystem:
    """Comprehensive A/B testing system for RAG experiments."""
    
    def __init__(self, database_path: str = "ab_experiments.db"):
        """Initialize A/B testing system."""
        self.db = ExperimentDatabase(database_path)
        self.analyzer = StatisticalAnalyzer()
    
    def create_experiment(self, name: str, description: str,
                         control_config: Dict[str, Any],
                         treatment_config: Dict[str, Any],
                         primary_metric: str = "f1@5",
                         secondary_metrics: List[str] = None,
                         minimum_detectable_effect: float = 0.05,
                         statistical_power: float = 0.8,
                         significance_level: float = 0.05) -> ExperimentConfiguration:
        """Create a new A/B test experiment."""
        
        if secondary_metrics is None:
            secondary_metrics = ["recall@5", "precision@5", "mrr", "latency_ms"]
        
        # Calculate required sample size
        sample_size = self.analyzer.calculate_sample_size(
            minimum_detectable_effect, statistical_power, significance_level
        )
        
        config = ExperimentConfiguration(
            experiment_id=str(uuid.uuid4()),
            name=name,
            description=description,
            control_config=control_config,
            treatment_config=treatment_config,
            primary_metric=primary_metric,
            secondary_metrics=secondary_metrics,
            minimum_detectable_effect=minimum_detectable_effect,
            statistical_power=statistical_power,
            significance_level=significance_level,
            sample_size_per_group=sample_size
        )
        
        self.db.save_experiment(config)
        logger.info(f"Created experiment {config.experiment_id}: {name}")
        
        return config
    
    def run_experiment(self, experiment_id: str, 
                      queries: List[SyntheticQuery],
                      multi_tool_factory: callable) -> BenchmarkResult:
        """Run an A/B test experiment."""
        
        config = self.db.load_experiment(experiment_id)
        if not config:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        logger.info(f"Running A/B experiment: {config.name}")
        
        # Update status to active
        config.status = ExperimentStatus.ACTIVE
        self.db.save_experiment(config)
        
        # Run control group
        control_multi_tool = multi_tool_factory()
        control_pipeline = EvaluationPipeline(control_multi_tool)
        
        control_result = await control_pipeline.run_evaluation(
            queries,
            evaluation_id=f"{experiment_id}_control",
            config=config.control_config
        )
        
        self.db.save_experiment_result(experiment_id, "control", control_result)
        
        # Run treatment group  
        treatment_multi_tool = multi_tool_factory()
        treatment_pipeline = EvaluationPipeline(treatment_multi_tool)
        
        treatment_result = await treatment_pipeline.run_evaluation(
            queries,
            evaluation_id=f"{experiment_id}_treatment", 
            config=config.treatment_config
        )
        
        self.db.save_experiment_result(experiment_id, "treatment", treatment_result)
        
        # Create benchmark result
        benchmark_result = BenchmarkResult(
            benchmark_id=experiment_id,
            comparison_name=config.name
        )
        
        benchmark_result.add_result("control", control_result, config.control_config)
        benchmark_result.add_result("treatment", treatment_result, config.treatment_config)
        benchmark_result.determine_winner(config.primary_metric)
        
        # Update status to completed
        config.status = ExperimentStatus.COMPLETED
        self.db.save_experiment(config)
        
        logger.info(f"Completed A/B experiment: {config.name}")
        
        return benchmark_result
    
    def analyze_experiment(self, experiment_id: str) -> Dict[str, StatisticalResult]:
        """Analyze experiment results with statistical tests."""
        
        config = self.db.load_experiment(experiment_id)
        if not config:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        results = self.db.get_experiment_results(experiment_id)
        
        if not results["control"] or not results["treatment"]:
            logger.warning("Insufficient data for statistical analysis")
            return {}
        
        analysis_results = {}
        
        # Analyze primary metric
        metrics_to_analyze = [config.primary_metric] + config.secondary_metrics
        
        for metric_name in metrics_to_analyze:
            # Extract metric values
            control_values = [r['metrics'].get(metric_name, 0.0) for r in results["control"]]
            treatment_values = [r['metrics'].get(metric_name, 0.0) for r in results["treatment"]]
            
            # Filter out None values
            control_values = [v for v in control_values if v is not None]
            treatment_values = [v for v in treatment_values if v is not None]
            
            if not control_values or not treatment_values:
                continue
            
            # Perform statistical test
            if len(control_values) >= 30 and len(treatment_values) >= 30:
                # Use Welch's t-test for larger samples
                stat_result = self.analyzer.welch_t_test(
                    control_values, treatment_values, config.significance_level
                )
            else:
                # Use bootstrap for smaller samples
                stat_result = self.analyzer.bootstrap_test(
                    control_values, treatment_values, alpha=config.significance_level
                )
            
            analysis_results[metric_name] = stat_result
            
            # Save to database
            self.db.save_statistical_test(experiment_id, metric_name, stat_result)
        
        return analysis_results
    
    def get_experiment_summary(self, experiment_id: str) -> Dict[str, Any]:
        """Get comprehensive experiment summary."""
        
        config = self.db.load_experiment(experiment_id)
        if not config:
            return {"error": f"Experiment {experiment_id} not found"}
        
        results = self.db.get_experiment_results(experiment_id)
        analysis = self.analyze_experiment(experiment_id) if results["control"] and results["treatment"] else {}
        
        # Calculate summary statistics
        summary = {
            "experiment_id": experiment_id,
            "name": config.name,
            "description": config.description,
            "status": config.status.value,
            "primary_metric": config.primary_metric,
            "sample_sizes": {
                "control": len(results["control"]),
                "treatment": len(results["treatment"]),
                "required_per_group": config.sample_size_per_group
            },
            "statistical_analysis": {},
            "recommendations": []
        }
        
        # Add statistical analysis results
        for metric_name, stat_result in analysis.items():
            summary["statistical_analysis"][metric_name] = {
                "p_value": stat_result.p_value,
                "effect_size": stat_result.effect_size,
                "is_significant": stat_result.is_significant,
                "confidence_interval": stat_result.confidence_interval,
                "conclusion": stat_result.conclusion,
                "recommendation": stat_result.recommendation
            }
        
        # Generate overall recommendations
        if config.primary_metric in analysis:
            primary_result = analysis[config.primary_metric]
            if primary_result.is_significant:
                if primary_result.effect_size > 0:
                    summary["recommendations"].append("🎉 Treatment shows significant improvement - consider deployment")
                else:
                    summary["recommendations"].append("⚠️ Treatment shows significant degradation - do not deploy")
            else:
                summary["recommendations"].append("📊 No significant difference detected - consider longer experiment or larger effect size")
        
        # Check if sample size is adequate
        control_size = len(results["control"])
        treatment_size = len(results["treatment"])
        required_size = config.sample_size_per_group or 100
        
        if control_size < required_size or treatment_size < required_size:
            summary["recommendations"].append(f"⚠️ Sample size insufficient (need {required_size} per group)")
        
        return summary
    
    def list_experiments(self, status: Optional[ExperimentStatus] = None) -> List[Dict[str, Any]]:
        """List all experiments, optionally filtered by status."""
        
        with sqlite3.connect(self.db.db_path) as conn:
            if status:
                cursor = conn.execute("""
                    SELECT experiment_id, name, status, created_at, primary_metric
                    FROM experiments 
                    WHERE status = ?
                    ORDER BY created_at DESC
                """, (status.value,))
            else:
                cursor = conn.execute("""
                    SELECT experiment_id, name, status, created_at, primary_metric
                    FROM experiments 
                    ORDER BY created_at DESC
                """)
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


# Utility functions for easy access

def create_ab_test(name: str, description: str,
                  control_config: Dict[str, Any],
                  treatment_config: Dict[str, Any],
                  primary_metric: str = "f1@5",
                  database_path: str = "ab_experiments.db") -> str:
    """Create a new A/B test experiment."""
    ab_system = ABTestingSystem(database_path)
    config = ab_system.create_experiment(
        name, description, control_config, treatment_config, primary_metric
    )
    return config.experiment_id


def run_ab_test(experiment_id: str, queries: List[SyntheticQuery],
               multi_tool_factory: callable,
               database_path: str = "ab_experiments.db") -> Dict[str, Any]:
    """Run an A/B test and return summary results."""
    ab_system = ABTestingSystem(database_path)
    benchmark_result = ab_system.run_experiment(experiment_id, queries, multi_tool_factory)
    summary = ab_system.get_experiment_summary(experiment_id)
    
    return {
        "benchmark_result": benchmark_result,
        "statistical_summary": summary
    }


def analyze_ab_test(experiment_id: str,
                   database_path: str = "ab_experiments.db") -> Dict[str, Any]:
    """Analyze A/B test results and return statistical analysis."""
    ab_system = ABTestingSystem(database_path)
    return ab_system.get_experiment_summary(experiment_id)
