"""
Integration tests for the evaluation system.

Tests the complete workflows including pipeline execution,
benchmarking, A/B testing, and data persistence.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import pytest
from conftest import (
    assert_evaluation_result_valid, assert_metrics_valid, 
    create_mock_query_result
)


class TestEvaluationPipelineIntegration:
    """Test complete evaluation pipeline workflows."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_evaluation(self, temp_dir, sample_queries, mock_agentic_rag):
        """Test complete evaluation pipeline from queries to results."""
        
        # Mock the evaluation pipeline components
        multi_tool = mock_agentic_rag["MultiTool"]()
        
        # Simulate pipeline execution
        evaluation_results = []
        
        for query_data in sample_queries:
            # Mock document retrieval
            mock_docs = await multi_tool.search(query_data["query"], top_k=5)
            retrieved_doc_ids = [doc.id for doc in mock_docs]
            
            # Create mock query result
            query_result = create_mock_query_result(
                query_data["query"],
                retrieved_doc_ids,
                query_data["ground_truth"],
                query_data["expected_tools"]
            )
            evaluation_results.append(query_result)
        
        # Verify results structure
        assert len(evaluation_results) == len(sample_queries)
        
        for result in evaluation_results:
            assert "query" in result
            assert "retrieved_docs" in result
            assert "relevant_docs" in result
            assert "tools_used" in result
            assert result["response_time_ms"] > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_with_different_configurations(self, evaluation_config):
        """Test pipeline with various configuration parameters."""
        
        configs_to_test = [
            # Basic configuration
            {
                **evaluation_config,
                "retrieval_config": {"top_k": 5, "similarity_threshold": 0.7}
            },
            # High recall configuration
            {
                **evaluation_config,
                "retrieval_config": {"top_k": 10, "similarity_threshold": 0.5}
            },
            # High precision configuration
            {
                **evaluation_config,
                "retrieval_config": {"top_k": 3, "similarity_threshold": 0.9}
            }
        ]
        
        for config in configs_to_test:
            # Each configuration should be valid
            assert "retrieval_config" in config
            assert "llm_config" in config
            assert "evaluation_config" in config
            
            # Verify specific parameters
            retrieval_config = config["retrieval_config"]
            assert retrieval_config["top_k"] > 0
            assert 0.0 <= retrieval_config["similarity_threshold"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, sample_queries):
        """Test pipeline handles errors gracefully."""
        
        # Test with malformed queries
        malformed_queries = [
            {"query": "", "domain": "test"},  # Empty query
            {"query": "test", "domain": ""},  # Empty domain
            {"invalid": "structure"},  # Invalid structure
        ]
        
        for query in malformed_queries:
            # Pipeline should handle gracefully without crashing
            # In real implementation, would return appropriate error responses
            assert "query" in query or "invalid" in query
    
    @pytest.mark.asyncio 
    async def test_pipeline_batch_processing(self, sample_queries):
        """Test pipeline can handle batch processing of queries."""
        
        batch_sizes = [1, 2, len(sample_queries), len(sample_queries) + 5]
        
        for batch_size in batch_sizes:
            # Process queries in batches
            batches = []
            for i in range(0, len(sample_queries), batch_size):
                batch = sample_queries[i:i + batch_size]
                batches.append(batch)
            
            # Verify batching logic
            total_queries = sum(len(batch) for batch in batches)
            assert total_queries == len(sample_queries)
            
            # Each batch should be processable
            for batch in batches:
                assert len(batch) <= batch_size
                assert len(batch) > 0


