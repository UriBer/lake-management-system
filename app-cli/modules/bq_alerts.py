#!/usr/bin/env python3
"""
BigQuery Table Size Alerts Module

Detects significant table size changes by comparing day-over-day data
from the batch_management table and writes alerts to BigQuery.
Alerts are designed to be consumed by GCP Cloud Monitoring.
"""

import os
import sys
import json
import argparse
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal

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

def ensure_alerts_table(client: bigquery.Client, alerts_table: str, project_id: str) -> str:
    """Get or create alerts table. Returns full table reference."""
    # Handle table reference
    if '.' not in alerts_table or len(alerts_table.split('.')) == 2:
        alerts_table = f"{project_id}.{alerts_table}"
    
    try:
        client.get_table(alerts_table)
        print(f"✅ Alerts table exists: {alerts_table}")
        return alerts_table
    except NotFound:
        print(f"📝 Creating alerts table: {alerts_table}")
        schema = [
            bigquery.SchemaField("alert_id", "STRING", mode="REQUIRED", description="Unique alert identifier"),
            bigquery.SchemaField("alert_timestamp", "TIMESTAMP", mode="REQUIRED", description="When alert was generated"),
            bigquery.SchemaField("project_id", "STRING", mode="REQUIRED", description="BigQuery project ID"),
            bigquery.SchemaField("batch_id_current", "STRING", mode="REQUIRED", description="Current batch ID"),
            bigquery.SchemaField("batch_id_previous", "STRING", mode="NULLABLE", description="Previous batch ID for comparison"),
            bigquery.SchemaField("alert_type", "STRING", mode="REQUIRED", description="Type: SIZE_INCREASE, SIZE_DECREASE, MISSING_DATA, NEW_DATA"),
            bigquery.SchemaField("severity", "STRING", mode="REQUIRED", description="Severity: LOW, MEDIUM, HIGH, CRITICAL"),
            bigquery.SchemaField("metric_name", "STRING", mode="REQUIRED", description="Metric: total_bytes, num_tables, num_datasets, total_rows"),
            bigquery.SchemaField("current_value", "NUMERIC", mode="REQUIRED", description="Current metric value"),
            bigquery.SchemaField("previous_value", "NUMERIC", mode="NULLABLE", description="Previous metric value"),
            bigquery.SchemaField("change_value", "NUMERIC", mode="REQUIRED", description="Absolute change"),
            bigquery.SchemaField("change_percent", "NUMERIC", mode="REQUIRED", description="Percentage change"),
            bigquery.SchemaField("alert_message", "STRING", mode="REQUIRED", description="Human-readable alert message"),
            bigquery.SchemaField("metadata_json", "STRING", mode="NULLABLE", description="Additional context as JSON"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED", description="Status: PENDING, SENT, RESOLVED, ACKNOWLEDGED"),
            bigquery.SchemaField("resolved_at", "TIMESTAMP", mode="NULLABLE", description="When alert was resolved"),
            bigquery.SchemaField("resolved_by", "STRING", mode="NULLABLE", description="Who resolved the alert"),
        ]
        
        table = bigquery.Table(alerts_table, schema=schema)
        table.description = "Table size alerts for Cloud Monitoring integration"
        
        # Partition by date for efficient querying
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="alert_timestamp"
        )
        
        # Cluster by status and severity for efficient filtering
        table.clustering_fields = ["status", "severity", "alert_type"]
        
        client.create_table(table)
        print(f"✅ Created alerts table: {alerts_table}")
        return alerts_table

def get_latest_batch_records(client: bigquery.Client, mgmt_table: str, project_id: str, 
                             days: int = 2) -> List[Dict[str, Any]]:
    """Get latest batch records for comparison."""
    # Handle table reference
    if '.' not in mgmt_table or len(mgmt_table.split('.')) == 2:
        mgmt_table = f"{project_id}.{mgmt_table}"
    
    query = f"""
    SELECT 
        batch_id,
        project_id,
        ldts,
        num_datasets,
        num_tables,
        num_views,
        total_rows,
        total_bytes
    FROM `{mgmt_table}`
    WHERE project_id = @project_id
      AND DATE(ldts) >= DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY)
    ORDER BY ldts DESC
    LIMIT @days
    """
    
    try:
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("project_id", "STRING", project_id),
                bigquery.ScalarQueryParameter("days", "INT64", days),
            ]
        )
        
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        # Convert to list of dicts
        records = []
        for row in results:
            records.append({
                "batch_id": row.batch_id,
                "project_id": row.project_id,
                "ldts": row.ldts,
                "num_datasets": row.num_datasets,
                "num_tables": row.num_tables,
                "num_views": row.num_views,
                "total_rows": row.total_rows,
                "total_bytes": int(row.total_bytes) if row.total_bytes else 0
            })
        
        return sorted(records, key=lambda x: x["ldts"])
        
    except Exception as e:
        print(f"❌ Error querying batch management table: {e}")
        return []

