from scrape import league_table, top_scorers
from api_ingest import premier_league_teams

import os
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# reads variables from the .env file into the environment
load_dotenv()

# list of functions to be called and pushed to azure sql database
functions = [league_table,top_scorers,premier_league_teams]


def get_engine():

    '''
    Builds a SQLAlchemy engine for Azure SQL Database using credentials from .env.
    Azure SQL is SQL Server, so it uses pyodbc + "ODBC Driver 17 for SQL Server" (psycopg2 is Postgres only).
    Returns:
        sqlalchemy.engine.Engine
    '''

    server = os.getenv("AZURE_SQL_SERVER")        # e.g. myserver.database.windows.net
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")
    driver = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 17 for SQL Server")

    missing = [name for name, value in {
        "AZURE_SQL_SERVER": server,
        "AZURE_SQL_DATABASE": database,
        "AZURE_SQL_USERNAME": username,
        "AZURE_SQL_PASSWORD": password,
    }.items() if not value]
    if missing:
        raise RuntimeError(f"Missing in .env: {', '.join(missing)}. See .env.example.")

    # URL.create escapes special characters in the password (@, #, / etc.)
    connection_url = URL.create(
        "mssql+pyodbc",
        username=username,
        password=password,
        host=server,
        port=1433,
        database=database,
        query={
            "driver": driver,
            "Encrypt": "yes",
            "TrustServerCertificate": "no",
            "Connection Timeout": "30",
        },
    )
    # fast_executemany speeds up bulk inserts from pandas a lot
    return create_engine(connection_url, fast_executemany=True)


def to_sql(func, engine):

    '''
    Calls the given function and writes its DataFrame to Azure SQL Database.
    The function's name is used as the table name, and the table is replaced on every run.
    Example:
        to_sql(top_scorers, engine) -> table dbo.top_scorers
    '''

    table_name = func.__name__
    df = func()

    df.to_sql(table_name, engine, schema="dbo", if_exists="replace", index=False, chunksize=1000)
    print(f"{table_name} successfully loaded ({len(df)} rows)")


if __name__ == "__main__":
    engine = get_engine()

    # quick connection test before loading anything
    with engine.connect() as conn:
        print("Connected to:", conn.execute(text("SELECT DB_NAME()")).scalar())

    for items in functions:
        to_sql(items, engine)
