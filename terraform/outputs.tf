output "repository_url" {
  description = "The Artifact Registry Docker repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.backend_repo.repository_id}"
}

output "backend_url" {
  description = "The public URL of the deployed FastAPI backend service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "service_account_email" {
  description = "The Service Account email used by Cloud Run"
  value       = google_service_account.cloud_run_sa.email
}
