FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY main.py ./

# Create outputs volume
RUN mkdir -p outputs

EXPOSE 8000 8501

ENV PYTHONUNBUFFERED=1
ENV LLM_PROVIDER=openai

# Default entrypoint starts CLI or API based on args
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
