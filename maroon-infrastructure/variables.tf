variable "project_id" {
  description = "The ID of the Google Cloud Project hosting Maroon Technologies"
  type        = string
}

variable "region" {
  description = "The default GCP region for the clusters"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The default GCP zone for the clusters"
  type        = string
  default     = "us-central1-a"
}

variable "master_admin_email" {
  description = "The absolute sovereign admin email for the infrastructure"
  type        = string
  default     = "api@maroontechnologies.org"
}
