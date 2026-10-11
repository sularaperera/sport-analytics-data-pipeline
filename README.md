<div align="center">

# Sport Analytics Data Pipeline

**An end-to-end, cloud-based ELT pipeline that extracts Premier League data from the web and a REST API, lands it in Azure as Parquet, loads it into Azure SQL, and runs on GitHub Actions.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-Web%20Scraping-4B8BBE)
![Azure Blob Storage](https://img.shields.io/badge/Azure%20Blob%20Storage-0078D4?logo=microsoftazure&logoColor=white)
![Azure SQL](https://img.shields.io/badge/Azure%20SQL%20Database-0078D4?logo=microsoftsqlserver&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)
![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9)
![Power BI](https://img.shields.io/badge/Power%20BI-planned-F2C811?logo=powerbi&logoColor=black)

</div>

---

## Overview

Football data changes every matchweek. League standings, top scorers and team details are spread across web pages and APIs, and none of it arrives in a form that is ready for analysis.

This project automates the full journey from **raw source → cloud storage → queryable database**:

- **Extract:** scrape the Premier League table and top-scorers list from BBC Sport, and pull team details from the TheSportsDB REST API.
- **Transform:** clean each source into a tidy tabular shape with `pandas` (fix headers, drop duplicated desktop/mobile columns, repair encoding, trim a 70-column API payload down to 8 useful fields).
- **Load (raw layer):** write each dataset to **Azure Blob Storage** as **Parquet**.
- **Load (serving layer):** write the same datasets to **Azure SQL Database** as `dbo` tables, ready for BI tools.
- **Orchestrate:** run the whole pipeline in **GitHub Actions**, with credentials kept in GitHub Secrets.


---

## Architecture

![High-level architecture](images/High-level%20architecture.png)


---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | **Python 3.11** | Pipeline logic |
| Extraction | `requests`, **BeautifulSoup4** | HTTP calls and HTML parsing |
| Transformation | **pandas**, NumPy | Cleaning and shaping into DataFrames |
| Serialization | **PyArrow** | In-memory Parquet conversion |
| Raw storage | **Azure Blob Storage** (`azure-storage-blob`) | Landing zone for Parquet files |
| Serving database | **Azure SQL Database** (`SQLAlchemy` + `pyodbc`, ODBC Driver 17/18) | Relational tables for analytics |
| Orchestration / CI | **GitHub Actions** | Automated pipeline runs |
| Dependency management | **uv** (`pyproject.toml` + `uv.lock`) | Reproducible, locked environments |
| Config & secrets | `python-dotenv`, GitHub Secrets | No credentials in source code |
| Visualisation | **Power BI** *(planned)* | Exploratory analysis and dashboards |

---

## Data Sources

| Dataset | Source | Type | Extraction method |
|---|---|---|---|
| `league_table` | [BBC Sport: Premier League Table](https://www.bbc.com/sport/football/premier-league/table) | HTML page | Web scraping (BeautifulSoup) |
| `top_scorers` | [BBC Sport: Top Scorers](https://www.bbc.com/sport/football/premier-league/top-scorers) | HTML page | Web scraping (BeautifulSoup) |
| `premier_league_teams` | [TheSportsDB](https://www.thesportsdb.com/free_sports_api) | REST API (JSON) | API ingestion (`requests`) |

> ℹ️ TheSportsDB's free public test key returns a subset of the Premier League teams.

---

## Pipeline Workflow

`run_pipeline.py` is the single entry point. For each dataset it runs:

```
for each dataset in [league_table, top_scorers, premier_league_teams]:
    1. Extract   → call the source function, which returns a pandas DataFrame
    2. Land      → convert to Parquet (PyArrow) and upload to Azure Blob Storage
    3. Load      → write the DataFrame to Azure SQL (dbo.<dataset>, full replace)
    4. Log       → print step status and timing
```

**Key design decisions**

- **Function-name-driven loading:** each extract function's name becomes the blob name and the SQL table name, so adding a new dataset means writing one function and adding it to a list.
- **In-memory Parquet:** files are serialized into a `BytesIO` buffer and uploaded directly. Nothing is written to local disk.
- **Two storage layers:** Blob keeps a cheap, columnar raw copy, and Azure SQL provides a queryable serving layer for BI.
- **Idempotent runs:** blobs are overwritten and tables are replaced (`if_exists="replace"`), so a re-run never creates duplicates.
- **Fail loudly:** HTTP timeouts, `raise_for_status()`, and explicit errors when a page layout changes or a secret is missing.
- **Fast bulk inserts:** the SQLAlchemy engine uses `fast_executemany=True`.

---

## Data Outputs

| Dataset | Azure Blob (container `testtech`) | Azure SQL (`sport_analytics_db`) | Example columns |
|---|---|---|---|
| League table | `league_table.parquet` | `dbo.league_table` | Position, Team, Played, Won, Drawn, Lost, …, Points |
| Top scorers | `top_scorers.parquet` | `dbo.top_scorers` | Position, Player, Team, Goals, Assists, … |
| Teams | `premier_league_teams.parquet` | `dbo.premier_league_teams` | Team ID, Team, Short Name, Formed, Stadium, Location, Country, Website |

---

## Project Structure

```
sport-analytics-data-pipeline/
│
├── .github/
│   └── workflows/
│       └── run_pipeline.yml          # GitHub Actions workflow: installs ODBC 18 + uv, checks secrets, runs the pipeline
│
├── src/
│   └── 1_sport_analytics_data_pipeline_v1/
│       ├── scrape.py                 # Extract: scrapes BBC league table & top scorers into DataFrames
│       ├── api_ingest.py             # Extract: pulls Premier League teams from TheSportsDB REST API
│       ├── push_to_azure_blob.py     # Load: DataFrame → Parquet (PyArrow) → Azure Blob Storage
│       ├── push_to_azure_sql.py      # Load: builds SQLAlchemy engine, writes DataFrames to Azure SQL
│       └── run_pipeline.py           # Orchestrator: runs extract → Blob → SQL for every dataset, with timings
│
├── .env.example                      # Template for required environment variables (no real secrets)
├── .gitignore                        # Excludes .env, virtual envs, caches and local credential files
├── .python-version                   # Pins Python 3.11
├── pyproject.toml                    # Project metadata and dependencies
└── uv.lock                           # Locked dependency versions for reproducible installs
```

---

## Getting Started

### Prerequisites

- Python **3.11+** and [**uv**](https://docs.astral.sh/uv/)
- An **Azure** subscription with:
  - a **Storage Account** and a Blob container (e.g. `testtech`)
  - an **Azure SQL Database**, with a firewall rule for your client IP
- **Microsoft ODBC Driver 17 or 18 for SQL Server**

### 1. Clone the repository

```bash
git clone https://github.com/sularaperera/sport-analytics-data-pipeline.git
cd sport-analytics-data-pipeline
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

```dotenv
AZURE_STORAGE_CONNECTION_STRING=<storage-account-connection-string>
AZURE_SQL_SERVER=<your-server>.database.windows.net
AZURE_SQL_DATABASE=<your-database>
AZURE_SQL_USERNAME=<your-admin-login>
AZURE_SQL_PASSWORD=<your-password>
AZURE_SQL_DRIVER=ODBC Driver 17 for SQL Server
```

> `.env` is git-ignored. Never commit real credentials.

### 4. Run the pipeline

```bash
cd src/1_sport_analytics_data_pipeline_v1
uv run python run_pipeline.py
```

You can also run each stage on its own:

```bash
uv run python push_to_azure_blob.py   # extract + land to Blob only
uv run python push_to_azure_sql.py    # extract + load to Azure SQL only
```

**Sample output**

```
==================================================
Pipeline started
==================================================

[Setup] Creating Azure SQL engine...
[Setup] Azure SQL engine ready

[Step 1/3] league_table
  -> Running league_table and uploading to Azure Blob Storage...
league_table.parquet successfully updated
  -> Running league_table and loading to Azure SQL...
league_table successfully loaded (20 rows)
[Step 1/3] league_table completed
...
```

---

## CI/CD with GitHub Actions

The workflow [`.github/workflows/run_pipeline.yml`](.github/workflows/run_pipeline.yml):

1. Checks out the code on an `ubuntu-latest` runner.
2. Installs **Microsoft ODBC Driver 18** for SQL Server.
3. Installs **uv** (with caching) and runs `uv sync --locked`.
4. **Validates secrets**: fails early with a clear message if any secret is missing (names only, never values).
5. Runs `run_pipeline.py`.

**Triggers**

- `workflow_dispatch`: manual "Run workflow" button
- `schedule` *(currently disabled)*: cron schedule for automatic weekend runs during the season

**Required repository secrets** (*Settings → Secrets and variables → Actions*)

| Secret | Description |
|---|---|
| `AZURE_STORAGE_CONNECTION_STRING` | Storage account connection string |
| `AZURE_SQL_SERVER` | Full server name, e.g. `myserver.database.windows.net` |
| `AZURE_SQL_DATABASE` | Database name |
| `AZURE_SQL_USERNAME` | SQL login |
| `AZURE_SQL_PASSWORD` | SQL password |

> ✅ A `concurrency` group stops two pipeline runs from overlapping, and a 30-minute `timeout-minutes` keeps a hung run from consuming runner minutes.

---

## Challenges & Lessons Learned

| Challenge | Root cause | Fix |
|---|---|---|
| Scraper blocked or empty on cloud runners | BBC serves different content to requests without a browser User-Agent | Send a browser `User-Agent` header and fail loudly if the table isn't found |
| Garbled player names (e.g. `JoÃ£o`) | BBC doesn't declare a charset, so `requests` falls back to Latin-1 | Force `page.encoding = "utf-8"` |
| Duplicated stat columns | BBC renders every stat twice (desktop + mobile labels) | Select one column per stat by index |
| `Cannot open server … (40615)` | Azure SQL blocks all client IPs by default | Add a server firewall rule for the client IP |
| `AttributeError` in `df.to_sql` | pandas 3.x doesn't recognise SQLAlchemy 2.0.20 engines | Upgrade to `sqlalchemy>=2.0.36` |
| `Login timeout expired (HYT00)` in GitHub Actions | Serverless Azure SQL was **auto-paused** and took 30–60 s to wake | Raise the connection timeout to 60 s and disable auto-pause |
| Hard-coded storage key | Account key in source code would leak through git history | Move secrets to `.env` locally and GitHub Secrets in CI, and rotate the key |

---

## Roadmap

- [ ] Enable the **timely cron schedule** in GitHub Actions for the season
- [ ] Connect **Power BI** to Azure SQL and build EDA dashboards
- [ ] Keep **history**: date-partitioned Parquet paths (`/yyyy/mm/dd/`) and append-mode snapshots instead of full replace
- [ ] Add **data quality checks** (row counts, nulls, schema validation) before loading
- [ ] Add **retry with backoff** for source and database connections
- [ ] Move to **Azure Key Vault + Managed Identity** (`DefaultAzureCredential`) so no keys are needed
- [ ] Introduce a **medallion layout** (bronze/silver/gold) and **dbt** models for transformations
- [ ] Add unit tests for the scrapers with saved HTML fixtures

---

<div align="center">

**Built by [Sulara Perera](https://github.com/sularaperera)** · Data & Automation Engineer · Auckland, NZ 🇳🇿

⭐ If you found this project useful, consider giving it a star!

</div>
