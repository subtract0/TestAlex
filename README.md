# ACIMguide - A Custom AI Companion

This project aims to build a focused, gentle, and precise AI companion for practicing *A Course in Miracles (CE)*. It starts as a local Python-based chatbot and is designed to evolve into a full-fledged Android application backed by Firebase and the OpenAI Assistants API.

---

## Project Vision

The goal is to provide users with a reliable tool for guided chat, offering exact quotes with citations from the source material, and helpful features to support their spiritual practice.

## Current Status

The project is currently in its initial phase: a functional, local Python application that can hold a conversation based on a custom knowledge base.

- **Core Logic**: Python scripts for setup, updates, and interactive chat.
- **Knowledge Base**: Uses the OpenAI Assistants API with a Vector Store for file-based knowledge.
- **Configuration**: Managed via a local `.env` file.

## Development Roadmap

The full, detailed development plan is documented in `specs.md`. This roadmap outlines the three major phases to take this project from its current state to a production-ready application:

1.  **Phase 1: Harden and Refactor the Core Python Logic**
2.  **Phase 2: Transition to a Cloud-Based Backend (Firebase)**
3.  **Phase 3: Develop the Mobile Application (Android)**

Please refer to **[`specs.md`](./specs.md)** for a complete breakdown of the features, architecture, and step-by-step implementation plan.

---

### Local Setup (Previous Version)

For details on how to set up and run the previous local Python version of the application, please see the commit history prior to this update. The project is being rebooted to follow the new roadmap.
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
