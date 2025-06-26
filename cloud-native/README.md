# BigQuery Column Description Updater

This solution updates column descriptions in BigQuery tables using metadata stored in a governance table. It is built to run via a FastAPI service deployed on Cloud Run, with optional daily triggering using Cloud Scheduler.

---

## 📦 Contents

- `update_column_descriptions.py` – Python script to update BigQuery column descriptions.
- `api_server.py` – FastAPI server exposing a `/run` endpoint to trigger the script.
- `Dockerfile` – Container to run the FastAPI service.
- `requirements.txt` – Python dependencies.
- `main.tf` – Terraform configuration for Cloud Run deployment.
- `cloud_scheduler.tf` – Terraform to schedule daily execution via Cloud Scheduler.
- `iam_permissions.tf` – Terraform to provision service account and necessary IAM permissions.

---

## 🚀 Setup Instructions

### 1. Build & Push Docker Image

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/bq-column-updater
```

### 2. Deploy Infrastructure with Terraform

```bash
terraform init
terraform apply \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="image_url=gcr.io/YOUR_PROJECT_ID/bq-column-updater" \
  -var="metadata_table=your_dataset.system_metadata" \
  -var="job_run_table=your_dataset.job_runs" \
  -var="scheduler_sa=cloud-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

---

## 🧪 API Usage

Once deployed, trigger a manual run using:

```bash
curl -X POST https://YOUR-CLOUDRUN-URL/run \
  -H 'Content-Type: application/json' \
  -d '{
    "project_id": "your-project",
    "metadata_table": "dataset.system_metadata",
    "job_run_table": "dataset.job_runs",
    "sleep_ms": 500,
    "max_workers": 5
  }'
```

---

## 📅 Scheduled Runs

A Cloud Scheduler job will automatically invoke the updater daily at 03:00 UTC.

---

## 🔐 IAM Requirements

The Cloud Scheduler service account must have the following roles:
- `roles/run.invoker`
- `roles/logging.logWriter`

These are provisioned via `iam_permissions.tf`.

---

## 🌐 Notes

- Ensure BigQuery datasets and tables exist before deployment.
- The script logs all changes to a `job_run_table` for audit and tracking.

