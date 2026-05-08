FROM python:3.11-slim
WORKDIR /vraksha

RUN apt-get update && \
    apt-get install -y --no-install-recommends docker.io && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY get_root.py .
COPY memory/ ./memory/
COPY workspace/ ./workspace/
COPY main.py .
COPY vraksha.sh . 
COPY models.yaml .

CMD ["python", "main.py"]

