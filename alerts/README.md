# BigQuery Table Size Alerts - Cloud Monitoring Configuration

This directory contains Terraform configurations for setting up GCP Cloud Monitoring alert policies that monitor BigQuery table size changes.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Daily Dataset Hierarchy Analysis                       │
│  └─> Writes to batch_management table                    │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  bq-alerts CLI Command                                  │
│  └─> Compares day-over-day data                          │
│  └─> Writes alerts to alerts table                       │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Cloud Monitoring Alert Policies                        │
│  └─> Monitor alerts table via metrics                    │
│  └─> Trigger notifications                               │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Notification Channels (Email, Slack, etc.)              │
│  └─> Send alerts to configured recipients                │
└─────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **Run dataset hierarchy analysis daily** - Uses `batch_management` table
2. **Run bq-alerts command** - Detects changes and writes to `alerts` table
3. **Terraform** (>= 1.3)
4. **GCP Project** with appropriate permissions
5. **BigQuery tables**:
   - `batch_management` table (from dataset-hierarchy command)
   - `alerts` table (created automatically by bq-alerts command)

## Setup

### 1. Configure Variables

Create `terraform.tfvars`:

```hcl
project_id                = "your-project-id"
region                    = "us-central1"
batch_management_table    = "governance_metadata.batch_management"
alerts_table             = "governance_metadata.size_alerts"

alert_email_recipients = [
  "team-lead@example.com",
  "data-eng@example.com"
]

# Alert thresholds
critical_size_increase_percent = 100.0  # >100% = CRITICAL
high_size_increase_percent     = 50.0   # >50% = HIGH
medium_size_increase_percent   = 20.0   # >20% = MEDIUM

critical_size_increase_gb = 50.0  # >50GB = CRITICAL
high_size_increase_gb     = 20.0  # >20GB = HIGH
medium_size_increase_gb   = 10.0  # >10GB = MEDIUM
```

### 2. Initialize Terraform

```bash
cd alerts
terraform init
```

### 3. Review Plan

```bash
terraform plan
```

### 4. Apply Configuration

```bash
terraform apply
```

This will create:
- Email notification channels
- Cloud Monitoring alert policies
- Optional: Cloud Function for metric export (if using cloud_function.tf)

## Usage

### Daily Workflow

1. **Run dataset hierarchy analysis:**
   ```bash
   ./lc dataset-hierarchy \
     --project your-project-id \
     --batch-mgmt-table governance_metadata.batch_management \
     --bq-table governance_metadata.hierarchy_analysis
   ```

2. **Run alert detection:**
   ```bash
   ./lc bq-alerts \
     --project your-project-id \
     --batch-mgmt-table governance_metadata.batch_management \
     --alerts-table governance_metadata.size_alerts
   ```

3. **Alerts are automatically detected** and saved to the alerts table

4. **Cloud Monitoring policies** monitor the alerts and send notifications

### Query Alerts

```sql
-- View all pending alerts
SELECT * 
FROM `governance_metadata.size_alerts`
WHERE status = 'PENDING'
ORDER BY alert_timestamp DESC;

-- View critical alerts
SELECT * 
FROM `governance_metadata.size_alerts`
WHERE severity = 'CRITICAL'
  AND status = 'PENDING'
ORDER BY alert_timestamp DESC;

-- View alerts by metric
SELECT 
  metric_name,
  severity,
  change_percent,
  alert_message
FROM `governance_metadata.size_alerts`
WHERE status = 'PENDING'
ORDER BY severity DESC, change_percent DESC;
```

## Alert Thresholds

### Default Thresholds

| Severity | Percent Threshold | Absolute Threshold (GB) |
|----------|-------------------|------------------------|
| CRITICAL | >100%             | >50 GB                 |
| HIGH     | >50%              | >20 GB                 |
| MEDIUM   | >20%              | >10 GB                 |
| LOW      | <20%              | <10 GB                 |

### Customizing Thresholds

Set environment variables in your `.env` file:

```bash
# Percentage thresholds
ALERT_SIZE_INCREASE_PERCENT=20.0
ALERT_TOTAL_BYTES_PERCENT=20.0
ALERT_NUM_TABLES_PERCENT=10.0
ALERT_NUM_DATASETS_PERCENT=5.0
ALERT_TOTAL_ROWS_PERCENT=20.0

# Absolute thresholds (GB)
ALERT_SIZE_INCREASE_ABSOLUTE_GB=10.0
ALERT_TOTAL_BYTES_ABSOLUTE_GB=10.0

# Severity thresholds
ALERT_CRITICAL_PERCENT=100.0
ALERT_CRITICAL_ABSOLUTE_GB=50.0
ALERT_HIGH_PERCENT=50.0
ALERT_HIGH_ABSOLUTE_GB=20.0
ALERT_MEDIUM_PERCENT=20.0
ALERT_MEDIUM_ABSOLUTE_GB=10.0

# Options
ALERT_ON_LOW=false  # Set to true to also alert on LOW severity
```

