FROM python:3.11-slim
WORKDIR /workspace

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API server
COPY api_server.py .

# Copy legacy update script (if exists, for backward compatibility)
COPY update_column_descriptions.py* ./

# Copy CLI modules from app-cli
COPY modules/ ./modules/

# Ensure modules is a package
RUN touch modules/__init__.py

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8080"]
