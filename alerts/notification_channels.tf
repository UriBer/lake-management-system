# Notification Channels for Cloud Monitoring Alerts

# Email notification channels
resource "google_monitoring_notification_channel" "email_alerts" {
  count = length(var.alert_email_recipients)
  
  display_name = "Data Lake Alerts - ${var.alert_email_recipients[count.index]}"
  type         = "email"
  
  labels = {
    email_address = var.alert_email_recipients[count.index]
  }
  
  enabled = true
}

# Optional: Slack notification channel
# Uncomment and configure if you want Slack notifications
# resource "google_monitoring_notification_channel" "slack_alerts" {
#   display_name = "Data Lake Alerts - Slack"
#   type         = "slack"
#   
#   labels = {
#     channel_name = "#data-lake-alerts"
#   }
#   
#   sensitive_labels {
#     auth_token = var.slack_webhook_url
#   }
#   
#   enabled = true
# }

# Optional: PagerDuty notification channel
# Uncomment and configure if you want PagerDuty notifications
# resource "google_monitoring_notification_channel" "pagerduty_alerts" {
#   display_name = "Data Lake Alerts - PagerDuty"
#   type         = "pagerduty"
#   
#   labels = {
#     service_key = var.pagerduty_service_key
#   }
#   
#   enabled = true
# }