## Notification Channels

### Email (Currently Supported)

Configure email recipients in `terraform.tfvars`:

```hcl
alert_email_recipients = [
  "team@example.com"
]
```

### Slack (Optional)

Uncomment and configure in `notification_channels.tf`:

```hcl
resource "google_monitoring_notification_channel" "slack_alerts" {
  display_name = "Data Lake Alerts - Slack"
  type         = "slack"
  
  labels = {
    channel_name = "#data-lake-alerts"
  }
  
  sensitive_labels {
    auth_token = var.slack_webhook_url
  }
}
```

### PagerDuty (Optional)

Uncomment and configure in `notification_channels.tf`:

```hcl
resource "google_monitoring_notification_channel" "pagerduty_alerts" {
  display_name = "Data Lake Alerts - PagerDuty"
  type         = "pagerduty"
  
  labels = {
    service_key = var.pagerduty_service_key
  }
}
```

## Integration with Cloud Scheduler

### Option 1: Manual CLI Runs

Run both commands manually after daily dataset-hierarchy:

```bash
# Daily workflow
./lc dataset-hierarchy --project your-project --batch-mgmt-table dataset.batch_management
./lc bq-alerts --project your-project --batch-mgmt-table dataset.batch_management
```

### Option 2: Cloud Scheduler

Create a Cloud Scheduler job to run bq-alerts after dataset-hierarchy:

```bash
gcloud scheduler jobs create http bq-alerts-daily \
  --location=us-central1 \
  --schedule="0 4 * * *" \
  --uri="https://your-cloud-function-url/run" \
  --http-method=POST \
  --message-body='{"project_id":"your-project","batch_mgmt_table":"dataset.batch_management"}' \
  --oidc-service-account-email=your-sa@project.iam.gserviceaccount.com
```

## Monitoring the Monitoring System

Query alert statistics:

```sql
-- Alert summary by severity
SELECT 
  severity,
  COUNT(*) as count,
  AVG(change_percent) as avg_change_percent,
  MAX(change_percent) as max_change_percent
FROM `governance_metadata.size_alerts`
WHERE DATE(alert_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY severity
ORDER BY 
  CASE severity
    WHEN 'CRITICAL' THEN 1
    WHEN 'HIGH' THEN 2
    WHEN 'MEDIUM' THEN 3
    WHEN 'LOW' THEN 4
  END;

-- Alert trend over time
SELECT 
  DATE(alert_timestamp) as date,
  COUNT(*) as alert_count,
  COUNTIF(severity = 'CRITICAL') as critical_count,
  COUNTIF(severity = 'HIGH') as high_count
FROM `governance_metadata.size_alerts`
WHERE DATE(alert_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY date
ORDER BY date DESC;
```

## Troubleshooting

### Alerts Not Being Generated

1. **Check batch_management table:**
   ```sql
   SELECT * FROM `governance_metadata.batch_management`
   ORDER BY ldts DESC LIMIT 5;
   ```

2. **Check for data:**
   ```sql
   SELECT COUNT(*) FROM `governance_metadata.batch_management`
   WHERE project_id = 'your-project-id';
   ```

3. **Run bq-alerts manually:**
   ```bash
   ./lc bq-alerts --project your-project-id --batch-mgmt-table dataset.batch_management --alerts-table dataset.size_alerts
   ```

### Cloud Monitoring Policies Not Triggering

1. **Check notification channels:**
   - GCP Console → Monitoring → Alerting → Notification Channels
   - Verify email addresses are correct

2. **Check alert policies:**
   - GCP Console → Monitoring → Alerting → Policies
   - Verify policies are enabled

3. **Check BigQuery alerts table:**
   ```sql
   SELECT * FROM `governance_metadata.size_alerts`
   WHERE status = 'PENDING'
   ORDER BY alert_timestamp DESC LIMIT 10;
   ```

### Cloud Function Not Running

If using the optional Cloud Function:

1. **Check function logs:**
   ```bash
   gcloud functions logs read bq-alerts-to-metrics --region=us-central1
   ```

2. **Verify Pub/Sub topic exists:**
   ```bash
   gcloud pubsub topics list
   ```

3. **Test function manually:**
   ```bash
   gcloud functions call bq-alerts-to-metrics --region=us-central1
   ```

## Cleanup

To remove all resources:

```bash
terraform destroy
```

This will remove:
- Alert policies
- Notification channels
- Cloud Function (if created)
- Service accounts and IAM bindings

**Note:** This does NOT delete the BigQuery alerts table. Manually delete if needed:

```sql
DROP TABLE `governance_metadata.size_alerts`;
```

