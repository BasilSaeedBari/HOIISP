FROM python:3.14-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the app directory and the project template
COPY app/ ./app/
COPY project_template.md .

# Create directory for persistent data
RUN mkdir -p /app/data

# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1

# Override Database path to point to persistent volume
ENV DATABASE_PATH=/app/data/app.db

EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
