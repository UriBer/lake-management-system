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

resource "google_cloud_run_service" "column_updater" {
  name     = "bq-column-updater"
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
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true
}

resource "google_cloud_run_service_iam_member" "invoker" {
  location        = google_cloud_run_service.column_updater.location
  service         = google_cloud_run_service.column_updater.name
  role            = "roles/run.invoker"
  member          = "allUsers"
}

variable "project_id" {}
variable "region"     { default = "us-central1" }
variable "image_url"  { description = "Docker image deployed to Artifact Registry or GCR" }