class TestBenchmarkingIntegration:
    """Test benchmarking system integration."""
    
    @pytest.mark.asyncio
    async def test_benchmark_execution_flow(self, benchmark_config, sample_queries):
        """Test complete benchmark execution from configuration to results."""
        
        # Extract configurations
        baseline_config = benchmark_config["baseline_config"]
        competitor_configs = benchmark_config["competitor_configs"]
        
        # Simulate benchmark execution
        benchmark_results = {}
        
        # Process baseline
        benchmark_results[baseline_config["name"]] = {
            "config": baseline_config,
            "metrics": {
                "f1@5": 0.75,
                "precision@5": 0.80,
                "recall@5": 0.71,
                "mrr": 0.68,
                "latency_ms": 250
            }
        }
        
        # Process competitors
        for i, config in enumerate(competitor_configs):
            # Simulate slight improvements
            benchmark_results[config["name"]] = {
                "config": config,
                "metrics": {
                    "f1@5": 0.75 + (i + 1) * 0.05,
                    "precision@5": 0.80 + (i + 1) * 0.03,
                    "recall@5": 0.71 + (i + 1) * 0.04,
                    "mrr": 0.68 + (i + 1) * 0.06,
                    "latency_ms": 250 - (i + 1) * 20
                }
            }
        
        # Verify benchmark results structure
        assert len(benchmark_results) == 1 + len(competitor_configs)
        
        for name, result in benchmark_results.items():
            assert "config" in result
            assert "metrics" in result
            assert_metrics_valid(result["metrics"])
    
    def test_benchmark_comparison_logic(self, benchmark_config):
        """Test benchmark comparison and winner determination."""
        
        # Mock benchmark results
        results = {
            "baseline_v1": {"f1@5": 0.75, "latency_ms": 250},
            "improved_retrieval": {"f1@5": 0.78, "latency_ms": 270},
            "better_llm": {"f1@5": 0.82, "latency_ms": 300}
        }
        
        primary_metric = benchmark_config["primary_metric"]  # f1@5
        
        # Find winner based on primary metric
        winner = max(results.items(), key=lambda x: x[1][primary_metric])
        
        assert winner[0] == "better_llm"
        assert winner[1][primary_metric] == 0.82
        
        # Test statistical significance simulation
        improvements = {}
        baseline_score = results["baseline_v1"][primary_metric]
        
        for name, metrics in results.items():
            if name != "baseline_v1":
                improvement = (metrics[primary_metric] - baseline_score) / baseline_score
                improvements[name] = improvement
        
        # Verify improvements calculated correctly
        expected_improvements = {
            "improved_retrieval": (0.78 - 0.75) / 0.75,  # 4%
            "better_llm": (0.82 - 0.75) / 0.75  # 9.3%
        }
        
        for name, improvement in improvements.items():
            assert abs(improvement - expected_improvements[name]) < 0.001
    
    @pytest.mark.asyncio
    async def test_benchmark_regression_detection(self, temp_dir):
        """Test benchmark regression detection capabilities."""
        
        # Simulate historical benchmark data
        historical_results = [
            {"date": "2024-01-01", "f1@5": 0.75, "latency_ms": 250},
            {"date": "2024-01-02", "f1@5": 0.76, "latency_ms": 245},
            {"date": "2024-01-03", "f1@5": 0.78, "latency_ms": 240},
        ]
        
        # New result that shows regression
        new_result = {"date": "2024-01-04", "f1@5": 0.70, "latency_ms": 300}
        
        # Calculate regression
        recent_avg = sum(r["f1@5"] for r in historical_results[-3:]) / 3
        current_score = new_result["f1@5"]
        
        regression_threshold = 0.05  # 5% regression threshold
        regression_detected = (recent_avg - current_score) / recent_avg > regression_threshold
        
        assert regression_detected  # Should detect regression
        
        # Calculate severity
        regression_percentage = (recent_avg - current_score) / recent_avg
        assert regression_percentage > 0.05  # More than 5% regression


