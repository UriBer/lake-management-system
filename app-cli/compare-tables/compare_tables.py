
import os
from google.cloud import bigquery
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

audit_project = os.getenv("PROJECT_ID")
audit_dataset = "audit_dataset"
audit_table = "table_between_envs"

# Initialize BigQuery clients
preprod_client = bigquery.Client(project=os.getenv("PROJECT_ID"))
prod_client = bigquery.Client(project="dgt-gcp-moe-dlk-data-prod")

output_path = "table_comparison.txt"

def get_all_tables(client):
    tables = set()
    for dataset in client.list_datasets():
        dataset_id = dataset.dataset_id
        for table in client.list_tables(dataset_id):
            tables.add((dataset_id, table.table_id))
    return tables

# Fetch tables
preprod_tables = get_all_tables(preprod_client)
prod_tables = get_all_tables(prod_client)

only_in_preprod = preprod_tables - prod_tables
only_in_prod = prod_tables - preprod_tables
in_both = preprod_tables & prod_tables

run_time = datetime.utcnow().isoformat()
rows_for_bq = []

with open(output_path, "w") as f:
    f.write("✅ Tables in both:\n")
    for dataset_id, table_id in sorted(in_both):
        f.write(f"{dataset_id}.{table_id}\n")
        rows_for_bq.append({
            "run_time": run_time,
            "dataset": dataset_id,
            "table_name": table_id,
            "status": "in both"
        })

    f.write("\n❌ Only in preprod:\n")
    for dataset_id, table_id in sorted(only_in_preprod):
        f.write(f"{dataset_id}.{table_id}\n")
        rows_for_bq.append({
            "run_time": run_time,
            "dataset": dataset_id,
            "table_name": table_id,
            "status": "only in preprod"
        })

    f.write("\n❌ Only in prod:\n")
    for dataset_id, table_id in sorted(only_in_prod):
        f.write(f"{dataset_id}.{table_id}\n")
        rows_for_bq.append({
            "run_time": run_time,
            "dataset": dataset_id,
            "table_name": table_id,
            "status": "only in prod"
        })

# Define and create table if not exists
table_ref = f"{audit_project}.{audit_dataset}.{audit_table}"
schema = [
    bigquery.SchemaField("run_time", "TIMESTAMP"),
    bigquery.SchemaField("dataset", "STRING"),
    bigquery.SchemaField("table_name", "STRING"),
    bigquery.SchemaField("status", "STRING")
]

try:
    preprod_client.get_table(table_ref)
except:
    table = bigquery.Table(table_ref, schema=schema)
    preprod_client.create_table(table)

# Insert into BigQuery
errors = preprod_client.insert_rows_json(table_ref, rows_for_bq)
if errors:
    print("Errors while inserting:", errors)
else:
    print(f"✅ Exported {len(rows_for_bq)} rows to {table_ref}")
    print(f"📄 Comparison saved to: {output_path}")
