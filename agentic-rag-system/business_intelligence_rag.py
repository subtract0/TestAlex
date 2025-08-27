#!/usr/bin/env python3
"""
Business Intelligence RAG System
================================

A RAG system designed specifically to help achieve 10k/month passive income
by analyzing your codebase, business metrics, and interactions to suggest
strategic next steps.

Business Focus:
- Track revenue progress toward 10k/month goal
- Analyze what's working vs what's not
- Suggest concrete next actions
- Learn from your interaction patterns
- Monitor business-critical metrics

Technical Focus:
- Simple, practical, gets things done
- Learns from your actual codebase and business data
- Provides actionable business intelligence
- Tracks progress toward revenue goals
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
import openai
from openai import OpenAI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BusinessMetric:
    """Track business metrics toward 10k/month goal"""
    date: str
    revenue: float  # Monthly revenue
    users: int      # Active users
    conversions: float  # Conversion rate
    traffic: int    # Website traffic
    goal_progress: float  # % toward 10k/month
    notes: str      # What happened this month

@dataclass
class InteractionPattern:
    """Learn from user interaction patterns"""
    timestamp: str
    question: str
    category: str  # 'revenue', 'technical', 'strategy', 'marketing'
    response: str
    outcome: Optional[str] = None  # Did it help? What happened?

@dataclass
class BusinessInsight:
    """Strategic insights for business growth"""
    timestamp: str
    insight_type: str  # 'opportunity', 'bottleneck', 'optimization'
    priority: int      # 1-5 (5 = urgent)
    description: str
    suggested_actions: List[str]
    expected_impact: str  # Revenue impact estimate
    effort_required: str  # Low/Medium/High

class BusinessIntelligenceRAG:
    """RAG system focused on business growth and revenue optimization"""
    
    def __init__(self, base_dir: str = "/home/am/TestAlex"):
        self.base_dir = Path(base_dir)
        self.db_path = self.base_dir / "business_intelligence.db"
        self.openai_client = None
        self.goal_monthly_revenue = 10000  # 10k/month goal
        
        # Initialize database
        self._init_database()
        
        # Setup OpenAI if available
        self._setup_openai()
        
        logger.info("Business Intelligence RAG initialized")
        logger.info(f"Goal: €{self.goal_monthly_revenue}/month")
        
    def _init_database(self):
        """Initialize SQLite database for business intelligence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Business metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                revenue REAL NOT NULL,
                users INTEGER NOT NULL,
                conversions REAL NOT NULL,
                traffic INTEGER NOT NULL,
                goal_progress REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Interaction patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interaction_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                question TEXT NOT NULL,
                category TEXT NOT NULL,
                response TEXT NOT NULL,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Business insights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                insight_type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                description TEXT NOT NULL,
                suggested_actions TEXT NOT NULL,  -- JSON array
                expected_impact TEXT NOT NULL,
                effort_required TEXT NOT NULL,
                status TEXT DEFAULT 'active',  -- active, implemented, dismissed
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Codebase analysis table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS codebase_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                business_relevance TEXT NOT NULL,  -- 'high', 'medium', 'low'
                revenue_potential TEXT,  -- How this could make money
                current_status TEXT,     -- 'working', 'needs_work', 'idea'
                last_modified TEXT,
                content_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Business intelligence database initialized")
    
    def _setup_openai(self):
        """Setup OpenAI client if API key is available"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client configured")
        else:
            logger.warning("OPENAI_API_KEY not found - AI features will be limited")
    
    def analyze_codebase(self) -> Dict[str, Any]:
        """Analyze existing codebase for business opportunities"""
        logger.info("Analyzing codebase for business opportunities...")
        
        business_files = []
        revenue_opportunities = []
        
        # Key business files to analyze
        key_files = [
            "STRATEGIC_VISION.md",
            "README.md", 
            "orchestrator_v2_demo.py",
            "functions/index.js",  # Firebase functions
            "main.py",
            "manage_assistant.py"
        ]
        
        for file_name in key_files:
            file_path = self.base_dir / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Analyze business relevance
                    analysis = self._analyze_file_business_potential(file_name, content)
                    business_files.append(analysis)
                    
                    # Store in database
                    self._store_codebase_analysis(analysis)
                    
                except Exception as e:
                    logger.error(f"Error analyzing {file_name}: {e}")
        
        # Generate insights
        insights = self._generate_business_insights()
        
        return {
            "files_analyzed": len(business_files),
            "revenue_opportunities": len([f for f in business_files if f['revenue_potential']]),
            "key_insights": insights[:3],  # Top 3 insights
            "next_actions": self._get_recommended_actions()
        }
    
    def _analyze_file_business_potential(self, file_name: str, content: str) -> Dict[str, Any]:
        """Analyze a file's business potential"""
        
        # Simple business relevance scoring
        revenue_keywords = [
            "€7", "premium", "course", "coaching", "payment", "revenue", 
            "subscription", "pricing", "conversion", "funnel"
        ]
        
        technical_keywords = [
            "firebase", "openai", "api", "function", "deploy", "production"
        ]
        
        strategy_keywords = [
            "strategic", "vision", "business", "goal", "metric", "growth"
        ]
        
        content_lower = content.lower()
        
        # Score business relevance
        revenue_score = sum(1 for keyword in revenue_keywords if keyword in content_lower)
        technical_score = sum(1 for keyword in technical_keywords if keyword in content_lower)
        strategy_score = sum(1 for keyword in strategy_keywords if keyword in content_lower)
        
        # Determine business relevance
        if revenue_score >= 3 or strategy_score >= 3:
            business_relevance = "high"
        elif revenue_score >= 1 or technical_score >= 2:
            business_relevance = "medium"
        else:
            business_relevance = "low"
        
        # Determine revenue potential
        revenue_potential = ""
        current_status = "unknown"
        
        if "strategic_vision" in file_name.lower():
            revenue_potential = "Core business strategy - €7 courses + premium coaching"
            current_status = "documented"
        elif "firebase" in content_lower or "function" in content_lower:
            revenue_potential = "Payment processing and user management infrastructure"
            current_status = "working"
        elif "openai" in content_lower or "assistant" in content_lower:
            revenue_potential = "AI-powered features for premium tiers"
            current_status = "working"
        elif "orchestrat" in file_name.lower():
            revenue_potential = "Automation for content creation and marketing"
            current_status = "needs_work"
        
        return {
            "file_path": file_name,
            "file_type": Path(file_name).suffix or "script",
            "business_relevance": business_relevance,
            "revenue_potential": revenue_potential,
            "current_status": current_status,
            "last_modified": datetime.now().isoformat(),
            "content_summary": content[:500] + "..." if len(content) > 500 else content
        }
    
    def _store_codebase_analysis(self, analysis: Dict[str, Any]):
        """Store codebase analysis in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO codebase_analysis 
            (file_path, file_type, business_relevance, revenue_potential, 
             current_status, last_modified, content_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            analysis["file_path"],
            analysis["file_type"], 
            analysis["business_relevance"],
            analysis["revenue_potential"],
            analysis["current_status"],
            analysis["last_modified"],
            analysis["content_summary"]
        ))
        
        conn.commit()
        conn.close()
    
    def record_business_metrics(self, revenue: float, users: int, conversions: float, 
                               traffic: int, notes: str = "") -> BusinessMetric:
        """Record current business metrics"""
        
        goal_progress = (revenue / self.goal_monthly_revenue) * 100
        
        metric = BusinessMetric(
            date=datetime.now().strftime("%Y-%m"),
            revenue=revenue,
            users=users,
            conversions=conversions,
            traffic=traffic,
            goal_progress=goal_progress,
            notes=notes
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO business_metrics 
            (date, revenue, users, conversions, traffic, goal_progress, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metric.date, metric.revenue, metric.users, metric.conversions,
            metric.traffic, metric.goal_progress, metric.notes
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Recorded metrics: €{revenue} ({goal_progress:.1f}% of goal)")
        return metric
    
    def ask_business_question(self, question: str) -> str:
        """Ask a business-focused question and get strategic advice"""
        
        # Categorize the question
        category = self._categorize_question(question)
        
        # Get relevant context
        context = self._get_business_context(category)
        
        # Generate response
        if self.openai_client:
            response = self._generate_ai_response(question, context, category)
        else:
            response = self._generate_fallback_response(question, context, category)
        
        # Record the interaction
        self._record_interaction(question, category, response)
        
        return response
    
    def _categorize_question(self, question: str) -> str:
        """Categorize business question"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["revenue", "money", "income", "profit", "sales"]):
            return "revenue"
        elif any(word in question_lower for word in ["technical", "code", "bug", "deploy", "api"]):
            return "technical"
        elif any(word in question_lower for word in ["strategy", "plan", "goal", "next", "should"]):
            return "strategy"
        elif any(word in question_lower for word in ["marketing", "traffic", "seo", "users", "growth"]):
            return "marketing"
        else:
            return "general"
    
    def _get_business_context(self, category: str) -> Dict[str, Any]:
        """Get relevant business context for the question category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        context = {}
        
        # Get recent metrics
        cursor.execute("""
            SELECT * FROM business_metrics 
            ORDER BY created_at DESC LIMIT 3
        """)
        context["recent_metrics"] = cursor.fetchall()
        
        # Get relevant files
        if category == "technical":
            cursor.execute("""
                SELECT * FROM codebase_analysis 
                WHERE current_status = 'working' OR current_status = 'needs_work'
                ORDER BY business_relevance DESC LIMIT 5
            """)
        else:
            cursor.execute("""
                SELECT * FROM codebase_analysis 
                WHERE business_relevance = 'high'
                ORDER BY created_at DESC LIMIT 5
            """)
        
        context["relevant_files"] = cursor.fetchall()
        
        # Get recent insights
        cursor.execute("""
            SELECT * FROM business_insights 
            WHERE status = 'active' 
            ORDER BY priority DESC, created_at DESC LIMIT 3
        """)
        context["active_insights"] = cursor.fetchall()
        
        conn.close()
        return context
    
    def _generate_ai_response(self, question: str, context: Dict[str, Any], category: str) -> str:
        """Generate AI-powered business advice"""
        try:
            # Build context prompt
            context_prompt = self._build_context_prompt(context, category)
            
            system_prompt = f"""You are a business intelligence assistant helping achieve €10,000/month passive income through ACIMguide, a spiritual guidance platform.

