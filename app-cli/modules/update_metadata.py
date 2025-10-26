"""
Update Metadata Module - Update column descriptions from metadata table.
"""

import os
import sys
import time
from datetime import datetime, timezone
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

from . import get_project_id, log

def get_config():
    """Get configuration from environment variables."""
    project_id = get_project_id()
    metadata_table = os.getenv("METADATA_TABLE")
    job_run_table = os.getenv("JOB_RUN_TABLE")
    sleep_ms = int(os.getenv("SLEEP_MSECONDS", "500"))
    max_workers = int(os.getenv("MAX_PARALLEL_WORKERS", "10"))
    
    if not all([metadata_table, job_run_table]):
        sys.exit("❌ METADATA_TABLE / JOB_RUN_TABLE must be set in .env file")
    
    return project_id, metadata_table, job_run_table, sleep_ms, max_workers

def now_iso():
    """Get current time in ISO format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def write_log(msg, log_file=None):
    """Write message to console and optionally to log file."""
    print(msg)
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{now_iso()}  {msg}\n")

def process_table(client, project_id, dataset, table, columns, sleep_ms, run_id):
    """Process a single table to update column descriptions."""
    table_ref = f"{project_id}.{dataset}.{table}"
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
                if sleep_ms: 
                    time.sleep(sleep_ms / 1000)
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

def main(args):
    """Main function for update-metadata command."""
    # Get configuration
    project_id, metadata_table, job_run_table, sleep_ms, max_workers = get_config()
    
    start_time = time.time()
    client = bigquery.Client(project=project_id)
    run_id = f"job_{now_iso().replace(':', '-')}"
    
    log_file = None
    if args.log:
        log_file = f"column_updates_{run_id}.log"
        write_log(f"📝 Logging to {log_file}", log_file)

    write_log(f"🚀 Starting run : {run_id}", log_file)
    write_log(f"📄 Metadata     : {metadata_table}", log_file)
    write_log(f"📄 Log          : {job_run_table}", log_file)

    # Get metadata from the metadata table
    sql = f"""
        SELECT target_dataset_name AS dataset_name,
               table_name, column_name, column_metadata AS description
        FROM `{metadata_table}`
        WHERE column_metadata IS NOT NULL
    """
    
    try:
        rows = list(client.query(sql).result())
    except Exception as e:
        write_log(f"❌ Error querying metadata table: {e}", log_file)
        return 1
    
    total_columns = len(rows)

    # Group by dataset and table
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r.dataset_name, r.table_name)].append((r.column_name, r.description.strip()))

    stats = {"updated": 0, "skipped": 0, "unmatched": 0, "error": 0}
    log_rows = []

    # Process tables in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(process_table, client, project_id, ds, tb, cols, sleep_ms, run_id): (ds, tb) 
            for (ds, tb), cols in grouped.items()
        }
        
        for f in as_completed(futures):
            logs, st, jobs = f.result()
            for line in logs: 
                write_log(line, log_file)
            for k in stats: 
                stats[k] += st.get(k, 0)
            log_rows.extend(jobs)

    # Write job log to BigQuery
    write_log("\n📥 Writing job log to BigQuery …", log_file)
    if client.insert_rows_json(job_run_table, log_rows):
        write_log("⚠️ Failed writing logs!", log_file)
    else:
        write_log("✅ Log written.", log_file)

    # Print summary
    end = time.time()
    duration = end - start_time
    write_log("\n🏁 Run complete:", log_file)
    for k, v in stats.items():
        write_log(f"  {k.capitalize():9}: {v}", log_file)
    write_log(f"  Total columns : {total_columns}", log_file)
    write_log(f"  Run ID        : {run_id}", log_file)
    write_log(f"  Duration      : {duration:.2f} sec ({duration/60:.2f} min)", log_file)

    return 0
