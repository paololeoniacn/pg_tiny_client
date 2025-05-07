import os
import json
import psycopg
from dotenv import load_dotenv
import logging

# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Carica .env
load_dotenv()
logger.info("Variabili d'ambiente caricate.")

CONFIG_FILE = "db_config.json"

DEFAULT_QUERY = """
    SELECT schemaname, tablename
    FROM pg_catalog.pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
"""

TRIGGER_QUERY = """
SELECT
    event_object_schema AS schema,
    event_object_table AS table,
    trigger_name,
    action_timing AS timing,
    event_manipulation AS event,
    action_orientation AS orientation,
    action_statement AS definition
FROM
    information_schema.triggers
ORDER BY
    event_object_schema,
    event_object_table,
    trigger_name;
"""


def load_db_config():
    """Ritorna la configurazione del DB. Se esiste db_config.json, ha la precedenza su .env."""
    config = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        # "name": os.getenv("DB_NAME"),
        "name": "postgres",
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                file_config = json.load(f)
                logger.info("✅ Configurazione DB letta da db_config.json")
                config.update(
                    {k: v for k, v in file_config.items() if v}
                )  # sovrascrive solo se il valore non è vuoto
        except Exception as e:
            logger.warning("⚠️ Errore nella lettura di db_config.json: %s", e)
    else:
        logger.info("✅ Configurazione DB letta da ENV")
    return config


def get_db_info():
    """Ritorna solo i dati non sensibili per visualizzazione UI."""
    config = load_db_config()
    return {k: config[k] for k in ("host", "port", "name", "user")}


def get_default_tables():
    logger.info("Esecuzione query default per elencare le tabelle.")
    result = run_query(DEFAULT_QUERY)

    if isinstance(result, list) and not result:
        return "Nessuna tabella trovata nel database."

    return result


def get_connection():
    logger.info("Inizio connessione DB...")
    config = load_db_config()

    try:
        conn = psycopg.connect(
            host=config["host"],
            port=config["port"],
            dbname=config["name"],
            user=config["user"],
            password=config["password"],
            connect_timeout=5,
        )
        logger.info("✅ Connessione DB riuscita.")
        return conn
    except Exception as e:
        logger.exception("❌ Errore nella connessione al database.")
        raise


def run_query(query):
    logger.info("Esecuzione query: %s", query)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                try:
                    logger.info("quering...")
                    return cur.fetchall()
                except psycopg.errors.NoData:
                    return "Query eseguita con successo (nessun risultato)."
    except Exception as e:
        logger.error("Errore nell'esecuzione della query: %s", e)
        return f"Errore: {e}"
