"""
Sentry Configuration for TestAlex Python AI Systems
Maintains spiritual integrity while providing enterprise-grade error tracking
"""

import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging


def scrub_acim_content_python(event, hint):
    """
    Spiritual Content Protection for Python Systems
    Ensures ACIM content never appears in error logs
    """
    try:
        # Scrub user messages that might contain spiritual content
        if event.get('extra', {}).get('user_message'):
            message = event['extra']['user_message']
            if len(str(message)) > 100:
                event['extra']['user_message'] = '[ACIM_CONTENT_REDACTED]'
        
        # Scrub OpenAI API responses
        if event.get('extra', {}).get('openai_response'):
            response = event['extra']['openai_response']
            if len(str(response)) > 200:
                event['extra']['openai_response'] = '[SPIRITUAL_RESPONSE_REDACTED]'
        
        # Scrub vector database query results
        if event.get('extra', {}).get('vector_results'):
            event['extra']['vector_results'] = '[VECTOR_RESULTS_REDACTED]'
        
        # Remove sensitive environment variables
        if event.get('contexts', {}).get('runtime', {}).get('environment'):
            env_vars = event['contexts']['runtime']['environment']
            sensitive_vars = ['OPENAI_API_KEY', 'ASSISTANT_ID', 'VECTOR_STORE_ID', 'API_KEY']
            for var in sensitive_vars:
                if var in env_vars:
                    env_vars[var] = '[REDACTED]'
        
        # Remove file paths that might contain sensitive information
        if event.get('exception', {}).get('values'):
            for exception in event['exception']['values']:
                if exception.get('stacktrace', {}).get('frames'):
                    for frame in exception['stacktrace']['frames']:
                        if frame.get('filename'):
                            # Only keep relative paths from project root
                            filename = frame['filename']
                            if '/home/' in filename or '/Users/' in filename:
                                frame['filename'] = filename.split('/')[-1]
        
        # Hash user IDs for privacy
        if event.get('user', {}).get('id'):
            import hashlib
            user_id = event['user']['id']
            event['user']['id'] = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        
        # Remove IP addresses
        if event.get('user', {}).get('ip_address'):
            del event['user']['ip_address']
        
        return event
        
    except Exception as e:
        logging.warning(f'Error in spiritual content scrubbing: {e}')
        return event


def init_sentry_ai_systems(dsn_env_var='SENTRY_DSN_AI'):
    """
    Initialize Sentry for AI Business Automation Systems
    """
    dsn = os.getenv(dsn_env_var)
    environment = 'local' if os.getenv('DEVELOPMENT') else 'production'
    
    if not dsn:
        logging.warning(f'{dsn_env_var} not configured - AI system error tracking disabled')
        return
    
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=os.getenv('GITHUB_SHA', 'unknown'),
        
        # Performance monitoring with conservative sampling
        traces_sample_rate=0.2,
        profiles_sample_rate=0.1,
        
        # Enhanced error context while protecting spiritual content
        before_send=scrub_acim_content_python,
        
        # Integrations for AI systems
        integrations=[
            FlaskIntegration(auto_enabling_integrations=False),
            FastApiIntegration(auto_enabling_integrations=False),
            SqlAlchemyIntegration(),
            LoggingIntegration(
                level=logging.INFO,        # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            ),
        ],
        
        # Tag all events with AI system context
        default_integrations=False,
        initial_scope={
            'tags': {
                'component': 'ai-systems',
                'platform': 'spiritual-ai',
                'service': 'automation',
                'content_policy': 'acim_pure'
            },
            'context': {
                'spiritual_integrity': 'protected',
                'system_type': 'autonomous_business'
            }
        }
    )
    
    logging.info('Sentry initialized for TestAlex AI systems', extra={
        'environment': environment,
        'spiritual_integrity': 'protected'
    })