Current Business Situation:
- ACIMguide.com: Working ACIM-GPT platform (spiritual guidance)
- Revenue Model: €7 courses + premium coaching (3-4 digits)
- Technical Foundation: Firebase + OpenAI (working)
- Goal: €10,000/month passive income

Your responses should be:
1. ACTIONABLE - specific next steps
2. REVENUE-FOCUSED - how does this make money?
3. PRACTICAL - considering current resources
4. MEASURABLE - how to track progress

{context_prompt}

Always end with a concrete next action and revenue impact estimate."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective for business analysis
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.1  # More focused responses
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return self._generate_fallback_response(question, context, category)
    
    def _build_context_prompt(self, context: Dict[str, Any], category: str) -> str:
        """Build context prompt from business data"""
        prompt_parts = []
        
        # Recent metrics
        if context.get("recent_metrics"):
            prompt_parts.append("Recent Business Metrics:")
            for metric in context["recent_metrics"][:2]:  # Last 2 months
                prompt_parts.append(f"- {metric[1]}: €{metric[2]} revenue, {metric[3]} users, {metric[5]:.1f}% of goal")
        
        # High-value opportunities
        if context.get("relevant_files"):
            prompt_parts.append("\nKey Business Assets:")
            for file_info in context["relevant_files"][:3]:
                if file_info[4]:  # revenue_potential
                    prompt_parts.append(f"- {file_info[1]}: {file_info[4]} (Status: {file_info[5]})")
        
        # Active insights
        if context.get("active_insights"):
            prompt_parts.append("\nActive Business Insights:")
            for insight in context["active_insights"][:2]:
                prompt_parts.append(f"- Priority {insight[3]}: {insight[4]}")
        
        return "\n".join(prompt_parts) if prompt_parts else "No specific context available."
    
    def _generate_fallback_response(self, question: str, context: Dict[str, Any], category: str) -> str:
        """Generate fallback response when AI is not available"""
        
        # Simple rule-based responses
        if category == "revenue":
            return """Based on your ACIMguide platform:

**Revenue Opportunities:**
1. Launch €7 14-day courses immediately (documented in STRATEGIC_VISION.md)
2. Premium coaching tiers (3-4 digit pricing potential) 
3. ACIMcoach.com blog for organic traffic

**Next Action:** Implement course purchase flow in Firebase
**Revenue Impact:** €7 x 100 courses = €700/month (7% of goal)"""

        elif category == "strategy":
            return """Strategic Analysis for 10k/month goal:

**Current Assets:**
- ✅ Working ACIMguide.com platform
- ✅ Firebase + OpenAI integration
- ✅ Documented business strategy

**Missing Pieces:**
- Payment processing for courses
- Blog automation for traffic
- Premium tier implementation

**Next Action:** Focus on €7 course implementation first
**Timeline:** 30-60 days to first revenue"""

        elif category == "technical":
            return """Technical Priority Assessment:

**Working Systems:**
- Firebase backend + OpenAI integration
- User authentication and management
- Real-time chat interface

**Needs Work:**
- Payment processing integration
- Course progress tracking
- Blog automation system

**Next Action:** Implement Stripe integration for €7 courses
**Impact:** Enables immediate revenue generation"""

        else:
            return f"""I'll help you reach €10k/month with ACIMguide.

Your question category: {category}

**Current Status:** You have a working spiritual guidance platform
**Goal:** €10,000/month passive income
**Path:** €7 courses + premium coaching + organic traffic

**Next Action:** Ask me specifically about revenue, strategy, or technical implementation.
**Focus Areas:** Course sales, premium coaching, traffic growth"""
    
    def _record_interaction(self, question: str, category: str, response: str):
        """Record interaction for learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO interaction_patterns 
            (timestamp, question, category, response)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            question,
            category,
            response
        ))
        
        conn.commit()
        conn.close()
    
    def _generate_business_insights(self) -> List[Dict[str, Any]]:
        """Generate strategic business insights"""
        insights = []
        
        # Analyze current state
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we have working revenue infrastructure
        cursor.execute("""
            SELECT COUNT(*) FROM codebase_analysis 
            WHERE revenue_potential LIKE '%payment%' AND current_status = 'working'
        """)
        payment_ready = cursor.fetchone()[0] > 0
        
        if not payment_ready:
            insights.append({
                "insight_type": "bottleneck",
                "priority": 5,
                "description": "No payment processing system detected - blocking all revenue",
                "suggested_actions": [
                    "Integrate Stripe into Firebase functions",
                    "Create €7 course purchase flow", 
                    "Test payment processing with small amounts"
                ],
                "expected_impact": "€700-2000/month (100+ course sales)",
                "effort_required": "Medium (1-2 weeks)"
            })
        
        # Check for documented but unimplemented features
        cursor.execute("""
            SELECT COUNT(*) FROM codebase_analysis 
            WHERE revenue_potential LIKE '%course%' AND current_status = 'documented'
        """)
        documented_courses = cursor.fetchone()[0] > 0
        
        if documented_courses:
            insights.append({
                "insight_type": "opportunity", 
                "priority": 4,
                "description": "14-day course strategy is documented but not implemented",
                "suggested_actions": [
                    "Build course content delivery system",
                    "Create personalized course progression",
                    "Set up Firebase backend for course tracking"
                ],
                "expected_impact": "€2000-5000/month (scale depends on traffic)",
                "effort_required": "High (4-6 weeks)"
            })
        
        # Traffic generation insight
        insights.append({
            "insight_type": "optimization",
            "priority": 3, 
            "description": "ACIMcoach.com blog funnel not implemented - missing organic traffic",
            "suggested_actions": [
                "Set up automated blog post generation",
                "Implement SEO optimization for ACIM keywords",
                "Create traffic funnels to €7 courses"
            ],
            "expected_impact": "€1000-3000/month (organic conversions)",
            "effort_required": "Medium (2-3 weeks)"
        })
        
        conn.close()
        return insights
    
    def _get_recommended_actions(self) -> List[str]:
        """Get prioritized list of recommended actions"""
        return [
            "1. Implement Stripe payment processing for €7 courses (HIGH PRIORITY)",
            "2. Build 14-day course content delivery system", 
            "3. Set up ACIMcoach.com blog automation for traffic",
            "4. Create premium coaching tier and booking system",
            "5. Implement analytics to track conversion rates"
        ]
    
    def get_business_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive business dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get latest metrics
        cursor.execute("""
            SELECT * FROM business_metrics 
            ORDER BY created_at DESC LIMIT 1
        """)
        latest_metrics = cursor.fetchone()
        
        # Get progress toward goal
        current_revenue = latest_metrics[2] if latest_metrics else 0
        goal_progress = (current_revenue / self.goal_monthly_revenue) * 100
        
        # Get active insights
        cursor.execute("""
            SELECT * FROM business_insights 
            WHERE status = 'active' 
            ORDER BY priority DESC LIMIT 5
        """)
        active_insights = cursor.fetchall()
        
        # Get recent interactions
        cursor.execute("""
            SELECT category, COUNT(*) FROM interaction_patterns 
            WHERE datetime(timestamp) >= datetime('now', '-7 days')
            GROUP BY category
        """)
        interaction_patterns = cursor.fetchall()
        
        conn.close()
        
        return {
            "goal": f"€{self.goal_monthly_revenue}/month",
            "current_revenue": f"€{current_revenue}/month",
            "goal_progress": f"{goal_progress:.1f}%",
            "revenue_gap": f"€{self.goal_monthly_revenue - current_revenue}",
            "active_insights": len(active_insights),
            "high_priority_actions": [insight[4] for insight in active_insights if insight[3] >= 4],
            "interaction_patterns": dict(interaction_patterns),
            "next_milestone": "€1000/month (10% of goal)"
        }

def main():
    """Demo the Business Intelligence RAG system"""
    print("🚀 Business Intelligence RAG - Path to €10k/month")
    print("=" * 50)
    
    # Initialize system
    bi_rag = BusinessIntelligenceRAG()
    
    # Analyze current codebase
    print("📊 Analyzing your business assets...")
    analysis = bi_rag.analyze_codebase()
    
    print(f"✅ Analyzed {analysis['files_analyzed']} key business files")
    print(f"💰 Found {analysis['revenue_opportunities']} revenue opportunities")
    
    # Show key insights
    print("\n🎯 Top Business Insights:")
    for i, insight in enumerate(analysis['key_insights'], 1):
        print(f"{i}. {insight['description']}")
        print(f"   Impact: {insight['expected_impact']}")
        print(f"   Effort: {insight['effort_required']}")
        print()
    
    # Show recommended actions
    print("📋 Recommended Next Actions:")
    for action in analysis['next_actions'][:3]:
        print(f"• {action}")
    
    # Get business dashboard
    print("\n📈 Business Dashboard:")
    dashboard = bi_rag.get_business_dashboard()
    print(f"Goal: {dashboard['goal']}")
    print(f"Current: {dashboard['current_revenue']}")  
    print(f"Progress: {dashboard['goal_progress']}")
    print(f"Gap: {dashboard['revenue_gap']}")
    
    # Interactive demo
    print("\n💬 Ask me business questions to get strategic advice!")
    print("Examples:")
    print("- 'How can I implement the €7 course system?'")
    print("- 'What should I focus on to increase revenue?'") 
    print("- 'How do I set up payment processing?'")
    print("- 'What are my biggest bottlenecks?'")
    
    while True:
        try:
            question = input("\n🤔 Your question (or 'quit'): ").strip()
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if question:
                print("🧠 Analyzing...")
                response = bi_rag.ask_business_question(question)
                print(f"\n💡 Strategic Advice:\n{response}")
                
        except KeyboardInterrupt:
            break
    
    print("\n✅ Ready to help you reach €10k/month!")
    print("Run this script anytime for business intelligence.")

if __name__ == "__main__":
    main()
