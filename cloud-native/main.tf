terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
  required_version = ">= 1.3"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_cloud_run_service" "lake_management_api" {
  name     = "lake-management-api"
  location = var.region

  template {
    spec {
      containers {
        image = var.image_url
        ports {
          container_port = 8080
        }
        env {
          name  = "GOOGLE_PROJECT"
          value = var.project_id
        }
        
        # Optional: Set default environment variables
        dynamic "env" {
          for_each = var.default_env_vars
          content {
            name  = env.key
            value = env.value
          }
        }
      }
      
      service_account_name = google_service_account.api_sa.email
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}

# Service account for Cloud Run service
resource "google_service_account" "api_sa" {
  account_id   = "lake-management-api"
  display_name = "Lake Management API Service Account"
}

# IAM permissions for the service account
resource "google_project_iam_member" "api_bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_bigquery_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

# Cloud Run service IAM - allow Cloud Scheduler to invoke
resource "google_cloud_run_service_iam_member" "invoker" {
  location = google_cloud_run_service.lake_management_api.location
  service  = google_cloud_run_service.lake_management_api.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_sa.email}"
}

# Optional: Allow public access (remove if using only authenticated calls)
# resource "google_cloud_run_service_iam_member" "public_invoker" {
#   location = google_cloud_run_service.lake_management_api.location
#   service  = google_cloud_run_service.lake_management_api.name
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "image_url" {
  description = "Docker image URL (Artifact Registry or GCR)"
  type        = string
}

variable "default_env_vars" {
  description = "Default environment variables for the container"
  type        = map(string)
  default     = {}
}

output "service_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_service.lake_management_api.status[0].url
}

output "service_account_email" {
  description = "Service account email for the API"
  value       = google_service_account.api_sa.email
}
