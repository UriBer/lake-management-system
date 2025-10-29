#!/usr/bin/env python3
"""
Dataset Hierarchy Analysis Module

Analyzes all datasets in a BigQuery project, providing:
- Complete dataset hierarchy
- Table counts per dataset
- Row counts per table (from metadata)
- Change detection between runs
- Comprehensive logging for comparison
- BigQuery table persistence with LDTS and batch_id
"""

import os
import sys
import json
import uuid
import argparse
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_project_id(project_arg: Optional[str] = None) -> str:
    """Get project ID from argument or environment."""
    if project_arg:
        return project_arg
    
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        print("❌ PROJECT_ID must be set in .env file or provided via --project")
        sys.exit(1)
    
    return project_id

def analyze_table(client: bigquery.Client, project_id: str, dataset_id: str, table_item: Any, 
                  include_views: bool) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Analyze a single table.
    
    Args:
        client: BigQuery client
        project_id: Project ID
        dataset_id: Dataset ID
        table_item: Table list item from BigQuery
        include_views: Whether to include views
    
    Returns:
        Tuple of (table_id, table_info_dict) or (None, None) if skipped
    """
    table_id = table_item.table_id
    table_type = table_item.table_type
    
    # Skip views if not requested
    if table_type == "VIEW" and not include_views:
        return None, None
    
    table_info = {
        "table_id": table_id,
        "table_type": table_type,
        "created": getattr(table_item, 'created', None),
        "modified": getattr(table_item, 'modified', None),
        "row_count": 0,
        "size_bytes": 0,
        "num_bytes": 0,
        "num_long_term_bytes": 0
    }
    
    # Convert datetime objects to ISO format if they exist
    if table_info["created"]:
        table_info["created"] = table_info["created"].isoformat()
    if table_info["modified"]:
        table_info["modified"] = table_info["modified"].isoformat()
    
    try:
        # Get detailed table information
        table_ref = f"{project_id}.{dataset_id}.{table_id}"
        table_obj = client.get_table(table_ref)
        
        # Get row count from metadata
        table_info["row_count"] = getattr(table_obj, 'num_rows', 0) if getattr(table_obj, 'num_rows', None) else 0
        table_info["size_bytes"] = getattr(table_obj, 'num_bytes', 0) if getattr(table_obj, 'num_bytes', None) else 0
        table_info["num_bytes"] = getattr(table_obj, 'num_bytes', 0) if getattr(table_obj, 'num_bytes', None) else 0
        table_info["num_long_term_bytes"] = getattr(table_obj, 'num_long_term_bytes', 0) if getattr(table_obj, 'num_long_term_bytes', None) else 0
        
    except Exception as e:
        print(f"      ⚠️  Error analyzing {table_type} {table_id}: {e}")
        table_info["error"] = str(e)
    
    return table_id, table_info

def analyze_dataset(client: bigquery.Client, project_id: str, dataset_item: Any, 
                    include_views: bool, max_workers: int, 
                    summary_lock: threading.Lock, global_summary: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Analyze a single dataset and all its tables (in parallel).
    
    Args:
        client: BigQuery client
        project_id: Project ID
        dataset_item: Dataset list item from BigQuery
        include_views: Whether to include views
        max_workers: Maximum parallel workers for table processing
        summary_lock: Thread lock for summary updates
        global_summary: Global summary dictionary to update
    
    Returns:
        Tuple of (dataset_id, dataset_info_dict)
    """
    dataset_id = dataset_item.dataset_id
    print(f"  📁 Analyzing dataset: {dataset_id}")
    
    dataset_info = {
        "dataset_id": dataset_id,
        "location": getattr(dataset_item, 'location', 'Unknown'),
        "created": getattr(dataset_item, 'created', None),
        "modified": getattr(dataset_item, 'modified', None),
        "tables": {},
        "summary": {
            "total_tables": 0,
            "total_views": 0,
            "total_rows": 0
        }
    }
    
    # Convert datetime objects to ISO format if they exist
    if dataset_info["created"]:
        dataset_info["created"] = dataset_info["created"].isoformat()
    if dataset_info["modified"]:
        dataset_info["modified"] = dataset_info["modified"].isoformat()
    
    try:
        # Get all tables/views in dataset
        tables = list(client.list_tables(dataset_id))
        
        # Process tables in parallel
        tables_to_process = [t for t in tables if include_views or t.table_type != "VIEW"]
        
        if tables_to_process:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all table analysis tasks
                future_to_table = {
                    executor.submit(analyze_table, client, project_id, dataset_id, table, include_views): table
                    for table in tables_to_process
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_table):
                    try:
                        table_id, table_info = future.result()
                        if table_id and table_info:
                            dataset_info["tables"][table_id] = table_info
                            table_type = table_info["table_type"]
                            row_count = table_info["row_count"]
                            
                            # Update dataset summary
                            if table_type == "TABLE":
                                dataset_info["summary"]["total_tables"] += 1
                            elif table_type == "VIEW":
                                dataset_info["summary"]["total_views"] += 1
                            
                            dataset_info["summary"]["total_rows"] += row_count
                            
                            # Update global summary with lock
                            with summary_lock:
                                if table_type == "TABLE":
                                    global_summary["total_tables"] += 1
                                elif table_type == "VIEW":
                                    global_summary["total_views"] += 1
                                global_summary["total_rows"] += row_count
                            
                            print(f"      ✅ {table_type}: {table_id} - {row_count:,} rows")
                    except Exception as e:
                        table_item = future_to_table[future]
                        print(f"      ⚠️  Error processing table {table_item.table_id}: {e}")
        
        print(f"  ✅ Dataset {dataset_id}: {dataset_info['summary']['total_tables']} tables, {dataset_info['summary']['total_views']} views, {dataset_info['summary']['total_rows']:,} rows")
        
    except Exception as e:
        print(f"  ❌ Error analyzing dataset {dataset_id}: {e}")
        dataset_info["error"] = str(e)
    
    return dataset_id, dataset_info

