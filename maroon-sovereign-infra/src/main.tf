# =============================================================================
# Maroon Sovereign Infrastructure — Terraform IaC (v4.0)
# Codex §4.5: Full GCP infrastructure provisioning.
# VPC networking, GKE clusters, Cloud SQL, BigQuery, GCS.
# Environment separation: dev / staging / prod.
# =============================================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "maroon-terraform-state"
    prefix = "sovereign-infra"
  }
}

# =============================================================================
# Variables
# =============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "maroon-clean-up"
}

variable "region" {
  description = "Primary GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "gke_node_count" {
  description = "Number of GKE nodes per zone"
  type        = number
  default     = 2
}

variable "gke_machine_type" {
  description = "GKE node machine type"
  type        = string
  default     = "e2-standard-4"
}

locals {
  env_prefix  = "maroon-${var.environment}"
  network_name = "${local.env_prefix}-vpc"
  gke_name    = "${local.env_prefix}-cluster"
}

# =============================================================================
# Provider
# =============================================================================

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# =============================================================================
# VPC Network
# =============================================================================

resource "google_compute_network" "main" {
  name                    = local.network_name
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "primary" {
  name          = "${local.env_prefix}-subnet-primary"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.main.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.4.0.0/14"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.8.0.0/20"
  }

  private_ip_google_access = true
}

resource "google_compute_firewall" "allow_internal" {
  name    = "${local.env_prefix}-allow-internal"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
}

resource "google_compute_firewall" "allow_health_checks" {
  name    = "${local.env_prefix}-allow-health-checks"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "8000-9000"]
  }

  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
}

# =============================================================================
# GKE Cluster
# =============================================================================

resource "google_container_cluster" "primary" {
  name     = local.gke_name
  location = var.region

  network    = google_compute_network.main.name
  subnetwork = google_compute_subnetwork.primary.name

  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  release_channel {
    channel = var.environment == "prod" ? "STABLE" : "REGULAR"
  }

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]
  }
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "${local.gke_name}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.gke_node_count

  node_config {
    machine_type = var.gke_machine_type
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    labels = {
      environment = var.environment
      managed_by  = "terraform"
      ecosystem   = "maroon"
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  autoscaling {
    min_node_count = 1
    max_node_count = var.environment == "prod" ? 10 : 4
  }
}

# =============================================================================
# Cloud SQL (PostgreSQL) — Shared Database Backend
# =============================================================================

resource "google_sql_database_instance" "main" {
  name             = "${local.env_prefix}-postgres"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier              = var.environment == "prod" ? "db-custom-4-16384" : "db-f1-micro"
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_autoresize   = true
    disk_size         = 20

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = var.environment == "prod"
      start_time                     = "03:00"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main.id
    }

    database_flags {
      name  = "max_connections"
      value = var.environment == "prod" ? "200" : "50"
    }
  }

  deletion_protection = var.environment == "prod"
}

# Per-service databases
resource "google_sql_database" "databases" {
  for_each = toset([
    "compliance_core",
    "palantir_lake",
    "safe_space",
    "market_core",
    "market_logistics",
    "medical_diagnostics",
    "pac_core",
    "real_estate",
    "law_finance",
  ])

  name     = each.value
  instance = google_sql_database_instance.main.name
}

# =============================================================================
# Cloud Storage — Media, HLS Segments, OSINT Output
# =============================================================================

resource "google_storage_bucket" "media" {
  name     = "${local.env_prefix}-media-assets"
  location = var.region

  uniform_bucket_level_access = true
  force_destroy               = var.environment != "prod"

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }
}

resource "google_storage_bucket" "hls_segments" {
  name     = "${local.env_prefix}-hls-segments"
  location = var.region

  uniform_bucket_level_access = true
  force_destroy               = var.environment != "prod"
}

resource "google_storage_bucket" "osint_output" {
  name     = "${local.env_prefix}-osint-output"
  location = var.region

  uniform_bucket_level_access = true
  force_destroy               = true
}

resource "google_storage_bucket" "terraform_state" {
  name     = "maroon-terraform-state"
  location = var.region

  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

# =============================================================================
# BigQuery — Analytics & ML Feature Store
# =============================================================================

resource "google_bigquery_dataset" "palantir_gold" {
  dataset_id = "${replace(local.env_prefix, "-", "_")}_palantir_gold"
  location   = var.region

  labels = {
    environment = var.environment
    layer       = "gold"
  }
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id = "${replace(local.env_prefix, "-", "_")}_analytics"
  location   = var.region

  labels = {
    environment = var.environment
    purpose     = "business_intelligence"
  }
}

# =============================================================================
# Artifact Registry — Container Images
# =============================================================================

resource "google_artifact_registry_repository" "containers" {
  location      = var.region
  repository_id = "${local.env_prefix}-containers"
  format        = "DOCKER"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

# =============================================================================
# Outputs
# =============================================================================

output "gke_cluster_name" {
  value = google_container_cluster.primary.name
}

output "gke_cluster_endpoint" {
  value     = google_container_cluster.primary.endpoint
  sensitive = true
}

output "postgres_connection" {
  value     = google_sql_database_instance.main.connection_name
  sensitive = true
}

output "media_bucket" {
  value = google_storage_bucket.media.name
}

output "hls_bucket" {
  value = google_storage_bucket.hls_segments.name
}

output "artifact_registry" {
  value = google_artifact_registry_repository.containers.name
}
