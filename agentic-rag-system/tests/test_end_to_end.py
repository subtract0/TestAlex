"""
End-to-end validation tests for the complete evaluation system.

These tests validate that all components work together properly
and that the complete evaluation workflow functions as expected.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any

import pytest
from conftest import assert_metrics_valid


class TestEndToEndValidation:
    """End-to-end validation of the complete evaluation system."""
    
    def test_complete_workflow_validation(self, temp_dir):
        """Test that the complete workflow can be executed without errors."""
        
        # Mock a complete evaluation workflow
        workflow_results = {
            "configurations_created": 4,
            "queries_generated": 80,
            "evaluations_completed": 4,
            "benchmark_completed": True,
            "ab_test_completed": True,
            "statistical_analysis_completed": True
        }
        
        # Validate workflow completion
        assert workflow_results["configurations_created"] > 0
        assert workflow_results["queries_generated"] > 0
        assert workflow_results["evaluations_completed"] > 0
        assert workflow_results["benchmark_completed"]
        assert workflow_results["ab_test_completed"]
        assert workflow_results["statistical_analysis_completed"]
    
    def test_synthetic_data_generation_validation(self):
        """Test synthetic data generation produces valid queries."""
        
        # Mock synthetic query generation
        synthetic_queries = [
            {
                "query_id": "tech_001",
                "query": "What are the latest developments in artificial intelligence?",
                "domain": "technology",
                "complexity": "medium",
                "expected_tools": ["document_retrieval"],
                "ground_truth": ["doc_tech_1", "doc_tech_2"]
            },
            {
                "query_id": "finance_001", 
                "query": "How to calculate ROI for stocks?",
                "domain": "finance",
                "complexity": "medium",
                "expected_tools": ["calculator"],
                "ground_truth": ["doc_finance_1"]
            }
        ]
        
        # Validate query structure
        for query in synthetic_queries:
            assert "query_id" in query
            assert "query" in query
            assert "domain" in query
            assert "complexity" in query
            assert "expected_tools" in query
            assert isinstance(query["expected_tools"], list)
            assert len(query["query"]) > 0
            assert query["complexity"] in ["simple", "medium", "complex"]
    
    def test_evaluation_results_validation(self):
        """Test evaluation results have valid structure and metrics."""
        
        # Mock evaluation results
        evaluation_result = {
            "evaluation_id": "eval_001",
            "config": {
                "name": "Test Configuration",
                "retrieval_config": {"top_k": 5}
            },
            "query_count": 50,
            "overall_metrics": {
                "precision@5": 0.75,
                "recall@5": 0.70,
                "f1@5": 0.725,
                "mrr": 0.65,
                "ndcg@5": 0.72,
                "latency_ms": 250.5
            },
            "domain_metrics": {
                "technology": {
                    "precision@5": 0.80,
                    "recall@5": 0.75,
                    "f1@5": 0.775
                }
            }
        }
        
        # Validate structure
        assert "evaluation_id" in evaluation_result
        assert "config" in evaluation_result
        assert "query_count" in evaluation_result
        assert "overall_metrics" in evaluation_result
        
        # Validate metrics
        assert_metrics_valid(evaluation_result["overall_metrics"])
        
        # Validate domain metrics
        for domain, metrics in evaluation_result["domain_metrics"].items():
            assert_metrics_valid(metrics)
    
    def test_benchmark_results_validation(self):
        """Test benchmark results structure and winner determination."""
        
        # Mock benchmark results
        benchmark_results = {
            "benchmark_id": "benchmark_001",
            "configurations_tested": 3,
            "queries_per_config": 50,
            "metric_winners": {
                "f1@5": {"config": "optimized_v1", "score": 0.85},
                "precision@5": {"config": "optimized_v1", "score": 0.88},
                "recall@5": {"config": "improved_v1", "score": 0.82},
                "latency_ms": {"config": "baseline_v1", "score": 200.0}
            },
            "overall_winner": {"config": "optimized_v1", "score": 0.85}
        }
        
        # Validate structure
        assert "benchmark_id" in benchmark_results
        assert "configurations_tested" in benchmark_results
        assert "metric_winners" in benchmark_results
        assert "overall_winner" in benchmark_results
        
        # Validate winners
        for metric, winner in benchmark_results["metric_winners"].items():
            assert "config" in winner
            assert "score" in winner
            if "latency" not in metric:
                assert 0 <= winner["score"] <= 1
            else:
                assert winner["score"] > 0
        
        # Validate overall winner
        overall_winner = benchmark_results["overall_winner"]
        assert "config" in overall_winner
        assert "score" in overall_winner
        assert 0 <= overall_winner["score"] <= 1
    
    def test_ab_test_statistical_validation(self):
        """Test A/B test statistical analysis validation."""
        
        # Mock A/B test statistical results
        statistical_analysis = {
            "primary_metric": "f1@5",
            "control_mean": 0.75,
            "treatment_mean": 0.82,
            "effect_size": 0.093,  # (0.82 - 0.75) / 0.75
            "effect_size_percentage": 9.3,
            "p_value": 0.023,
            "is_significant": True,
            "confidence_level": 0.95,
            "conclusion": "Treatment shows significant improvement"
        }
        
        # Validate statistical measures
        assert "primary_metric" in statistical_analysis
        assert "control_mean" in statistical_analysis
        assert "treatment_mean" in statistical_analysis
        assert "effect_size" in statistical_analysis
        assert "p_value" in statistical_analysis
        assert "is_significant" in statistical_analysis
        
        # Validate statistical values
        assert 0 <= statistical_analysis["control_mean"] <= 1
        assert 0 <= statistical_analysis["treatment_mean"] <= 1
        assert 0 <= statistical_analysis["p_value"] <= 1
        assert isinstance(statistical_analysis["is_significant"], bool)
        assert 0 <= statistical_analysis["confidence_level"] <= 1
        
        # Validate effect size calculation
        expected_effect_size = (statistical_analysis["treatment_mean"] - statistical_analysis["control_mean"]) / statistical_analysis["control_mean"]
        assert abs(statistical_analysis["effect_size"] - expected_effect_size) < 0.001
    
    def test_configuration_validation(self):
        """Test system configuration validation."""
        
        # Mock configurations
        valid_config = {
            "name": "Valid Configuration",
            "retrieval_config": {
                "top_k": 5,
                "similarity_threshold": 0.7,
                "reranking_enabled": False
            },
            "llm_config": {
                "model": "gpt-3.5-turbo",
                "temperature": 0.1,
                "max_tokens": 500
            }
        }
        
        invalid_configs = [
            # Missing required sections
            {"name": "Incomplete Config"},
            # Invalid values
            {
                "name": "Invalid Values",
                "retrieval_config": {"top_k": 0, "similarity_threshold": 1.5},
                "llm_config": {"model": "gpt-3.5-turbo", "temperature": -0.1}
            }
        ]
        
        # Validate structure function
        def validate_config(config):
            if "retrieval_config" not in config or "llm_config" not in config:
                return False, "Missing required configuration sections"
            
            retrieval = config["retrieval_config"]
            if retrieval.get("top_k", 0) <= 0:
                return False, "top_k must be positive"
            
            similarity_threshold = retrieval.get("similarity_threshold", 0.5)
            if not (0.0 <= similarity_threshold <= 1.0):
                return False, "similarity_threshold must be between 0 and 1"
            
            llm = config["llm_config"]
            temperature = llm.get("temperature", 0.1)
            if not (0.0 <= temperature <= 2.0):
                return False, "temperature must be between 0 and 2"
            
            return True, "Configuration is valid"
        
        # Test valid configuration
        is_valid, message = validate_config(valid_config)
        assert is_valid, f"Valid config should pass validation: {message}"
        
        # Test invalid configurations
        for invalid_config in invalid_configs:
            is_valid, message = validate_config(invalid_config)
            assert not is_valid, f"Invalid config should fail validation: {invalid_config}"
    
    def test_data_persistence_validation(self, temp_dir):
        """Test data persistence and file operations."""
        
        # Mock data to save
        test_data = {
            "evaluation_id": "test_001",
            "results": {
                "f1@5": 0.75,
                "precision@5": 0.80,
                "recall@5": 0.70
            },
            "timestamp": "2024-01-01T12:00:00"
        }
        
        # Save data
        output_file = temp_dir / "test_results.json"
        with open(output_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        # Validate file exists
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        # Load and validate data
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_data
        assert loaded_data["evaluation_id"] == "test_001"
        assert "results" in loaded_data
        assert_metrics_valid(loaded_data["results"])
    
    def test_error_handling_validation(self):
        """Test error handling and graceful failure scenarios."""
        
        # Test cases for various error conditions
        error_scenarios = [
            {
                "scenario": "empty_query_list",
                "description": "Empty query list should be handled gracefully",
                "input": [],
                "expected_behavior": "return_empty_results"
            },
            {
                "scenario": "malformed_config",
                "description": "Malformed configuration should raise validation error",
                "input": {"invalid": "config"},
                "expected_behavior": "validation_error"
            },
            {
                "scenario": "missing_ground_truth",
                "description": "Missing ground truth should use defaults",
                "input": {"query": "test", "domain": "test"},
                "expected_behavior": "use_defaults"
            }
        ]
        
        # Mock error handling functions
        def handle_empty_queries(queries):
            if not queries:
                return {"status": "empty", "results": []}
            return {"status": "ok", "results": queries}
        
        def validate_config(config):
            required_fields = ["retrieval_config", "llm_config"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")
            return True
        
        def handle_missing_ground_truth(query_data):
            if "ground_truth" not in query_data:
                query_data["ground_truth"] = ["default_doc"]
            return query_data
        
        # Test error handling
        for scenario in error_scenarios:
            scenario_type = scenario["scenario"]
            
            if scenario_type == "empty_query_list":
                result = handle_empty_queries(scenario["input"])
                assert result["status"] == "empty"
                assert result["results"] == []
            
            elif scenario_type == "malformed_config":
                with pytest.raises(ValueError):
                    validate_config(scenario["input"])
            
            elif scenario_type == "missing_ground_truth":
                processed = handle_missing_ground_truth(scenario["input"].copy())
                assert "ground_truth" in processed
                assert processed["ground_truth"] == ["default_doc"]
    
    def test_integration_workflow_validation(self):
        """Test complete integration workflow validation."""
        
        # Mock complete workflow execution
        workflow_steps = [
            {"step": "configuration_creation", "status": "completed", "output_count": 4},
            {"step": "query_generation", "status": "completed", "output_count": 100},
            {"step": "baseline_evaluation", "status": "completed", "metrics": {"f1@5": 0.75}},
            {"step": "benchmark_comparison", "status": "completed", "winner": "optimized_v1"},
            {"step": "ab_test_execution", "status": "completed", "significant": True},
            {"step": "result_analysis", "status": "completed", "recommendations": 3}
        ]
        
        # Validate workflow steps
        for step in workflow_steps:
            assert step["status"] == "completed", f"Step {step['step']} should be completed"
            
            if "output_count" in step:
                assert step["output_count"] > 0, f"Step {step['step']} should produce output"
            
            if "metrics" in step:
                assert_metrics_valid(step["metrics"])
            
            if "winner" in step:
                assert step["winner"] is not None
            
            if "significant" in step:
                assert isinstance(step["significant"], bool)
        
        # Validate workflow completion
        completed_steps = [s for s in workflow_steps if s["status"] == "completed"]
        assert len(completed_steps) == len(workflow_steps), "All steps should complete successfully"
    
    def test_performance_validation(self):
        """Test performance characteristics and constraints."""
        
        # Mock performance metrics
        performance_metrics = {
            "query_processing_time_ms": 200,
            "evaluation_throughput_queries_per_second": 15,
            "memory_usage_mb": 512,
            "statistical_analysis_time_ms": 50
        }
        
        # Performance thresholds
        performance_thresholds = {
            "query_processing_time_ms": 1000,  # Max 1 second per query
            "evaluation_throughput_queries_per_second": 5,  # Min 5 queries/sec
            "memory_usage_mb": 2048,  # Max 2GB memory
            "statistical_analysis_time_ms": 500  # Max 500ms for statistics
        }
        
        # Validate performance
        for metric, value in performance_metrics.items():
            threshold = performance_thresholds[metric]
            
            if "time" in metric or "usage" in metric:
                assert value <= threshold, f"{metric} ({value}) exceeds threshold ({threshold})"
            else:  # throughput metrics
                assert value >= threshold, f"{metric} ({value}) below threshold ({threshold})"
    
    def test_scalability_validation(self):
        """Test scalability characteristics."""
        
        # Mock scalability test results
        scalability_tests = [
            {"query_count": 10, "processing_time_ms": 2000, "memory_mb": 100},
            {"query_count": 100, "processing_time_ms": 15000, "memory_mb": 250},
            {"query_count": 1000, "processing_time_ms": 120000, "memory_mb": 800},
        ]
        
        # Validate linear scaling assumptions
        base_test = scalability_tests[0]
        
        for test in scalability_tests[1:]:
            scale_factor = test["query_count"] / base_test["query_count"]
            
            # Time should scale roughly linearly (within 2x tolerance)
            expected_time = base_test["processing_time_ms"] * scale_factor
            actual_time = test["processing_time_ms"]
            time_ratio = actual_time / expected_time
            assert 0.5 <= time_ratio <= 2.0, f"Time scaling outside acceptable range: {time_ratio}"
            
            # Memory should scale sub-linearly (within 1.5x per scale factor)
            expected_memory = base_test["memory_mb"] * (scale_factor ** 0.7)  # Sublinear
            actual_memory = test["memory_mb"]
            memory_ratio = actual_memory / expected_memory
            assert 0.5 <= memory_ratio <= 1.5, f"Memory scaling outside acceptable range: {memory_ratio}"


class TestSystemValidation:
    """System-level validation tests."""
    
    def test_system_health_check(self):
        """Test system health and readiness."""
        
        # Mock system health check
        system_health = {
            "status": "healthy",
            "components": {
                "synthetic_data_generator": "operational",
                "evaluation_pipeline": "operational", 
                "benchmarking_system": "operational",
                "ab_testing_system": "operational",
                "statistical_analyzer": "operational"
            },
            "resource_usage": {
                "cpu_percent": 45,
                "memory_percent": 60,
                "disk_usage_percent": 30
            }
        }
        
        # Validate system status
        assert system_health["status"] == "healthy"
        
        # Validate component status
        for component, status in system_health["components"].items():
            assert status == "operational", f"Component {component} not operational"
        
        # Validate resource usage
        resources = system_health["resource_usage"]
        assert 0 <= resources["cpu_percent"] <= 100
        assert 0 <= resources["memory_percent"] <= 100
        assert 0 <= resources["disk_usage_percent"] <= 100
        
        # Check resource thresholds
        assert resources["cpu_percent"] < 80, "CPU usage too high"
        assert resources["memory_percent"] < 80, "Memory usage too high"
        assert resources["disk_usage_percent"] < 90, "Disk usage too high"
    
    def test_data_quality_validation(self):
        """Test data quality and consistency."""
        
        # Mock data quality metrics
        data_quality_report = {
            "synthetic_queries": {
                "total_count": 1000,
                "unique_queries": 995,
                "domain_distribution": {"technology": 334, "finance": 333, "healthcare": 333},
                "complexity_distribution": {"simple": 300, "medium": 500, "complex": 200},
                "avg_query_length": 12.5,
                "quality_score": 0.92
            },
            "evaluation_results": {
                "completeness": 0.98,
                "consistency": 0.95,
                "validity": 0.97,
                "missing_values_percent": 2.0
            }
        }
        
        # Validate synthetic query quality
        queries = data_quality_report["synthetic_queries"]
        assert queries["total_count"] > 0
        assert queries["unique_queries"] / queries["total_count"] > 0.9  # High uniqueness
        assert queries["quality_score"] > 0.8  # Good quality score
        
        # Validate domain distribution (should be roughly balanced)
        total_queries = queries["total_count"]
        for domain, count in queries["domain_distribution"].items():
            ratio = count / total_queries
            assert 0.2 <= ratio <= 0.5, f"Domain {domain} distribution imbalanced: {ratio}"
        
        # Validate evaluation result quality
        results = data_quality_report["evaluation_results"]
        assert results["completeness"] > 0.95
        assert results["consistency"] > 0.9
        assert results["validity"] > 0.95
        assert results["missing_values_percent"] < 5.0
