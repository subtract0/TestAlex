import os
import openai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get API key and Assistant ID from environment
api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")

if not api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

if not assistant_id:
    raise ValueError("Assistant ID not found. Please run setup_assistant.py first.")

# Initialize the OpenAI client
client = openai.OpenAI(api_key=api_key)

# Define the new model
new_model = "gpt-4.1"

def update_assistant_model():
    """Updates the model of the existing assistant."""
    print(f"Updating assistant {assistant_id} to use model: {new_model}...")
    try:
        # Update the assistant
        my_assistant = client.beta.assistants.update(
            assistant_id,
            model=new_model,
        )
        print(f"Successfully updated assistant. Current model: {my_assistant.model}")
    except Exception as e:
        print(f"An error occurred during the update: {e}")

if __name__ == "__main__":
    update_assistant_model()
