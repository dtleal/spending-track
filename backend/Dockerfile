FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies first (for better caching)
COPY pyproject.toml .

# Extract and install dependencies directly
RUN pip install --no-cache-dir \
    "fastapi[all]>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "sqlalchemy>=2.0.0" \
    "alembic>=1.13.0" \
    "psycopg2-binary>=2.9.0" \
    "pydantic>=2.5.0" \
    "pydantic-settings>=2.1.0" \
    "python-jose[cryptography]>=3.3.0" \
    "passlib[bcrypt]>=1.7.4" \
    "python-multipart>=0.0.9" \
    "elasticsearch>=8.12.0" \
    "pandas>=2.1.0" \
    "numpy>=1.26.0" \
    "openai>=1.40.0" \
    "httpx>=0.27.0" \
    "redis>=5.0.0" \
    "celery>=5.3.0" \
    "python-dateutil>=2.8.0" \
    "google-auth>=2.22.0" \
    "google-auth-oauthlib>=1.0.0" \
    "google-auth-httplib2>=0.1.0" \
    && pip install --no-cache-dir \
    "pytest>=8.0.0" \
    "pytest-asyncio>=0.23.0" \
    "pytest-cov>=4.1.0" \
    "black>=24.0.0" \
    "ruff>=0.1.0" \
    "pylint>=3.0.0" \
    "mypy>=1.8.0"

# Copy application code
COPY app app/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]