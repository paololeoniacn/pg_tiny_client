import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from db import (
    run_query,
    get_db_info,
    load_db_config,
    get_default_tables,
    get_table_fullnames,
    DEFAULT_QUERY,
    TRIGGER_QUERY,
    safe_env
)
import logging
from zoneinfo import ZoneInfo
from dotenv import dotenv_values
import datetime


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Necessario per flash messages


@app.context_processor
def inject_globals():
    selected_env = safe_env(request.args.get("env", "dev"))
    return dict(
        db_info=get_db_info(selected_env),
        table_list=get_table_fullnames(selected_env)
    )


CONFIG_FILE = "db_config.json"
QUERY_HISTORY_FILE = "data/query_history.json"


@app.errorhandler(404)
def page_not_found(e):
    # Redirect a una route specifica, ad esempio la homepage
    return render_template("404.html")


@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500


@app.route("/", methods=["GET", "POST"])
def index():
    selected_env = safe_env(request.args.get("env", "dev"))
    raw_query = request.form.get("query")
    result = None
    cleaned_query = ""

    timestamp = datetime.datetime.now(ZoneInfo("Europe/Rome")).strftime("%Y-%m-%d %H:%M:%S")

    if request.method == "POST":
        if raw_query:
            cleaned_query = clean_submitted_query(raw_query)
            save_query_to_history(cleaned_query)
            result = run_query(cleaned_query, env=selected_env)
        else:
            result = get_default_tables(env=selected_env)
    else:
        result = get_default_tables(env=selected_env)
        raw_query = DEFAULT_QUERY
        cleaned_query = clean_submitted_query(DEFAULT_QUERY)


    if isinstance(result, list) and len(result) == 0:
        result = "Nessun risultato trovato per la query eseguita."

    smart_log(result)
    return render_template(
        "index.html",
        result=result,
        query=raw_query,
        executed_query=cleaned_query,
        history=load_query_history(),
        executed_time=timestamp
    )


def load_query_history():
    if os.path.exists(QUERY_HISTORY_FILE):
        with open(QUERY_HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def clean_submitted_query(query: str) -> str:
    # Rimuove le righe che iniziano con --
    cleaned_lines = []
    for line in query.splitlines():
        stripped = line.strip()
        if not stripped.startswith("--") and stripped != "":
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def save_query_to_history(query: str):
    query = query.strip()
    entry = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "query": query
    }

    if os.path.exists(QUERY_HISTORY_FILE):
        with open(QUERY_HISTORY_FILE, "r") as f:
            history = json.load(f)
    else:
        history = []

    # 🔍 Verifica se esiste già (ignorando spazi)
    if any(q["query"].strip() == query for q in history):
        return  # Non salva se già presente

    # Aggiunge in cima
    history.insert(0, entry)

    # Limita la lunghezza dello storico (es. max 20)
    history = history[:20]

    with open(QUERY_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


@app.route("/triggers", methods=["GET"])
def show_triggers():
    selected_env = safe_env(request.args.get("env", "dev"))
    result = run_query(TRIGGER_QUERY, env=selected_env)
    return render_template(
        "index.html",
        result=result,
        query=TRIGGER_QUERY,
    )

@app.route("/config", methods=["GET", "POST"])
def config():
    selected_env = safe_env(request.args.get("env") or request.form.get("env") or "dev")
    env_filename = f"env.{selected_env}"

    if request.method == "POST":
        if "delete" in request.form:
            if os.path.exists(env_filename):
                os.remove(env_filename)
                flash(f"Configurazione '{env_filename}' eliminata.", "warning")
            else:
                flash("Nessun file di configurazione da eliminare.", "info")
        else:
            # Salvataggio nuovo contenuto
            with open(env_filename, "w") as f:
                f.write(f"DB_HOST={request.form['host']}\n")
                f.write(f"DB_PORT={request.form['port']}\n")
                f.write(f"DB_NAME={request.form['name']}\n")
                f.write(f"DB_USER={request.form['user']}\n")
                f.write(f"DB_PASSWORD={request.form['password']}\n")
            flash(f"Configurazione '{env_filename}' salvata con successo!", "success")

    # Carica valori correnti, se esistono
    config_data = dotenv_values(env_filename) if os.path.exists(env_filename) else {}

    # Prepara dati per il form
    config_data = {
        "host": config_data.get("DB_HOST", ""),
        "port": config_data.get("DB_PORT", ""),
        "name": config_data.get("DB_NAME", ""),
        "user": config_data.get("DB_USER", ""),
        "password": config_data.get("DB_PASSWORD", "")
    }

    return render_template(
        "config.html",
        config=config_data,
        selected_env=selected_env
    )

def truncate_log(data, max_length=500):
    text = str(data)
    return text[:max_length] + ("..." if len(text) > max_length else "")

def smart_log(result):
    if isinstance(result, list):
        logger.info(f"📊 Query restituita: {len(result)} righe.")
    else:
        logger.info(f"📊 Risultato: {truncate_log(result)}")


if __name__ == "__main__":
    app.run(debug=True)
