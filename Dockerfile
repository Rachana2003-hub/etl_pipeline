# Use a lightweight official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Set workspace directory
WORKDIR /app

# Create a non-privileged user to run the app
RUN groupadd -g 10001 etlgroup && \
    useradd -u 10001 -g etlgroup -m -s /bin/bash etluser

# Install system dependencies if any are needed (e.g., build-essential, default-libmysqlclient-dev)
# For sqlalchemy and pymysql, we mostly run pure python, but we need cryptography.
# We'll install typical build tools dynamically if needed, but slim is sufficient here.

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code and data
COPY config.py etl_pipeline.py ./
COPY data/ ./data/

# Create logs directory and set permissions for our non-root user
RUN mkdir -p logs && \
    chown -R etluser:etlgroup /app

# Switch to the non-root user
USER etluser

# Run the pipeline
CMD ["python", "etl_pipeline.py"]
