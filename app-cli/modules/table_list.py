"""
Table List Module - Extract table information from BigQuery datasets to CSV.
"""

import csv
from datetime import datetime
from typing import List, Dict, Any

from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

from . import get_project_id, log

def get_output_filename(dataset: str, output_arg: str = None) -> str:
    """Generate output filename."""
    if output_arg:
        return output_arg
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{dataset}_tables_{timestamp}.csv"

def extract_table_info(client: bigquery.Client, project_id: str, dataset: str, include_views: bool = False, verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Extract table information using BigQuery INFORMATION_SCHEMA.
    
    Args:
        client: BigQuery client
        project_id: Project ID
        dataset: Dataset name
        include_views: Whether to include views
        verbose: Enable verbose output
    
    Returns:
        List of dictionaries containing table information
    """
    
    # Build the query based on requirements
    table_types = "'BASE TABLE'"
    if include_views:
        table_types += ", 'VIEW'"
    
    # First get basic table information
    query = f"""
    SELECT
      table_schema AS schema,
      table_type AS object_type,
      table_name AS name,
      'No' AS primary_keys
    FROM `{project_id}.{dataset}.INFORMATION_SCHEMA.TABLES`
    WHERE table_type IN ({table_types})
    ORDER BY table_name
    """
    
    try:
        log(f"Executing query on dataset: {project_id}.{dataset}", verbose)
        query_job = client.query(query)
        results = query_job.result()
        
        table_info = []
        for row in results:
            table_info.append({
                'schema': row.schema,
                'object_type': row.object_type,
                'name': row.name,
                'primary_keys': row.primary_keys,
                'row_count': 0  # Will be updated below
            })
        
        # Now get row counts for each table
        log(f"Getting row counts for {len(table_info)} tables...", verbose)
        for i, table in enumerate(table_info):
            try:
                table_ref = f"{project_id}.{dataset}.{table['name']}"
                table_obj = client.get_table(table_ref)
                table_info[i]['row_count'] = table_obj.num_rows if table_obj.num_rows else 0
                log(f"  {i+1}/{len(table_info)}: {table['name']} = {table_info[i]['row_count']:,} rows", verbose)
            except Exception as e:
                log(f"  {i+1}/{len(table_info)}: {table['name']} - Error getting row count: {e}", verbose)
                table_info[i]['row_count'] = 0
        
        return table_info
        
    except NotFound as e:
        print(f"❌ Dataset not found: {project_id}.{dataset}")
        return []
    except BadRequest as e:
        print(f"❌ Bad request: {e}")
        return []
    except Exception as e:
        print(f"❌ Error executing query: {e}")
        return []

def write_to_csv(table_info: List[Dict[str, Any]], output_file: str):
    """Write table information to CSV file."""
    
    if not table_info:
        print("⚠️  No tables found to export")
        return
    
    fieldnames = ['schema', 'object_type', 'name', 'primary_keys', 'row_count']
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(table_info)
        
        print(f"✅ Successfully exported {len(table_info)} tables to {output_file}")
        
    except Exception as e:
        print(f"❌ Error writing CSV file: {e}")

def print_summary(table_info: List[Dict[str, Any]], dataset: str):
    """Print summary of extracted table information."""
    
    if not table_info:
        print("📊 No tables found in dataset")
        return
    
    tables_count = len([t for t in table_info if t['object_type'] == 'BASE TABLE'])
    views_count = len([t for t in table_info if t['object_type'] == 'VIEW'])
    with_pk = len([t for t in table_info if t['primary_keys'] == 'Yes'])
    total_rows = sum(t['row_count'] for t in table_info if t['row_count'])
    
    print(f"\n📊 Dataset Summary: {dataset}")
    print(f"  Tables: {tables_count}")
    print(f"  Views: {views_count}")
    print(f"  With Primary Keys: {with_pk}")
    print(f"  Total Rows: {total_rows:,}")

def main(args):
    """Main function for table-list command."""
    # Get configuration
    project_id = get_project_id(args.project)
    dataset = args.dataset
    output_file = get_output_filename(dataset, args.output)
    
    print(f"🚀 Extracting table information from {project_id}.{dataset}")
    print(f"📄 Output file: {output_file}")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=project_id)
        log(f"Connected to BigQuery project: {project_id}", args.verbose)
    except Exception as e:
        print(f"❌ Error connecting to BigQuery: {e}")
        return 1
    
    # Extract table information
    log("Extracting table information...", args.verbose)
    table_info = extract_table_info(client, project_id, dataset, args.include_views, args.verbose)
    
    # Write to CSV
    log("Writing to CSV...", args.verbose)
    write_to_csv(table_info, output_file)
    
    # Print summary
    print_summary(table_info, dataset)
    
    print(f"\n🏁 Extraction complete!")
    return 0
