FROM python:3.10-slim
WORKDIR /app
# Install system packages required for compiling psycopg2 binary
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir flask psycopg2-binary
COPY app.py .
EXPOSE 5000
CMD ["python", "app.py"]
