import time
import os
from datetime import datetime
from google.cloud import bigquery
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Config - read from environment variables
project_id = os.getenv('PROJECT_ID', 'your-default-gcp-proj-id')
print(f"Project ID: {project_id}")
metadata_table = os.getenv('METADATA_TABLE', 'governance_metadata.your-dataset-name')
print(f"Metadata Table: {metadata_table}")
job_run_table = os.getenv('JOB_RUN_TABLE', 'governance_metadata.job_runs')
print(f"Job Run Table: {job_run_table}")
sleep_seconds = int(os.getenv('SLEEP_SECONDS', '2'))  # delay between ALTER commands to avoid rate limit
print(f"Sleep Seconds: {sleep_seconds}")

def update_column_descriptions():
    client = bigquery.Client(project=project_id)

    timestamp = datetime.utcnow().isoformat()
    job_run_id = f"job_{timestamp.replace(':', '-')}"

    # Step 0: Fetch all metadata rows
    metadata_query = f"""
    SELECT
      table_name,
      column_name,
      column_metadata,
      target_dataset_name
    FROM `{metadata_table}`
    """
    metadata_rows = list(client.query(metadata_query).result())

    success, error, unmatched = 0, 0, 0
    results_to_log = []

    for row in metadata_rows:
        table = row.table_name
        column = row.column_name
        description = row.column_metadata.replace('"', '\\"')
        target_dataset = row.target_dataset_name
        status = ""

        # Check if the column exists in the target dataset/table
        check_query = f"""
        SELECT 1 FROM `{project_id}.{target_dataset}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
          AND TRIM(UPPER(column_name)) = TRIM(UPPER('{column}'))
        LIMIT 1
        """
        check_result = list(client.query(check_query).result())

        if check_result:
            # Column exists, try to update
            sql = f"""
            ALTER TABLE `{project_id}.{target_dataset}.{table}`
            ALTER COLUMN `{column}`
            SET OPTIONS (description = "{description}")
            """
            try:
                client.query(sql).result()
                success += 1
                status = "updated"
                print(f"✅ Updated {target_dataset}.{table}.{column}")
            except Exception as e:
                error += 1
                status = "error"
                print(f"❌ Failed {target_dataset}.{table}.{column} – {e}")
        else:
            unmatched += 1
            status = "unmatched"
            print(f"⚠️ Unmatched: {target_dataset}.{table}.{column}")

        results_to_log.append({
            "job_run_id": job_run_id,
            "timestamp": timestamp,
            "status": status,
            "table_name": table,
            "column_name": column,
            "column_metadata": row.column_metadata,
            "target_dataset": target_dataset
        })
        time.sleep(sleep_seconds)

    # Step 2: Write job run results to BigQuery
    print(f"\n📋 Writing {len(results_to_log)} log records into {job_run_table}...")
    errors = client.insert_rows_json(job_run_table, results_to_log)

    if errors:
        print(f"⚠️ Errors occurred while logging to BigQuery: {errors}")
    else:
        print(f"✅ Log successfully written.")

    print("\n✅ Run Summary:")
    print(f"  Updated columns: {success}")
    print(f"  Failed columns: {error}")
    print(f"  Unmatched columns: {unmatched}")
    print(f"  Job Run ID: {job_run_id}")

if __name__ == "__main__":
    update_column_descriptions()