def calculate_severity(change_percent: float, change_absolute_gb: float, 
                       alert_type: str, thresholds: Dict[str, Any]) -> str:
    """Calculate alert severity based on thresholds."""
    if alert_type == "SIZE_INCREASE":
        if change_percent > thresholds.get("critical_percent", 100.0) or change_absolute_gb > thresholds.get("critical_absolute_gb", 50.0):
            return "CRITICAL"
        elif change_percent > thresholds.get("high_percent", 50.0) or change_absolute_gb > thresholds.get("high_absolute_gb", 20.0):
            return "HIGH"
        elif change_percent > thresholds.get("medium_percent", 20.0) or change_absolute_gb > thresholds.get("medium_absolute_gb", 10.0):
            return "MEDIUM"
        else:
            return "LOW"
    elif alert_type == "SIZE_DECREASE":
        if abs(change_percent) > thresholds.get("critical_percent", 50.0):
            return "HIGH"
        elif abs(change_percent) > thresholds.get("high_percent", 25.0):
            return "MEDIUM"
        else:
            return "LOW"
    else:
        return "MEDIUM"

def detect_alerts(current: Dict[str, Any], previous: Optional[Dict[str, Any]],
                  thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detect alerts by comparing current and previous batch records.
    
    Args:
        current: Current batch record
        previous: Previous batch record (optional)
        thresholds: Alert thresholds configuration
    
    Returns:
        List of alert dictionaries
    """
    alerts = []
    
    if not previous:
        # No previous data - alert on missing baseline
        alerts.append({
            "alert_type": "MISSING_DATA",
            "severity": "LOW",
            "metric_name": "all",
            "current_value": Decimal(str(current.get("total_bytes", 0))),
            "previous_value": None,
            "change_value": Decimal("0"),
            "change_percent": Decimal("0"),
            "alert_message": "No previous batch data available for comparison - this is the baseline",
            "metadata_json": json.dumps({"batch_id": current.get("batch_id")}, ensure_ascii=False)
        })
        return alerts
    
    # Compare metrics
    metrics = {
        "total_bytes": {
            "name": "Total Data Size",
            "unit": "GB",
            "divisor": 1024 ** 3
        },
        "num_tables": {
            "name": "Number of Tables",
            "unit": "tables",
            "divisor": 1
        },
        "num_datasets": {
            "name": "Number of Datasets",
            "unit": "datasets",
            "divisor": 1
        },
        "total_rows": {
            "name": "Total Rows",
            "unit": "rows",
            "divisor": 1
        }
    }
    
    for metric_key, metric_info in metrics.items():
        current_value = Decimal(str(current.get(metric_key, 0)))
        previous_value = Decimal(str(previous.get(metric_key, 0)))
        
        if previous_value == 0:
            continue
        
        change_value = current_value - previous_value
        change_percent = (change_value / previous_value) * 100
        
        # Convert to display units
        current_display = float(current_value / metric_info["divisor"])
        previous_display = float(previous_value / metric_info["divisor"])
        change_display = float(change_value / metric_info["divisor"])
        
        # Determine if alert should be triggered
        threshold_percent = thresholds.get(f"{metric_key}_percent", thresholds.get("default_percent", 20.0))
        threshold_absolute = thresholds.get(f"{metric_key}_absolute", thresholds.get("default_absolute", 10.0))
        
        # Only alert on significant increases (or decreases if configured)
        if abs(change_percent) > threshold_percent or abs(change_display) > threshold_absolute:
            alert_type = "SIZE_INCREASE" if change_value > 0 else "SIZE_DECREASE"
            
            severity = calculate_severity(
                float(change_percent),
                abs(change_display) if metric_key == "total_bytes" else 0,
                alert_type,
                thresholds
            )
            
            # Skip LOW severity alerts if configured
            if severity == "LOW" and not thresholds.get("alert_on_low", False):
                continue
            
            alert = {
                "alert_type": alert_type,
                "severity": severity,
                "metric_name": metric_key,
                "current_value": current_value,
                "previous_value": previous_value,
                "change_value": change_value,
                "change_percent": change_percent,
                "alert_message": (
                    f"{metric_info['name']} changed by {change_percent:.1f}% "
                    f"({change_display:+,.2f} {metric_info['unit']}) - "
                    f"From {previous_display:,.2f} to {current_display:,.2f} {metric_info['unit']}"
                ),
                "metadata_json": json.dumps({
                    "metric": metric_key,
                    "current": float(current_value),
                    "previous": float(previous_value),
                    "change": float(change_value),
                    "current_display": current_display,
                    "previous_display": previous_display,
                    "change_display": change_display
                }, ensure_ascii=False)
            }
            
            alerts.append(alert)
    
    return alerts

def save_alerts_to_bigquery(client: bigquery.Client, alerts: List[Dict[str, Any]],
                            project_id: str, batch_id_current: str,
                            batch_id_previous: Optional[str], alerts_table: str) -> None:
    """Save alerts to BigQuery alerts table."""
    if not alerts:
        print("✅ No alerts detected")
        return
    
    full_table_ref = ensure_alerts_table(client, alerts_table, project_id)
    
    ldts = datetime.now(timezone.utc)
    rows_to_insert = []
    
    for i, alert in enumerate(alerts):
        alert_id = f"{batch_id_current}_{i:04d}_{uuid.uuid4().hex[:8]}"
        
        # Format timestamp for BigQuery
        ldts_str = ldts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        row = {
            "alert_id": alert_id,
            "alert_timestamp": ldts_str,
            "project_id": project_id,
            "batch_id_current": batch_id_current,
            "batch_id_previous": batch_id_previous or "",
            "alert_type": alert["alert_type"],
            "severity": alert["severity"],
            "metric_name": alert["metric_name"],
            "current_value": str(alert["current_value"]),  # BigQuery NUMERIC as string
            "previous_value": str(alert["previous_value"]) if alert["previous_value"] is not None else None,
            "change_value": str(alert["change_value"]),
            "change_percent": str(alert["change_percent"]),
            "alert_message": alert["alert_message"],
            "metadata_json": alert.get("metadata_json"),
            "status": "PENDING",
            "resolved_at": None,
            "resolved_by": None
        }
        
        rows_to_insert.append(row)
    
    # Batch insert alerts
    errors = client.insert_rows_json(full_table_ref, rows_to_insert)
    if errors:
        print(f"❌ Error saving alerts: {errors}")
        return
    
    # Count by severity
    severity_counts = {}
    for alert in alerts:
        sev = alert["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    severity_summary = ", ".join([f"{count} {sev}" for sev, count in sorted(severity_counts.items())])
    print(f"✅ Saved {len(alerts)} alerts to {full_table_ref} ({severity_summary})")

def print_alerts_summary(alerts: List[Dict[str, Any]]) -> None:
    """Print a summary of detected alerts."""
    if not alerts:
        print("✅ No alerts detected - all metrics within thresholds")
        return
    
    print("\n" + "="*80)
    print("🚨 ALERT SUMMARY")
    print("="*80)
    
    # Group by severity
    by_severity = {}
    for alert in alerts:
        sev = alert["severity"]
        if sev not in by_severity:
            by_severity[sev] = []
        by_severity[sev].append(alert)
    
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if severity in by_severity:
            print(f"\n{severity} Alerts ({len(by_severity[severity])}):")
            for alert in by_severity[severity]:
                print(f"  • {alert['alert_message']}")
    
    print("="*80)

def main(args):
    """Main entry point for alert detection."""
    project_id = get_project_id(args.project)
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=project_id)
        print(f"✅ Connected to BigQuery project: {project_id}")
    except Exception as e:
        print(f"❌ Error connecting to BigQuery: {e}")
        return 1
    
    # Get table references
    mgmt_table = args.batch_mgmt_table or os.getenv("BATCH_MGMT_TABLE")
    if not mgmt_table:
        print("❌ BATCH_MGMT_TABLE must be set in .env or provided via --batch-mgmt-table")
        return 1
    
    alerts_table = args.alerts_table or os.getenv("ALERTS_TABLE", "governance_metadata.size_alerts")
    
    # Load thresholds from environment or use defaults
    thresholds = {
        "default_percent": float(os.getenv("ALERT_SIZE_INCREASE_PERCENT", "20.0")),
        "default_absolute": float(os.getenv("ALERT_SIZE_INCREASE_ABSOLUTE_GB", "10.0")),
        "total_bytes_percent": float(os.getenv("ALERT_TOTAL_BYTES_PERCENT", "20.0")),
        "total_bytes_absolute": float(os.getenv("ALERT_TOTAL_BYTES_ABSOLUTE_GB", "10.0")),
        "num_tables_percent": float(os.getenv("ALERT_NUM_TABLES_PERCENT", "10.0")),
        "num_datasets_percent": float(os.getenv("ALERT_NUM_DATASETS_PERCENT", "5.0")),
        "total_rows_percent": float(os.getenv("ALERT_TOTAL_ROWS_PERCENT", "20.0")),
        "critical_percent": float(os.getenv("ALERT_CRITICAL_PERCENT", "100.0")),
        "critical_absolute_gb": float(os.getenv("ALERT_CRITICAL_ABSOLUTE_GB", "50.0")),
        "high_percent": float(os.getenv("ALERT_HIGH_PERCENT", "50.0")),
        "high_absolute_gb": float(os.getenv("ALERT_HIGH_ABSOLUTE_GB", "20.0")),
        "medium_percent": float(os.getenv("ALERT_MEDIUM_PERCENT", "20.0")),
        "medium_absolute_gb": float(os.getenv("ALERT_MEDIUM_ABSOLUTE_GB", "10.0")),
        "alert_on_low": os.getenv("ALERT_ON_LOW", "false").lower() == "true",
    }
    
    print(f"📊 Alert thresholds: {thresholds['default_percent']:.1f}% or {thresholds['default_absolute']:.1f} GB")
    
    # Get latest batch records for comparison
    print(f"🔍 Querying batch management table: {mgmt_table}")
    records = get_latest_batch_records(client, mgmt_table, project_id, days=2)
    
    if len(records) < 1:
        print("❌ No batch records found in batch management table")
        return 1
    
    if len(records) < 2:
        print("⚠️  Only one batch record found - need at least 2 for comparison")
        print(f"   Using batch: {records[0]['batch_id']} (baseline)")
        current = records[-1]  # Latest
        previous = None
    else:
        current = records[-1]  # Latest
        previous = records[-2]  # Previous
        print(f"📅 Comparing batches:")
        print(f"   Current:  {current['batch_id']} ({current['ldts']})")
        print(f"   Previous: {previous['batch_id']} ({previous['ldts']})")
    
    # Detect alerts
    print(f"\n🔎 Detecting alerts...")
    alerts = detect_alerts(current, previous, thresholds)
    
    # Print summary
    print_alerts_summary(alerts)
    
    # Save alerts to BigQuery
    if alerts:
        batch_id_current = current["batch_id"]
        batch_id_previous = previous["batch_id"] if previous else None
        save_alerts_to_bigquery(client, alerts, project_id, batch_id_current, 
                               batch_id_previous, alerts_table)
        
        # Print next steps
        print(f"\n📧 Next steps:")
        print(f"   1. Alerts saved to: {alerts_table}")
        print(f"   2. Set up Cloud Monitoring alert policies (see alerts/README.md)")
        print(f"   3. Configure notification channels in GCP Console or via Terraform")
        print(f"   4. Query alerts: SELECT * FROM `{alerts_table}` WHERE status='PENDING'")
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detect BigQuery table size alerts from batch_management table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic alert detection
  python bq_alerts.py --project my-project-id --batch-mgmt-table dataset.batch_management
  
  # Custom alerts table
  python bq_alerts.py --project my-project-id --batch-mgmt-table dataset.batch_management --alerts-table dataset.alerts
  
  # Alert on all severity levels
  ALERT_ON_LOW=true python bq_alerts.py --project my-project-id --batch-mgmt-table dataset.batch_management
        """
    )
    
    parser.add_argument(
        "--project", "-p",
        help="BigQuery project ID (overrides PROJECT_ID from .env)"
    )
    
    parser.add_argument(
        "--batch-mgmt-table",
        help="Batch management table (format: project.dataset.table or dataset.table)"
    )
    
    parser.add_argument(
        "--alerts-table",
        help="Alerts table (default: governance_metadata.size_alerts)"
    )
    
    args = parser.parse_args()
    sys.exit(main(args))

