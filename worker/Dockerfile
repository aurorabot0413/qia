# Worker Dockerfile - QA Automation
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set entrypoint for Cloud Build compatibility
ENTRYPOINT ["python", "/app/qa_script.py"]
