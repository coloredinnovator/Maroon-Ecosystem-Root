terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# ---------------------------------------------------------
# NASA-Grade Control Plane: The Kubernetes Cluster
# ---------------------------------------------------------
resource "google_container_cluster" "maroon_matrix" {
  name     = "maroon-microservice-matrix"
  location = var.region

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  # Network Policies for Zero-Trust Inter-pod communication
  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  release_channel {
    channel = "REGULAR"
  }

  # Workload Identity for seamless GCP service access without raw keys
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
}

resource "google_container_node_pool" "maroon_nodes" {
  name       = "maroon-engine-pool"
  location   = var.region
  cluster    = google_container_cluster.maroon_matrix.name
  node_count = 3

  node_config {
    preemptible  = false
    machine_type = "e2-standard-4" # Sufficient for Palantir Lake embeddings and LangGraph reasoning

    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    service_account = google_service_account.cluster_sa.email
    oauth_scopes    = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}
