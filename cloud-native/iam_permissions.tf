# IAM Permissions for Cloud Scheduler Service Account

resource "google_service_account" "scheduler_sa" {
  account_id   = "cloud-scheduler"
  display_name = "Cloud Scheduler SA for Lake Management"
}

# Permission to invoke Cloud Run service
resource "google_project_iam_member" "invoke_run_permission" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

resource "google_project_iam_member" "logging_permission" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

output "scheduler_service_account_email" {
  description = "Service account email for Cloud Scheduler"
  value       = google_service_account.scheduler_sa.email
}
