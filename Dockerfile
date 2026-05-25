FROM python:3.10-slim

ENV FLASK_APP=src.app
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]
