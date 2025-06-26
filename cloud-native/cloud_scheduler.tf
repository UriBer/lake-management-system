resource "google_cloud_scheduler_job" "column_updater_schedule" {
  name             = "column-updater-job"
  description      = "Trigger BigQuery column updater via Cloud Scheduler"
  schedule         = "0 3 * * *"
  time_zone        = "UTC"
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = google_cloud_run_service.column_updater.status[0].url
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode(jsonencode({
      project_id     = var.project_id,
      metadata_table = var.metadata_table,
      job_run_table  = var.job_run_table,
      sleep_ms       = 500,
      max_workers    = 5
    }))
    oidc_token {
      service_account_email = var.scheduler_sa
    }
  }
}

variable "metadata_table" {}
variable "job_run_table" {}
variable "scheduler_sa" {
  description = "Service Account used to authenticate Cloud Scheduler job"
}
