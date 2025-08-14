#!/usr/bin/env python3
"""
End-to-End Orchestration System Test
Validates complete autonomous orchestration workflow
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
import sys

sys.path.append('/home/am/TestAlex/orchestration')
from live_orchestrator import LiveOrchestrationSystem
from autonomous_monitor import AutonomousMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchestrationE2ETest:
    """End-to-end test suite for orchestration system."""
    
    def __init__(self):
        self.test_results = []
        self.project_root = Path("/home/am/TestAlex")
        
    async def run_complete_test(self):
        """Run complete end-to-end test suite."""
        logger.info("🚀 ACIM GUIDE ORCHESTRATION - END-TO-END TEST")
        logger.info("=" * 60)
        
        # Test 1: System Initialization
        await self._test_system_initialization()
        
        # Test 2: Production Metrics Monitoring
        await self._test_metrics_monitoring()
        
        # Test 3: Opportunity Identification
        await self._test_opportunity_identification()
        
        # Test 4: Agent Task Execution
        await self._test_agent_execution()
        
        # Test 5: Results Storage
        await self._test_results_storage()
        
        # Test 6: Autonomous Monitor
        await self._test_autonomous_monitor()
        
        # Generate test report
        self._generate_test_report()
        
        return self._calculate_test_score()
    
    async def _test_system_initialization(self):
        """Test system initialization and API connections."""
        logger.info("📋 Test 1: System Initialization")
        
        try:
            # Test orchestrator initialization
            orchestrator = LiveOrchestrationSystem()
            
            # Verify OpenAI client
            if orchestrator.openai_client is None:
                raise Exception("OpenAI client not initialized")
            
            # Verify agents registry loaded
            if len(orchestrator.agents_registry) == 0:
                raise Exception("No agents loaded from registry")
            
            self._record_test_result("system_initialization", True, 
                                   f"✅ System initialized with {len(orchestrator.agents_registry)} agents")
                                   
        except Exception as e:
            self._record_test_result("system_initialization", False, f"❌ {str(e)}")
    
    async def _test_metrics_monitoring(self):
        """Test production metrics monitoring."""
        logger.info("📋 Test 2: Production Metrics Monitoring")
        
        try:
            orchestrator = LiveOrchestrationSystem()
            metrics = await orchestrator.monitor_production_health()
            
            # Validate metrics structure
            required_sections = ['user_engagement', 'technical_health', 'content_quality', 'business_metrics']
            for section in required_sections:
                if section not in metrics:
                    raise Exception(f"Missing metrics section: {section}")
            
            self._record_test_result("metrics_monitoring", True, 
                                   "✅ Production metrics collected successfully")
                                   
        except Exception as e:
            self._record_test_result("metrics_monitoring", False, f"❌ {str(e)}")
    
    async def _test_opportunity_identification(self):
        """Test opportunity identification logic."""
        logger.info("📋 Test 3: Opportunity Identification")
        
        try:
            orchestrator = LiveOrchestrationSystem()
            
            # Get metrics
            metrics = await orchestrator.monitor_production_health()
            
            # Identify opportunities
            opportunities = await orchestrator.identify_improvement_opportunities(metrics)
            
            if len(opportunities) == 0:
                logger.warning("⚠️ No opportunities identified (this may be normal)")
            
            # Validate opportunity structure
            for opp in opportunities:
                required_fields = ['id', 'type', 'priority', 'title', 'description', 'agents']
                for field in required_fields:
                    if field not in opp:
                        raise Exception(f"Opportunity missing field: {field}")
            
            self._record_test_result("opportunity_identification", True, 
                                   f"✅ Identified {len(opportunities)} improvement opportunities")
                                   
        except Exception as e:
            self._record_test_result("opportunity_identification", False, f"❌ {str(e)}")
    
    async def _test_agent_execution(self):
        """Test AI agent task execution."""
        logger.info("📋 Test 4: Agent Task Execution")
        
        try:
            orchestrator = LiveOrchestrationSystem()
            
            # Create a test task
            test_task = {
                "id": "test_task_001",
                "type": "test_execution",
                "priority": "medium",
                "title": "Test ACIM Content Validation",
                "description": "Validate that A Course in Miracles content meets quality standards",
                "agents": ["acim_scholar"],
                "potential_impact": "Improved spiritual authenticity",
                "estimated_hours": 2
            }
            
            # Execute task
            result = await orchestrator.execute_agent_task(test_task)
            
            # Validate result
            if result['success_rate'] < 0.5:
                raise Exception(f"Low task success rate: {result['success_rate']}")
            
            # Check agent results
            if len(result['agent_results']) == 0:
                raise Exception("No agent results returned")
            
            # Validate OpenAI API usage
            for agent_result in result['agent_results']:
                if agent_result['success'] and 'tokens_used' in agent_result['result']:
                    logger.info(f"   🤖 {agent_result['agent_name']}: "
                               f"{agent_result['result']['tokens_used']} tokens used")
            
            self._record_test_result("agent_execution", True, 
                                   f"✅ Task executed with {result['success_rate']*100:.0f}% success rate")
                                   
        except Exception as e:
            self._record_test_result("agent_execution", False, f"❌ {str(e)}")
    
    async def _test_results_storage(self):
        """Test results storage and persistence."""
        logger.info("📋 Test 5: Results Storage")
        
        try:
            orchestrator = LiveOrchestrationSystem()
            
            # Create test cycle result
            test_cycle = {
                "cycle_id": "test_cycle_001",
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": 30.5,
                "opportunities_identified": 2,
                "tasks_executed": 1,
                "success_rate": 1.0,
                "test": True
            }
            
            # Save results
            await orchestrator.save_cycle_results(test_cycle)
            
            # Verify file was created
            results_dir = self.project_root / "orchestration" / "results"
            cycle_file = results_dir / "cycle_test_cycle_001.json"
            
            if not cycle_file.exists():
                raise Exception("Cycle results file not created")
            
            # Verify file content
            with open(cycle_file, 'r') as f:
                saved_data = json.load(f)
                if saved_data['cycle_id'] != test_cycle['cycle_id']:
                    raise Exception("Saved data doesn't match original")
            
            self._record_test_result("results_storage", True, 
                                   "✅ Results saved and validated successfully")
                                   
        except Exception as e:
            self._record_test_result("results_storage", False, f"❌ {str(e)}")
    
    async def _test_autonomous_monitor(self):
        """Test autonomous monitoring system initialization."""
        logger.info("📋 Test 6: Autonomous Monitor")
        
        try:
            # Test monitor initialization
            monitor = AutonomousMonitor()
            
            # Test configuration loading
            if not monitor.monitoring_config:
                raise Exception("Monitoring configuration not loaded")
            
            # Test thresholds
            thresholds = monitor.monitoring_config.get('thresholds', {})
            required_thresholds = ['response_time_critical', 'error_rate_critical', 'citation_accuracy_critical']
            for threshold in required_thresholds:
                if threshold not in thresholds:
                    raise Exception(f"Missing threshold: {threshold}")
            
            # Test logs directory creation
            logs_dir = self.project_root / "orchestration" / "logs"
            if not logs_dir.exists():
                raise Exception("Logs directory not created")
            
            self._record_test_result("autonomous_monitor", True, 
                                   "✅ Autonomous monitor initialized successfully")
                                   
        except Exception as e:
            self._record_test_result("autonomous_monitor", False, f"❌ {str(e)}")
    
    def _record_test_result(self, test_name: str, success: bool, message: str):
        """Record a test result."""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        logger.info(f"   {message}")
    
    def _generate_test_report(self):
        """Generate comprehensive test report."""
        logger.info("\n📊 END-TO-END TEST REPORT")
        logger.info("=" * 60)
        
        passed = sum(1 for r in self.test_results if r['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        logger.info(f"📈 Overall Results: {passed}/{total} tests passed ({success_rate:.1f}%)")
        logger.info("\n📋 Detailed Results:")
        
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            logger.info(f"   {status} - {result['test']}")
            if not result['success']:
                logger.info(f"      {result['message']}")
        
        # Save test report
        self._save_test_report(success_rate)
    
    def _save_test_report(self, success_rate: float):
        """Save test report to file."""
        try:
            report_data = {
                "test_run_id": f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "success_rate": success_rate,
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for r in self.test_results if r['success']),
                "results": self.test_results
            }
            
            # Save to orchestration directory
            report_file = self.project_root / "orchestration" / "test_reports" / f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            logger.info(f"💾 Test report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to save test report: {e}")
    
    def _calculate_test_score(self) -> float:
        """Calculate overall test score."""
        if not self.test_results:
            return 0.0
        
        passed = sum(1 for r in self.test_results if r['success'])
        return passed / len(self.test_results)


async def main():
    """Run the end-to-end test suite."""
    tester = OrchestrationE2ETest()
    
    try:
        test_score = await tester.run_complete_test()
        
        logger.info(f"\n🎯 FINAL TEST SCORE: {test_score*100:.1f}%")
        
        if test_score >= 0.8:
            logger.info("🎉 ORCHESTRATION SYSTEM READY FOR PRODUCTION!")
            return True
        else:
            logger.warning("⚠️ Some tests failed. Review before production deployment.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
