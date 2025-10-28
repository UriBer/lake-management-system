#!/usr/bin/env python3
"""
Dataset Hierarchy Analysis Module

Analyzes all datasets in a BigQuery project, providing:
- Complete dataset hierarchy
- Table counts per dataset
- Row counts per table (from metadata)
- Change detection between runs
- Comprehensive logging for comparison
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

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

def analyze_dataset_hierarchy(client: bigquery.Client, project_id: str, include_views: bool = False) -> Dict[str, Any]:
    """
    Analyze complete dataset hierarchy for a project.
    
    Args:
        client: BigQuery client
        project_id: Project ID to analyze
        include_views: Whether to include views in analysis
    
    Returns:
        Dictionary containing complete hierarchy analysis
    """
    print(f"🔍 Analyzing dataset hierarchy for project: {project_id}")
    
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
    
    try:
        # Get all datasets
        datasets = list(client.list_datasets())
        hierarchy["summary"]["total_datasets"] = len(datasets)
        
        print(f"📊 Found {len(datasets)} datasets")
        
        for dataset in datasets:
            dataset_id = dataset.dataset_id
            print(f"  📁 Analyzing dataset: {dataset_id}")
            
            dataset_info = {
                "dataset_id": dataset_id,
                "location": getattr(dataset, 'location', 'Unknown'),
                "created": getattr(dataset, 'created', None),
                "modified": getattr(dataset, 'modified', None),
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
                
                for table in tables:
                    table_id = table.table_id
                    table_type = table.table_type
                    
                    # Skip views if not requested
                    if table_type == "VIEW" and not include_views:
                        continue
                    
                    print(f"    📋 Analyzing {table_type.lower()}: {table_id}")
                    
                    table_info = {
                        "table_id": table_id,
                        "table_type": table_type,
                        "created": getattr(table, 'created', None),
                        "modified": getattr(table, 'modified', None),
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
                        
                        # Update dataset summary
                        if table_type == "TABLE":
                            dataset_info["summary"]["total_tables"] += 1
                            hierarchy["summary"]["total_tables"] += 1
                        elif table_type == "VIEW":
                            dataset_info["summary"]["total_views"] += 1
                            hierarchy["summary"]["total_views"] += 1
                        
                        dataset_info["summary"]["total_rows"] += table_info["row_count"]
                        hierarchy["summary"]["total_rows"] += table_info["row_count"]
                        
                        print(f"      ✅ {table_type}: {table_id} - {table_info['row_count']:,} rows")
                        
                    except Exception as e:
                        print(f"      ⚠️  Error analyzing {table_type} {table_id}: {e}")
                        table_info["error"] = str(e)
                    
                    dataset_info["tables"][table_id] = table_info
                
                print(f"  ✅ Dataset {dataset_id}: {dataset_info['summary']['total_tables']} tables, {dataset_info['summary']['total_views']} views, {dataset_info['summary']['total_rows']:,} rows")
                
            except Exception as e:
                print(f"  ❌ Error analyzing dataset {dataset_id}: {e}")
                dataset_info["error"] = str(e)
            
            hierarchy["datasets"][dataset_id] = dataset_info
        
        print(f"🎯 Analysis complete: {hierarchy['summary']['total_datasets']} datasets, {hierarchy['summary']['total_tables']} tables, {hierarchy['summary']['total_views']} views, {hierarchy['summary']['total_rows']:,} total rows")
        
    except Exception as e:
        print(f"❌ Error analyzing project {project_id}: {e}")
        hierarchy["error"] = str(e)
    
    return hierarchy

def save_analysis_to_file(hierarchy: Dict[str, Any], output_file: str) -> None:
    """Save analysis results to JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hierarchy, f, indent=2, ensure_ascii=False)
        print(f"💾 Analysis saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving analysis: {e}")

def load_previous_analysis(previous_file: str) -> Optional[Dict[str, Any]]:
    """Load previous analysis for comparison."""
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
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"dataset_hierarchy_{project_id}_{timestamp}.json"
    
    if args.output:
        output_file = args.output
    
    # Analyze dataset hierarchy
    hierarchy = analyze_dataset_hierarchy(client, project_id, args.include_views)
    
    # Save analysis
    save_analysis_to_file(hierarchy, output_file)
    
    # Compare with previous analysis if requested
    if args.compare:
        previous_file = args.compare
        previous_analysis = load_previous_analysis(previous_file)
        comparison = compare_analyses(hierarchy, previous_analysis)
        
        # Save comparison
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
  
  # Include views in analysis
  python dataset_hierarchy.py --project my-project-id --include-views
  
  # Compare with previous analysis
  python dataset_hierarchy.py --project my-project-id --compare previous_analysis.json
  
  # Custom output file
  python dataset_hierarchy.py --project my-project-id --output my_analysis.json
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
    
    args = parser.parse_args()
    sys.exit(main(args))
