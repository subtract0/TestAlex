import os
import sys
import time
import logging
from openai import OpenAI
from dotenv import load_dotenv
import openai as openai_module

# Load environment variables from .env
load_dotenv()

# Configure logging
def setup_logging(verbose: bool = False):
    """Configure structured logging for the application."""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    if verbose:
        log_level = 'DEBUG'
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

# Initialize logging
logger = setup_logging()

# --- Configuration ---
# 1. Get OpenAI API Key and Assistant ID
api_key = os.environ.get("OPENAI_API_KEY")
assistant_id = os.environ.get("ASSISTANT_ID")

if not api_key:
    logger.error("OPENAI_API_KEY not found in .env file")
    raise ValueError("OPENAI_API_KEY not found in .env file.")
if not assistant_id:
    logger.error("ASSISTANT_ID not found in .env file. Please run 'python manage_assistant.py create' first")
    raise ValueError("ASSISTANT_ID not found in .env file. Please run 'python manage_assistant.py create' first.")

try:
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    raise

# --- Main Chat Logic ---
def main():
    print("Starting a new conversation with the ACIM Assistant.")
    logger.info("Starting new conversation")

    # 1. Create a new thread
    try:
        thread = client.beta.threads.create()
        logger.info(f"New conversation thread created with ID: {thread.id}")
        print(f"New conversation thread created with ID: {thread.id}")
    except openai_module.APIError as e:
        logger.error(f"OpenAI API error creating thread: {e}")
        print(f"Failed to create a new thread. OpenAI API error: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error creating thread: {e}")
        print(f"Failed to create a new thread. Error: {e}")
        return

    print("\nAssistant is ready. Type 'exit' to end the conversation.")

    # 2. Start chat loop
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Ending conversation. Goodbye!")
                logger.info("User ended conversation")
                break

            logger.debug(f"User input received: {len(user_input)} characters")
            
            # Add user message to the thread
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input
            )
            logger.debug("User message added to thread")

            # Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id,
            )
            logger.info(f"Assistant run started with ID: {run.id}")

            # Wait for the run to complete
            print("Assistant is thinking...")
            while run.status in ['queued', 'in_progress']:
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                logger.debug(f"Run status: {run.status}")

            # Display the assistant's response
            if run.status == 'completed':
                logger.info("Assistant run completed successfully")
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                # The latest message is usually the first in the list
                if messages.data and messages.data[0].role == 'assistant':
                    response = messages.data[0].content[0].text.value
                    logger.debug(f"Assistant response received: {len(response)} characters")
                    print(f"Assistant: {response}")
                else:
                    logger.warning("Assistant completed but provided no response")
                    print("Assistant did not provide a response.")
            else:
                logger.error(f"Run failed with status: {run.status}. Details: {run.last_error}")
                print(f"Run failed with status: {run.status}. Details: {run.last_error}")

        except KeyboardInterrupt:
            print("\nInterrupted by user. Ending conversation.")
            logger.info("Conversation interrupted by user")
            break
        except openai_module.APIError as e:
            logger.error(f"OpenAI API error during conversation: {e}")
            print(f"OpenAI API error: {e}")
            break
        except Exception as e:
            logger.error(f"Unexpected error during conversation: {e}")
            print(f"An error occurred: {e}")
            break

def run_single_query(thread_id, assistant_id, question):
    """Sends a single question to the assistant and prints the response."""
    logger.info(f"Running single query with {len(question)} characters")
    
    try:
        # Create a message
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=question,
        )
        logger.debug("User message added to thread")

        # Create a run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )
        logger.info(f"Assistant run started with ID: {run.id}")

        # Wait for the run to complete
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            logger.debug(f"Run status: {run.status}")

        if run.status == 'completed':
            logger.info("Single query completed successfully")
            messages = client.beta.threads.messages.list(
                thread_id=thread_id
            )
            # Print the assistant's response
            for msg in reversed(messages.data):
                if msg.role == 'assistant':
                    response = msg.content[0].text.value
                    logger.debug(f"Assistant response received: {len(response)} characters")
                    print(f"{response}")
                    break  # Only print the latest assistant message
        else:
            logger.error(f"Single query failed with status: {run.status}")
            print(f"Run failed with status: {run.status}")
    
    except openai_module.APIError as e:
        logger.error(f"OpenAI API error in single query: {e}")
        print(f"OpenAI API error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in single query: {e}")
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Non-interactive mode: run a single query from command-line argument
        question = " ".join(sys.argv[1:])
        assistant_id = os.getenv("ASSISTANT_ID")
        if not assistant_id:
            logger.error("ASSISTANT_ID not found for single query mode")
            print("ASSISTANT_ID not found in .env file. Please run 'python manage_assistant.py create' first.")
        else:
            try:
                thread = client.beta.threads.create()
                logger.info(f"Created thread for single query: {thread.id}")
                run_single_query(thread.id, assistant_id, question)
            except Exception as e:
                logger.error(f"Failed to create thread for single query: {e}")
                print(f"Failed to create thread: {e}")
    else:
        # Interactive mode
        main()
