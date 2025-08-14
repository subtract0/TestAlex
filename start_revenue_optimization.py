#!/usr/bin/env python3
"""
Revenue & Conversion Optimization Loop Launcher
Starts the complete revenue optimization system that pulls analytics,
computes funnel drop-offs, and creates conversion experiment tasks.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add orchestration to path
sys.path.insert(0, str(Path(__file__).parent / "orchestration"))

from revenue_analyst import RevenueAnalyst
from analytics_integration import AnalyticsIntegration, load_analytics_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestration/revenue_optimization.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Launch the complete Revenue & Conversion Optimization Loop."""
    
    print("=" * 80)
    print("🚀 ACIMguide Revenue & Conversion Optimization Loop")
    print("=" * 80)
    print()
    print("📊 Mission: Reach €10,000 Monthly Recurring Revenue (MRR)")
    print("🎯 Strategy: +20% conversion improvement per 2-week cycle")
    print("🔬 Method: Data-driven A/B experiments on pricing, copy, landing pages")
    print("🤖 System: Autonomous analytics pulling + task generation")
    print()
    print("Analytics Sources:")
    print("  📈 Mixpanel - Conversion funnel tracking")
    print("  🔥 Firebase Analytics - User behavior & revenue")
    print("  💰 Revenue data - MRR, ARPU, LTV calculations")
    print()
    print("Experiment Types:")
    print("  💰 Pricing - Trial duration, tier structure, value props")
    print("  ✍️  Copy - Headlines, CTAs, email sequences")
    print("  🎨 Landing Pages - Layout, testimonials, mobile UX")
    print("  🚪 Onboarding - Flow length, personalization, quick wins")
    print()
    print("=" * 80)
    
    try:
        # Initialize analytics integration
        logger.info("🔧 Initializing analytics integration...")
        analytics_config = load_analytics_config()
        analytics = AnalyticsIntegration(analytics_config)
        
        # Test analytics connection
        logger.info("🧪 Testing analytics connection...")
        test_data = await analytics.pull_complete_funnel_data()
        
        if test_data and test_data.get("normalized"):
            logger.info("✅ Analytics integration successful")
            
            # Log current metrics
            metrics = test_data["normalized"]
            funnel = metrics.get("funnel", {})
            revenue = metrics.get("revenue", {})
            
            print("\n📊 Current Funnel Metrics:")
            print(f"  Visitors: {funnel.get('visitor', 0):,}")
            print(f"  Signups: {funnel.get('signup', 0):,}")
            print(f"  Activations: {funnel.get('activation', 0):,}")
            print(f"  Trials: {funnel.get('trial', 0):,}")
            print(f"  Paid: {funnel.get('paid', 0):,}")
            print(f"  Retained: {funnel.get('retained', 0):,}")
            
            print("\n💰 Current Revenue:")
            print(f"  MRR: €{revenue.get('mrr', 0):,.2f}")
            print(f"  Total Revenue: €{revenue.get('total_revenue', 0):,.2f}")
            print(f"  ARPU: €{revenue.get('arpu', 0):,.2f}")
            
            if "derived_metrics" in metrics:
                derived = metrics["derived_metrics"]
                print(f"\n📈 Conversion Rates:")
                conv_rates = derived.get("conversion_rates", {})
                for stage, rate in conv_rates.items():
                    print(f"  {stage.replace('_', ' → ').title()}: {rate:.1%}")
        else:
            logger.warning("⚠️  Analytics test returned no data - using simulated data")
        
        print("\n" + "=" * 80)
        print("🔄 Starting Revenue Optimization Loop...")
        print("=" * 80)
        
        # Initialize and start Revenue Analyst
        revenue_analyst = RevenueAnalyst()
        
        # Start the optimization loop
        await revenue_analyst.start_revenue_optimization_loop()
        
    except KeyboardInterrupt:
        print("\n🛑 Revenue optimization loop stopped by user")
        logger.info("Revenue optimization loop interrupted by user")
    except Exception as e:
        print(f"\n❌ Error starting revenue optimization: {e}")
        logger.error(f"Error starting revenue optimization: {e}")
        raise
    finally:
        print("\n✅ Revenue optimization loop shutdown complete")

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required for asyncio features")
        sys.exit(1)
    
    # Run the optimization loop
    asyncio.run(main())
