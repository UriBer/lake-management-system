# Lake Management System - Cloud-Native Deployment

Unified API service for all BigQuery lake management operations, deployed on Cloud Run with scheduled execution via Cloud Scheduler.

## 📦 Overview

This cloud-native solution exposes all CLI commands as HTTP endpoints:
- **Dataset Hierarchy Analysis** - Complete project hierarchy with batch management
- **BigQuery Alerts** - Day-over-day size change detection
- **Update Metadata** - Column description updates
- **Table List** - Extract table information to CSV
- **Schema Compare** - Compare table schemas
- **Table Compare** - Compare table data

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Cloud Scheduler                                         │
│  ├─ dataset-hierarchy-daily (2 AM UTC)                 │
│  ├─ bq-alerts-daily (3 AM UTC)                          │
│  └─ update-metadata-daily (3 AM UTC)                    │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  Cloud Run - Lake Management API                        │
│  └─ FastAPI server with all CLI endpoints               │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  BigQuery                                                │
│  ├─ batch_management                                    │
│  ├─ hierarchy_analysis                                  │
│  ├─ size_alerts                                         │
│  └─ governance_metadata                                │
└─────────────────────────────────────────────────────────┘
```

## 📦 Contents

- `api_server.py` - FastAPI server with all endpoints
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies
- `main.tf` - Cloud Run deployment
- `cloud_scheduler.tf` - Scheduled jobs configuration
- `iam_permissions.tf` - Service account and IAM roles

## 🚀 Setup Instructions

### Prerequisites

1. **GCP Project** with BigQuery APIs enabled
2. **Terraform** (>= 1.3)
3. **Docker** (for building images)
4. **gcloud CLI** configured with appropriate permissions

### 1. Prepare Modules

Copy CLI modules from `app-cli` to `cloud-native`:

```bash
# From project root
mkdir -p cloud-native/modules
cp -r app-cli/modules/* cloud-native/modules/
```

### 2. Build Docker Image

```bash
cd cloud-native

# Build and push to Artifact Registry (recommended)
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/lake-management-api

# Or use Artifact Registry
# gcloud builds submit --tag REGION-docker.pkg.dev/YOUR_PROJECT_ID/REPO/lake-management-api
```

### 3. Configure Terraform Variables

Create `terraform.tfvars`:

```hcl
project_id = "your-project-id"
region     = "us-central1"
image_url  = "gcr.io/your-project-id/lake-management-api"

# Dataset Hierarchy Configuration
batch_mgmt_table  = "governance_metadata.batch_management"
hierarchy_bq_table = "governance_metadata.hierarchy_analysis"

# Alerts Configuration
alerts_table = "governance_metadata.size_alerts"

# Metadata Update Configuration
metadata_table = "governance_metadata.system_metadata"
job_run_table  = "governance_metadata.job_runs"
sleep_ms       = 500
max_workers    = 10

# Schedule Configuration (optional - uses defaults)
dataset_hierarchy_schedule = "0 2 * * *"  # Daily at 2 AM UTC
bq_alerts_schedule        = "0 3 * * *"   # Daily at 3 AM UTC (after hierarchy)
update_metadata_schedule  = "0 3 * * *"   # Daily at 3 AM UTC
timezone                  = "UTC"
```

### 4. Deploy with Terraform

```bash
terraform init
terraform plan
terraform apply
```

This will create:
- Cloud Run service
- Service accounts with IAM roles
- Cloud Scheduler jobs for daily execution

## 📡 API Endpoints

### Health Check

```bash
GET /
GET /health
```

### Dataset Hierarchy Analysis

```bash
POST /dataset-hierarchy
Content-Type: application/json

{
  "project_id": "your-project-id",
  "batch_mgmt_table": "governance_metadata.batch_management",
  "bq_table": "governance_metadata.hierarchy_analysis",
  "format": "json",
  "compare_latest": true,
  "include_views": false
}
```

### BigQuery Alerts

```bash
POST /bq-alerts
Content-Type: application/json

{
  "project_id": "your-project-id",
  "batch_mgmt_table": "governance_metadata.batch_management",
  "alerts_table": "governance_metadata.size_alerts"
}
```

### Update Metadata

```bash
POST /update-metadata
Content-Type: application/json

{
  "project_id": "your-project-id",
  "metadata_table": "governance_metadata.system_metadata",
  "job_run_table": "governance_metadata.job_runs",
  "sleep_ms": 500,
  "max_workers": 10
}
```

### Table List

```bash
POST /table-list
Content-Type: application/json

{
  "project_id": "your-project-id",
  "dataset": "my_dataset",
  "include_views": false,
  "verbose": true
}
```

### Schema Compare

```bash
POST /schema-compare
Content-Type: application/json

{
  "table_a": "dataset1.table1",
  "table_b": "dataset2.table2",
  "project_id": "your-project-id"
}
```

### Table Compare

```bash
POST /table-compare
Content-Type: application/json

{
  "table_a": "dataset1.table1",
  "table_b": "dataset2.table2",
  "project_id": "your-project-id"
}
```

### Generic Command Endpoint

```bash
POST /command
Content-Type: application/json

{
  "command": "dataset-hierarchy",
  "project_id": "your-project-id",
  "args": {
    "format": "tree",
    "batch_mgmt_table": "dataset.batch_management"
  }
}
```

## 📅 Scheduled Jobs

### Daily Dataset Hierarchy Analysis

- **Schedule**: Daily at 2:00 AM UTC (configurable)
- **Job Name**: `dataset-hierarchy-daily`
- **Purpose**: Analyze complete dataset hierarchy, save to BigQuery, track changes
- **Execution Time**: ~5-30 minutes depending on project size

### Daily BigQuery Alerts

- **Schedule**: Daily at 3:00 AM UTC (configurable, runs after hierarchy)
- **Job Name**: `bq-alerts-daily`
- **Purpose**: Detect significant size changes and generate alerts
- **Dependencies**: Requires `dataset-hierarchy-daily` to complete first

### Daily Metadata Update

- **Schedule**: Daily at 3:00 AM UTC (configurable)
- **Job Name**: `update-metadata-daily`
- **Purpose**: Update column descriptions from metadata table

### Managing Schedules

```bash
# Pause a job
gcloud scheduler jobs pause dataset-hierarchy-daily --location=us-central1

# Resume a job
gcloud scheduler jobs resume dataset-hierarchy-daily --location=us-central1

# Update schedule
terraform apply -var="dataset_hierarchy_schedule='0 4 * * *'"

# Disable jobs via Terraform
terraform apply -var="dataset_hierarchy_paused=true"
```

## 🔐 IAM Permissions

### Cloud Run Service Account

- `roles/bigquery.jobUser` - Execute BigQuery jobs
- `roles/bigquery.dataEditor` - Write to BigQuery tables
- `roles/bigquery.dataViewer` - Read from BigQuery tables
- `roles/logging.logWriter` - Write logs

### Cloud Scheduler Service Account

- `roles/run.invoker` - Invoke Cloud Run service
- `roles/logging.logWriter` - Write logs

## 🧪 Testing

### Manual API Invocation

```bash
# Get service URL
SERVICE_URL=$(terraform output -raw service_url)

# Health check
curl $SERVICE_URL/health

# Run dataset hierarchy
curl -X POST $SERVICE_URL/dataset-hierarchy \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "your-project-id",
    "batch_mgmt_table": "governance_metadata.batch_management"
  }'

# Run alerts detection
curl -X POST $SERVICE_URL/bq-alerts \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "your-project-id",
    "batch_mgmt_table": "governance_metadata.batch_management"
  }'
```

### Testing with Authentication

```bash
# Get ID token
TOKEN=$(gcloud auth print-identity-token)

# Invoke with authentication
curl -X POST $SERVICE_URL/dataset-hierarchy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{...}'
```

## 📊 Monitoring

### Cloud Run Logs

```bash
# View recent logs
gcloud run services logs read lake-management-api --region=us-central1 --limit=50

# Follow logs
gcloud run services logs tail lake-management-api --region=us-central1
```

### Cloud Scheduler Jobs

```bash
# List all jobs
gcloud scheduler jobs list --location=us-central1

# View job details
gcloud scheduler jobs describe dataset-hierarchy-daily --location=us-central1

# View job execution history
gcloud scheduler jobs describe dataset-hierarchy-daily --location=us-central1 \
  --format="value(state.lastAttemptTime)"
```

### Query Alert Results

```sql
-- View latest alerts
SELECT * 
FROM `governance_metadata.size_alerts`
WHERE status = 'PENDING'
ORDER BY alert_timestamp DESC
LIMIT 10;

-- Alert summary by severity
SELECT 
  severity,
  COUNT(*) as count,
  AVG(change_percent) as avg_change_percent
FROM `governance_metadata.size_alerts`
WHERE DATE(alert_timestamp) = CURRENT_DATE()
GROUP BY severity;
```

## 🔄 Updating

### Update Docker Image

```bash
# Rebuild and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/lake-management-api

# Update Cloud Run service
terraform apply -var="image_url=gcr.io/YOUR_PROJECT_ID/lake-management-api"
```

### Update Schedule

```bash
terraform apply -var="dataset_hierarchy_schedule='0 4 * * *'"
```

### Update Environment Variables

Edit `main.tf` and add to `default_env_vars`:

```hcl
variable "default_env_vars" {
  default = {
    "MAX_PARALLEL_WORKERS" = "20"
    "BATCH_MGMT_TABLE"     = "governance_metadata.batch_management"
  }
}
```

## 🛠️ Troubleshooting

### Service Not Starting

```bash
# Check Cloud Run service status
gcloud run services describe lake-management-api --region=us-central1

# Check logs for errors
gcloud run services logs read lake-management-api --region=us-central1 --limit=100
```

### Scheduler Jobs Failing

```bash
# Check job status
gcloud scheduler jobs describe dataset-hierarchy-daily --location=us-central1

# Check execution history
gcloud logging read "resource.type=cloud_scheduler_job" --limit=10

# Verify service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:cloud-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

### BigQuery Permission Errors

Ensure the Cloud Run service account has:
- `roles/bigquery.jobUser`
- `roles/bigquery.dataEditor` (for writes)
- `roles/bigquery.dataViewer` (for reads)

```bash
# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:lake-management-api@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

### Module Import Errors

Ensure modules are copied correctly:

```bash
# Verify modules directory
ls -la cloud-native/modules/

# Should include:
# - __init__.py
# - dataset_hierarchy.py
# - bq_alerts.py
# - table_list.py
# - schema_compare.py
# - table_compare.py
# - update_metadata.py
```

## 🗑️ Cleanup

To remove all resources:

```bash
terraform destroy
```

This will remove:
- Cloud Run service
- Cloud Scheduler jobs
- Service accounts and IAM bindings

**Note:** BigQuery tables are NOT deleted. Manually delete if needed:

```sql
DROP TABLE `governance_metadata.batch_management`;
DROP TABLE `governance_metadata.hierarchy_analysis`;
DROP TABLE `governance_metadata.size_alerts`;
```

## 📚 Related Documentation

- [CLI Documentation](../app-cli/README.md) - Local CLI usage
- [Alerts Documentation](../alerts/README.md) - Cloud Monitoring alert setup

## 🔗 Integration with Cloud Monitoring

After deployment, set up Cloud Monitoring alerts:

```bash
cd ../alerts
terraform apply
```

This will create alert policies that monitor the BigQuery alerts table and send notifications via email, Slack, or other configured channels.
