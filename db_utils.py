import sqlite3
import pandas as pd
import os
import re


def sanitize_column_name(col: str) -> str:
    """Clean column names for SQL compatibility."""
    col = col.strip().lower()
    col = re.sub(r'[^a-z0-9_]', '_', col)
    col = re.sub(r'_+', '_', col)
    col = col.strip('_')
    if col[0].isdigit():
        col = 'col_' + col
    return col


def load_csv_to_sqlite(csv_file, db_path: str = ":memory:") -> tuple:
    """
    Load a CSV file into a SQLite database.
    Returns (connection, table_name, dataframe)
    """
    df = pd.read_csv(csv_file)

    # Sanitize column names
    df.columns = [sanitize_column_name(c) for c in df.columns]

    # Get table name from file name
    if hasattr(csv_file, 'name'):
        table_name = os.path.splitext(os.path.basename(csv_file.name))[0]
    else:
        table_name = os.path.splitext(os.path.basename(csv_file))[0]

    table_name = sanitize_column_name(table_name)

    # Create SQLite connection and load data
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, if_exists='replace', index=False)

    return conn, table_name, df


def load_sqlite_db(db_file) -> tuple:
    """
    Load an existing SQLite database file.
    Returns (connection, list of table names)
    """
    if hasattr(db_file, 'read'):
        # Uploaded file — save to temp
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            f.write(db_file.read())
            tmp_path = f.name
        conn = sqlite3.connect(tmp_path)
    else:
        conn = sqlite3.connect(db_file)

    # Get all table names
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    return conn, tables


def get_schema_info(conn: sqlite3.Connection, table_names: list) -> str:
    """
    Get complete schema information for all tables.
    Returns formatted schema string for LLM context.
    """
    schema_parts = []
    cursor = conn.cursor()

    for table in table_names:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]

        # Get sample values for each column
        col_info = []
        for col in columns:
            col_name = col[1]
            col_type = col[2]

            try:
                cursor.execute(f"SELECT DISTINCT {col_name} FROM {table} LIMIT 3")
                samples = [str(r[0]) for r in cursor.fetchall() if r[0] is not None]
                sample_str = ', '.join(samples[:3])
            except:
                sample_str = "N/A"

            col_info.append(f"  - {col_name} ({col_type}) — e.g. {sample_str}")

        schema_parts.append(
            f"Table: {table} ({row_count:,} rows)\n" +
            "Columns:\n" +
            "\n".join(col_info)
        )

    return "\n\n".join(schema_parts)


def execute_query(conn: sqlite3.Connection, sql: str) -> pd.DataFrame:
    """Execute SQL query and return results as DataFrame."""
    try:
        df = pd.read_sql_query(sql, conn)
        return df, None
    except Exception as e:
        return None, str(e)


def get_sample_data(conn: sqlite3.Connection, table_name: str, n: int = 5) -> pd.DataFrame:
    """Get sample rows from a table."""
    return pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {n}", conn)