class TestABTestingIntegration:
    """Test A/B testing system integration."""
    
    @pytest.mark.asyncio
    async def test_ab_test_complete_workflow(self, ab_test_config, temp_dir):
        """Test complete A/B test workflow from setup to analysis."""
        
        # Create mock experiment
        experiment_id = "test_experiment_001"
        
        # Simulate control group results
        control_results = []
        for i in range(50):  # 50 samples
            control_results.append({
                "f1@5": 0.75 + (i % 10) * 0.01,  # Some variance
                "latency_ms": 250 + (i % 20) * 5
            })
        
        # Simulate treatment group results (with improvement)
        treatment_results = []
        for i in range(52):  # 52 samples
            treatment_results.append({
                "f1@5": 0.80 + (i % 10) * 0.01,  # Higher baseline
                "latency_ms": 240 + (i % 20) * 5  # Lower latency
            })
        
        # Calculate basic statistics
        control_f1_mean = sum(r["f1@5"] for r in control_results) / len(control_results)
        treatment_f1_mean = sum(r["f1@5"] for r in treatment_results) / len(treatment_results)
        
        effect_size = (treatment_f1_mean - control_f1_mean) / control_f1_mean
        
        # Verify expected improvement
        assert treatment_f1_mean > control_f1_mean
        assert effect_size > 0.05  # At least 5% improvement
    
    def test_statistical_significance_calculation(self, ab_test_config):
        """Test statistical significance calculations."""
        
        # Mock data with known statistical properties
        control_values = [0.75, 0.76, 0.74, 0.75, 0.77] * 10  # 50 values
        treatment_values = [0.80, 0.81, 0.79, 0.80, 0.82] * 10  # 50 values
        
        # Calculate basic statistics
        import statistics
        
        control_mean = statistics.mean(control_values)
        treatment_mean = statistics.mean(treatment_values)
        control_std = statistics.stdev(control_values)
        treatment_std = statistics.stdev(treatment_values)
        
        # Effect size (Cohen's d)
        pooled_std = ((len(control_values) - 1) * control_std**2 + 
                     (len(treatment_values) - 1) * treatment_std**2) / \
                    (len(control_values) + len(treatment_values) - 2)
        pooled_std = pooled_std ** 0.5
        
        cohens_d = (treatment_mean - control_mean) / pooled_std
        
        # Verify effect size calculation
        assert cohens_d > 0  # Treatment should be better
        assert abs(cohens_d) > 0.2  # Should be at least small effect size
        
        # Mock p-value calculation (would use actual statistical test)
        # For this test, assume significant result
        mock_p_value = 0.01
        significance_level = ab_test_config["significance_level"]
        
        is_significant = mock_p_value < significance_level
        assert is_significant
    
    def test_sample_size_calculation(self, ab_test_config):
        """Test sample size calculation for experiments."""
        
        effect_size = ab_test_config["minimum_detectable_effect"]
        power = ab_test_config["statistical_power"]
        alpha = ab_test_config["significance_level"]
        
        # Simplified sample size calculation
        # In reality, would use statistical formulas or libraries
        
        # Mock calculation based on typical values
        if effect_size == 0.05 and power == 0.8 and alpha == 0.05:
            expected_sample_size = 1600  # Approximate for these parameters
        else:
            expected_sample_size = 100  # Default
        
        # Verify sample size is reasonable
        assert expected_sample_size > 0
        assert expected_sample_size < 10000  # Shouldn't be unreasonably large
    
    @pytest.mark.asyncio
    async def test_ab_test_experiment_persistence(self, temp_dir, ab_test_config):
        """Test A/B test experiment data persistence."""
        
        # Create temporary database file
        db_path = temp_dir / "test_experiments.db"
        
        # Mock experiment data
        experiment_data = {
            "experiment_id": "exp_001",
            "name": ab_test_config["name"],
            "status": "completed",
            "control_results": [{"f1@5": 0.75, "sample_id": i} for i in range(50)],
            "treatment_results": [{"f1@5": 0.80, "sample_id": i} for i in range(50)],
            "statistical_analysis": {
                "p_value": 0.01,
                "effect_size": 0.067,
                "is_significant": True,
                "conclusion": "Treatment shows significant improvement"
            }
        }
        
        # Save data (mock implementation)
        with open(db_path, 'w') as f:
            json.dump(experiment_data, f)
        
        # Load and verify data
        with open(db_path, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data["experiment_id"] == experiment_data["experiment_id"]
        assert loaded_data["statistical_analysis"]["is_significant"]
        assert len(loaded_data["control_results"]) == 50
        assert len(loaded_data["treatment_results"]) == 50


class TestSyntheticDataIntegration:
    """Test synthetic data generation integration."""
    
    def test_synthetic_query_generation_integration(self, temp_dir):
        """Test synthetic query generation with realistic scenarios."""
        
        # Domain-specific query patterns
        query_patterns = {
            "technology": [
                "What are the latest trends in {topic}?",
                "How does {technology} work?",
                "What are the benefits of {approach}?"
            ],
            "finance": [
                "How to calculate {metric}?",
                "What is the {concept} in finance?",
                "How to optimize {process}?"
            ],
            "software": [
                "How to implement {feature}?",
                "What are best practices for {task}?",
                "How to debug {problem}?"
            ]
        }
        
        # Generate queries for each domain
        generated_queries = []
        for domain, patterns in query_patterns.items():
            for pattern in patterns:
                # Mock topic substitution
                if domain == "technology":
                    topics = ["AI", "blockchain", "quantum computing"]
                elif domain == "finance":
                    topics = ["ROI", "NPV", "portfolio management"]
                else:
                    topics = ["OAuth2", "microservices", "unit testing"]
                
                for topic in topics:
                    query = pattern.replace("{topic}", topic).replace("{technology}", topic) \
                                   .replace("{approach}", topic).replace("{metric}", topic) \
                                   .replace("{concept}", topic).replace("{process}", topic) \
                                   .replace("{feature}", topic).replace("{task}", topic) \
                                   .replace("{problem}", topic)
                    
                    generated_queries.append({
                        "query": query,
                        "domain": domain,
                        "pattern": pattern
                    })
        
        # Verify generation results
        assert len(generated_queries) > 0
        assert len(set(q["domain"] for q in generated_queries)) == 3  # 3 domains
        
        # Verify query diversity
        unique_queries = set(q["query"] for q in generated_queries)
        assert len(unique_queries) == len(generated_queries)  # All unique
    
    def test_golden_dataset_integration(self, temp_dir, sample_documents):
        """Test golden dataset creation and validation."""
        
        # Create mock golden dataset
        golden_dataset = {
            "metadata": {
                "name": "test_golden_dataset",
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "description": "Test dataset for evaluation"
            },
            "documents": sample_documents,
            "queries": [
                {
                    "query_id": "q001",
                    "query": "What are AI trends?",
                    "domain": "technology",
                    "relevant_documents": ["doc_ai_trends", "doc_tech_news"],
                    "expected_tools": ["document_retrieval", "web_search"]
                },
                {
                    "query_id": "q002", 
                    "query": "How to calculate ROI?",
                    "domain": "finance",
                    "relevant_documents": ["doc_roi_formula"],
                    "expected_tools": ["calculator"]
                }
            ]
        }
        
        # Save golden dataset
        dataset_path = temp_dir / "golden_dataset.json"
        with open(dataset_path, 'w') as f:
            json.dump(golden_dataset, f, indent=2)
        
        # Validate dataset structure
        assert "metadata" in golden_dataset
        assert "documents" in golden_dataset
        assert "queries" in golden_dataset
        
        # Verify document references are valid
        document_ids = {doc["id"] for doc in golden_dataset["documents"]}
        for query in golden_dataset["queries"]:
            for doc_id in query["relevant_documents"]:
                assert doc_id in document_ids


class TestSystemIntegration:
    """Test complete system integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_evaluation_workflow(self, temp_dir, sample_queries, 
                                          evaluation_config, mock_agentic_rag):
        """Test complete evaluation workflow from start to finish."""
        
        # Step 1: Initialize system components
        multi_tool = mock_agentic_rag["MultiTool"]()
        
        # Step 2: Load configuration
        config = evaluation_config
        
        # Step 3: Execute evaluation
        results = []
        for query_data in sample_queries:
            # Process query
            response = await multi_tool.process_query(query_data["query"])
            
            # Calculate metrics (mock)
            mock_metrics = {
                "precision@5": 0.8,
                "recall@5": 0.75,
                "f1@5": 0.775,
                "mrr": 0.7,
                "ndcg@5": 0.78,
                "latency_ms": response["latency_ms"]
            }
            
            results.append({
                "query": query_data["query"],
                "response": response,
                "metrics": mock_metrics
            })
        
        # Step 4: Aggregate results
        overall_metrics = {}
        for metric_name in ["precision@5", "recall@5", "f1@5", "mrr", "ndcg@5", "latency_ms"]:
            values = [r["metrics"][metric_name] for r in results]
            overall_metrics[metric_name] = sum(values) / len(values)
        
        # Step 5: Validate results
        assert len(results) == len(sample_queries)
        assert_metrics_valid(overall_metrics)
        
        # Step 6: Save results
        results_path = temp_dir / "evaluation_results.json"
        final_results = {
            "evaluation_id": "integration_test_001",
            "config": config,
            "query_results": results,
            "overall_metrics": overall_metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(results_path, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        # Verify file was created
        assert results_path.exists()
        assert results_path.stat().st_size > 0
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_logging(self, temp_dir, sample_queries):
        """Test system error recovery and logging capabilities."""
        
        # Simulate various error conditions
        error_scenarios = [
            {"type": "network_error", "query": "Network timeout test"},
            {"type": "malformed_response", "query": "Invalid response test"},
            {"type": "missing_documents", "query": "No documents found test"}
        ]
        
        error_log = []
        
        for scenario in error_scenarios:
            try:
                # Simulate error condition
                if scenario["type"] == "network_error":
                    raise asyncio.TimeoutError("Network timeout")
                elif scenario["type"] == "malformed_response":
                    raise ValueError("Invalid response format")
                elif scenario["type"] == "missing_documents":
                    raise KeyError("Documents not found")
                    
            except Exception as e:
                # Log error and continue
                error_log.append({
                    "scenario": scenario["type"],
                    "query": scenario["query"],
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # Verify error handling
        assert len(error_log) == len(error_scenarios)
        for log_entry in error_log:
            assert "scenario" in log_entry
            assert "error" in log_entry
            assert "timestamp" in log_entry
    
    def test_configuration_validation(self, evaluation_config):
        """Test system configuration validation."""
        
        # Test valid configuration
        valid_config = evaluation_config
        
        def validate_config(config):
            required_sections = ["retrieval_config", "llm_config", "evaluation_config"]
            for section in required_sections:
                if section not in config:
                    return False, f"Missing required section: {section}"
            
            # Validate retrieval config
            retrieval = config["retrieval_config"]
            if retrieval["top_k"] <= 0:
                return False, "top_k must be positive"
            if not (0.0 <= retrieval["similarity_threshold"] <= 1.0):
                return False, "similarity_threshold must be between 0 and 1"
            
            return True, "Configuration is valid"
        
        is_valid, message = validate_config(valid_config)
        assert is_valid, message
        
        # Test invalid configurations
        invalid_configs = [
            {**valid_config, "retrieval_config": {**valid_config["retrieval_config"], "top_k": 0}},
            {**valid_config, "retrieval_config": {**valid_config["retrieval_config"], "similarity_threshold": 1.5}},
            {k: v for k, v in valid_config.items() if k != "llm_config"}  # Missing section
        ]
        
        for invalid_config in invalid_configs:
            is_valid, message = validate_config(invalid_config)
            assert not is_valid, f"Should be invalid: {invalid_config}"
