import os
import json
import psycopg
from dotenv import dotenv_values
import logging
from functools import lru_cache


# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Ambienti supportati
VALID_ENVS = {"dev", "prod", "test", "custom"}


def safe_env(env):
    return env if env in VALID_ENVS else "dev"


CONFIG_FILE = "db_config.json"

GET_TABLE_LIST = """
    SELECT schemaname, tablename
    FROM pg_catalog.pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
"""

DEFAULT_QUERY = """ SELECT 1; """

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

def log_entry(fn):
    def wrapper(*args, **kwargs):
        logger.info(f"--- execute {fn.__name__}")
        return fn(*args, **kwargs)
    return wrapper

@log_entry
@lru_cache(maxsize=None)
def load_db_config(env: str = None):
    """Carica config da .env.{env}"""
    env = env or "dev"
    env_file = f".env.{env}"
    if os.path.exists(env_file):
        config_values = dotenv_values(env_file)
        logger.info(f"✅ Configurazione DB caricata da {env_file}")
    else:
        logger.warning(f"⚠️ File di configurazione {env_file} non trovato.")
        config_values = {}

    config = {
        "host": config_values.get("DB_HOST"),
        "port": config_values.get("DB_PORT"),
        "name": config_values.get("DB_NAME") or "postgres",
        "user": config_values.get("DB_USER"),
        "password": config_values.get("DB_PASSWORD"),
        "schema": config_values.get("DB_SCHEMA") or "public",
    }

    safe_config = {k: v if k != "password" else "****" for k, v in config.items()}
    logger.info(f"📦 Config caricato: {safe_config}")

    return config


@log_entry
def get_db_info(env):
    """Ritorna solo i dati non sensibili per visualizzazione UI."""
    config = load_db_config(env)
    return {k: config[k] for k in ("host", "port", "name", "user", "schema")}

@log_entry
def get_default_tables(env="dev"):
    logger.info("Esecuzione query default per elencare le tabelle.")
    result = run_query(GET_TABLE_LIST, env=env)

    if isinstance(result, list) and not result:
        return json.dumps(
            {"message": "Nessuna tabella trovata nel database."}, ensure_ascii=False
        )

    # se result è già una lista di dict, basta serializzarla
    return json.dumps(result, ensure_ascii=False)

@log_entry
def get_connection(env=None, config=None):
    logger.info("Inizio connessione DB...")
    logger.info(
        f"🔍 Tentativo connessione a {config['host']}:{config['port']}, DB: {config['name']}"
    )
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

@log_entry
def run_query(query, env="dev"):
    """
    Esegue una o più query separate da ';'.
    Restituisce il risultato dell'ultima query che produce righe (SELECT, etc.)
    oppure un messaggio se nessuna query produce risultati.
    """
    logger.info("Esecuzione query: %s", query)
    try:
        config = load_db_config(env)
        schema = config.get("schema") or "public"

        with get_connection(env=env, config=config) as conn:
            with conn.cursor() as cur:
                # Imposta lo schema come search_path
                logger.info(f"📌 Imposto search_path su schema: {schema}")
                cur.execute(f"SET search_path TO {schema};")

                final_result = None
                for statement in query.split(";"):
                    statement = statement.strip()
                    if not statement:
                        continue
                    logger.info("Eseguo: %s", statement)
                    cur.execute(statement)
                    if cur.description:
                        cols = [desc.name for desc in cur.description]
                        rows = cur.fetchall()
                        final_result = [dict(zip(cols, row)) for row in rows]
                    else:
                        final_result = [
                            {
                                "message": "Query eseguita con successo (nessun risultato)."
                            }
                        ]

                return final_result or [
                    {"message": "Nessun risultato utile da mostrare."}
                ]
    except Exception as e:
        logger.error("Errore nell'esecuzione della query: %s", e)
        return [{"error": str(e)}]

@log_entry
def get_table_fullnames(env="dev"):
    """
    Esegue la SELECT su pg_catalog.pg_tables e
    restituisce una lista di 'schemaname.tablename'.
    """
    rows = run_query(GET_TABLE_LIST, env=env)
    if not isinstance(rows, list):
        # in caso di errore o messaggio, ritorna lista vuota
        return []
    fullnames = []
    for row in rows:
        # assicurati che row sia dict con le chiavi giuste
        if isinstance(row, dict) and "schemaname" in row and "tablename" in row:
            fullnames.append(f"{row['schemaname']}.{row['tablename']}")
    return fullnames