def analyze_dataset_hierarchy(client: bigquery.Client, project_id: str, include_views: bool = False, max_workers: Optional[int] = None) -> Dict[str, Any]:
    """
    Analyze complete dataset hierarchy for a project with parallel processing.
    
    Args:
        client: BigQuery client
        project_id: Project ID to analyze
        include_views: Whether to include views in analysis
        max_workers: Maximum parallel workers (defaults to MAX_PARALLEL_WORKERS from env or 10)
    
    Returns:
        Dictionary containing complete hierarchy analysis
    """
    print(f"🔍 Analyzing dataset hierarchy for project: {project_id}")
    
    # Get max workers from environment or use default
    if max_workers is None:
        max_workers = int(os.getenv("MAX_PARALLEL_WORKERS", "10"))
    
    print(f"🚀 Using {max_workers} parallel workers")
    
    hierarchy = {
        "project_id": project_id,
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "datasets": {},
        "summary": {
            "total_datasets": 0,
            "total_tables": 0,
            "total_views": 0,
            "total_rows": 0
        }
    }
    
    # Thread lock for updating global summary
    summary_lock = threading.Lock()
    global_summary = hierarchy["summary"]
    
    try:
        # Get all datasets
        datasets = list(client.list_datasets())
        hierarchy["summary"]["total_datasets"] = len(datasets)
        
        print(f"📊 Found {len(datasets)} datasets")
        
        # Process datasets in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all dataset analysis tasks
            future_to_dataset = {
                executor.submit(analyze_dataset, client, project_id, dataset, include_views, max_workers, summary_lock, global_summary): dataset
                for dataset in datasets
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_dataset):
                try:
                    dataset_id, dataset_info = future.result()
                    if dataset_id and dataset_info:
                        hierarchy["datasets"][dataset_id] = dataset_info
                except Exception as e:
                    dataset_item = future_to_dataset[future]
                    print(f"  ❌ Error processing dataset {dataset_item.dataset_id}: {e}")
        
        print(f"🎯 Analysis complete: {hierarchy['summary']['total_datasets']} datasets, {hierarchy['summary']['total_tables']} tables, {hierarchy['summary']['total_views']} views, {hierarchy['summary']['total_rows']:,} total rows")
        
    except Exception as e:
        print(f"❌ Error analyzing project {project_id}: {e}")
        hierarchy["error"] = str(e)
    
    return hierarchy

