# EduMind API Backend

API for the EduMind project - an intelligent learning platform focusing on personalized learning paths and exercise evaluation. This backend system powers the entire EduMind application.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Environment Setup](#2-environment-setup)
  - [3. Running with Docker Compose](#3-running-with-docker-compose)
- [Database Migrations](#database-migrations)
- [API Documentation](#api-documentation)
- [Background Tasks](#background-tasks)
- [Project Structure](#project-structure)
- [License](#license)

## Overview

This repository contains the backend API for the EduMind application. It handles user authentication, data management for courses, lessons, exercises, user progress, integrations with external services like Judge0 for code evaluation, AWS S3 for file storage, and AI models (Google GenAI, OpenAI).

## Tech Stack

* **Language:** Python 3.11+
* **Framework:** FastAPI
* **Database:** PostgreSQL
* **Caching/Message Broker:** Redis (for Dramatiq and application caching)
* **Async:** Uvicorn (ASGI server), AsyncPG (Postgres driver)
* **ORM:** SQLAlchemy
* **Migrations:** Alembic
* **Dependency Management:** Poetry
* **Containerization:** Docker, Docker Compose
* **Background Tasks:** Dramatiq
* **Key Libraries:**
  * Pydantic (Data validation & settings management)
  * JWT (for token-based authentication)
  * fastapi-mail (Email sending)
  * Boto3 (AWS S3 integration)
  * google-generativeai, openai (AI model SDKs)

## Prerequisites

* **Git:** For cloning the repository
* **Docker & Docker Compose:** Essential for running the application and its services
  * [Download Docker](https://docs.docker.com/get-docker/)
* **Poetry (Optional):** Only if you intend to manage dependencies or run the project locally without Docker
  * [Install Poetry](https://python-poetry.org/docs/#installation)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/PhamThi1710/EduMind.git 
cd EduMind
```

### 2. Environment Setup

Create a `.env` file in the project root directory. You can copy from `env.example` (if it exists) or create a new file with the following template:

```
# Core Settings
ENV=development
DEBUG=True
APP_HOST=localhost
APP_PORT=8080
LOG_LEVEL=DEBUG

# Database Settings
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=codemate
SQLALCHEMY_POSTGRES_URI=postgresql+asyncpg://postgres:your_strong_password@127.0.0.1:5433/codemate
SQLALCHEMY_ECHO=False

# Redis Settings
REDIS_URL=redis://127.0.0.1:6379/0

# JUDGE0 API (Code Execution)
RAPIDAPI_KEY=your_actual_rapidapi_key_for_judge0

# AWS S3 Settings
AWS3_ACCESS_KEY_ID=your_aws_access_key_id
AWS3_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS3_REGION=ap-southeast-2
AWS3_BUCKET_NAME=specialized-project

# AI Model Settings
GOOGLE_GENAI_API_KEY=your_google_genai_api_key
GEMINI_API_KEY=your_google_genai_api_key
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

# JWT Settings
SECRET_KEY=your_strong_random_jwt_secret_key
REFRESH_SECRET_KEY=your_strong_random_jwt_refresh_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Additional Settings (if needed)
EXCEL_FILE_PATH=data/emails.xlsx
CLIENT_AUTH=your_google_client_id
GOOGLE_API_URL=https://www.googleapis.com/auth/drive.file
```

> **Security Note:** The `.env` file contains sensitive credentials. Ensure it is listed in your `.gitignore` file to prevent committing it to your repository. Generate strong, unique values for passwords and secret keys.

### 3. Running with Docker Compose

This is the recommended method as it bundles the application, PostgreSQL database, and Redis cache into manageable services.

**Build and Start Services:**

```bash
docker compose up --build
```

The first run will download base images and build your application image. This may take several minutes.

To run in detached (background) mode:

```bash
docker compose up --build -d
```

**Apply Database Migrations:**

Once the database container is running, apply migrations in a separate terminal: **!! Crucial !!: You must run this cml right after running docker to create database and relations** 

```bash
docker compose exec web poetry run alembic upgrade head
```

This creates all necessary database tables.

**Accessing the Application:**

- API: http://localhost:8080 (adjust if APP_PORT is different)
- API Documentation (Swagger UI): http://localhost:8080/api/docs
- Alternative API Documentation (ReDoc): http://localhost:8080/api/redoc

**Viewing Logs (when running in detached mode):**

```bash
docker compose logs -f          # All services
docker compose logs -f web      # FastAPI service only
docker compose logs -f worker   # Dramatiq worker only
docker compose logs -f db       # PostgreSQL service only
```

**Stopping the Services:**

If running in terminal, press `Ctrl+C`

If running in detached mode:

```bash
docker compose down
```

To stop services AND remove data volumes (deletes all database and Redis data):

```bash
docker compose down -v
```

## Database Migrations

This project uses Alembic for managing database schema changes.

**Apply All Pending Migrations:**

```bash
docker compose exec web poetry run alembic upgrade head
```

**Create a New Migration:**

```bash
docker compose exec web poetry run alembic revision -m "your_descriptive_migration_message"
```

**View Migration History:**

```bash
docker compose exec web poetry run alembic history
```

## API Documentation

Once the application is running, access the interactive API documentation:

- Swagger UI: http://localhost:8080/api/docs

**Authorizing in Swagger UI:**

1. Execute the POST `/api/v1/auth/login` endpoint with your credentials
2. Copy the `access_token` from the response
3. Click the "Authorize" button at the top-right
4. In the "ApiKeyAuth" section, paste the token prefixed with `Bearer ` (note the space)
5. Click "Authorize" and close the dialog

## Background Tasks

Background tasks are handled by Dramatiq workers, which are automatically started with Docker Compose.

Task definitions are primarily located in the `tasks/` directory.

## Project Structure

```
EduMind/
├── alembic/                # Alembic migration scripts
├── core/                   # Core components (database, cache, settings)
├── machine/                # Main FastAPI application module
│   ├── api/                # API route definitions
│   ├── controllers/        # Business logic layer
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic schemas
│   └── server.py           # FastAPI application configuration
├── migrations/             # Alembic-generated versions
├── tasks/                  # Dramatiq background tasks
├── templates/              # Email templates
├── .env                    # Environment variables (not committed)
├── .env.example            # Example template for .env file
├── alembic.ini             # Alembic configuration
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker service orchestration
├── main.py                 # Application entry point
├── poetry.lock             # Poetry lock file
├── pyproject.toml          # Project definition and dependencies
└── README.md               # This file
```

## License

Group 6 - HCMUT - HK242
