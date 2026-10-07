import time

from scrape import league_table, top_scorers
from api_ingest import premier_league_teams
from push_to_azure_blob import to_blob
from push_to_azure_sql import get_engine, to_sql

functions = [league_table, top_scorers, premier_league_teams]
pipeline_start = time.time()

print("=" * 50)
print("Pipeline started")
print("=" * 50)

print("\n[Setup] Creating Azure SQL engine...")
engine = get_engine()
print("[Setup] Azure SQL engine ready")

for step, func in enumerate(functions, start=1):
    name = func.__name__
    print(f"\n[Step {step}/{len(functions)}] {name}")

    print(f"  -> Running {name} and uploading to Azure Blob Storage...")
    start = time.time()
    to_blob(func)
    print(f"  -> Blob upload completed ({time.time() - start:.1f}s)")

    print(f"  -> Running {name} and loading to Azure SQL...")
    start = time.time()
    to_sql(func, engine)
    print(f"  -> SQL load completed ({time.time() - start:.1f}s)")

    print(f"[Step {step}/{len(functions)}] {name} completed")

print("\n" + "=" * 50)
print(f"Pipeline finished in {time.time() - pipeline_start:.1f}s")
print("=" * 50)
