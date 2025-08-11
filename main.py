import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# --- Configuration ---
# 1. Get OpenAI API Key and Assistant ID
api_key = os.environ.get("OPENAI_API_KEY")
assistant_id = os.environ.get("ASSISTANT_ID")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file.")
if not assistant_id:
    raise ValueError("ASSISTANT_ID not found in .env file. Please run 'setup_assistant.py' first.")

client = OpenAI(api_key=api_key)

# --- Main Chat Logic ---
def main():
    print("Starting a new conversation with the ACIM Assistant.")

    # 1. Create a new thread
    try:
        thread = client.beta.threads.create()
        print(f"New conversation thread created with ID: {thread.id}")
    except Exception as e:
        print(f"Failed to create a new thread. Error: {e}")
        return

    print("\nAssistant is ready. Type 'exit' to end the conversation.")

    # 2. Start chat loop
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                print("Ending conversation. Goodbye!")
                break

            # Add user message to the thread
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input
            )

            # Run the assistant
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id,
            )

            # Wait for the run to complete
            print("Assistant is thinking...")
            while run.status in ['queued', 'in_progress']:
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

            # Display the assistant's response
            if run.status == 'completed':
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                # The latest message is usually the first in the list
                if messages.data and messages.data[0].role == 'assistant':
                    response = messages.data[0].content[0].text.value
                    print(f"Assistant: {response}")
                else:
                    print("Assistant did not provide a response.")
            else:
                print(f"Run failed with status: {run.status}. Details: {run.last_error}")

        except KeyboardInterrupt:
            print("\nInterrupted by user. Ending conversation.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

def run_single_query(thread_id, assistant_id, question):
    """Sends a single question to the assistant and prints the response."""
    # Create a message
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question,
    )

    # Create a run
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )

    # Wait for the run to complete
    # print("Assistant is thinking...")
    while run.status in ['queued', 'in_progress', 'cancelling']:
        import time
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        # Print the assistant's response
        for msg in reversed(messages.data):
            if msg.role == 'assistant':
                print(f"{msg.content[0].text.value}")
                break  # Only print the latest assistant message
    else:
        print(f"Run failed with status: {run.status}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Non-interactive mode: run a single query from command-line argument
        question = " ".join(sys.argv[1:])
        assistant_id = os.getenv("ASSISTANT_ID")
        if not assistant_id:
            print("ASSISTANT_ID not found in .env file. Please run setup_assistant.py first.")
        else:
            thread = client.beta.threads.create()
            run_single_query(thread.id, assistant_id, question)
    else:
        # Interactive mode
        main()
