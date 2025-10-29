# Cloud Scheduler Jobs for Lake Management System

# ============================================================================
# Dataset Hierarchy - Daily Analysis
# ============================================================================

resource "google_cloud_scheduler_job" "dataset_hierarchy_daily" {
  name             = "dataset-hierarchy-daily"
  description      = "Daily dataset hierarchy analysis with batch management"
  schedule         = var.dataset_hierarchy_schedule
  time_zone        = var.timezone
  attempt_deadline = "600s"  # 10 minutes for large projects
  paused           = var.dataset_hierarchy_paused

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.lake_management_api.status[0].url}/dataset-hierarchy"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode(jsonencode({
      project_id        = var.project_id
      batch_mgmt_table  = var.batch_mgmt_table
      bq_table         = var.hierarchy_bq_table
      format           = "json"
      compare_latest   = true
    }))
    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }
}

# ============================================================================
# BigQuery Alerts - Daily Alert Detection
# ============================================================================

resource "google_cloud_scheduler_job" "bq_alerts_daily" {
  name             = "bq-alerts-daily"
  description      = "Daily BigQuery size alert detection (runs after dataset-hierarchy)"
  schedule         = var.bq_alerts_schedule
  time_zone        = var.timezone
  attempt_deadline = "300s"  # 5 minutes
  paused           = var.bq_alerts_paused

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.lake_management_api.status[0].url}/bq-alerts"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode(jsonencode({
      project_id      = var.project_id
      batch_mgmt_table = var.batch_mgmt_table
      alerts_table   = var.alerts_table
    }))
    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }
  
  # Run after dataset-hierarchy completes
  depends_on = [google_cloud_scheduler_job.dataset_hierarchy_daily]
}

# ============================================================================
# Update Metadata - Daily (Legacy)
# ============================================================================

resource "google_cloud_scheduler_job" "update_metadata_daily" {
  name             = "update-metadata-daily"
  description      = "Daily column metadata update"
  schedule         = var.update_metadata_schedule
  time_zone        = var.timezone
  attempt_deadline = "320s"
  paused           = var.update_metadata_paused

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.lake_management_api.status[0].url}/update-metadata"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode(jsonencode({
      project_id    = var.project_id
      metadata_table = var.metadata_table
      job_run_table  = var.job_run_table
      sleep_ms       = var.sleep_ms
      max_workers    = var.max_workers
    }))
    oidc_token {
      service_account_email = google_service_account.scheduler_sa.email
    }
  }
}

# ============================================================================
# Variables
# ============================================================================

variable "timezone" {
  description = "Timezone for scheduled jobs"
  type        = string
  default     = "UTC"
}

variable "dataset_hierarchy_schedule" {
  description = "Cron schedule for dataset hierarchy analysis (default: daily at 2 AM UTC)"
  type        = string
  default     = "0 2 * * *"
}

variable "bq_alerts_schedule" {
  description = "Cron schedule for BQ alerts (default: daily at 3 AM UTC, after dataset-hierarchy)"
  type        = string
  default     = "0 3 * * *"
}

variable "update_metadata_schedule" {
  description = "Cron schedule for metadata updates (default: daily at 3 AM UTC)"
  type        = string
  default     = "0 3 * * *"
}

variable "dataset_hierarchy_paused" {
  description = "Whether to pause the dataset hierarchy job"
  type        = bool
  default     = false
}

variable "bq_alerts_paused" {
  description = "Whether to pause the BQ alerts job"
  type        = bool
  default     = false
}

variable "update_metadata_paused" {
  description = "Whether to pause the update metadata job"
  type        = bool
  default     = false
}

variable "batch_mgmt_table" {
  description = "Batch management table for dataset hierarchy (format: dataset.table or project.dataset.table)"
  type        = string
  default     = ""
}

variable "hierarchy_bq_table" {
  description = "BigQuery table to save hierarchy analysis (format: dataset.table or project.dataset.table)"
  type        = string
  default     = ""
}

variable "alerts_table" {
  description = "Alerts table for size change alerts (format: dataset.table or project.dataset.table)"
  type        = string
  default     = "governance_metadata.size_alerts"
}

variable "metadata_table" {
  description = "Metadata table for column descriptions"
  type        = string
  default     = ""
}

variable "job_run_table" {
  description = "Job run tracking table"
  type        = string
  default     = ""
}

variable "sleep_ms" {
  description = "Sleep milliseconds between metadata updates"
  type        = number
  default     = 500
}

variable "max_workers" {
  description = "Maximum parallel workers for metadata updates"
  type        = number
  default     = 10
}
