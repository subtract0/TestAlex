# Custom Knowledge Chatbot with OpenAI Assistants API

This project provides a Python-based chatbot that uses the OpenAI Assistants API to answer questions based on a custom knowledge base. It includes scripts for one-time setup, updating the assistant, and running an interactive chat session.

---

## Features

- **Knowledge-Based Chat**: The assistant is linked to a vector store containing custom data files, allowing it to answer specific questions based on that knowledge.
- **Persistent Assistant**: The assistant is created once, and its ID is saved, avoiding repeated setup costs and effort.
- **Easy Configuration**: Key settings like the OpenAI API Key and Assistant ID are managed through a `.env` file.
- **Modular Scripts**:
  - `setup_assistant.py`: For initial, one-time creation of the vector store and assistant.
  - `update_assistant.py`: To modify the settings of the existing assistant (e.g., changing the model).
  - `main.py`: To run the interactive chat application.

---

## Setup and Usage

### 1. Prerequisites

- Python 3.8+
- An OpenAI API key.

### 2. Installation

Clone the repository and install the required dependencies into a virtual environment.

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

1.  **Create `.env` file**: Create a file named `.env` in the root of the project.
2.  **Add API Key**: Add your OpenAI API key to the `.env` file:
    ```
    OPENAI_API_KEY="your_openai_api_key_here"
    ```
3.  **Add Knowledge Files**: Place your custom knowledge files (e.g., PDFs, text files) into the `data/` directory.

### 4. First-Time Setup

Run the setup script to upload your files, create a vector store, and create the assistant. This only needs to be done once.

```bash
python setup_assistant.py
```

This will create the assistant and automatically add the `ASSISTANT_ID` to your `.env` file.

### 5. Running the Chatbot

Start the interactive chat application.

```bash
python main.py
```

You can now ask questions related to the knowledge files you provided.

### 6. Updating the Assistant

If you need to change the assistant's model or other settings, modify the `update_assistant.py` script and run it.

```bash
python update_assistant.py
```

This will update the existing assistant without creating a new one.
firestore.indexes.json # Database indexes ✅ CREATED
```

## Local Development Status
- ✅ **Firebase CLI**: Installed and authenticated
- ✅ **GitHub CLI**: Installed and authenticated (subtract0)
- ✅ **Firebase Project**: Connected to "acim-guide-test"
- ✅ **Cloud Functions**: Initialized with JavaScript + ESLint
- ✅ **Firestore**: Configured with rules and indexes
- ⏳ **OpenAI Setup**: Ready for step 2

## Original Repo layout (suggested)

## Analytics events (names)
`app_open`, `sign_in_success`, `message_send`, `message_stream_start`, `message_stream_end`, `quick_action_used`, `limit_reached_daily_tokens`, `settings_changed`.

---

That’s it. Ship the smallest valuable thing, then iterate.