def _bytes_to_human(num_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    idx = 0
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1
    if idx == 0:
        return f"{int(size)} {units[idx]}"
    return f"{size:.2f} {units[idx]}"

def print_hierarchy_tree(hierarchy: Dict[str, Any], max_tables_per_dataset: Optional[int] = None) -> None:
    """Pretty-print the hierarchy in a tree format for human review."""
    print("\n" + "="*80)
    print("📚 DATASET HIERARCHY (TREE VIEW)")
    print("="*80)
    summary = hierarchy.get("summary", {})
    print(f"Project: {hierarchy.get('project_id')}")
    print(f"Datasets: {summary.get('total_datasets', 0)} | Tables: {summary.get('total_tables', 0)} | Views: {summary.get('total_views', 0)} | Rows: {summary.get('total_rows', 0):,}")
    print()
    
    datasets = hierarchy.get("datasets", {})
    for dataset_id in sorted(datasets.keys()):
        ds = datasets[dataset_id]
        ds_sum = ds.get("summary", {})
        print(f"📁 {dataset_id}  (tables: {ds_sum.get('total_tables', 0)}, views: {ds_sum.get('total_views', 0)}, rows: {ds_sum.get('total_rows', 0):,})")
        tables = ds.get("tables", {})
        shown = 0
        for table_id in sorted(tables.keys()):
            if max_tables_per_dataset is not None and shown >= max_tables_per_dataset:
                remaining = max(0, len(tables) - shown)
                if remaining > 0:
                    print(f"   └─ … {remaining} more")
                break
            t = tables[table_id]
            icon = "🗂️ " if t.get("table_type") == "TABLE" else "🔎 "
            rows = t.get("row_count", 0)
            size_h = _bytes_to_human(int(t.get("size_bytes", 0) or 0))
            print(f"   └─ {icon}{table_id}  (rows: {rows:,}, size: {size_h})")
            shown += 1

def save_analysis_to_file(hierarchy: Dict[str, Any], output_file: str) -> None:
    """Save analysis results to JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hierarchy, f, indent=2, ensure_ascii=False)
        print(f"💾 Analysis saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving analysis: {e}")

def ensure_bq_table(client: bigquery.Client, table_ref: str) -> str:
    """Ensure the BigQuery table exists with correct schema. Returns full table reference."""
    try:
        client.get_table(table_ref)
        print(f"✅ BigQuery table exists: {table_ref}")
        return table_ref
    except NotFound:
        print(f"📝 Creating BigQuery table: {table_ref}")
        schema = [
            bigquery.SchemaField("ldts", "TIMESTAMP", mode="REQUIRED", description="Load timestamp"),
            bigquery.SchemaField("batch_id", "STRING", mode="REQUIRED", description="Batch identifier"),
            bigquery.SchemaField("project_id", "STRING", mode="REQUIRED", description="BigQuery project ID"),
            bigquery.SchemaField("hierarchy_json", "STRING", mode="REQUIRED", description="Complete hierarchy JSON"),
            bigquery.SchemaField("summary_json", "STRING", mode="REQUIRED", description="Summary statistics JSON"),
        ]
        
        table = bigquery.Table(table_ref, schema=schema)
        table.description = "Dataset hierarchy analysis results with LDTS and batch tracking"
        client.create_table(table)
        print(f"✅ Created BigQuery table: {table_ref}")
        return table_ref

def save_to_bigquery(client: bigquery.Client, hierarchy: Dict[str, Any], batch_id: str, bq_table: str, project_id: str) -> None:
    """
    Save hierarchy analysis to BigQuery table with automatic optimization.
    Uses load jobs for large data (>5MB) and streaming inserts for small data.
    
    Args:
        client: BigQuery client
        hierarchy: Hierarchy analysis dictionary
        batch_id: Batch identifier
        bq_table: BigQuery table reference (format: project.dataset.table or dataset.table)
        project_id: Project ID for fallback
    """
    try:
        # Handle table reference
        if '.' not in bq_table or len(bq_table.split('.')) == 2:
            bq_table = f"{project_id}.{bq_table}"
        
        full_table_ref = ensure_bq_table(client, bq_table)
        
        ldts = datetime.now(timezone.utc)
        hierarchy_json = json.dumps(hierarchy, ensure_ascii=False)
        summary_json = json.dumps(hierarchy.get("summary", {}), ensure_ascii=False)
        
        # Check JSON size to determine insertion method
        hierarchy_size = len(hierarchy_json.encode('utf-8'))
        summary_size = len(summary_json.encode('utf-8'))
        total_size = hierarchy_size + summary_size
        
        # Threshold: 5MB (BigQuery streaming insert limit is ~10MB per request, but we use 5MB as safe threshold)
        SIZE_THRESHOLD = 5 * 1024 * 1024  # 5MB in bytes
        
        if total_size > SIZE_THRESHOLD:
            # Use load job for large data (more reliable, handles large payloads)
            print(f"📦 Large hierarchy detected ({total_size / (1024*1024):.2f} MB), using batch load job...")
            
            from google.cloud.bigquery import LoadJobConfig, SourceFormat
            import io
            
            # Prepare data for load job (newline-delimited JSON)
            row_data = {
                "ldts": ldts.isoformat(),
                "batch_id": batch_id,
                "project_id": hierarchy.get("project_id", ""),
                "hierarchy_json": hierarchy_json,
                "summary_json": summary_json,
            }
            
            job_config = LoadJobConfig(
                source_format=SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition="WRITE_APPEND",
                schema=[
                    bigquery.SchemaField("ldts", "TIMESTAMP", mode="REQUIRED"),
                    bigquery.SchemaField("batch_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("project_id", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("hierarchy_json", "STRING", mode="REQUIRED"),
                    bigquery.SchemaField("summary_json", "STRING", mode="REQUIRED"),
                ],
                ignore_unknown_values=False,
            )
            
            # Write as newline-delimited JSON
            json_str = json.dumps(row_data, ensure_ascii=False) + "\n"
            
            job = client.load_table_from_file(
                io.StringIO(json_str),
                full_table_ref,
                job_config=job_config
            )
            
            # Wait for job to complete
            job.result()
            
            if job.errors:
                print(f"❌ Error in load job: {job.errors}")
                return
            
            print(f"✅ Saved to BigQuery via load job: {full_table_ref} (batch_id: {batch_id}, size: {total_size / (1024*1024):.2f} MB)")
            
        else:
            # Use streaming insert for small data (faster, lower latency)
            print(f"⚡ Small hierarchy ({total_size / (1024*1024):.2f} MB), using streaming insert...")
            
            # Format timestamp in BigQuery TIMESTAMP format (YYYY-MM-DD HH:MM:SS.ffffff)
            ldts_str = ldts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            rows_to_insert = [{
                "ldts": ldts_str,
                "batch_id": batch_id,
                "project_id": hierarchy.get("project_id", ""),
                "hierarchy_json": hierarchy_json,
                "summary_json": summary_json,
            }]
            
            errors = client.insert_rows_json(full_table_ref, rows_to_insert)
            if errors:
                print(f"❌ Error inserting rows: {errors}")
                return
            
            print(f"✅ Saved to BigQuery via streaming insert: {full_table_ref} (batch_id: {batch_id}, ldts: {ldts.isoformat()})")
        
    except Exception as e:
        print(f"❌ Error saving to BigQuery: {e}")
        import traceback
        print(f"Details: {traceback.format_exc()}")

def load_from_bigquery(client: bigquery.Client, bq_table: str, project_id: str, 
                       batch_id: Optional[str] = None, 
                       run_date: Optional[str] = None,
                       use_latest: bool = True) -> Optional[Dict[str, Any]]:
    """
    Load previous hierarchy analysis from BigQuery.
    
    Args:
        client: BigQuery client
        bq_table: BigQuery table reference (format: project.dataset.table or dataset.table)
        project_id: Project ID to filter by
        batch_id: Specific batch_id to load (optional)
        run_date: Specific date to load (YYYY-MM-DD format, optional)
        use_latest: If True and no batch_id/date specified, load latest by LDTS
    
    Returns:
        Previous hierarchy dictionary or None if not found
    """
    try:
        # Handle table reference
        if '.' not in bq_table or len(bq_table.split('.')) == 2:
            bq_table = f"{project_id}.{bq_table}"
        # Build query based on parameters
        if batch_id:
            query = f"""
            SELECT hierarchy_json, ldts, batch_id
            FROM `{bq_table}`
            WHERE project_id = @project_id
              AND batch_id = @batch_id
            ORDER BY ldts DESC
            LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("project_id", "STRING", project_id),
                    bigquery.ScalarQueryParameter("batch_id", "STRING", batch_id),
                ]
            )
        elif run_date:
            query = f"""
            SELECT hierarchy_json, ldts, batch_id
            FROM `{bq_table}`
            WHERE project_id = @project_id
              AND DATE(ldts) = @run_date
            ORDER BY ldts DESC
            LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("project_id", "STRING", project_id),
                    bigquery.ScalarQueryParameter("run_date", "DATE", run_date),
                ]
            )
        elif use_latest:
            query = f"""
            SELECT hierarchy_json, ldts, batch_id
            FROM `{bq_table}`
            WHERE project_id = @project_id
            ORDER BY ldts DESC
            LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("project_id", "STRING", project_id),
                ]
            )
        else:
            print("❌ No comparison criteria specified")
            return None
        
        print(f"🔍 Querying BigQuery for previous analysis...")
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if not results:
            print(f"📝 No previous analysis found in BigQuery table")
            return None
        
        row = results[0]
        hierarchy_json_str = row.hierarchy_json
        hierarchy = json.loads(hierarchy_json_str)
        
        print(f"📖 Loaded previous analysis from BigQuery (batch_id: {row.batch_id}, ldts: {row.ldts})")
        return hierarchy
        
    except Exception as e:
        print(f"⚠️  Error loading from BigQuery: {e}")
        return None

