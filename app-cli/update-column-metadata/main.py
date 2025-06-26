#!/usr/bin/env python3
"""
Parallelized BigQuery column description updater with execution timer.
"""

import os, sys, time, argparse
from datetime import datetime, timezone
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

# Load .env
load_dotenv()

# CLI
parser = argparse.ArgumentParser()
parser.add_argument("--log", action="store_true", help="write local log")
args = parser.parse_args()

# Config
PROJECT_ID     = os.getenv("PROJECT_ID")
METADATA_TABLE = os.getenv("METADATA_TABLE")
JOB_RUN_TABLE  = os.getenv("JOB_RUN_TABLE")
SLEEP_MS       = int(os.getenv("SLEEP_MSECONDS", "1000"))
MAX_WORKERS    = int(os.getenv("MAX_PARALLEL_WORKERS", "5"))

if not all([PROJECT_ID, METADATA_TABLE, JOB_RUN_TABLE]):
    sys.exit("❌ PROJECT_ID / METADATA_TABLE / JOB_RUN_TABLE must be set")

def now_iso(): return datetime.now(timezone.utc).isoformat(timespec="seconds")

def write(msg):
    print(msg)
    if args.log:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{now_iso()}  {msg}\n")

def update_column_descriptions():
    start_time = time.time()
    client = bigquery.Client(project=PROJECT_ID)
    run_id = f"job_{now_iso().replace(':', '-')}"
    if args.log:
        global log_path
        log_path = f"column_updates_{run_id}.log"
        write(f"📝 Logging to {log_path}")

    write(f"🚀 Starting run {run_id}")
    write(f"📄 Metadata: {METADATA_TABLE}")
    write(f"📄 Log     : {JOB_RUN_TABLE}")

    sql = f"""
        SELECT target_dataset_name AS dataset_name,
               table_name, column_name, column_metadata AS description
        FROM `{METADATA_TABLE}`
        WHERE column_metadata IS NOT NULL
    """
    rows = list(client.query(sql).result())
    total_columns = len(rows)

    grouped = defaultdict(list)
    for r in rows:
        grouped[(r.dataset_name, r.table_name)].append((r.column_name, r.description.strip()))

    stats = {"updated": 0, "skipped": 0, "unmatched": 0, "error": 0}
    log_rows = []

    def process_table(dataset, table, columns):
        table_ref = f"{PROJECT_ID}.{dataset}.{table}"
        lines, partial_stats, job_log = [], {"updated": 0, "skipped": 0, "unmatched": 0, "error": 0}, []

        try:
            schema = client.get_table(table_ref).schema
        except NotFound:
            partial_stats["unmatched"] += len(columns)
            lines.append(f"⚠️ Table not found: {table_ref}")
            return lines, partial_stats, job_log
        except Exception as e:
            partial_stats["error"] += len(columns)
            lines.append(f"❌ Error fetching {table_ref}: {e}")
            return lines, partial_stats, job_log

        field_map = {f.name.lower(): f for f in schema}
        for col, desc in columns:
            col_ref = f"{table_ref}.{col}"
            f = field_map.get(col.lower())
            if not f:
                partial_stats["unmatched"] += 1
                lines.append(f"⚠️ Column not found: {col_ref}")
                status = "unmatched"
            elif (f.description or "").strip() == desc:
                partial_stats["skipped"] += 1
                lines.append(f"ℹ️ Skipped: {col_ref}")
                status = "skipped"
            else:
                sql = f"ALTER TABLE `{table_ref}` ALTER COLUMN `{col}` SET OPTIONS (description = @desc)"
                cfg = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("desc", "STRING", desc)])
                try:
                    client.query(sql, job_config=cfg).result()
                    partial_stats["updated"] += 1
                    lines.append(f"✅ Updated: {col_ref}")
                    status = "updated"
                    if SLEEP_MS: time.sleep(SLEEP_MS / 1000)
                except BadRequest as e:
                    partial_stats["error"] += 1
                    lines.append(f"❌ BadRequest {col_ref}: {e.message}")
                    status = "error"
                except Exception as e:
                    partial_stats["error"] += 1
                    lines.append(f"❌ Failed {col_ref}: {e}")
                    status = "error"

            job_log.append({
                "job_run_id": run_id,
                "timestamp": now_iso(),
                "status": status,
                "table_name": table,
                "column_name": col,
                "column_metadata": desc,
                "target_dataset": dataset,
            })

        return lines, partial_stats, job_log

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(process_table, ds, tb, cols): (ds, tb) for (ds, tb), cols in grouped.items()}
        for f in as_completed(futures):
            logs, st, jobs = f.result()
            for line in logs: write(line)
            for k in stats: stats[k] += st.get(k, 0)
            log_rows.extend(jobs)

    write("\n📥 Writing job log to BigQuery …")
    if client.insert_rows_json(JOB_RUN_TABLE, log_rows):
        write("⚠️ Failed writing logs!")
    else:
        write("✅ Log written.")

    end = time.time()
    duration = end - start_time
    write("\n🏁 Run complete:")
    for k, v in stats.items():
        write(f"  {k.capitalize():9}: {v}")
    write(f"  Total columns : {total_columns}")
    write(f"  Run ID        : {run_id}")
    write(f"  Duration      : {duration:.2f} sec ({duration/60:.2f} min)")

if __name__ == "__main__":
    try:
        update_column_descriptions()
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted.")
        sys.exit(130)