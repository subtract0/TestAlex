# ACIMguide — MVP Technical Specs

## 1) Product scope (MVP)
- **Goal:** A one-screen **Android** app (iOS later) that chats with a predefined assistant called **CourseGPT** to help users study and practice *A Course in Miracles (CE)*, with exact quotes + citations when used.
- **Language:** English-only for MVP.
- **Non-goals (v1):** Voice, file/image uploads from user, multi-thread UI, paywall, advanced settings.

## 2) Architecture
- **Client:** React Native (Expo). One chat screen + minimal Settings.
- **Backend:** **Firebase**
  - **Auth:** Email + Google (Apple added when iOS ships).
  - **Firestore:** users, threads, messages, usage, settings.
  - **Cloud Functions:** a single HTTPS/Callable façade `coursegpt.chat` (and a `coursegpt.clear` helper) that owns all OpenAI calls.
  - **App Check, Analytics, Crashlytics** enabled.
- **Model API:** OpenAI **Assistants API** with **File Search** attached to a **Vector Store** containing the ACIM CE PDF and Wapnick Q&A. Default model **gpt-5-mini**. (Backend only; the app never exposes keys.)

### Why Assistants API for MVP
- Built‑in file indexing + retrieval.
- Threads/Messages/Runs pattern is simple to reason about.
- Easy to migrate later (keep a thin backend wrapper).

## 3) Assistant configuration (server-side, not user-editable)
- **Name/ID:** `CourseGPT`.
- **Model:** `gpt-5-mini` (toggle to `gpt-5` via Remote Config later).
- **Tools:** `file_search` with a Vector Store linked to uploaded PDFs.
- **Instructions (essentials):**
  - Ground answers in ACIM CE + Wapnick; **verbatim quotes must be exact** and include a **clear citation** (lesson/section and, if available, page).
  - Maintain a spiritual/forgiveness focus; deflect worldly/technical/medical fixes with one line and invite inner work.
  - English responses only for MVP.
- **Threads:** One server-owned thread per user (created lazily).

## 4) Data model (Cloud Firestore)
All documents are namespaced by `userId` and guarded by Security Rules.

- **users/{userId}**
  - `email`, `createdAt`, `plan` (`free`), `locale` (`en`), `tone` (`direct` | `gentle`), `dailyCapOutTokens` (default `2000`).
- **threads/{threadId}**
  - `userId`, `assistantThreadId`, `title`, `createdAt`, `lastMessageAt`, `msgCount`.
- **threads/{threadId}/messages/{messageId}**
  - `role` (`user` | `assistant`), `text`, `citations[]` (array of `{fileId, fileName, location, lesson}`), `tokenIn`, `tokenOut`, `createdAt`.
- **users/{userId}/usage/{yyyymmdd}**
  - `inTokens`, `outTokens`, `requests`, `limitHit` (bool).
- **users/{userId}/settings/default**
  - `showCitations` (bool), `model` (`gpt-5-mini` | `gpt-5`).

## 5) Security & privacy
- **Rules:**
  - Users can read/write only their own docs.
  - Only Cloud Functions can create `assistant` messages (enforced with custom claims / Callable context).
- **Secrets:** OpenAI key, Assistant ID, Vector Store ID stored in Functions env config.
- **App Check:** Required for all callable endpoints.
- **Moderation:** Lightweight check server-side; block/trim if needed.

## 6) Quoting & citation enforcement
- The Function inspects assistant output:
  1. If it contains quote markers or lesson references **without** `file_citation` annotations from File Search, the backend auto-reruns with an internal nudge: “Return exact quotes with citations.”
  2. If still missing, the Function returns a friendly error instructing the user to rephrase or proceed without quotations.
- The client renders citations as pills, e.g. `Workbook — Lesson 102` (tap → bottom sheet shows file + location snippet).

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