def load_previous_analysis(previous_file: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load previous analysis for comparison (from file)."""
    if not previous_file:
        return None
        
    try:
        if not os.path.exists(previous_file):
            print(f"📝 No previous analysis found at: {previous_file}")
            return None
        
        with open(previous_file, 'r', encoding='utf-8') as f:
            previous = json.load(f)
        print(f"📖 Loaded previous analysis from: {previous_file}")
        return previous
    except Exception as e:
        print(f"⚠️  Error loading previous analysis: {e}")
        return None

def compare_analyses(current: Dict[str, Any], previous: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare current analysis with previous analysis."""
    if not previous:
        return {
            "comparison_type": "baseline",
            "message": "No previous analysis found - this is the baseline analysis"
        }
    
    comparison = {
        "comparison_type": "delta",
        "previous_timestamp": previous.get("analysis_timestamp"),
        "current_timestamp": current.get("analysis_timestamp"),
        "changes": {
            "datasets": {
                "added": [],
                "removed": [],
                "modified": []
            },
            "tables": {
                "added": [],
                "removed": [],
                "modified": []
            },
            "summary_changes": {}
        }
    }
    
    # Compare datasets
    current_datasets = set(current["datasets"].keys())
    previous_datasets = set(previous["datasets"].keys())
    
    comparison["changes"]["datasets"]["added"] = list(current_datasets - previous_datasets)
    comparison["changes"]["datasets"]["removed"] = list(previous_datasets - current_datasets)
    
    # Compare tables within common datasets
    common_datasets = current_datasets & previous_datasets
    
    for dataset_id in common_datasets:
        current_tables = set(current["datasets"][dataset_id]["tables"].keys())
        previous_tables = set(previous["datasets"][dataset_id]["tables"].keys())
        
        # Added tables
        added_tables = current_tables - previous_tables
        for table_id in added_tables:
            comparison["changes"]["tables"]["added"].append(f"{dataset_id}.{table_id}")
        
        # Removed tables
        removed_tables = previous_tables - current_tables
        for table_id in removed_tables:
            comparison["changes"]["tables"]["removed"].append(f"{dataset_id}.{table_id}")
        
        # Modified tables (row count changes)
        common_tables = current_tables & previous_tables
        for table_id in common_tables:
            current_rows = current["datasets"][dataset_id]["tables"][table_id]["row_count"]
            previous_rows = previous["datasets"][dataset_id]["tables"][table_id]["row_count"]
            
            if current_rows != previous_rows:
                comparison["changes"]["tables"]["modified"].append({
                    "table": f"{dataset_id}.{table_id}",
                    "previous_rows": previous_rows,
                    "current_rows": current_rows,
                    "row_difference": current_rows - previous_rows
                })
    
    # Summary changes
    comparison["changes"]["summary_changes"] = {
        "datasets": {
            "previous": previous["summary"]["total_datasets"],
            "current": current["summary"]["total_datasets"],
            "difference": current["summary"]["total_datasets"] - previous["summary"]["total_datasets"]
        },
        "tables": {
            "previous": previous["summary"]["total_tables"],
            "current": current["summary"]["total_tables"],
            "difference": current["summary"]["total_tables"] - previous["summary"]["total_tables"]
        },
        "views": {
            "previous": previous["summary"]["total_views"],
            "current": current["summary"]["total_views"],
            "difference": current["summary"]["total_views"] - previous["summary"]["total_views"]
        },
        "rows": {
            "previous": previous["summary"]["total_rows"],
            "current": current["summary"]["total_rows"],
            "difference": current["summary"]["total_rows"] - previous["summary"]["total_rows"]
        }
    }
    
    return comparison

def get_batch_management_table(client: bigquery.Client, mgmt_table: str, project_id: str) -> str:
    """Get or create batch management table. Returns full table reference."""
    # Handle table reference
    if '.' not in mgmt_table or len(mgmt_table.split('.')) == 2:
        mgmt_table = f"{project_id}.{mgmt_table}"
    
    try:
        client.get_table(mgmt_table)
        print(f"✅ Batch management table exists: {mgmt_table}")
        return mgmt_table
    except NotFound:
        print(f"📝 Creating batch management table: {mgmt_table}")
        schema = [
            bigquery.SchemaField("project_id", "STRING", mode="REQUIRED", description="BigQuery project ID"),
            bigquery.SchemaField("batch_id", "STRING", mode="REQUIRED", description="Batch identifier (DDMMYYYY-NNNN format)"),
            bigquery.SchemaField("ldts", "TIMESTAMP", mode="REQUIRED", description="Load timestamp"),
            bigquery.SchemaField("num_datasets", "INTEGER", mode="REQUIRED", description="Number of datasets"),
            bigquery.SchemaField("num_tables", "INTEGER", mode="REQUIRED", description="Number of tables"),
            bigquery.SchemaField("num_views", "INTEGER", mode="REQUIRED", description="Number of views"),
            bigquery.SchemaField("total_rows", "INTEGER", mode="REQUIRED", description="Total number of rows across all tables"),
            bigquery.SchemaField("total_bytes", "INTEGER", mode="REQUIRED", description="Total data size in bytes"),
        ]
        
        table = bigquery.Table(mgmt_table, schema=schema)
        table.description = "Batch management table for dataset hierarchy analysis tracking"
        client.create_table(table)
        print(f"✅ Created batch management table: {mgmt_table}")
        return mgmt_table

def get_next_batch_id(client: bigquery.Client, mgmt_table: str, project_id: str) -> str:
    """
    Generate next batch_id in format DDMMYYYY-NNNN.
    
    Args:
        client: BigQuery client
        mgmt_table: Batch management table reference
        project_id: Project ID
    
    Returns:
        Next batch_id string (e.g., "29102025-0001")
    """
    # Ensure table exists first
    full_table_ref = get_batch_management_table(client, mgmt_table, project_id)
    
    # Get today's date in DDMMYYYY format
    today = datetime.now(timezone.utc)
    date_str = today.strftime("%d%m%Y")
    
    # Query for the latest batch_id for today for this project
    query = f"""
    SELECT batch_id
    FROM `{full_table_ref}`
    WHERE project_id = @project_id
      AND batch_id LIKE @date_pattern
    ORDER BY batch_id DESC
    LIMIT 1
    """
    
    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("project_id", "STRING", project_id),
                bigquery.ScalarQueryParameter("date_pattern", "STRING", f"{date_str}-%"),
            ]
        )
        
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if results:
            # Extract the counter from the last batch_id
            last_batch_id = results[0].batch_id
            # Format: DDMMYYYY-NNNN
            if '-' in last_batch_id:
                counter_str = last_batch_id.split('-')[1]
                counter = int(counter_str) + 1
            else:
                counter = 1
        else:
            # First batch of the day
            counter = 1
        
        # Format counter with zero padding (4 digits)
        batch_id = f"{date_str}-{counter:04d}"
        return batch_id
        
    except Exception as e:
        print(f"⚠️  Error querying batch management table: {e}")
        # Fallback to timestamp-based batch_id
        return f"{date_str}-0001"

