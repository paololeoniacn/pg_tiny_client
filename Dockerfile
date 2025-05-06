FROM python:3.11-slim

# Sicurezza: aggiornamenti base
RUN apt-get update && apt-get upgrade -y && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
