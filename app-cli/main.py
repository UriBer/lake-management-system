#!/usr/bin/env python3
"""
Update BigQuery column descriptions from a metadata table.

Environment variables (via .env or exported):
    PROJECT_ID        – target GCP project
    METADATA_TABLE    – fully-qualified metadata table, e.g. governance_metadata.system_metadata
    JOB_RUN_TABLE     – fully-qualified log table, e.g. governance_metadata.job_runs
    SLEEP_MSECONDS    – optional back-off between DDL statements (default 1000 ms)
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from google.api_core.exceptions import NotFound, BadRequest
from google.cloud import bigquery

# --------------------------------------------------------------------------- #
# Configuration & CLI
# --------------------------------------------------------------------------- #
load_dotenv()                               # ① read .env

parser = argparse.ArgumentParser(
    description="Update BigQuery column descriptions from metadata table")
parser.add_argument("--log", action="store_true",
                    help="also write a local log file")
args = parser.parse_args()

PROJECT_ID     = os.getenv("PROJECT_ID")
METADATA_TABLE = os.getenv("METADATA_TABLE")
JOB_RUN_TABLE  = os.getenv("JOB_RUN_TABLE")
SLEEP_MS       = int(os.getenv("SLEEP_MSECONDS", "1000"))

if not (PROJECT_ID and METADATA_TABLE and JOB_RUN_TABLE):
    sys.exit("❌  PROJECT_ID / METADATA_TABLE / JOB_RUN_TABLE must be set "
             "(export or put in .env)")

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def write(msg: str):
    """Print and optionally append to local log file."""
    print(msg)
    if args.log:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{now_iso()}  {msg}\n")

# --------------------------------------------------------------------------- #
# Main routine
# --------------------------------------------------------------------------- #
def update_column_descriptions() -> None:
    client = bigquery.Client(project=PROJECT_ID)

    # Make log file once we know the run-id
    run_id   = f"job_{now_iso().replace(':', '-')}"
    if args.log:
        global log_path     # noqa: PLW0603
        log_path = f"column_updates_{run_id}.log"
        write(f"📝  Local log enabled → {log_path}")

    write(f"🚀  Starting column-description sync (run-id {run_id})")
    write(f"📑  Metadata table  : {METADATA_TABLE}")
    write(f"📑  Job-run table   : {JOB_RUN_TABLE}")
    write(f"⏱️   Sleep between DDL: {SLEEP_MS} ms\n")

    # 1️⃣  Pull metadata rows (keep dataset WITHOUT project prefix)
    metadata_sql = f"""
        SELECT
            target_dataset_name AS dataset_name,
            table_name,
            column_name,
            column_metadata AS description
        FROM `{METADATA_TABLE}`
    """
    metadata_rows = list(client.query(metadata_sql).result())

    stats = {"updated": 0, "skipped": 0,
             "unmatched": 0, "error": 0}
    log_rows = []

    for row in metadata_rows:
        dataset   = row.dataset_name          # e.g. bronze_isv   (no project id)
        table     = row.table_name
        column    = row.column_name
        desc      = (row.description or "").strip()
        table_ref = f"{PROJECT_ID}.{dataset}.{table}"
        full_path = f"{table_ref}.{column}"

        try:
            bq_table = client.get_table(table_ref)        # may raise NotFound
        except NotFound:
            stats["unmatched"] += 1
            write(f"⚠️  Unmatched table   {table_ref}")
            continue
        except Exception as e:                            # network/auth etc.
            stats["error"] += 1
            write(f"❌  Error reading {table_ref}  →  {e}")
            continue

        # Locate the field
        field = next((f for f in bq_table.schema
                      if f.name.upper() == column.upper()), None)
        if field is None:
            stats["unmatched"] += 1
            write(f"⚠️  Unmatched column  {full_path}")
            continue

        if (field.description or "") == desc:
            stats["skipped"] += 1
            write(f"ℹ️  Skipped (no diff) {full_path}")
            status = "skipped"
        else:
            # Use query parameters to avoid quote-escaping headaches
            sql = f"""
                ALTER TABLE `{table_ref}`
                ALTER COLUMN `{column}`
                SET OPTIONS (description = @desc)
            """
            job_cfg = bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter(
                    "desc", "STRING", desc)]
            )
            try:
                client.query(sql, job_config=job_cfg).result()
                stats["updated"] += 1
                write(f"✅  Updated          {full_path}")
                status = "updated"
            except BadRequest as e:                       # malformed DDL
                stats["error"] += 1
                write(f"❌  BadRequest on {full_path}  →  {e.message}")
                status = "error"
            except Exception as e:
                stats["error"] += 1
                write(f"❌  Failed {full_path}  →  {e}")
                status = "error"

            # polite back-off
            time.sleep(SLEEP_MS / 1000)

        # Log row for job-run table
        log_rows.append({
            "job_run_id"     : run_id,
            "timestamp"      : now_iso(),
            "status"         : status,
            "table_name"     : table,
            "column_name"    : column,
            "column_metadata": desc,
            "target_dataset" : dataset,
        })

    # 2️⃣  Persist run summary
    write("\n📋  Writing job-run log to BigQuery …")
    errors = client.insert_rows_json(JOB_RUN_TABLE, log_rows)
    if errors:
        write(f"⚠️  BQ insert errors: {errors}")
    else:
        write("✅  Log written successfully")

    # 3️⃣  Final stats
    write("\n🏁  Run complete")
    for k, v in stats.items():
        write(f"   {k.capitalize():9}: {v}")
    write( "   Run-id     : " + run_id)


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    try:
        update_column_descriptions()
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user; exiting")
        sys.exit(130)