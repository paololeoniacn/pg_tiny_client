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
)
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Necessario per flash messages


@app.context_processor
def inject_globals():
    return dict(db_info=get_db_info(), table_list=get_table_fullnames())


CONFIG_FILE = "db_config.json"


@app.errorhandler(404)
def page_not_found(e):
    # Redirect a una route specifica, ad esempio la homepage
    return render_template("404.html")


@app.errorhandler(500)
def internal_error(e):
    return render_template("500.html"), 500


@app.route("/", methods=["GET", "POST"])
def index():
    query = request.form.get("query")
    result = None  # Inizializzazione sicura
    if request.method == "POST":
        if query:
            result = run_query(query)
        else:
            result = get_default_tables()
    else:
        # GET: mostra tabelle di default
        result = get_default_tables()
        query = DEFAULT_QUERY

    # Se è una lista vuota, mostra un messaggio chiaro
    if isinstance(result, list) and len(result) == 0:
        result = "Nessun risultato trovato per la query eseguita."

    logger.info(result)
    return render_template(
        "index.html",
        result=result,
        query=query,
    )


@app.route("/triggers", methods=["GET"])
def show_triggers():
    result = run_query(TRIGGER_QUERY)
    return render_template(
        "index.html",
        result=result,
        query=TRIGGER_QUERY,
    )


@app.route("/config", methods=["GET", "POST"])
def config():
    # Se il file non esiste, restituisci valori vuoti per il form
    if os.path.exists(CONFIG_FILE):
        config_data = load_db_config()
    else:
        config_data = {"host": "", "port": "", "name": "", "user": "", "password": ""}

    if request.method == "POST":
        if "delete" in request.form:
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
                flash(
                    "Configurazione eliminata. Ora vengono usati i valori di default da .env.",
                    "warning",
                )
            else:
                flash("Nessun file di configurazione da eliminare.", "info")
            return render_template(
                "config.html",
                config=config_data,
            )

        # Altrimenti è un salvataggio
        config_data["host"] = request.form["host"]
        config_data["port"] = request.form["port"]
        config_data["name"] = request.form["name"]
        config_data["user"] = request.form["user"]
        config_data["password"] = request.form["password"]

        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=2)

        flash("Configurazione aggiornata!", "success")
        return render_template(
            "config.html",
            config=config_data,
        )

    return render_template(
        "config.html",
        config=config_data,
    )


if __name__ == "__main__":
    app.run(debug=True)
