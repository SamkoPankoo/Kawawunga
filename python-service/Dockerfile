FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# For pdf2image functionality (if needed)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application files
COPY *.py ./

# Create upload folder with proper permissions
RUN mkdir -p uploads && chmod 777 uploads

EXPOSE 5000

CMD ["python", "app.py"]