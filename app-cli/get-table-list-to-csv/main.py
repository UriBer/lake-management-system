#!/usr/bin/env python3
"""
BigQuery Table List Extractor to CSV

Extracts table information from a specific BigQuery dataset and exports to CSV.
Includes schema, object type, table name, primary keys status, and row count.
"""

import os
import sys
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

# Load environment variables
load_dotenv()

def setup_cli():
    """Setup command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Extract BigQuery table information to CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --dataset my_dataset
  python main.py --dataset my_dataset --project my-project-id
  python main.py --dataset my_dataset --output tables.csv
  python main.py --dataset my_dataset --include-views
        """
    )
    
    parser.add_argument(
        "--dataset", 
        required=True,
        help="BigQuery dataset name to extract tables from"
    )
    
    parser.add_argument(
        "--project",
        help="BigQuery project ID (defaults to PROJECT_ID from .env)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output CSV file path (defaults to dataset_tables_YYYYMMDD_HHMMSS.csv)"
    )
    
    parser.add_argument(
        "--include-views",
        action="store_true",
        help="Include views in addition to tables"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()

def get_project_id(args) -> str:
    """Get project ID from args or environment."""
    if args.project:
        return args.project
    
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        sys.exit("❌ PROJECT_ID must be set in .env file or provided via --project")
    
    return project_id

def get_output_filename(dataset: str, args) -> str:
    """Generate output filename."""
    if args.output:
        return args.output
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{dataset}_tables_{timestamp}.csv"

def log(message: str, verbose: bool = False):
    """Print message if verbose mode is enabled."""
    if verbose:
        print(f"ℹ️  {message}")

def extract_table_info(client: bigquery.Client, project_id: str, dataset: str, include_views: bool = False) -> List[Dict[str, Any]]:
    """
    Extract table information using BigQuery INFORMATION_SCHEMA.
    
    Args:
        client: BigQuery client
        project_id: Project ID
        dataset: Dataset name
        include_views: Whether to include views
    
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
        log(f"Executing query on dataset: {project_id}.{dataset}")
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
        log(f"Getting row counts for {len(table_info)} tables...")
        for i, table in enumerate(table_info):
            try:
                table_ref = f"{project_id}.{dataset}.{table['name']}"
                table_obj = client.get_table(table_ref)
                table_info[i]['row_count'] = table_obj.num_rows if table_obj.num_rows else 0
                log(f"  {i+1}/{len(table_info)}: {table['name']} = {table_info[i]['row_count']:,} rows")
            except Exception as e:
                log(f"  {i+1}/{len(table_info)}: {table['name']} - Error getting row count: {e}")
                table_info[i]['row_count'] = 0
        
        return table_info
        
    except NotFound as e:
        sys.exit(f"❌ Dataset not found: {project_id}.{dataset}")
    except BadRequest as e:
        sys.exit(f"❌ Bad request: {e}")
    except Exception as e:
        sys.exit(f"❌ Error executing query: {e}")

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
        sys.exit(f"❌ Error writing CSV file: {e}")

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

def main():
    """Main function."""
    args = setup_cli()
    
    # Get configuration
    project_id = get_project_id(args)
    dataset = args.dataset
    output_file = get_output_filename(dataset, args)
    
    print(f"🚀 Extracting table information from {project_id}.{dataset}")
    print(f"📄 Output file: {output_file}")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=project_id)
        log(f"Connected to BigQuery project: {project_id}")
    except Exception as e:
        sys.exit(f"❌ Error connecting to BigQuery: {e}")
    
    # Extract table information
    log("Extracting table information...")
    table_info = extract_table_info(client, project_id, dataset, args.include_views)
    
    # Write to CSV
    log("Writing to CSV...")
    write_to_csv(table_info, output_file)
    
    # Print summary
    print_summary(table_info, dataset)
    
    print(f"\n🏁 Extraction complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)