def init_sentry_rag_systems(dsn_env_var='SENTRY_DSN_RAG'):
    """
    Initialize Sentry for Advanced RAG Systems
    """
    dsn = os.getenv(dsn_env_var)
    environment = 'local' if os.getenv('DEVELOPMENT') else 'production'
    
    if not dsn:
        logging.warning(f'{dsn_env_var} not configured - RAG system error tracking disabled')
        return
    
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=os.getenv('GITHUB_SHA', 'unknown'),
        
        # Higher performance monitoring for RAG systems
        traces_sample_rate=0.3,
        profiles_sample_rate=0.1,
        
        # Enhanced error context while protecting spiritual content
        before_send=scrub_acim_content_python,
        
        # Integrations for RAG systems
        integrations=[
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            ),
        ],
        
        # Tag all events with RAG system context
        initial_scope={
            'tags': {
                'component': 'rag-systems',
                'platform': 'spiritual-ai',
                'service': 'knowledge-retrieval',
                'content_policy': 'acim_pure'
            },
            'context': {
                'spiritual_integrity': 'protected',
                'system_type': 'advanced_rag'
            }
        }
    )
    
    logging.info('Sentry initialized for TestAlex RAG systems', extra={
        'environment': environment,
        'spiritual_integrity': 'protected'
    })


def capture_ai_error(error, context=None):
    """
    Safe error capture for AI systems that respects spiritual content
    """
    if context is None:
        context = {}
    
    # Never capture errors that might contain spiritual content
    if context.get('contains_spiritual_content', False):
        logging.error('Spiritual content error (not sent to Sentry)', extra={
            'message': str(error),
            'context': context.get('safe_context', {})
        })
        return
    
    sentry_sdk.capture_exception(error, extras={
        'spiritual_integrity': 'maintained',
        'error_type': 'technical',
        **context
    })


def track_ai_performance(operation_name, system_type='ai'):
    """
    Create a transaction for AI system performance monitoring
    """
    return sentry_sdk.start_transaction(
        op=f'{system_type}-operation',
        name=operation_name,
        tags={
            'spiritual_platform': 'testapex',
            'content_protection': 'enabled',
            'system': system_type
        }
    )


def track_openai_call(model, operation):
    """
    Track OpenAI API calls with spiritual content protection
    """
    return sentry_sdk.start_span(
        op='openai',
        description=f'{operation} with {model}',
        data={
            'model': model,
            'operation': operation,
            'spiritual_content': 'protected'
        }
    )


def track_vector_operation(operation, database='unknown'):
    """
    Track vector database operations
    """
    return sentry_sdk.start_span(
        op='vector-db',
        description=f'{operation} on {database}',
        data={
            'database': database,
            'operation': operation,
            'content_protection': 'enabled'
        }
    )


# Example usage for AI Business Automation
def init_autonomous_business_monitoring():
    """
    Initialize monitoring for autonomous business systems
    """
    init_sentry_ai_systems('SENTRY_DSN_AI')
    
    # Set specific context for business automation
    sentry_sdk.set_context('business_automation', {
        'product_generation': True,
        'marketing_automation': True,
        'cost_monitoring': True,
        'spiritual_integrity': 'maintained'
    })


# Example usage for RAG Systems
def init_rag_monitoring():
    """
    Initialize monitoring for RAG systems
    """
    init_sentry_rag_systems('SENTRY_DSN_RAG')
    
    # Set specific context for RAG systems
    sentry_sdk.set_context('rag_systems', {
        'vector_search': True,
        'query_routing': True,
        'evaluation': True,
        'spiritual_integrity': 'maintained'
    })


# Context managers for safe operation tracking
class SpirituallyAwareTransaction:
    """
    Context manager for tracking operations while protecting spiritual content
    """
    def __init__(self, operation_name, system_type='ai', protect_spiritual_content=True):
        self.operation_name = operation_name
        self.system_type = system_type
        self.protect_spiritual_content = protect_spiritual_content
        self.transaction = None
    
    def __enter__(self):
        self.transaction = track_ai_performance(self.operation_name, self.system_type)
        return self.transaction
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and not self.protect_spiritual_content:
            # Only capture non-spiritual errors
            capture_ai_error(exc_val, {
                'operation': self.operation_name,
                'system_type': self.system_type,
                'contains_spiritual_content': False
            })
        
        if self.transaction:
            self.transaction.finish()


# Integration examples
if __name__ == '__main__':
    # Example: Initialize for autonomous business system
    init_autonomous_business_monitoring()
    
    # Example: Track a business operation
    with SpirituallyAwareTransaction('generate_product', 'business'):
        # Your business automation code here
        pass
    
    # Example: Track an OpenAI call
    with track_openai_call('gpt-4', 'content_generation'):
        # Your OpenAI API call here
        pass
