#!/usr/bin/env python3
"""
ACIMguide Autonomous Pipeline Startup Script
Single command to launch the complete autonomous value generation system.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add orchestration directory to Python path
project_root = Path(__file__).parent
orchestration_path = project_root / "orchestration"
sys.path.insert(0, str(orchestration_path))

from autonomous_value_maximizer import AutonomousValueMaximizer

async def main():
    """Launch the complete autonomous pipeline."""
    print("🚀 Starting ACIMguide Autonomous Value Generation Pipeline")
    print("=" * 60)
    print("💰 Mission: Maximize project value and generate sustainable cashflow")
    print("🤖 Integrating all specialized AI agents for autonomous operation")
    print("📊 Monitoring system health and performance metrics")
    print("🎯 Targeting $10k/month recurring revenue")
    print("=" * 60)
    
    # Initialize and start the autonomous value maximizer
    maximizer = AutonomousValueMaximizer()
    
    try:
        await maximizer.start_autonomous_value_maximization()
    except KeyboardInterrupt:
        print("\n🛑 Pipeline stopped by user")
    except Exception as e:
        print(f"\n💥 Pipeline error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
