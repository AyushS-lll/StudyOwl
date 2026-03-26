# 🦉 StudyOwl — Homework Assistant Agent

> Your AI-powered homework companion. Guided by wisdom, never by spoilers.

StudyOwl is an AI agent that helps students work through assignments using Socratic questioning and graduated hints. It never gives direct answers — it guides students to find them on their own, escalating to a teacher only when truly needed.

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Architecture](#architecture)
- [Hint System](#hint-system)
- [Escalation Logic](#escalation-logic)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Guardrails](#guardrails)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Subject detection** — automatically routes questions across Math, Science, English, History, and more
- **3-level hint engine** — starts with a gentle nudge, escalates to near-answers only when needed
- **Error identification** — detects exactly where a student went wrong and tailors the next hint
- **Photo input support** — students can upload a photo of their problem (OCR powered)
- **Progress tracking** — per-student, per-subject performance profiles updated after every session
- **Teacher alerts** — automatic escalation when a student is stuck beyond defined thresholds
- **Encouragement built-in** — every response includes a positive message

---

## How It Works

```
1. Student submits a question or photo
           ↓
2. Input parsed (NLP + OCR if needed)
           ↓
3. Subject classified → routed to domain handler
           ↓
4. Hint Engine generates Level 1 hint
           ↓
5. Student reads hint → submits attempt
           ↓
6. Answer Verifier checks attempt
   ├── Correct → Progress logged → Session ends ✓
   └── Wrong   → Hint level advances → Back to step 4
           ↓ (if Level 3 exhausted)
7. Full answer + explanation revealed
           ↓
8. Stuck check: attempts > threshold?
   ├── No  → Session ends normally
   └── Yes → Teacher alert triggered
```

---

## Architecture

StudyOwl is structured in 4 layers:

### Layer 1 — Input
| Task | Description |
|---|---|
| Receive input | Accepts text questions, typed working, or photo uploads |
| Pre-process | OCR for photos, text normalisation, input logging |

### Layer 2 — Processing
| Task | Description |
|---|---|
| Parse intent | Extracts question type, key concepts, difficulty via NLP |
| Classify subject | Routes to the correct domain handler |
| Generate hint | Hint engine produces the appropriate level hint |

**Domain handlers:**
- **Math** → equation/formula parser, SymPy / Wolfram Alpha for verification
- **Science** → concept graph lookup
- **English** → grammar and essay structure checker
- **History / Other** → knowledge base retrieval

### Layer 3 — Output
| Task | Description |
|---|---|
| Deliver hint | Returns hint, encouragement message, and "try again" prompt |
| Verify attempt | Checks answer; identifies errors for partial attempts |
| Update tracker | Logs session data to per-student performance profile |

### Layer 4 — Escalation
| Task | Description |
|---|---|
| Monitor for stuck state | Watches attempts, inactivity, and explicit distress signals |
| Send teacher alert | Dispatches alert payload with full session context |

---

## Hint System

Hints are delivered in 3 graduated levels. The agent always starts at Level 1 and advances only after a wrong attempt.

| Level | Style | Example |
|---|---|---|
| 1 — Subtle | Socratic question | *"What do you think the first step might be?"* |
| 2 — Moderate | Guided pointer | *"Think about the formula for speed. What values do you have?"* |
| 3 — Explicit | Near-answer | *"Use v = d/t. You have d=100 and t=5. What does that give you?"* |

After Level 3 is exhausted, the full answer and a complete explanation are revealed.

---

## Escalation Logic

A teacher alert is triggered if **any** of the following conditions are met:

- Student fails **3+ times** at the same hint level
- Student is **inactive for more than 10 minutes** mid-session
- Student explicitly signals distress (e.g. *"I don't understand anything"*)

**Alert payload includes:**
- Student name and ID
- Question / topic they are stuck on
- Number of attempts made
- Hints already shown
- Time spent on the problem
- Recommended action (e.g. review topic, book a 1:1 session)

---

## Tech Stack

| Component | Tool |
|---|---|
| NLP / Hint generation | Claude API (Anthropic) |
| OCR (photo input) | Google Vision API / Tesseract |
| Math verification | SymPy / Wolfram Alpha API |
| Subject classifier | Fine-tuned classifier or LLM prompt routing |
| Student database | PostgreSQL / Firebase |
| Progress tracker | REST API + React dashboard |
| Teacher alerts | SendGrid (email) / Twilio (SMS) / Push notifications |

---

## Getting Started

### Prerequisites
- Node.js 18+ or Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)
- PostgreSQL or Firebase project

### Installation

```bash
git clone https://github.com/your-org/studyowl.git
cd studyowl
npm install
```

### Environment Variables

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=your_api_key_here
GOOGLE_VISION_API_KEY=your_key_here
WOLFRAM_API_KEY=your_key_here
DATABASE_URL=your_database_url
SENDGRID_API_KEY=your_key_here
```

### Run the development server

```bash
npm run dev
```

---

## Guardrails

| Rule | Detail |
|---|---|
| No spoilers | Direct answer never shown before Level 3 is exhausted |
| Attempt tracking | Every attempt logged; hint level only advances on wrong answer |
| Encouragement required | Every response must include a positive message |
| Time monitoring | Inactivity beyond 10 min flags as stuck |
| Teacher-in-the-loop | All escalations go to a human; agent never makes final decisions |
| Data privacy | All student data anonymised in logs; GDPR and FERPA compliant |

---

## Roadmap

- [ ] Core hint engine (MVP)
- [ ] Math domain handler with SymPy verification
- [ ] OCR photo input support
- [ ] Teacher alert system
- [ ] Progress tracker dashboard
- [ ] Science and English domain handlers
- [ ] Integration with Personalised Learning Agent
- [ ] Mobile app (React Native)
- [ ] Multi-language support

---

## Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

<p align="center">Built with curiosity. Powered by AI. Guided by wisdom. 🦉</p>
