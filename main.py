from db import get_connection

def list_tables():
    query = """
        SELECT schemaname, tablename
        FROM pg_catalog.pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                tables = cur.fetchall()
                print("Tabelle presenti:")
                for schema, table in tables:
                    print(f"- {schema}.{table}")
    except Exception as e:
        print("Errore durante l'elenco delle tabelle:", e)

if __name__ == "__main__":
    list_tables()
