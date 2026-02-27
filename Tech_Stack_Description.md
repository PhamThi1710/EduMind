# EduMind — Tech Stack & Feature Overview

> **EduMind** is an AI-powered intelligent learning platform built as a graduation project at HCMUT. It focuses on personalized learning paths, adaptive content delivery, and intelligent exercise evaluation.

---

## 📌 Core Features

### 1. Authentication & User Management
- Email/password registration and login with JWT (access + refresh tokens)
- Google OAuth2 login
- Role-based access: **Student** and **Professor**
- Password reset via email
- User profile management

### 2. Course & Content Management
- Professors can create and manage **Courses**, **Lessons**, **Modules**, and **Exercises**
- Support for rich learning materials: PDF, Word (.docx), PowerPoint (.pptx) files
- Document upload and storage via **AWS S3**
- Automatic text extraction from uploaded documents (PDF, Word)
- Exercise types: Quiz (multiple-choice) and written exercises

### 3. Personalized Learning Path (AI-Powered)
- **AI Learning Path Planning** using a LangGraph agentic workflow
- The agent retrieves the learner's proficiency profile and course lessons, then designs a personalized learning path with per-module objectives, descriptions, and estimated time
- Learner proficiency tracked via **Bayesian Knowledge Tracing (BKT)** — mastery of each concept is updated as the student completes exercises
- Knowledge Graph of learning resources built and queried via **Neo4j**

### 4. Intelligent Recommendation
- Recommend lessons and documents based on learner proficiency
- Recommend quizzes tailored to student knowledge gaps
- Cosine similarity (scikit-learn) used for content-based filtering

### 5. AI Tutoring & Conversations
- LLM-powered Q&A conversations per lesson/module (multi-turn)
- AI generates quiz questions from lesson content
- AI generates written exercise content and sample answers
- Powered by **Google Gemini** (primary) and **OpenAI GPT-4o-mini** (fallback/secondary)
- Unified LLM calls via **LiteLLM**

### 6. Progress Tracking
- Students: track completed lessons, quiz scores, and module progress
- Professors: view per-student progress across the course
- Dashboard with overall learning activity and statistics
- Schedule management for learning sessions

### 7. Feedback System
- Students can submit feedback on lessons and courses
- Professors can view feedback aggregated per course

### 8. Notifications & Email
- System sends emails via SMTP (Gmail): account verification, password reset, notifications
- Email templating with Jinja2 HTML templates

### 9. Monitoring & Reliability
- Error tracking with **Sentry**
- Structured logging with **Loguru**
- Retry logic on external service calls with **Tenacity**

---

## 🛠 Tech Stack

### Language & Runtime
| Component | Choice |
|---|---|
| Language | Python 3.11+ |
| Package Manager | Poetry |

### Web Framework
| Component | Choice |
|---|---|
| Framework | **FastAPI** |
| ASGI Server | **Uvicorn** (dev) / **Gunicorn** (prod) |
| Data Validation | **Pydantic v2** + pydantic-settings |

### Databases
| Database | Purpose |
|---|---|
| **PostgreSQL** | Primary relational database (users, courses, lessons, exercises, submissions, progress) |
| **Neo4j** | Graph database for knowledge graph of learning resources and concepts |
| **Redis** | Application-level cache (response caching layer) |

### ORM & Migrations
| Component | Choice |
|---|---|
| ORM | **SQLAlchemy** (async mode) |
| Async Driver | **asyncpg** + **psycopg** |
| Migrations | **Alembic** |

### AI / LLM Stack
| Component | Choice |
|---|---|
| Agentic Workflows | **LangGraph** |
| LLM Orchestration | **LangChain** |
| Unified LLM Client | **LiteLLM** |
| Primary LLM | **Google Gemini** (gemini-2.0-flash) |
| Secondary LLM | **OpenAI GPT-4o-mini** |
| ML Utilities | **scikit-learn**, **numpy** (similarity, vectors) |
| Knowledge Tracing | **pybkt** (Bayesian Knowledge Tracing) |

