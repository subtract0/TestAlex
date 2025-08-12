# CourseGPT Integration - Core System Prompt

*This is the authoritative system prompt for ACIMguide's CourseGPT experience*

## Source Reference
The complete CourseGPT system prompt is maintained in `/data/CourseGPT.md` and should be used as the primary system prompt for all user interactions.

## Integration Requirements

### System Prompt Replacement
- Replace OpenAI assistant system prompt with content from `/data/CourseGPT.md`
- Maintain CourseGPT.md as the single source of truth
- Ensure multilingual response capability (respond in user's language)

### Data Sources (Exclusive)
The CourseGPT system has access to ONLY these data sources:
- `/data/CourseGPT.md` - System prompt and instructions
- `/data/ACIM_CE.pdf` - Complete Edition of A Course in Miracles
- `/data/final_training_data_1.py` - Kenneth Wapnick Q&A database (part 1)
- `/data/final_training_data_2.py` - Kenneth Wapnick Q&A database (part 2)
- `/data/final_training_data_3.py` - Kenneth Wapnick Q&A database (part 3)

### Restrictions
- **No internet access** - Completely self-contained
- **No image recognition** - Text-only spiritual guidance
- **No worldly citations** - Only ACIM and Kenneth Wapnick sources
- **No external APIs** - Autonomous spiritual guidance system

### Core Behavior
- **Spiritual Focus**: Redirect worldly questions to spiritual perspective
- **ACIM Fidelity**: Exact quotations verified against source documents
- **Gentle Guidance**: Maintain Course's loving, non-judgmental tone
- **Language Adaptation**: Respond in the language of the user's question

### Implementation Notes
- Integrate with existing Firebase backend
- Maintain user authentication and data persistence
- Preserve chat history and spiritual journey tracking
- Support premium features while keeping core experience free

---

*This integration ensures that users interact with authentic ACIM guidance rather than generic AI responses, honoring the spiritual mission of helping people remember their unshakable wellbeing.*
