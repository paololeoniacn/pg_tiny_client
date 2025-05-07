# Usa un'immagine base leggera
FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia tutti i file del progetto nella directory di lavoro
COPY . .

# Installa le dipendenze da requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Espone la porta 8000, usata da Flask
EXPOSE 8000

# Imposta variabili d'ambiente per Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8000

# Comando per avviare l'app Flask
CMD ["flask", "run"]
