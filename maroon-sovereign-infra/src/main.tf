###############################################################################
# Maroon Sovereign Infrastructure — Terraform IaC (v4.0)
# Codex §4.5: Full GCP provisioning with environment separation.
###############################################################################

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "maroon-terraform-state"
    prefix = "sovereign-infra"
  }
}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "maroon-sovereign-infra"
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
    error_message = "Must be dev, staging, or prod."
  }
}

# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

provider "google" {
  project = var.project_id
  region  = var.region
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------

resource "google_compute_network" "vpc" {
  name                    = "maroon-${var.environment}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "services" {
  name          = "maroon-${var.environment}-services"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/20"
  }
}

resource "google_compute_firewall" "allow_internal" {
  name    = "maroon-${var.environment}-allow-internal"
  network = google_compute_network.vpc.name
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  source_ranges = ["10.0.0.0/8"]
}

# ---------------------------------------------------------------------------
# GKE Cluster (Kubernetes for all microservices)
# ---------------------------------------------------------------------------

resource "google_container_cluster" "primary" {
  name     = "maroon-${var.environment}-gke"
  location = var.region

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.services.name

  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "maroon-${var.environment}-nodes"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.environment == "prod" ? 3 : 1

  node_config {
    machine_type = var.environment == "prod" ? "e2-standard-4" : "e2-medium"
    disk_size_gb = 50
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

# ---------------------------------------------------------------------------
# Cloud SQL (PostgreSQL for Palantir Lake)
# ---------------------------------------------------------------------------

resource "google_sql_database_instance" "palantir_db" {
  name             = "maroon-${var.environment}-palantir"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = var.environment == "prod" ? "db-custom-4-16384" : "db-f1-micro"
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"

    database_flags {
      name  = "max_connections"
      value = "200"
    }

    backup_configuration {
      enabled = true
    }
  }
}

resource "google_sql_database" "palantir_lake" {
  name     = "palantir_lake"
  instance = google_sql_database_instance.palantir_db.name
}

# ---------------------------------------------------------------------------
# BigQuery (Gold Layer Analytics)
# ---------------------------------------------------------------------------

resource "google_bigquery_dataset" "palantir_gold" {
  dataset_id    = "palantir_gold_${var.environment}"
  friendly_name = "Palantir Gold Layer — ${var.environment}"
  description   = "Aggregated analytics and ML feature stores."
  location      = "US"
}

# ---------------------------------------------------------------------------
# Cloud Storage (Media, HLS segments, backups)
# ---------------------------------------------------------------------------

resource "google_storage_bucket" "media" {
  name          = "maroon-${var.environment}-media"
  location      = "US"
  force_destroy = var.environment != "prod"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition { age = 90 }
    action { type = "SetStorageClass" storage_class = "COLDLINE" }
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "gke_cluster_name" {
  value = google_container_cluster.primary.name
}

output "db_connection_name" {
  value = google_sql_database_instance.palantir_db.connection_name
}

output "media_bucket" {
  value = google_storage_bucket.media.url
}
