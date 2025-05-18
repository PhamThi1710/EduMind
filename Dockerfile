# 1. Choose a base Python image
# Using a -slim variant for a smaller image size.
# Choose a Python version compatible with your project (e.g., 3.10, 3.11)
# Check your pyproject.toml for the specified python version range.
FROM python:3.12-slim

# 2. Set environment variables
# Prevents Python from writing .pyc files to disc (improves performance in Docker)
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to terminal (makes debugging easier)
ENV PYTHONUNBUFFERED 1

# 3. Install Poetry
# Pinning the version is good practice for reproducibility
RUN pip install "poetry==1.8.2" --no-cache-dir 

# 4. Set the working directory in the container
WORKDIR /app

# 5. Copy only pyproject.toml and poetry.lock first
# This leverages Docker's layer caching. If these files don't change,
# Docker won't re-run the dependency installation step.
COPY pyproject.toml poetry.lock ./

# 6. Install project dependencies using Poetry
# --no-interaction: Do not ask any interactive question
# --no-ansi: Disable ANSI output
# --no-dev: Do not install development dependencies (for production image)
# poetry config virtualenvs.create false: Instructs Poetry to install packages
# into the system Python environment (which is isolated within the Docker container)
# rather than creating a separate virtual environment inside the container.
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

# 7. Copy the rest of your application code into the image
COPY . .

# 8. Expose the port your application will run on
# This is informational; the actual port mapping happens in docker-compose.yml
EXPOSE 8080

# 9. Command to run the application
# This will be overridden by docker-compose.yml for more flexibility,
# especially since you have a web server and background workers.
# If this Dockerfile was ONLY for the web app, it would be:
# CMD ["uvicorn", "machine.server:machine", "--host", "0.0.0.0", "--port", "8080"]
# If it was ONLY for the worker, it might be:
# CMD ["dramatiq", "worker", "--processes", "3"] or ["python", "worker.py"]
# Since docker-compose will define separate services, we can leave CMD out
# or put a default that will be overridden. For now, let's assume it's for the web app.
# CMD ["python", "main.py"] # This would try to run both, which is not ideal for separate scaling.
                            # We will define specific commands in docker-compose.yml