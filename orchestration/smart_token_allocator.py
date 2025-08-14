#!/usr/bin/env python3
"""
Smart Token Allocation System
Intelligently allocates promotional tokens to maximize user value and spiritual impact
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class UserTier(Enum):
    """User tier classifications for token allocation"""
    SPIRITUAL_SEEKER = "spiritual_seeker"      # High engagement, spiritual focus
    PREMIUM_USER = "premium_user"              # Paying customers
    FREE_USER = "free_user"                    # Regular free users
    NEW_USER = "new_user"                      # First-time users
    RETURNING_USER = "returning_user"          # Returning after absence

class TaskPriority(Enum):
    """Task priority levels for token allocation"""
    SPIRITUAL_CRITICAL = "spiritual_critical"  # ACIM content integrity
    USER_EXPERIENCE = "user_experience"       # Direct user interaction
    BUSINESS_GROWTH = "business_growth"       # Revenue and engagement
    OPTIMIZATION = "optimization"             # Background improvements
    ANALYTICS = "analytics"                   # Data analysis and insights

@dataclass
class TokenAllocation:
    """Token allocation decision"""
    model: str
    max_tokens: int
    reason: str
    user_tier: UserTier
    task_priority: TaskPriority
    estimated_cost: float
    value_score: float

class SmartTokenAllocator:
    """Intelligently allocates promotional tokens to maximize user value"""
    
    def __init__(self):
        self.promotional_tokens = {
            'premium_remaining': 250000,      # GPT-5-chat-latest tokens
            'budget_remaining': 2500000,      # Budget model tokens
            'premium_used': 0,
            'budget_used': 0
        }
        
        self.model_costs = {
            'gpt-5-chat-latest': {'input': 0.05, 'output': 0.10},  # Per 1K tokens
            'gpt-5-thinking': {'input': 0.06, 'output': 0.12},     # Estimated higher cost
            'gpt-5-mini': {'input': 0.015, 'output': 0.03},
            'gpt-4o': {'input': 0.025, 'output': 0.05}
        }
        
        # Value scoring matrix (higher = more valuable)
        self.value_matrix = {
            (UserTier.SPIRITUAL_SEEKER, TaskPriority.SPIRITUAL_CRITICAL): 10.0,
            (UserTier.SPIRITUAL_SEEKER, TaskPriority.USER_EXPERIENCE): 9.0,
            (UserTier.PREMIUM_USER, TaskPriority.USER_EXPERIENCE): 8.5,
            (UserTier.PREMIUM_USER, TaskPriority.SPIRITUAL_CRITICAL): 8.0,
            (UserTier.NEW_USER, TaskPriority.USER_EXPERIENCE): 7.5,
            (UserTier.RETURNING_USER, TaskPriority.USER_EXPERIENCE): 7.0,
            (UserTier.FREE_USER, TaskPriority.USER_EXPERIENCE): 6.0,
            (UserTier.SPIRITUAL_SEEKER, TaskPriority.BUSINESS_GROWTH): 5.5,
            (UserTier.PREMIUM_USER, TaskPriority.OPTIMIZATION): 5.0,
            (UserTier.FREE_USER, TaskPriority.OPTIMIZATION): 3.0,
            (UserTier.FREE_USER, TaskPriority.ANALYTICS): 2.0,
        }
    
    def classify_user(self, user_data: Dict[str, Any]) -> UserTier:
        """Classify user based on engagement and behavior patterns"""
        engagement_score = user_data.get('engagement_score', 0)
        is_premium = user_data.get('is_premium', False)
        sessions_count = user_data.get('total_sessions', 0)
        spiritual_topics = user_data.get('spiritual_topic_engagement', 0)
        days_since_signup = user_data.get('days_since_signup', 0)
        days_since_last_visit = user_data.get('days_since_last_visit', 0)
        
        # Premium users get special treatment
        if is_premium:
            return UserTier.PREMIUM_USER
        
        # Highly engaged spiritual seekers
        if (engagement_score > 0.8 and 
            spiritual_topics > 0.7 and 
            sessions_count > 10):
            return UserTier.SPIRITUAL_SEEKER
        
        # New users (first 7 days)
        if days_since_signup <= 7:
            return UserTier.NEW_USER
        
        # Returning users (absent for 30+ days)
        if days_since_last_visit >= 30 and sessions_count > 3:
            return UserTier.RETURNING_USER
        
        # Default to free user
        return UserTier.FREE_USER
    
    def classify_task_priority(self, task_type: str, context: Dict[str, Any]) -> TaskPriority:
        """Classify task priority for token allocation"""
        
        # ACIM content integrity is always highest priority
        if any(keyword in task_type.lower() for keyword in 
               ['acim', 'spiritual', 'citation', 'content_quality', 'doctrinal']):
            return TaskPriority.SPIRITUAL_CRITICAL
        
        # Direct user interactions are high priority
        if any(keyword in task_type.lower() for keyword in 
               ['user_', 'chat', 'response', 'guidance', 'question']):
            return TaskPriority.USER_EXPERIENCE
        
        # Business growth tasks
        if any(keyword in task_type.lower() for keyword in 
               ['revenue', 'conversion', 'growth', 'marketing', 'acquisition']):
            return TaskPriority.BUSINESS_GROWTH
        
        # Background optimization
        if any(keyword in task_type.lower() for keyword in 
               ['optimization', 'performance', 'infrastructure', 'deployment']):
            return TaskPriority.OPTIMIZATION
        
        # Analytics and reporting
        if any(keyword in task_type.lower() for keyword in 
               ['analytics', 'metrics', 'reporting', 'analysis']):
            return TaskPriority.ANALYTICS
        
        # Default to optimization
        return TaskPriority.OPTIMIZATION
    
    def calculate_value_score(self, user_tier: UserTier, task_priority: TaskPriority) -> float:
        """Calculate value score for this allocation"""
        base_score = self.value_matrix.get((user_tier, task_priority), 1.0)
        
        # Boost scores for combinations that create spiritual value
        if (user_tier in [UserTier.SPIRITUAL_SEEKER, UserTier.NEW_USER] and 
            task_priority == TaskPriority.SPIRITUAL_CRITICAL):
            base_score *= 1.2
        
        # Boost premium user experience
        if (user_tier == UserTier.PREMIUM_USER and 
            task_priority == TaskPriority.USER_EXPERIENCE):
            base_score *= 1.1
        
        return base_score
    
    def estimate_cost(self, model: str, estimated_tokens: int) -> float:
        """Estimate cost for token usage"""
        if model not in self.model_costs:
            return 0.0
        
        # Assume 1:3 input to output ratio
        input_tokens = estimated_tokens * 0.25
        output_tokens = estimated_tokens * 0.75
        
        costs = self.model_costs[model]
        total_cost = (input_tokens/1000 * costs['input'] + 
                     output_tokens/1000 * costs['output'])
        
        return total_cost
    
    def allocate_tokens(self, 
                       task_type: str, 
                       user_data: Dict[str, Any], 
                       context: Dict[str, Any]) -> TokenAllocation:
        """Main allocation logic - determines optimal model and token allocation"""
        
        user_tier = self.classify_user(user_data)
        task_priority = self.classify_task_priority(task_type, context)
        value_score = self.calculate_value_score(user_tier, task_priority)
        
        estimated_tokens = context.get('estimated_tokens', 1000)
        requires_reasoning = context.get('requires_reasoning', False)
        
        # Decision logic based on value score and token availability
        
        # Highest value: Use GPT-5-thinking for complex reasoning
        if (requires_reasoning and 
            value_score >= 8.0 and 
            self.promotional_tokens['premium_remaining'] > estimated_tokens * 1.5):
            
            model = 'gpt-5-thinking'
            max_tokens = min(3000, estimated_tokens * 2)  # Allow more tokens for reasoning
            reason = f"High-value reasoning task for {user_tier.value}"
            
        # High value: Use GPT-5-chat-latest
        elif (value_score >= 7.0 and 
              self.promotional_tokens['premium_remaining'] > estimated_tokens):
            
            model = 'gpt-5-chat-latest'
            max_tokens = min(2000, estimated_tokens)
            reason = f"Premium experience for {user_tier.value}"
            
        # Medium-high value: Use GPT-5-mini from budget allocation
        elif (value_score >= 5.0 and 
              self.promotional_tokens['budget_remaining'] > estimated_tokens):
            
            model = 'gpt-5-mini'
            max_tokens = min(1500, estimated_tokens)
            reason = f"Cost-effective GPT-5 for {task_priority.value}"
            
        # Medium value: Use GPT-4o from budget allocation
        elif (value_score >= 3.0 and 
              self.promotional_tokens['budget_remaining'] > estimated_tokens):
            
            model = 'gpt-4o'
            max_tokens = min(1000, estimated_tokens)
            reason = f"Reliable model for {task_priority.value}"
            
        # Low value: Minimal allocation
        else:
            model = 'gpt-4o'
            max_tokens = min(500, estimated_tokens // 2)
            reason = f"Conservative allocation for {task_priority.value}"
        
        estimated_cost = self.estimate_cost(model, max_tokens)
        
        return TokenAllocation(
            model=model,
            max_tokens=max_tokens,
            reason=reason,
            user_tier=user_tier,
            task_priority=task_priority,
            estimated_cost=estimated_cost,
            value_score=value_score
        )
    
    def update_usage(self, allocation: TokenAllocation, actual_tokens: int):
        """Update token usage tracking"""
        if allocation.model in ['gpt-5-chat-latest', 'gpt-5-thinking']:
            self.promotional_tokens['premium_used'] += actual_tokens
            self.promotional_tokens['premium_remaining'] -= actual_tokens
        else:
            self.promotional_tokens['budget_used'] += actual_tokens
            self.promotional_tokens['budget_remaining'] -= actual_tokens
        
        logger.info(f"Token usage updated: {actual_tokens} tokens used for {allocation.model}")
        logger.info(f"Remaining: Premium={self.promotional_tokens['premium_remaining']}, "
                   f"Budget={self.promotional_tokens['budget_remaining']}")
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """Get current allocation status and recommendations"""
        premium_utilization = (self.promotional_tokens['premium_used'] / 
                             (self.promotional_tokens['premium_used'] + 
                              self.promotional_tokens['premium_remaining']))
        
        budget_utilization = (self.promotional_tokens['budget_used'] / 
                            (self.promotional_tokens['budget_used'] + 
                             self.promotional_tokens['budget_remaining']))
        
        return {
            'token_status': self.promotional_tokens.copy(),
            'utilization': {
                'premium': premium_utilization,
                'budget': budget_utilization
            },
            'recommendations': self._generate_recommendations(premium_utilization, budget_utilization)
        }
    
    def _generate_recommendations(self, premium_util: float, budget_util: float) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        if premium_util > 0.8:
            recommendations.append("Premium tokens running low - prioritize highest-value users")
        
        if budget_util > 0.7:
            recommendations.append("Consider more conservative token allocation")
        
        if premium_util < 0.3 and budget_util < 0.5:
            recommendations.append("Opportunity to increase user value with available tokens")
        
        return recommendations

# Example usage and testing
async def test_smart_allocation():
    """Test the smart token allocation system"""
    allocator = SmartTokenAllocator()
    
    # Test cases representing different user scenarios
    test_cases = [
        {
            'name': 'High-value spiritual seeker asking ACIM question',
            'task_type': 'acim_guidance_response',
            'user_data': {
                'engagement_score': 0.9,
                'spiritual_topic_engagement': 0.8,
                'total_sessions': 25,
                'is_premium': False,
                'days_since_signup': 30
            },
            'context': {
                'estimated_tokens': 800,
                'requires_reasoning': True
            }
        },
        {
            'name': 'Premium user personal guidance',
            'task_type': 'user_chat_response',
            'user_data': {
                'engagement_score': 0.7,
                'is_premium': True,
                'total_sessions': 15,
                'days_since_signup': 60
            },
            'context': {
                'estimated_tokens': 1200,
                'requires_reasoning': False
            }
        },
        {
            'name': 'Background optimization task',
            'task_type': 'performance_optimization',
            'user_data': {},
            'context': {
                'estimated_tokens': 500,
                'requires_reasoning': False
            }
        }
    ]
    
    print("🧠 SMART TOKEN ALLOCATION TEST")
    print("=" * 50)
    
    for test_case in test_cases:
        allocation = allocator.allocate_tokens(
            test_case['task_type'],
            test_case['user_data'],
            test_case['context']
        )
        
        print(f"\n📊 {test_case['name']}")
        print(f"   Model: {allocation.model}")
        print(f"   Max Tokens: {allocation.max_tokens}")
        print(f"   Value Score: {allocation.value_score:.1f}")
        print(f"   User Tier: {allocation.user_tier.value}")
        print(f"   Task Priority: {allocation.task_priority.value}")
        print(f"   Reason: {allocation.reason}")
        print(f"   Est. Cost: €{allocation.estimated_cost:.4f}")
        
        # Simulate token usage
        allocator.update_usage(allocation, allocation.max_tokens)
    
    # Show final summary
    summary = allocator.get_allocation_summary()
    print(f"\n📈 ALLOCATION SUMMARY")
    print(f"   Premium Used: {summary['token_status']['premium_used']:,}")
    print(f"   Budget Used: {summary['token_status']['budget_used']:,}")
    print(f"   Premium Utilization: {summary['utilization']['premium']:.1%}")
    print(f"   Budget Utilization: {summary['utilization']['budget']:.1%}")
    
    if summary['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in summary['recommendations']:
            print(f"   • {rec}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_smart_allocation())
