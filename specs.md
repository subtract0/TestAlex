# ACIMguide — MVP Technical Specs

## 1) Product scope (MVP)
- **Goal:** A one-screen **Android** app (iOS later) that chats with a predefined assistant called **CourseGPT** to help users study and practice *A Course in Miracles (CE)*, with exact quotes + citations when used.
- **Language:** English-only for MVP.
- **Non-goals (v1):** Voice, file/image uploads from user, multi-thread UI, paywall, advanced settings.

## 2) Architecture

## Phase 1: Harden and Refactor the Core Python Logic

The current scripts are functional but not yet production-grade. This phase makes them robust, easier to manage, and ready for a backend integration.

### Step 1.1: Consolidate Assistant Management

-   **Goal**: Replace `setup_assistant.py` and `update_assistant.py` with a single, powerful management script.
-   **Action**:
    1.  Create a new file: `manage_assistant.py`.
    2.  Implement command-line argument parsing (using Python's `argparse`) to support distinct actions:
        -   `python manage_assistant.py create`: Performs the full setup, creating a new vector store and assistant. It will first check for an existing `ASSISTANT_ID` in `.env` and require a `--force` flag to overwrite, preventing accidental deletion.
        -   `python manage_assistant.py update --model gpt-4o`: Updates the existing assistant's properties.
        -   `python manage_assistant.py sync-files`: **(New Feature)** This command will intelligently synchronize the files in your local `data/` directory with the OpenAI Vector Store, adding new files and removing obsolete ones without recreating the entire store.
    3.  Once the new script is verified, delete `setup_assistant.py` and `update_assistant.py`.
    4.  Update the `README.md` to document the new `manage_assistant.py` script and its commands.

### Step 1.2: Implement Structured Logging

-   **Goal**: Replace all `print()` statements with a proper logging framework for better debugging and monitoring.
-   **Action**:
    1.  In `main.py` and `manage_assistant.py`, configure Python's built-in `logging` module.
    2.  Set the log level based on an environment variable (`LOG_LEVEL=INFO`) or a command-line flag (`--verbose`).
    3.  Replace `print("Status message...")` with `logging.info("Status message...")`.
    4.  Replace `print("Error...")` with `logging.error("Error...")`.
    5.  Wrap all OpenAI API calls in `try...except` blocks that log specific errors (e.g., `openai.APIError`).

---

## Phase 2: Transition to a Cloud-Based Backend (Firebase)

To make this accessible to a mobile app, we must move the core logic to a secure, scalable cloud backend.

### Step 2.1: Set Up Cloud Functions Environment

-   **Goal**: Prepare the `functions/` directory for development.
-   **Action**:
    1.  In the `functions/` directory, run `npm install openai firebase-admin firebase-functions`.
    2.  Configure Firebase environment variables using the CLI: `firebase functions:config:set openai.key="your_key" assistant.id="your_id"`. This keeps secrets out of the code.

### Step 2.2: Create the Main Chat Endpoint

-   **Goal**: Create a secure HTTPS Callable Function that the mobile app can call to interact with the assistant.
-   **Action**:
    1.  In `functions/index.js`, create a new callable function named `chatWithAssistant`.
    2.  This function will receive the user's message as input.
    3.  Inside the function, it will perform the logic currently in `main.py`:
        -   Create a new OpenAI Thread if one doesn't exist for the user.
        -   Add the user's message to the Thread.
        -   Create and poll a Run.
        -   Return the assistant's final response.
    4.  Deploy the function using `firebase deploy --only functions`.

---

## Phase 3: Develop the Mobile Application (Android)

With the backend in place, we can build the user-facing mobile app.

### Step 3.1: Basic App Shell and Firebase Connection

-   **Goal**: Create a minimal Android app that can connect to your Firebase project.
-   **Action**:
    1.  Create a new Android Studio project with the package name `com.acimguide.mvp`.
    2.  Add the `google-services.json` file (which you would download from the Firebase console) to the app.
    3.  Add Firebase SDK dependencies (`firebase-auth`, `firebase-functions`) to the app's `build.gradle` file.

### Step 3.2: Build the Chat Interface

-   **Goal**: Create the main screen where users interact with the chatbot.
-   **Action**:
    1.  Design a simple UI with a message list, a text input field, and a send button.
    2.  When the user presses "send," the app will call the `chatWithAssistant` Cloud Function from Phase 2.
    3.  The app will display the response from the function in the message list.

## 7) API contract (Cloud Functions)
### `coursegpt.chat` (Callable HTTPS)
**Request** (from client):
```json
{
  "message": "string",
  "tone": "direct|gentle"  // optional; defaults to user setting
}
```
**Behavior:**
1. Validate auth + throttle (10 rpm/user) + daily token cap (outTokens ≤ 2000).
2. Ensure a server-owned **Thread** exists for the user; create if absent.
3. Append user message → create a **Run** on the Assistant (stream internally).
4. As tokens arrive, write progressive chunks to the Firestore `messages` doc (`text` field grows).
5. After completion, attach `citations[]`, `tokenIn`, `tokenOut` and return `{ messageId }`.

**Response** (final):
```json
{
  "messageId": "string",
  "tokenIn": 123,
  "tokenOut": 456,
  "limitRemaining": 1544
}
```

### `coursegpt.clear` (Callable HTTPS)
- Deletes the server-owned Assistant Thread and the Firestore thread for the user, then recreates an empty one.

## 8) Client UX (MVP)
- **Onboarding:** Sign-in → set **Tone** (Direct/Gentle) → one-sentence promise.
- **Chat:** input, send, streaming bubbles, **Retry**/**Edit last**, **Copy**.
- **Quick Actions** (insert prompts):
  - **Clarity Flip** – “Summarize my situation in 3 bullets and offer 2 spiritual options.”
  - **Forgiveness Walkthrough** – “Guide me through 5 steps to release this.”
  - **Calm-in-90s** – “One-minute breath, one reframing thought, one next step.”
- **History:** Single thread; rename; delete.
- **Settings:** `showCitations`, model switch (5‑mini ↔ 5), delete all data, app version.

## 9) Observability
- **Client events:** `app_open`, `sign_in_success`, `message_send`, `message_stream_start`, `message_stream_end`, `quick_action_used`, `limit_reached_daily_tokens`, `settings_changed`.
- **Server logs:** userId, threadId, tokens in/out, latency, result status.

## 10) Environments & config
- **Functions env:** `OPENAI_API_KEY`, `ASSISTANT_ID`, `VECTOR_STORE_ID`, `DAILY_OUT_TOKENS_CAP`, `ALLOWED_ORIGINS`.
- **Remote Config:** `model_default` (`gpt-5-mini`), `enableACIMFlavor` (false).

## 11) Release targets
- **Android first** (staged rollout). iOS later (adds Apple Sign-In + StoreKit).

## 12) Roadmap after MVP
- Multi-thread UI, voice (Realtime), attachments, paywall, migration to Responses API if preferred.
