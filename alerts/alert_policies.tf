# Cloud Monitoring Alert Policies for BigQuery Table Size Changes

# Note: These alert policies work in conjunction with the alerts written to BigQuery
# by the bq-alerts CLI command. The alerts table is populated daily when the
# dataset-hierarchy command runs and then bq-alerts detects changes.
#
# To use these policies, you have two options:
#
# Option 1: Use Log-based Metrics (Recommended)
#   - The bq-alerts command writes to BigQuery alerts table
#   - Create a Cloud Function that reads alerts and writes to Cloud Logging
#   - Create log-based metrics from those logs
#   - Create alert policies on those metrics
#
# Option 2: Use BigQuery Scheduled Queries + MQL
#   - Create a BigQuery scheduled query that checks for new alerts
#   - Use Cloud Monitoring MQL to query BigQuery (if supported)
#
# Option 3: Direct BigQuery Metric Export (Current Implementation)
#   - We provide alert policies that can monitor BigQuery dataset metrics
#   - These work alongside the alerts table for comprehensive monitoring

# Alert Policy: Critical Size Increase
resource "google_monitoring_alert_policy" "critical_size_increase" {
  display_name = "BigQuery Data Lake - Critical Size Increase"
  combiner     = "OR"
  
  conditions {
    display_name = "Critical size increase detected in alerts table"
    
    condition_threshold {
      filter          = "resource.type=\"bigquery_dataset\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.critical_size_increase_percent
      
      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_RATE"
      }
      
      # Note: This is a placeholder filter.
      # In practice, you'll need to create a log-based metric or
      # use a Cloud Function to convert BigQuery alerts to metrics
      filter = <<-EOT
        resource.type="global"
        metric.type="custom.googleapis.com/bigquery/size_increase_percent"
      EOT
    }
  }
  
  notification_channels = google_monitoring_notification_channel.email_alerts[*].name
  
  alert_strategy {
    auto_close = var.alert_auto_close_seconds > 0 ? "${var.alert_auto_close_seconds}s" : null
  }
  
  documentation {
    content = <<-EOT
      A critical size increase (>${var.critical_size_increase_percent}% or >${var.critical_size_increase_gb}GB) 
      has been detected in the BigQuery data lake.
      
      Check the alerts table: ${var.alerts_table}
      
      This alert is generated from the batch_management table comparisons.
      Run: ./lc bq-alerts --project ${var.project_id} --batch-mgmt-table ${var.batch_management_table}
    EOT
    mime_type = "text/markdown"
  }
}

# Alert Policy: High Severity Size Increase
resource "google_monitoring_alert_policy" "high_size_increase" {
  display_name = "BigQuery Data Lake - High Size Increase"
  combiner     = "OR"
  
  conditions {
    display_name = "High size increase detected in alerts table"
    
    condition_threshold {
      filter          = "resource.type=\"bigquery_dataset\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.high_size_increase_percent
      
      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_RATE"
      }
      
      filter = <<-EOT
        resource.type="global"
        metric.type="custom.googleapis.com/bigquery/size_increase_percent"
      EOT
    }
  }
  
  notification_channels = google_monitoring_notification_channel.email_alerts[*].name
  
  alert_strategy {
    auto_close = var.alert_auto_close_seconds > 0 ? "${var.alert_auto_close_seconds}s" : null
  }
  
  documentation {
    content = <<-EOT
      A high severity size increase (>${var.high_size_increase_percent}% or >${var.high_size_increase_gb}GB) 
      has been detected in the BigQuery data lake.
      
      Check the alerts table: ${var.alerts_table}
    EOT
    mime_type = "text/markdown"
  }
}

# Alert Policy: Medium Severity Size Increase
resource "google_monitoring_alert_policy" "medium_size_increase" {
  display_name = "BigQuery Data Lake - Medium Size Increase"
  combiner     = "OR"
  
  conditions {
    display_name = "Medium size increase detected in alerts table"
    
    condition_threshold {
      filter          = "resource.type=\"bigquery_dataset\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.medium_size_increase_percent
      
      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_RATE"
      }
      
      filter = <<-EOT
        resource.type="global"
        metric.type="custom.googleapis.com/bigquery/size_increase_percent"
      EOT
    }
  }
  
  notification_channels = google_monitoring_notification_channel.email_alerts[*].name
  
  alert_strategy {
    auto_close = var.alert_auto_close_seconds > 0 ? "${var.alert_auto_close_seconds}s" : null
  }
  
  documentation {
    content = <<-EOT
      A medium severity size increase (>${var.medium_size_increase_percent}% or >${var.medium_size_increase_gb}GB) 
      has been detected in the BigQuery data lake.
      
      Check the alerts table: ${var.alerts_table}
    EOT
    mime_type = "text/markdown"
  }
}

