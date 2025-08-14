# ACIM Guide Production Infrastructure
# Complete DevOps setup with monitoring, auto-scaling, and cost control

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta" 
      version = "~> 4.0"
    }
  }
  
  backend "gcs" {
    bucket = "acimguide-terraform-state"
    prefix = "production"
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID for ACIM Guide"
  type        = string
  default     = "acimguide-app"
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west3"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "monthly_budget_eur" {
  description = "Monthly budget in EUR"
  type        = number
  default     = 500
}

variable "alert_email" {
  description = "Email for alerts and notifications"
  type        = string
}

variable "billing_account" {
  description = "GCP Billing Account ID"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository for CI/CD"
  type        = string
  default     = "your-org/acimguide-app"
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudfunctions.googleapis.com",
    "firestore.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "cloudbilling.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "firebase.googleapis.com"
  ])
  
  service = each.value
  
  disable_dependent_services = false
  disable_on_destroy         = false
}

# Firebase Monitoring Module
module "firebase_monitoring" {
  source = "./modules/firebase-monitoring"
  
  project_id         = var.project_id
  environment        = var.environment
  monthly_budget_eur = var.monthly_budget_eur
  alert_email        = var.alert_email
  billing_account    = var.billing_account
  region            = var.region
  
  depends_on = [google_project_service.required_apis]
}

# Cloud Scheduler for auto-scaling
resource "google_cloud_scheduler_job" "auto_scaling" {
  name             = "auto-scaling-trigger"
  description      = "Trigger auto-scaling function every 10 minutes"
  schedule         = "*/10 * * * *"
  time_zone        = "UTC"
  attempt_deadline = "300s"
  
  retry_config {
    retry_count = 3
  }
  
  pubsub_target {
    topic_name = google_pubsub_topic.auto_scaling.id
    data       = base64encode(jsonencode({
      trigger_time = timestamp()
      environment  = var.environment
    }))
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "auto_scaling" {
  name = "auto-scaling-trigger"
}

# Cloud Scheduler for daily budget maintenance
resource "google_cloud_scheduler_job" "budget_maintenance" {
  name             = "daily-budget-maintenance"
  description      = "Daily budget maintenance and cleanup"
  schedule         = "0 0 * * *"
  time_zone        = "UTC"
  attempt_deadline = "600s"
  
  retry_config {
    retry_count = 1
  }
  
  pubsub_target {
    topic_name = google_pubsub_topic.budget_maintenance.id
    data       = base64encode(jsonencode({
      trigger_time = timestamp()
      environment  = var.environment
    }))
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_pubsub_topic" "budget_maintenance" {
  name = "daily-budget-maintenance"
}

# Secret Manager for sensitive configuration
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret" "assistant_id" {
  secret_id = "openai-assistant-id"
  
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret" "firebase_token" {
  secret_id = "firebase-deployment-token"
  
  replication {
    automatic = true
  }
}

# IAM roles for Cloud Functions
resource "google_service_account" "cloud_functions" {
  account_id   = "cloud-functions-sa"
  display_name = "ACIM Guide Cloud Functions Service Account"
  description  = "Service account for ACIM Guide Cloud Functions"
}

resource "google_project_iam_member" "cloud_functions_roles" {
  for_each = toset([
    "roles/firestore.user",
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter",
    "roles/secretmanager.secretAccessor",
    "roles/pubsub.publisher"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_functions.email}"
}

# Firestore database
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  
  depends_on = [google_project_service.required_apis]
}

# Storage bucket for Terraform state (if not exists)
resource "google_storage_bucket" "terraform_state" {
  name          = "${var.project_id}-terraform-state"
  location      = var.region
  force_destroy = false
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# GitHub Actions service account for CI/CD
resource "google_service_account" "github_actions" {
  account_id   = "github-actions-sa"
  display_name = "GitHub Actions Service Account"
  description  = "Service account for GitHub Actions CI/CD"
}

resource "google_project_iam_member" "github_actions_roles" {
  for_each = toset([
    "roles/cloudfunctions.admin",
    "roles/firebase.admin",
    "roles/storage.admin",
    "roles/secretmanager.secretAccessor",
    "roles/monitoring.editor",
    "roles/logging.admin"
  ])
  
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Service account key for GitHub Actions
resource "google_service_account_key" "github_actions_key" {
  service_account_id = google_service_account.github_actions.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# Cost control - quota on Cloud Functions invocations
resource "google_service_usage_consumer_quota_override" "cloud_functions_requests" {
  provider       = google-beta
  project        = var.project_id
  service        = "cloudfunctions.googleapis.com"
  metric         = "cloudfunctions.googleapis.com/function/execution_count"
  limit          = "/d/project"
  override_value = "2000000" # 2M requests per day
  
  force = true
  
  depends_on = [google_project_service.required_apis]
}

# Monitoring workspace
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notification Channel"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
  
  lifecycle {
    prevent_destroy = true
  }
}

# Custom metrics for token usage
resource "google_logging_metric" "openai_token_usage" {
  name   = "openai_daily_tokens"
  filter = "resource.type=\"cloud_function\" AND textPayload:\"Token usage recorded\""
  
  metric_descriptor {
    metric_kind = "GAUGE"
    value_type  = "INT64"
    unit        = "1"
    labels {
      key         = "user_id"
      value_type  = "STRING"
      description = "User ID"
    }
  }
  
  label_extractors = {
    user_id = "EXTRACT(jsonPayload.userId)"
  }
  
  value_extractor = "EXTRACT(jsonPayload.tokensOut)"
}

# Log sink for cost analysis
resource "google_logging_project_sink" "cost_analysis_sink" {
  name                   = "cost-analysis-sink"
  destination            = "storage.googleapis.com/${google_storage_bucket.cost_analysis.name}"
  filter                 = "resource.type=\"cloud_function\" AND (textPayload:\"Token usage recorded\" OR textPayload:\"Auto-scaling\")"
  unique_writer_identity = true
}

resource "google_storage_bucket" "cost_analysis" {
  name          = "${var.project_id}-cost-analysis"
  location      = var.region
  force_destroy = false
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket_iam_member" "cost_analysis_writer" {
  bucket = google_storage_bucket.cost_analysis.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.cost_analysis_sink.writer_identity
}

# Outputs
output "monitoring_dashboard_url" {
  description = "URL to the monitoring dashboard"
  value       = "https://console.cloud.google.com/monitoring/dashboards/custom/${module.firebase_monitoring.dashboard_id}?project=${var.project_id}"
}

output "budget_alert_channel_id" {
  description = "Notification channel ID for budget alerts"
  value       = module.firebase_monitoring.notification_channel_id
}

output "github_actions_key" {
  description = "Service account key for GitHub Actions (base64 encoded)"
  value       = google_service_account_key.github_actions_key.private_key
  sensitive   = true
}

output "project_setup_complete" {
  description = "Confirmation that the project setup is complete"
  value = {
    project_id              = var.project_id
    environment            = var.environment
    monitoring_enabled     = true
    auto_scaling_enabled   = true
    budget_control_enabled = true
    cicd_configured       = true
  }
}

# Data sources for existing resources
data "google_project" "current" {
  project_id = var.project_id
}

data "google_billing_account" "account" {
  billing_account = var.billing_account
}
