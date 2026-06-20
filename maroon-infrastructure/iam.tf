# ---------------------------------------------------------
# The Zero-Trust IAM Policy (Phase 4 Cut-Over)
# ---------------------------------------------------------

# The Dedicated Cluster Service Account
resource "google_service_account" "cluster_sa" {
  account_id   = "maroon-matrix-node-sa"
  display_name = "Maroon Matrix Node Service Account"
}

# Grant the cluster access to pull Docker images from Artifact Registry
resource "google_project_iam_member" "cluster_sa_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.cluster_sa.email}"
}

# Grant the cluster access to write to Cloud Logging and Monitoring
resource "google_project_iam_member" "cluster_sa_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cluster_sa.email}"
}

resource "google_project_iam_member" "cluster_sa_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.cluster_sa.email}"
}

# ---------------------------------------------------------
# Identity Cut-Over: Anchoring the new API Admin
# ---------------------------------------------------------
# We explicitly bind the api@maroontechnologies.org identity as the absolute owner
# of the Kubernetes infrastructure.

resource "google_project_iam_member" "api_admin_cluster_admin" {
  project = var.project_id
  role    = "roles/container.admin"
  member  = "user:${var.master_admin_email}"
}

resource "google_project_iam_member" "api_admin_project_owner" {
  project = var.project_id
  role    = "roles/owner"
  member  = "user:${var.master_admin_email}"
}

# (Note: In a true cut-over, you would run gcloud commands to explicitly revoke
# maroontemp@gmail.com from the project IAM bindings after this is applied.)
