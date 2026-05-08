FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /code/app
COPY TermsAndConditions.md /code/TermsAndConditions.md

ENV DATABASE_PATH=/data/app.db
ENV UPLOAD_DIR=/data/uploads
ENV SECRET_KEY=change-me

VOLUME ["/data"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