def calculate_total_bytes(hierarchy: Dict[str, Any]) -> int:
    """Calculate total data size in bytes across all tables."""
    total_bytes = 0
    for dataset_id, dataset_info in hierarchy.get("datasets", {}).items():
        for table_id, table_info in dataset_info.get("tables", {}).items():
            # Use num_bytes or size_bytes, whichever is available
            table_bytes = table_info.get("num_bytes", 0) or table_info.get("size_bytes", 0)
            total_bytes += int(table_bytes) if table_bytes else 0
    return total_bytes

def save_to_batch_management(client: bigquery.Client, hierarchy: Dict[str, Any], batch_id: str, 
                              mgmt_table: str, project_id: str) -> None:
    """
    Save summary to batch management table.
    
    Args:
        client: BigQuery client
        hierarchy: Hierarchy analysis dictionary
        batch_id: Batch identifier
        mgmt_table: Batch management table reference
        project_id: Project ID
    """
    try:
        full_table_ref = get_batch_management_table(client, mgmt_table, project_id)
        
        ldts = datetime.now(timezone.utc)
        summary = hierarchy.get("summary", {})
        total_bytes = calculate_total_bytes(hierarchy)
        
        # Format timestamp in BigQuery TIMESTAMP format
        ldts_str = ldts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        rows_to_insert = [{
            "project_id": project_id,
            "batch_id": batch_id,
            "ldts": ldts_str,
            "num_datasets": summary.get("total_datasets", 0),
            "num_tables": summary.get("total_tables", 0),
            "num_views": summary.get("total_views", 0),
            "total_rows": summary.get("total_rows", 0),
            "total_bytes": total_bytes,
        }]
        
        errors = client.insert_rows_json(full_table_ref, rows_to_insert)
        if errors:
            print(f"❌ Error inserting into batch management table: {errors}")
            return
        
        # Format total_bytes for display
        total_gb = total_bytes / (1024 ** 3)
        print(f"✅ Saved to batch management: {full_table_ref}")
        print(f"   Batch ID: {batch_id} | Datasets: {summary.get('total_datasets', 0)} | "
              f"Tables: {summary.get('total_tables', 0)} | Rows: {summary.get('total_rows', 0):,} | "
              f"Size: {total_gb:.2f} GB")
        
    except Exception as e:
        print(f"❌ Error saving to batch management table: {e}")

