# Firebase Monitoring & Cost Control Module
# Manages quotas, alerts, and cost optimization for ACIM Guide

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment (staging, production)"
  type        = string
  default     = "production"
}

variable "monthly_budget_eur" {
  description = "Monthly budget in EUR"
  type        = number
  default     = 500
}

variable "alert_email" {
  description = "Email for budget alerts"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west3"
}

# Budget Alert for €500/month
resource "google_billing_budget" "monthly_budget" {
  billing_account = var.billing_account
  display_name    = "ACIM Guide Monthly Budget - ${var.environment}"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "EUR"
      units         = tostring(var.monthly_budget_eur)
    }
  }

  # Alert at 50%, 80%, and 100%
  threshold_rules {
    threshold_percent = 0.5
    spend_basis       = "CURRENT_SPEND"
  }
  threshold_rules {
    threshold_percent = 0.8
    spend_basis       = "CURRENT_SPEND"
  }
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }

  # Alert on forecasted spend at 100%
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "FORECASTED_SPEND"
  }

  all_updates_rule {
    monitoring_notification_channels = [
      google_monitoring_notification_channel.budget_alert.id
    ]
    disable_default_iam_recipients = false
  }
}

# Email notification channel for budget alerts
resource "google_monitoring_notification_channel" "budget_alert" {
  display_name = "Budget Alert Email - ${var.environment}"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Cloud Functions quota monitoring
resource "google_monitoring_alert_policy" "cloud_functions_quota" {
  display_name = "Cloud Functions Quota Alert - ${var.environment}"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Functions invocations approaching quota"

    condition_threshold {
      filter          = "resource.type=\"cloud_function\" AND metric.type=\"cloudfunctions.googleapis.com/function/executions\""
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 1800000 # 90% of 2M daily quota
      duration        = "300s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.budget_alert.id
  ]

  alert_strategy {
    auto_close = "1800s" # 30 minutes
  }
}

# Firestore quota monitoring
resource "google_monitoring_alert_policy" "firestore_quota" {
  display_name = "Firestore Operations Quota Alert - ${var.environment}"
  combiner     = "OR"

  conditions {
    display_name = "Firestore operations approaching quota"

    condition_threshold {
      filter          = "resource.type=\"gce_instance\" AND metric.type=\"firestore.googleapis.com/api/request_count\""
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 45000000 # 90% of 50M daily quota
      duration        = "300s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.budget_alert.id
  ]
}

# OpenAI token budget monitoring (custom metric)
resource "google_monitoring_alert_policy" "openai_token_budget" {
  display_name = "OpenAI Token Budget Alert - ${var.environment}"
  combiner     = "OR"

  conditions {
    display_name = "Daily OpenAI tokens approaching budget"

    condition_threshold {
      filter          = "resource.type=\"cloud_function\" AND metric.type=\"custom.googleapis.com/openai/daily_tokens\""
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 40000 # Alert at 80% of 50K token daily budget
      duration        = "300s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_MAX"
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.budget_alert.id
  ]
}

# Error rate monitoring for production stability
resource "google_monitoring_alert_policy" "cloud_functions_error_rate" {
  display_name = "Cloud Functions Error Rate Alert - ${var.environment}"
  combiner     = "OR"

  conditions {
    display_name = "High error rate in Cloud Functions"

    condition_threshold {
      filter     = "resource.type=\"cloud_function\" AND metric.type=\"cloudfunctions.googleapis.com/function/execution_count\" AND metric.label.status!=\"ok\""
      comparison = "COMPARISON_GREATER_THAN"
      threshold_value = 10 # More than 10 errors in 5 minutes
      duration   = "300s"

      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields      = ["resource.label.function_name"]
      }
    }
  }

  notification_channels = [
    google_monitoring_notification_channel.budget_alert.id
  ]
}

# Resource utilization dashboard
resource "google_monitoring_dashboard" "acim_guide_dashboard" {
  dashboard_json = jsonencode({
    displayName = "ACIM Guide - ${var.environment} Overview"
    
    mosaicLayout = {
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Cloud Functions Invocations"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_function\" AND metric.type=\"cloudfunctions.googleapis.com/function/executions\""
                    aggregation = {
                      alignmentPeriod    = "60s"
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                      groupByFields      = ["resource.label.function_name"]
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Executions/sec"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          width  = 6
          height = 4
          widget = {
            title = "Daily Token Usage"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_function\" AND metric.type=\"custom.googleapis.com/openai/daily_tokens\""
                    aggregation = {
                      alignmentPeriod    = "3600s"
                      perSeriesAligner   = "ALIGN_MAX"
                      crossSeriesReducer = "REDUCE_MAX"
                    }
                  }
                }
                plotType = "LINE"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Tokens"
                scale = "LINEAR"
              }
              thresholds = [{
                value = 40000
                color = "YELLOW"
                direction = "ABOVE"
              }, {
                value = 50000
                color = "RED"
                direction = "ABOVE"
              }]
            }
          }
        },
        {
          width  = 12
          height = 4
          widget = {
            title = "Function Memory and CPU Usage"
            xyChart = {
              dataSets = [
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_function\" AND metric.type=\"cloudfunctions.googleapis.com/function/user_memory_bytes\""
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_MEAN"
                        crossSeriesReducer = "REDUCE_MEAN"
                        groupByFields      = ["resource.label.function_name"]
                      }
                    }
                  }
                  plotType = "LINE"
                },
                {
                  timeSeriesQuery = {
                    timeSeriesFilter = {
                      filter = "resource.type=\"cloud_function\" AND metric.type=\"cloudfunctions.googleapis.com/function/execution_times\""
                      aggregation = {
                        alignmentPeriod    = "60s"
                        perSeriesAligner   = "ALIGN_MEAN"
                        crossSeriesReducer = "REDUCE_MEAN"
                        groupByFields      = ["resource.label.function_name"]
                      }
                    }
                  }
                  plotType = "LINE"
                }
              ]
              yAxis = {
                label = "Usage"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })
}

# Outputs
output "budget_id" {
  description = "ID of the created budget"
  value       = google_billing_budget.monthly_budget.id
}

output "notification_channel_id" {
  description = "ID of the notification channel"
  value       = google_monitoring_notification_channel.budget_alert.id
}

output "dashboard_id" {
  description = "ID of the monitoring dashboard"
  value       = google_monitoring_dashboard.acim_guide_dashboard.id
}
