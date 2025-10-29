# OPTIONAL: Cloud Function to convert BigQuery alerts to Cloud Monitoring metrics
# 
# This is an optional component. The alert policies can work directly with BigQuery
# queries or log-based metrics. Uncomment and configure if you need automatic metric
# export from BigQuery alerts table to Cloud Monitoring.
#
# To use this:
# 1. Package the bq_alerts.py module or create a separate Cloud Function handler
# 2. Update source_archive_object to point to the packaged zip file
# 3. Uncomment the resources below

# resource "google_cloudfunctions_function" "alert_to_metric" {
#   name        = "bq-alerts-to-metrics"
#   description = "Converts BigQuery alerts to Cloud Monitoring metrics"
#   runtime     = "python39"
#   region      = var.region
# 
#   available_memory_mb   = 256
#   source_archive_bucket = google_storage_bucket.functions_source.name
#   source_archive_object = google_storage_bucket_object.function_source.name
#   entry_point           = "process_alerts"
#   timeout               = 540
# 
#   environment_variables = {
#     PROJECT_ID           = var.project_id
#     ALERTS_TABLE         = var.alerts_table
#     BATCH_MGMT_TABLE     = var.batch_management_table
#   }
# 
#   event_trigger {
#     event_type = "google.pubsub.topic.publish"
#     resource   = google_pubsub_topic.alert_trigger.name
#   }
# 
#   service_account_email = google_service_account.function_sa.email
# }
# 
# resource "google_service_account" "function_sa" {
#   account_id   = "bq-alerts-function"
#   display_name = "Cloud Function SA for BigQuery Alerts"
# }
# 
# resource "google_project_iam_member" "function_bigquery_user" {
#   project = var.project_id
#   role    = "roles/bigquery.dataViewer"
#   member  = "serviceAccount:${google_service_account.function_sa.email}"
# }
# 
# resource "google_project_iam_member" "function_monitoring_writer" {
#   project = var.project_id
#   role    = "roles/monitoring.metricWriter"
#   member  = "serviceAccount:${google_service_account.function_sa.email}"
# }
# 
# resource "google_pubsub_topic" "alert_trigger" {
#   name = "bq-alerts-trigger"
# }
# 
# resource "google_storage_bucket" "functions_source" {
#   name     = "${var.project_id}-functions-source"
#   location = var.region
# }
# 
# resource "google_storage_bucket_object" "function_source" {
#   name   = "bq-alerts-function-${timestamp()}.zip"
#   bucket = google_storage_bucket.functions_source.name
#   source = "../app-cli/modules/bq_alerts.py"  # Update with packaged zip
# }

