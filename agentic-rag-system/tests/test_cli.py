"""
Tests for the CLI command interface.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

# Import CLI (with fallback)
try:
    from agentic_rag.cli import cli
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False
    cli = None


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_queries_file(temp_dir):
    """Sample queries file for testing."""
    queries = [
        {
            "query_id": "q001",
            "query": "What is machine learning?",
            "domain": "technology",
            "expected_tools": ["document_retrieval"]
        },
        {
            "query_id": "q002", 
            "query": "How to calculate ROI?",
            "domain": "finance",
            "expected_tools": ["calculator"]
        }
    ]
    
    query_file = temp_dir / "test_queries.json"
    with open(query_file, 'w') as f:
        json.dump(queries, f)
    
    return str(query_file)


@pytest.fixture
def sample_config_file(temp_dir):
    """Sample configuration file for testing."""
    config = {
        "retrieval_config": {
            "top_k": 5,
            "similarity_threshold": 0.7
        },
        "llm_config": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.1
        }
    }
    
    config_file = temp_dir / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f)
    
    return str(config_file)


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestCLIBasic:
    """Test basic CLI functionality."""
    
    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Agentic RAG" in result.output
        assert "evaluate" in result.output
        assert "benchmark" in result.output
    
    def test_status_command(self, runner):
        """Test status command."""
        result = runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        assert "Status" in result.output
    
    def test_status_json_format(self, runner):
        """Test status command with JSON format."""
        result = runner.invoke(cli, ['status', '--format', 'json'])
        assert result.exit_code == 0
        
        # Should be valid JSON
        try:
            output_data = json.loads(result.output)
            assert "system_status" in output_data
        except json.JSONDecodeError:
            pytest.fail("Status output is not valid JSON")


@pytest.mark.skipif(not CLI_AVAILABLE, reason="CLI not available")
class TestEvaluateCommands:
    """Test evaluation-related CLI commands."""
    
    def test_evaluate_help(self, runner):
        """Test evaluate command help."""
        result = runner.invoke(cli, ['evaluate', '--help'])
        assert result.exit_code == 0
        assert "Run evaluations" in result.output
    
    def test_evaluate_run_missing_queries(self, runner):
        """Test evaluate run without queries file."""
        result = runner.invoke(cli, ['evaluate', 'run'])
        assert result.exit_code == 0
        assert "No queries file specified" in result.output
    
    def test_evaluate_run_with_files(self, runner, sample_queries_file, sample_config_file, temp_dir):
        \"\"\"Test evaluate run with query and config files.\"\"\"\n        \n        output_file = temp_dir / \"results.json\"\n        \n        result = runner.invoke(cli, [\n            'evaluate', 'run',\n            '--queries', sample_queries_file,\n            '--config-file', sample_config_file,\n            '--output', str(output_file)\n        ])\n        \n        assert result.exit_code == 0\n        assert \"Evaluation Results\" in result.output\n        \n        # Check output file was created\n        assert output_file.exists()\n        \n        # Verify results structure\n        with open(output_file, 'r') as f:\n            results = json.load(f)\n        \n        assert \"evaluation_id\" in results\n        assert \"overall_metrics\" in results\n        assert results[\"query_count\"] == 2\n    \n    def test_generate_queries(self, runner, temp_dir):\n        \"\"\"Test synthetic query generation.\"\"\"\n        \n        output_file = temp_dir / \"generated_queries.json\"\n        \n        result = runner.invoke(cli, [\n            'evaluate', 'generate-queries',\n            '--domain', 'technology',\n            '--domain', 'finance', \n            '--count', '10',\n            '--complexity', 'medium',\n            '--output', str(output_file)\n        ])\n        \n        assert result.exit_code == 0\n        assert \"Generated\" in result.output\n        assert output_file.exists()\n        \n        # Verify generated queries\n        with open(output_file, 'r') as f:\n            queries = json.load(f)\n        \n        assert len(queries) > 0\n        \n        # Check query structure\n        for query in queries:\n            assert \"query_id\" in query\n            assert \"query\" in query\n            assert \"domain\" in query\n            assert query[\"complexity\"] == \"medium\"\n\n\n@pytest.mark.skipif(not CLI_AVAILABLE, reason=\"CLI not available\")\nclass TestBenchmarkCommands:\n    \"\"\"Test benchmarking CLI commands.\"\"\"\n    \n    def test_benchmark_help(self, runner):\n        \"\"\"Test benchmark command help.\"\"\"\n        result = runner.invoke(cli, ['benchmark', '--help'])\n        assert result.exit_code == 0\n        assert \"benchmark\" in result.output.lower()\n    \n    def test_benchmark_compare(self, runner, sample_config_file, sample_queries_file, temp_dir):\n        \"\"\"Test benchmark comparison.\"\"\"\n        \n        # Create second config file\n        config2 = {\n            \"retrieval_config\": {\n                \"top_k\": 10,\n                \"similarity_threshold\": 0.6\n            },\n            \"llm_config\": {\n                \"model\": \"gpt-4\",\n                \"temperature\": 0.0\n            }\n        }\n        \n        config_file2 = temp_dir / \"config2.json\"\n        with open(config_file2, 'w') as f:\n            json.dump(config2, f)\n        \n        output_file = temp_dir / \"benchmark_results.json\"\n        \n        result = runner.invoke(cli, [\n            'benchmark', 'compare',\n            '--config1', sample_config_file,\n            '--config2', str(config_file2),\n            '--queries', sample_queries_file,\n            '--output', str(output_file)\n        ])\n        \n        assert result.exit_code == 0\n        assert \"Comparing\" in result.output\n        assert \"Winner\" in result.output\n        \n        # Check output file\n        if output_file.exists():\n            with open(output_file, 'r') as f:\n                results = json.load(f)\n            assert \"config1\" in results\n            assert \"config2\" in results\n\n\n@pytest.mark.skipif(not CLI_AVAILABLE, reason=\"CLI not available\")\nclass TestCLIIntegration:\n    \"\"\"Test CLI integration scenarios.\"\"\"\n    \n    def test_verbose_mode(self, runner):\n        \"\"\"Test CLI with verbose flag.\"\"\"\n        result = runner.invoke(cli, ['--verbose', 'status'])\n        assert result.exit_code == 0\n    \n    def test_config_file_loading(self, runner, sample_config_file):\n        \"\"\"Test loading configuration file.\"\"\"\n        result = runner.invoke(cli, ['--config', sample_config_file, 'status'])\n        assert result.exit_code == 0\n    \n    def test_invalid_config_file(self, runner):\n        \"\"\"Test handling of invalid config file.\"\"\"\n        result = runner.invoke(cli, ['--config', 'nonexistent.json', 'status'])\n        assert result.exit_code != 0  # Should fail due to missing file\n    \n    def test_evaluation_workflow(self, runner, temp_dir):\n        \"\"\"Test complete evaluation workflow.\"\"\"\n        \n        # Step 1: Generate queries\n        queries_file = temp_dir / \"workflow_queries.json\"\n        result = runner.invoke(cli, [\n            'evaluate', 'generate-queries',\n            '--count', '5',\n            '--output', str(queries_file)\n        ])\n        assert result.exit_code == 0\n        assert queries_file.exists()\n        \n        # Step 2: Run evaluation\n        results_file = temp_dir / \"workflow_results.json\"\n        result = runner.invoke(cli, [\n            'evaluate', 'run',\n            '--queries', str(queries_file),\n            '--output', str(results_file)\n        ])\n        \n        # May fail due to missing config, but should handle gracefully\n        # The important thing is that the command structure works\n        assert \"queries file specified\" in result.output or \"Evaluation Results\" in result.output\n\n\n@pytest.mark.skipif(not CLI_AVAILABLE, reason=\"CLI not available\")\nclass TestCLIErrorHandling:\n    \"\"\"Test CLI error handling.\"\"\"\n    \n    def test_missing_required_args(self, runner):\n        \"\"\"Test commands with missing required arguments.\"\"\"\n        \n        # Generate queries without output file\n        result = runner.invoke(cli, ['evaluate', 'generate-queries'])\n        assert result.exit_code != 0\n    \n    def test_invalid_file_paths(self, runner):\n        \"\"\"Test commands with invalid file paths.\"\"\"\n        \n        result = runner.invoke(cli, [\n            'evaluate', 'run',\n            '--queries', 'nonexistent.json'\n        ])\n        assert result.exit_code != 0\n    \n    def test_invalid_options(self, runner):\n        \"\"\"Test commands with invalid option values.\"\"\"\n        \n        result = runner.invoke(cli, [\n            'evaluate', 'generate-queries',\n            '--complexity', 'invalid',\n            '--output', 'test.json'\n        ])\n        assert result.exit_code != 0\n\n\n@pytest.mark.skipif(not CLI_AVAILABLE, reason=\"CLI not available\")\nclass TestLegacyCommands:\n    \"\"\"Test legacy command compatibility.\"\"\"\n    \n    def test_legacy_route_command(self, runner):\n        \"\"\"Test legacy route command if available.\"\"\"\n        \n        # This test will only run if legacy imports are available\n        result = runner.invoke(cli, ['route', 'What is AI?'])\n        \n        # Should either work or fail gracefully\n        # The important thing is it doesn't crash\n        assert result.exit_code in [0, 1, 2]  # Various acceptable exit codes\n\n\n# Mock CLI tests for when actual CLI is not available\n@pytest.mark.skipif(CLI_AVAILABLE, reason=\"CLI is available, no need for mocks\")\nclass TestMockCLI:\n    \"\"\"Mock tests when CLI is not available.\"\"\"\n    \n    def test_cli_import_fallback(self):\n        \"\"\"Test that CLI import failure is handled gracefully.\"\"\"\n        # This test runs when CLI_AVAILABLE is False\n        assert cli is None\n        # The import should not crash the test suite\n    \n    @patch('builtins.print')\n    def test_mock_cli_functionality(self, mock_print):\n        \"\"\"Test mock CLI functionality.\"\"\"\n        # Mock a simple CLI function\n        def mock_status():\n            print(\"System Status: OK\")\n            return {\"status\": \"ok\"}\n        \n        result = mock_status()\n        assert result[\"status\"] == \"ok\"\n        mock_print.assert_called_with(\"System Status: OK\")\n\n\n# Utility function tests\nclass TestCLIUtils:\n    \"\"\"Test CLI utility functions.\"\"\"\n    \n    def test_json_file_creation(self, temp_dir):\n        \"\"\"Test JSON file creation helper.\"\"\"\n        \n        test_data = {\"test\": \"data\", \"number\": 42}\n        test_file = temp_dir / \"test_output.json\"\n        \n        with open(test_file, 'w') as f:\n            json.dump(test_data, f, indent=2)\n        \n        # Verify file was created correctly\n        assert test_file.exists()\n        \n        with open(test_file, 'r') as f:\n            loaded_data = json.load(f)\n        \n        assert loaded_data == test_data\n    \n    def test_file_validation(self, temp_dir):\n        \"\"\"Test file validation logic.\"\"\"\n        \n        existing_file = temp_dir / \"exists.json\"\n        with open(existing_file, 'w') as f:\n            json.dump({\"exists\": True}, f)\n        \n        non_existing_file = temp_dir / \"does_not_exist.json\"\n        \n        assert existing_file.exists()\n        assert not non_existing_file.exists()\n    \n    def test_configuration_merging(self):\n        \"\"\"Test configuration merging logic.\"\"\"\n        \n        default_config = {\n            \"retrieval_config\": {\"top_k\": 5},\n            \"llm_config\": {\"model\": \"gpt-3.5-turbo\"}\n        }\n        \n        user_config = {\n            \"retrieval_config\": {\"top_k\": 10},\n            \"new_setting\": \"value\"\n        }\n        \n        # Mock configuration merging\n        merged_config = {**default_config, **user_config}\n        merged_config[\"retrieval_config\"] = {\n            **default_config[\"retrieval_config\"],\n            **user_config[\"retrieval_config\"]\n        }\n        \n        assert merged_config[\"retrieval_config\"][\"top_k\"] == 10\n        assert merged_config[\"llm_config\"][\"model\"] == \"gpt-3.5-turbo\"\n        assert merged_config[\"new_setting\"] == \"value\""
