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

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "alert_email_recipients" {
  description = "List of email addresses to receive alerts"
  type        = list(string)
  default     = []
}

variable "batch_management_table" {
  description = "BigQuery batch management table (format: project.dataset.table or dataset.table)"
  type        = string
}

variable "alerts_table" {
  description = "BigQuery alerts table (format: project.dataset.table or dataset.table)"
  type        = string
  default     = "governance_metadata.size_alerts"
}

variable "critical_size_increase_percent" {
  description = "Critical alert threshold for size increase (percentage)"
  type        = number
  default     = 100.0
}

variable "high_size_increase_percent" {
  description = "High severity alert threshold for size increase (percentage)"
  type        = number
  default     = 50.0
}

variable "medium_size_increase_percent" {
  description = "Medium severity alert threshold for size increase (percentage)"
  type        = number
  default     = 20.0
}

variable "critical_size_increase_gb" {
  description = "Critical alert threshold for size increase (GB)"
  type        = number
  default     = 50.0
}

variable "high_size_increase_gb" {
  description = "High severity alert threshold for size increase (GB)"
  type        = number
  default     = 20.0
}

variable "medium_size_increase_gb" {
  description = "Medium severity alert threshold for size increase (GB)"
  type        = number
  default     = 10.0
}

variable "alert_auto_close_seconds" {
  description = "Auto-close alerts after this many seconds (0 to disable)"
  type        = number
  default     = 1800  # 30 minutes
}

output "notification_channels" {
  description = "Created notification channel IDs"
  value       = google_monitoring_notification_channel.email_alerts[*].name
}

output "alert_policies" {
  description = "Created alert policy IDs"
  value       = {
    critical = google_monitoring_alert_policy.critical_size_increase.id
    high     = google_monitoring_alert_policy.high_size_increase.id
    medium   = google_monitoring_alert_policy.medium_size_increase.id
  }
}