### Document Processing
| Library | Purpose |
|---|---|
| `pymupdf` | PDF parsing (fast, accurate) |
| `pdfminer-six` | PDF text extraction (fallback) |
| `python-docx` | Word document parsing |
| `python-pptx` | PowerPoint parsing |
| `openpyxl` | Excel file handling |

### Storage & External Services
| Service | Purpose |
|---|---|
| **AWS S3** (boto3) | File storage for uploaded learning materials |
| **SMTP / Gmail** (fastapi-mail) | Transactional emails |
| **Google OAuth2** | Social login |

### Auth & Security
| Library | Purpose |
|---|---|
| `pyjwt` | JWT access + refresh token issuance |
| `passlib` + `bcrypt` | Password hashing |
| `google-auth-oauthlib` | Google OAuth2 flow |

### Observability & Reliability
| Tool | Purpose |
|---|---|
| **Sentry SDK** | Error tracking & alerting |
| **Loguru** | Structured logging |
| **Tenacity** | Retry logic for flaky external calls |
| **httpx** | Async HTTP client |

### Infrastructure & DevOps
| Tool | Purpose |
|---|---|
| **Docker** + **Docker Compose** | Containerized local and production environment |
| **Supervisor** | Process management (web + worker processes) |

---

## 🗂 Project Structure

```
EduMind/
├── core/               # Shared infrastructure (DB session, cache, settings, LLM config)
│   ├── cache/          # Redis cache manager & backend
│   ├── db/             # SQLAlchemy engine & session management
│   ├── llm/            # LLM model config abstraction
│   └── settings.py     # Environment-based configuration (pydantic-settings)
├── machine/            # Main application domain
│   ├── api/v1/         # FastAPI route handlers
│   ├── controllers/    # Business logic layer
│   ├── models/         # SQLAlchemy ORM models
│   ├── repositories/   # Data access layer (DB queries)
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Service layer (LLM, AI workflows, document processing)
│   │   └── workflows/  # LangGraph agentic workflows
├── migrations/         # Alembic migration versions
├── tasks/              # Background task definitions
├── templates/          # Email HTML templates
├── tests/              # Test suite
├── main.py             # Application entry point
├── worker.py           # Dramatiq worker entry point
├── docker-compose.yml  # Service orchestration
└── pyproject.toml      # Dependency manifest
```

---

## 🔌 API Overview

All endpoints are versioned under `/api/v1/`. Key route groups:

| Route Group | Description |
|---|---|
| `/auth` | Register, login, Google OAuth, token refresh |
| `/users` | Profile management, avatar upload |
| `/courses` | CRUD for courses, enrollment |
| `/lessons` | Lesson content, reading materials |
| `/modules` | Module management within lessons |
| `/exercises` | Quiz and written exercises |
| `/recommend` | AI-powered lesson & document recommendations |
| `/progress` | Student progress tracking |
| `/professor` | Professor dashboard & course analytics |
| `/feedback` | Student feedback submission & retrieval |
| `/schedule` | Learning session scheduling |
| `/llm` | Direct LLM interaction endpoints |
| `/ai` | AI tutoring conversations, LP planning |
| `/conversations` | Multi-turn tutor conversation management |

---

## ⚙️ Environment Variables Summary

| Variable | Purpose |
|---|---|
| `SQLALCHEMY_POSTGRES_URI` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection URL |
| `NEO4J_URI / _USERNAME / _PASSWORD` | Neo4j graph database |
| `GEMINI_API_KEY` | Google Gemini LLM |
| `OPENAI_API_KEY` | OpenAI GPT models |
| `AWS3_*` | AWS S3 bucket credentials |
| `MAIL_*` | SMTP email configuration |
| `SECRET_KEY / REFRESH_SECRET_KEY` | JWT signing keys |
| `CLIENT_AUTH` | Google OAuth2 Client ID |