def print_comparison_summary(comparison: Dict[str, Any]) -> None:
    """Print a summary of changes."""
    print("\n" + "="*80)
    print("📊 DATASET HIERARCHY COMPARISON SUMMARY")
    print("="*80)
    
    if comparison["comparison_type"] == "baseline":
        print("🎯 This is the baseline analysis - no previous data to compare")
        return
    
    print(f"📅 Previous Analysis: {comparison['previous_timestamp']}")
    print(f"📅 Current Analysis:  {comparison['current_timestamp']}")
    print()
    
    # Summary changes
    summary = comparison["changes"]["summary_changes"]
    print("📈 SUMMARY CHANGES:")
    print(f"  Datasets: {summary['datasets']['previous']} → {summary['datasets']['current']} ({summary['datasets']['difference']:+d})")
    print(f"  Tables:   {summary['tables']['previous']} → {summary['tables']['current']} ({summary['tables']['difference']:+d})")
    print(f"  Views:    {summary['views']['previous']} → {summary['views']['current']} ({summary['views']['difference']:+d})")
    print(f"  Rows:     {summary['rows']['previous']:,} → {summary['rows']['current']:,} ({summary['rows']['difference']:+,})")
    print()
    
    # Dataset changes
    datasets = comparison["changes"]["datasets"]
    if datasets["added"]:
        print(f"➕ ADDED DATASETS ({len(datasets['added'])}):")
        for dataset in datasets["added"]:
            print(f"    + {dataset}")
        print()
    
    if datasets["removed"]:
        print(f"➖ REMOVED DATASETS ({len(datasets['removed'])}):")
        for dataset in datasets["removed"]:
            print(f"    - {dataset}")
        print()
    
    # Table changes
    tables = comparison["changes"]["tables"]
    if tables["added"]:
        print(f"➕ ADDED TABLES ({len(tables['added'])}):")
        for table in tables["added"]:
            print(f"    + {table}")
        print()
    
    if tables["removed"]:
        print(f"➖ REMOVED TABLES ({len(tables['removed'])}):")
        for table in tables["removed"]:
            print(f"    - {table}")
        print()
    
    if tables["modified"]:
        print(f"🔄 MODIFIED TABLES ({len(tables['modified'])}):")
        for table in tables["modified"]:
            print(f"    ~ {table['table']}: {table['previous_rows']:,} → {table['current_rows']:,} ({table['row_difference']:+,})")
        print()
    
    print("="*80)

