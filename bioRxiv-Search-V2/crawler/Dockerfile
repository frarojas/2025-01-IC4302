FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY crawler.py .
CMD ["python", "-u", "crawler.py"]