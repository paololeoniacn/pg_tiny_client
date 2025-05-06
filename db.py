import os
import psycopg
from dotenv import load_dotenv
import logging

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Carica variabili d'ambiente
load_dotenv()
logger.info("Variabili d'ambiente caricate.")

def get_connection():
    logger.info("Inizio procedura di connessione al database...")

    db_config = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        # Non logghiamo la password!
        "connect_timeout": 5
    }

    # Mostra configurazione (escludendo password)
    logger.info("Configurazione DB: host=%s port=%s dbname=%s user=%s",
                db_config["host"], db_config["port"], db_config["dbname"], db_config["user"])

    try:
        conn = psycopg.connect(
            host=db_config["host"],
            port=db_config["port"],
            dbname=db_config["dbname"],
            user=db_config["user"],
            password=os.getenv("DB_PASSWORD"), 
            connect_timeout=db_config["connect_timeout"]
        )
        logger.info("✅ Connessione al database riuscita.")
        return conn

    except Exception as e:
        logger.exception("❌ Errore nella connessione al database")
        raise