def main(args):
    """Main entry point for dataset hierarchy analysis."""
    project_id = get_project_id(args.project)
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=project_id)
        print(f"✅ Connected to BigQuery project: {project_id}")
    except Exception as e:
        print(f"❌ Error connecting to BigQuery: {e}")
        return 1
    
    # Get batch management table from args or env
    mgmt_table = getattr(args, 'batch_mgmt_table', None) or os.getenv("BATCH_MGMT_TABLE")
    
    # Generate batch_id if not provided
    if getattr(args, 'batch_id', None):
        batch_id = args.batch_id
    elif mgmt_table:
        # Use batch management table to generate auto-incrementing batch_id
        batch_id = get_next_batch_id(client, mgmt_table, project_id)
        print(f"📦 Generated batch_id: {batch_id}")
    else:
        # Fallback to timestamp-based batch_id
        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    # Analyze dataset hierarchy
    hierarchy = analyze_dataset_hierarchy(client, project_id, args.include_views)
    
    # Save to batch management table if configured
    if mgmt_table:
        save_to_batch_management(client, hierarchy, batch_id, mgmt_table, project_id)
    
    # Save to BigQuery if requested
    bq_table = getattr(args, 'bq_table', None)
    if bq_table:
        save_to_bigquery(client, hierarchy, batch_id, bq_table, project_id)
    
    # Generate output filename with timestamp
    output_format = getattr(args, "format", "json")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"dataset_hierarchy_{project_id}_{timestamp}.json"
    
    if args.output:
        output_file = args.output
    
    # Output selection
    if output_format in ("json", "both"):
        save_analysis_to_file(hierarchy, output_file)
    if output_format in ("tree", "both"):
        print_hierarchy_tree(hierarchy, getattr(args, "max_tables", None))
    
    # Handle comparison
    previous_analysis = None
    
    # Priority: 1. BigQuery (if enabled), 2. File, 3. None
    if bq_table:
        # Load from BigQuery
        compare_batch_id = getattr(args, 'compare_batch_id', None)
        compare_date = getattr(args, 'compare_date', None)
        # Default to latest if no specific batch_id or date is provided
        use_latest = getattr(args, 'compare_latest', False) or (not compare_batch_id and not compare_date)
        
        previous_analysis = load_from_bigquery(
            client, 
            bq_table, 
            project_id,
            batch_id=compare_batch_id,
            run_date=compare_date,
            use_latest=use_latest
        )
    
    # Fallback to file if BigQuery didn't return results
    if not previous_analysis and args.compare:
        previous_analysis = load_previous_analysis(args.compare)
    
    # Perform comparison if we have previous data
    if previous_analysis or args.compare or bq_table:
        comparison = compare_analyses(hierarchy, previous_analysis)
        
        # Save comparison if outputting JSON
        if output_format in ("json", "both"):
            comparison_file = output_file.replace('.json', '_comparison.json')
            try:
                with open(comparison_file, 'w', encoding='utf-8') as f:
                    json.dump(comparison, f, indent=2, ensure_ascii=False)
                print(f"💾 Comparison saved to: {comparison_file}")
            except Exception as e:
                print(f"❌ Error saving comparison: {e}")
        
        # Print comparison summary
        print_comparison_summary(comparison)
    
    # Print summary
    print(f"\n🎯 Analysis complete!")
    print(f"📊 Project: {project_id}")
    print(f"📁 Datasets: {hierarchy['summary']['total_datasets']}")
    print(f"📋 Tables: {hierarchy['summary']['total_tables']}")
    print(f"👁️  Views: {hierarchy['summary']['total_views']}")
    print(f"📊 Total Rows: {hierarchy['summary']['total_rows']:,}")
    if bq_table:
        print(f"💾 BigQuery: {bq_table} (batch_id: {batch_id})")
    if output_format in ("json", "both"):
        print(f"💾 Output: {output_file}")
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze BigQuery dataset hierarchy and track changes over time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic analysis
  python dataset_hierarchy.py --project my-project-id
  
  # Use batch management table (auto-generates DDMMYYYY-NNNN batch_id)
  python dataset_hierarchy.py --project my-project-id --batch-mgmt-table dataset.batch_management
  
  # Save to BigQuery with auto batch_id from batch management
  python dataset_hierarchy.py --project my-project-id --bq-table dataset.hierarchy_analysis --batch-mgmt-table dataset.batch_management
  
  # Save to BigQuery with custom batch_id
  python dataset_hierarchy.py --project my-project-id --bq-table dataset.hierarchy_analysis --batch-id 29102025-0001
  
  # Compare with latest BigQuery run
  python dataset_hierarchy.py --project my-project-id --bq-table dataset.hierarchy_analysis --compare-latest
  
  # Compare with specific batch_id
  python dataset_hierarchy.py --project my-project-id --bq-table dataset.hierarchy_analysis --compare-batch-id batch_20241027_120000
  
  # Compare with specific date
  python dataset_hierarchy.py --project my-project-id --bq-table dataset.hierarchy_analysis --compare-date 2024-10-27
  
  # Tree view output
  python dataset_hierarchy.py --project my-project-id --format tree --max-tables 20
        """
    )
    
    parser.add_argument(
        "--project", "-p",
        help="BigQuery project ID (overrides PROJECT_ID from .env)"
    )
    
    parser.add_argument(
        "--include-views",
        action="store_true",
        help="Include views in the analysis (default: tables only)"
    )
    
    parser.add_argument(
        "--compare", "-c",
        help="Path to previous analysis JSON file for comparison"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: auto-generated with timestamp)"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "tree", "both"],
        default="json",
        help="Choose output format: json (default), tree (human-readable), or both"
    )
    
    parser.add_argument(
        "--max-tables",
        type=int,
        help="Limit number of tables shown per dataset in tree view"
    )
    
    parser.add_argument(
        "--bq-table",
        help="BigQuery table to save/load hierarchy (format: project.dataset.table or dataset.table)"
    )
    
    parser.add_argument(
        "--batch-mgmt-table",
        help="Batch management table for tracking runs (format: project.dataset.table or dataset.table). Enables auto batch_id generation in DDMMYYYY-NNNN format."
    )
    
    parser.add_argument(
        "--batch-id",
        help="Custom batch identifier (default: auto-generated via batch management table in DDMMYYYY-NNNN format or timestamp)"
    )
    
    parser.add_argument(
        "--compare-latest",
        action="store_true",
        default=True,
        help="Compare with latest BigQuery run (default: True when --bq-table is specified)"
    )
    
    parser.add_argument(
        "--compare-batch-id",
        help="Compare with specific batch_id from BigQuery table"
    )
    
    parser.add_argument(
        "--compare-date",
        help="Compare with specific run date (YYYY-MM-DD format)"
    )
    
    args = parser.parse_args()
    sys.exit(main(args))

