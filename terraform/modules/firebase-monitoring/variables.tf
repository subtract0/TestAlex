variable "billing_account" {
  description = "Google Cloud billing account ID"
  type        = string
}

variable "project_id" {
  description = "GCP Project ID for ACIM Guide"
  type        = string
}

variable "environment" {
  description = "Environment (staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "monthly_budget_eur" {
  description = "Monthly budget in EUR for cost control"
  type        = number
  default     = 500
  
  validation {
    condition     = var.monthly_budget_eur > 0
    error_message = "Monthly budget must be greater than 0."
  }
}

variable "alert_email" {
  description = "Email address for budget and monitoring alerts"
  type        = string
  
  validation {
    condition     = can(regex("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$", var.alert_email))
    error_message = "Alert email must be a valid email address."
  }
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "europe-west3"
}

variable "openai_daily_token_budget" {
  description = "Daily OpenAI token budget"
  type        = number
  default     = 50000
}

variable "openai_daily_token_alert_threshold" {
  description = "Alert threshold for daily OpenAI tokens (percentage)"
  type        = number
  default     = 0.8
  
  validation {
    condition     = var.openai_daily_token_alert_threshold > 0 && var.openai_daily_token_alert_threshold <= 1
    error_message = "OpenAI token alert threshold must be between 0 and 1."
  }
}

variable "cloud_functions_quota_alert_threshold" {
  description = "Alert threshold for Cloud Functions quota (percentage of 2M daily quota)"
  type        = number
  default     = 0.9
  
  validation {
    condition     = var.cloud_functions_quota_alert_threshold > 0 && var.cloud_functions_quota_alert_threshold <= 1
    error_message = "Cloud Functions quota alert threshold must be between 0 and 1."
  }
}

variable "firestore_quota_alert_threshold" {
  description = "Alert threshold for Firestore operations quota (percentage of 50M daily quota)"
  type        = number
  default     = 0.9
  
  validation {
    condition     = var.firestore_quota_alert_threshold > 0 && var.firestore_quota_alert_threshold <= 1
    error_message = "Firestore quota alert threshold must be between 0 and 1."
  }
}
