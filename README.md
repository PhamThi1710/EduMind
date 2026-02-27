# EduMind API Backend

API for the EduMind project — an intelligent learning platform focusing on personalized learning paths, AI-powered content generation, and exercise evaluation.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Supabase Setup](#2-supabase-setup)
  - [3. Environment Setup](#3-environment-setup)
  - [4. Running with Docker Compose](#4-running-with-docker-compose)
- [Database Migrations](#database-migrations)
- [Authentication](#authentication)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [License](#license)

## Overview

EduMind is an intelligent learning management system that provides:

- **Personalized Learning Paths** — AI-generated study plans tailored to individual student goals
- **Course & Lesson Management** — Full CRUD for courses, lessons, and documents
- **Exercise Evaluation** — Code exercise grading with AI-powered feedback
- **Progress Tracking** — Detailed analytics for students and professors
- **AI Assistants** — Conversational AI for learning support and quiz generation

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.11+ |
| **Framework** | FastAPI |
| **Database** | PostgreSQL (hosted on [Supabase](https://supabase.com)) |
| **Auth** | Supabase Auth (JWT-based) |
| **Storage** | Supabase Storage + AWS S3 |
| **ORM** | SQLAlchemy 2.x (async) |
| **DB Driver** | asyncpg |
| **Migrations** | Alembic |
| **Caching** | Redis |
| **AI / LLM** | Google Gemini, OpenAI, LangChain, LangGraph |
| **Containerization** | Docker, Docker Compose |
| **Dependency Mgmt** | Poetry |
| **ASGI Server** | Uvicorn |

## Prerequisites

- **Docker & Docker Compose** — [Install Docker](https://docs.docker.com/get-docker/)
- **Git** — For cloning the repository
- **Supabase Account** — [Sign up at supabase.com](https://supabase.com) (free tier works)
- **Poetry** *(optional)* — Only needed for local development without Docker

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/PhamThi1710/EduMind.git
cd EduMind
```

### 2. Supabase Setup

1. Create a new project on the [Supabase Dashboard](https://supabase.com/dashboard)
2. Note your **Project URL** and **API keys** from **Settings → API**
3. Get your **database connection string** from **Connect** (top-right green button):
   - Select **Method: Session pooler** (required for IPv4 networks / Docker)
   - Copy the **URI** — it will look like:
     ```
     postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-X-[REGION].pooler.supabase.com:5432/postgres
     ```

> **Important:** The direct database connection (`db.[ref].supabase.co`) is IPv6-only. Docker containers require IPv4, so you **must** use the Session Pooler connection string.

### 3. Environment Setup

Create a `.env` file in the project root:

```bash
# Core Settings
ENV=development
DEBUG=True
APP_HOST=localhost
APP_PORT=8080
LOG_LEVEL=DEBUG

# Database Settings (Supabase Session Pooler)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_supabase_db_password
POSTGRES_DB=postgres
SQLALCHEMY_POSTGRES_URI=postgresql+asyncpg://postgres.[PROJECT-REF]:[PASSWORD]@aws-X-[REGION].pooler.supabase.com:5432/postgres
SQLALCHEMY_ECHO=False

# Redis Settings
REDIS_URL=redis://127.0.0.1:6379/0

# Supabase Settings
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# AWS S3 Settings
AWS3_ACCESS_KEY_ID=your_aws_access_key_id
AWS3_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS3_REGION=ap-southeast-2
AWS3_BUCKET_NAME=your_bucket_name

# AI Model Settings
GOOGLE_GENAI_API_KEY=your_google_genai_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Email Settings
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your_email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=True
MAIL_SSL_TLS=False
USE_CREDENTIALS=True

# Additional Settings
EXCEL_FILE_PATH=data/emails.xlsx
CLIENT_AUTH=your_google_client_id
GOOGLE_API_URL=https://www.googleapis.com/auth/drive.file
```

> **Security Note:** The `.env` file contains sensitive credentials. Ensure it is listed in `.gitignore` and never committed to the repository.

### 4. Running with Docker Compose

**Build and start services:**

```bash
docker compose up --build
```

To run in detached (background) mode:

```bash
docker compose up --build -d
```

**Apply database migrations** (run this after the containers are up):

```bash
docker compose exec web poetry run alembic upgrade head
```

This creates all necessary database tables in your Supabase database.

**Accessing the application:**

| Resource | URL |
|----------|-----|
| API | `http://localhost:8080` |
| Swagger UI | `http://localhost:8080/api/docs` |
| ReDoc | `http://localhost:8080/api/redoc` |

**Viewing logs** (when running in detached mode):

```bash
docker compose logs -f          # All services
docker compose logs -f web      # FastAPI service only
```

**Stopping the services:**

```bash
docker compose down             # Stop services
docker compose down -v          # Stop + remove Redis data
```

## Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for managing database schema changes.

| Action | Command |
|--------|---------|
| Apply all pending migrations | `docker compose exec web poetry run alembic upgrade head` |
| Create a new migration | `docker compose exec web poetry run alembic revision -m "description"` |
| Auto-generate migration from models | `docker compose exec web poetry run alembic revision --autogenerate -m "description"` |
| View migration history | `docker compose exec web poetry run alembic history` |
| Downgrade one version | `docker compose exec web poetry run alembic downgrade -1` |

## Authentication

EduMind uses **Supabase Auth** for all authentication. The backend does not manage passwords — all sign-up/sign-in happens through Supabase.

### Flow

```
Frontend ──► Supabase Auth (email + password) ──► JWT access_token
Frontend ──► Backend API (Authorization: Bearer <token>) ──► Response
```

### Creating Your First Admin User

1. **Create a user in Supabase:** Dashboard → Authentication → Users → Add User

2. **Get a JWT token:**
   ```bash
   curl -X POST 'https://[PROJECT-REF].supabase.co/auth/v1/token?grant_type=password' \
     -H "apikey: YOUR_SUPABASE_ANON_KEY" \
     -H "Content-Type: application/json" \
     -d '{"email": "your@email.com", "password": "your-password"}'
   ```

3. **Call the API** to auto-provision the user row:
   ```bash
   curl http://localhost:8080/api/auth/me \
     -H "Authorization: Bearer ACCESS_TOKEN_FROM_STEP_2"
   ```

4. **Promote to admin** via Supabase SQL Editor:
   ```sql
   UPDATE public.users SET role = 'admin' WHERE email = 'your@email.com';
   ```

## API Documentation

Once the application is running, open **Swagger UI** at `http://localhost:8080/api/docs`.

**To authorize:**

1. Click the **"Authorize"** button (🔒) at the top
2. Paste your Supabase JWT `access_token` in the **Value** field
3. Click **Authorize** → **Close**

All subsequent API calls will include the token automatically.

## Project Structure

```
EduMind/
├── core/                       # Core framework components
│   ├── db/                     #   Database session management
│   ├── cache/                  #   Redis cache layer
│   ├── fastapi/middlewares/    #   SQLAlchemy middleware
│   ├── settings.py             #   Configuration (loaded from .env)
│   ├── supabase.py             #   Supabase client initialization
│   └── utils/                  #   Auth utilities, file helpers
├── machine/                    # Main application module
│   ├── api/v1/                 #   API route definitions
│   │   ├── auth.py             #     Auth endpoints (GET /auth/me)
│   │   ├── user.py             #     User management (admin)
│   │   ├── courses.py          #     Course CRUD
│   │   ├── lesson.py           #     Lesson management
│   │   ├── exercise.py         #     Exercise evaluation
│   │   ├── ai_routers.py       #     AI/LLM endpoints
│   │   ├── feedback.py         #     Student feedback
│   │   └── ...                 #     Other domain routes
│   ├── controllers/            #   Business logic layer
│   ├── models/                 #   SQLAlchemy ORM models
│   ├── schemas/                #   Pydantic request/response schemas
│   ├── repositories/           #   Data access layer
│   ├── providers/              #   Dependency injection
│   ├── services/               #   External service integrations
│   └── server.py               #   FastAPI app factory
├── migrations/                 # Alembic migration versions
├── utils/                      # Shared utilities
├── templates/                  # Email templates
├── tests/                      # Test suite
├── .env                        # Environment variables (not committed)
├── alembic.ini                 # Alembic configuration
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker service orchestration
├── main.py                     # Application entry point
├── pyproject.toml              # Project dependencies (Poetry)
└── README.md                   # This file
```

## License
Jenny - Thi Pham
